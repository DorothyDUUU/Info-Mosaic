from atexit import register
from uuid import uuid4
from typing import Dict, Callable
from openai import OpenAI
import json
import requests
import time
import traceback
from tool_manager import StreamToolManager, execute_code
from utils import register_forward, BenchArgs


# OpenAI API配置
base_url = os.getenv("OPENAI_API_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")


serper_api_key = "768ccc7aff19e8d4bd416a2c961b2fbe8f7a8ead"

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

    return serper_google_search(key_word, serper_api_key, 10, "us", "en")


def execute_python_code(code: str) -> str:
    """在沙盒中执行Python代码"""
    tool_manager = StreamToolManager(url="sandbox_url", session_id=str(uuid4()), timeout=1800)
    outputs, tool_stats = execute_code(code, tool_manager)
    return outputs


# tool_functions = {
#     "Python_code_interpreter":execute_python_code
# }


def call_model(
    system_prompt: str,
    user_prompt: str,
    tools: list = [],
    tool_functions: Dict[str, Callable] = {},
    model_name: str = "gpt-5",
    max_tool_calls: int = 20,
    user_template: str = "You are a helpful assistant. Please answer the question based on the following information: {information}\n You can use the web_search tool to get more information."
) -> str:
    """调用GPT模型并处理工具调用
    
    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        tools: 可用的工具列表
        tool_functions: 工具名称到实现函数的映射
        model_name: 模型名称
        max_tool_calls: 最大工具调用次数
        user_template: 用户提示词模板
        
    Returns:
        str: 模型的最终回答
    """
    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_template.format(information=user_prompt)}
    ]
    
    num_tool_calls = 0
    while True:
        if num_tool_calls >= max_tool_calls:
            messages.append({
                "role": "system",
                "content": "You have reached the maximum number of tool calls. Please provide your final answer without using tools."
            })
            completion = client.chat.completions.create(
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
    return content, num_tool_calls

@register_forward([
    'gpt5_multi_tool'
])
def forward(args:BenchArgs, item:Dict[str, str]):
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
    model_name = 'gpt-5-2025-08-07'
    max_tool_calls = 20
    user_template = args.user_template

    response, num_tool_calls = call_model(
        system_prompt=args.system_prompt,
        user_prompt=query,
        tools=tools,
        tool_functions=tool_functions,
        model_name=model_name,
        max_tool_calls=max_tool_calls,
        user_template=user_template
    )
    item['response'] = response
    item['num_tool_calls'] = num_tool_calls
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
    tool_functions = {"web_search": web_search}
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
        