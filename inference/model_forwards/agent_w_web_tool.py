from atexit import register
from uuid import uuid4
from typing import Dict, Callable
from openai import OpenAI
import json
import requests
import time
import traceback
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tool_manager import StreamToolManager
from utils import register_forward, BenchArgs
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout


# OpenAI API Configuration
serper_api_key = os.getenv("SERPER_API_KEY")
base_url = os.getenv("BASE_URL")
api_key = os.getenv("API_KEY")

def serper_google_search(query, serper_api_key, top_k, region, lang, depth=0):
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": top_k,
        "gl": region,
        "hl": lang,
        "location": "United States"
    }
    headers = {
        'X-API-KEY': serper_api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}")

        data = response.json()
        data.pop('searchParameters', None)
        data.pop('credits', None)

        if not data:
            raise Exception("The google search API is temporarily unavailable, please try again later.")
        return data

    except Exception as e:
        if depth < 3:
            time.sleep(1)
            return serper_google_search(query, serper_api_key, top_k, region, lang, depth=depth + 1)
        print(f"search failed: {e}")
        print(traceback.format_exc())
        return []
    
def web_search(key_word:str):
    # Ensure to re-acquire serper_api_key from environment variables
    current_api_key = os.getenv("SERPER_API_KEY")
    if not current_api_key:
        print("Warning: SERPER_API_KEY environment variable is not set, using fallback value")
        # Here you can set a default value or use a passed fallback value
    return serper_google_search(key_word, current_api_key or serper_api_key, 10, "us", "en")

def _llm_call_with_timeout(client, timeout_sec, **kwargs):
    # Define an inner function to invoke the chat completion creation
    def _invoke():
        return client.chat.completions.create(**kwargs)

    # Use a thread pool executor with a single worker
    with ThreadPoolExecutor(max_workers=1) as ex:
        # Submit the invocation task to the executor
        fut = ex.submit(_invoke)
        try:
            # Wait for the task to complete within the specified timeout
            return fut.result(timeout=timeout_sec)
        except FuturesTimeout:
            # Simulate a normal message object with a timeout message
            return type("DummyResp", (), {
                "choices": [
                    type("DummyChoice", (), {
                        "message": {
                            "role": "assistant",
                            "content": f"⚠️  Model call timed out (>{timeout_sec}s), please try again later."
                        },
                        "finish_reason": "stop"
                    })
                ]
            })()
        except Exception as e:
            # Simulate a normal message object with a failure message
            return type("DummyResp", (), {
                "choices": [
                    type("DummyChoice", (), {
                        "message": {
                            "role": "assistant",
                            "content": f"⚠️  Model call failed: {e}"
                        },
                        "finish_reason": "stop"
                    })
                ]
            })()

def call_model(
    system_prompt: str,
    user_prompt: str,
    tools: list = [],
    tool_functions: Dict[str, Callable] = {},
    model_name: str = "gpt-5",
    max_tool_calls: int = 20,
    max_tokens: int = 4096,
    base_url: str = base_url,
    api_key: str = api_key,
    user_template: str = "Please answer the question:\n INFORMARION\n You can use the web_search tool to get more information.\n You should provide all information for answering every subqueries in the question and illustrate your reasoning process for these subquestions in the end, rather than a single answer.",
    finish_template: str = "You have reached the maximum number of tool calls. Please provide your final answer according to the above tool usage results and answer the question anyway.\n Remember you should provide all information for answering every subqueries in the question rather than a single answer.",
    timeout: int = 300
) -> str:
    """Call GPT model and handle tool calls
    
    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        tools: List of available tools
        tool_functions: Mapping from tool names to implementation functions
        model_name: Model name
        max_tool_calls: Maximum number of tool calls
        max_tokens: Maximum number of tokens
        base_url: API base URL
        api_key: API key    

    Returns:
        str: Final answer from the model
    """

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_template.replace("INFORMARION", user_prompt)}
    ]
    
    num_tool_calls = 0
    while True:
        if num_tool_calls >= max_tool_calls:
            messages.append({
                "role": "system",
                "content": finish_template })
            print(f"messages: {messages}")
            completion = _llm_call_with_timeout(
                    client,
                    timeout_sec=timeout,   # 设定超时秒数
                    model=model_name,
                    messages=messages,
                    tools=tools,
                )
            messages.append(completion.choices[0].message)
            break
        
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
        )
        
        print(f"--------------- num of tool calls: {num_tool_calls} -----------------")
        print(completion.choices[0].message.content)
        print(completion.choices[0].message.tool_calls)
        print("--------------------------------")

        messages.append(completion.choices[0].message)
        
        if completion.choices[0].finish_reason == 'stop':
            break
        
        tool_call_list = completion.choices[0].message.tool_calls

        for tool_call in tool_call_list:
            try:
                call_args = json.loads(tool_call.function.arguments)
                result = tool_functions[tool_call.function.name](**call_args)
            except Exception as e:
                result = traceback.format_exc()

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

        num_tool_calls += 1

    try:
        content = messages[-1].content.strip()
    except Exception as e:
        print(f"error: {e}")
    
    planner_metadata = []
    for msg in messages:
        if isinstance(msg, dict):
            planner_metadata.append(msg)
        elif hasattr(msg, 'model_dump'):
            planner_metadata.append(msg.model_dump())
        else:
            planner_metadata.append(vars(msg))

    return content, num_tool_calls, planner_metadata

@register_forward([
    'agent_w_web_tool'
])
def forward(args, item:Dict[str, str]):
    query = item['query']
    tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "search information from the web.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key_word": {
                                "type": "string",
                                "description": "search keyword",
                            }
                        },
                        "required": ["key_word"],
                        "additionalProperties": False,
                    },
                },
            },
        ]
    tool_functions = {"web_search": web_search}
    model_name = args.llm_name
    max_tool_calls = args.max_tool_calls    

    response, num_tool_calls, messages = call_model(
        system_prompt=args.system_prompt,
        user_prompt=query,
        tools=tools,
        tool_functions=tool_functions,
        model_name=model_name,
        max_tool_calls=max_tool_calls,
        max_tokens=args.max_tokens,
        base_url=args.api_base,
        api_key=args.api_key,
        user_template=args.user_template,
        finish_template=args.finish_template,
        timeout=300,
    )
    item['response'] = response
    item['num_tool_calls'] = num_tool_calls
    item['messages'] = messages

    return item

if __name__ == '__main__':
    
    system_prompt = "You are a helpful assistant."
    user_prompt = "Which researchers rediscovered a frog species last seen in the year Theodore Roosevelt became the first American president to ride in an automobile, in which river basins of the region named after the indigenous people who resisted Spanish conquest in present-day Chile?"
    user_prompt = "What is a village located in a rural district that is part of a county whose capital is Kabudarahang, in Hamadan Province? Additionally, at the 2006 census, it had a population of 168 in 38 families."
    tools = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "search information from the web.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key_word": {
                            "type": "string",
                            "description": "search keyword",
                        }
                    },
                    "required": ["key_word"],
                    "additionalProperties": False,
                },
            },
        }
    ]
    tool_functions = {"web_search":web_search}
    result, num_tool_calls = call_model(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tools=tools,
        tool_functions=tool_functions,
        model_name="gpt-5-2025-08-07",
        max_tool_calls=20,
    )
    print(result)
    print(num_tool_calls)
        