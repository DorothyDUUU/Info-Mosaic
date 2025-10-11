from atexit import register
from uuid import uuid4
from typing import Dict, Callable
from openai import OpenAI
import json
import requests
import time
import traceback
from inference.tool_manager import StreamToolManager
from utils import register_forward, BenchArgs
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
import os
from inference.model_forwards.multitool_utils import convert_tools_to_schema_list, load_json, dict_to_args_str



# OpenAI API Configuration
serper_api_key = os.getenv("SERPER_API_KEY")
base_url = os.getenv("BASE_URL")
api_key = os.getenv("API_KEY")

base_manager = StreamToolManager(url="http://localhost:30010", timeout=1800)


def exec_code(code_snippet:str):
    base_manager.session_id = str(uuid4())
#     test_code = """results = gene_getter(gene_id_or_symbol="SMARCAL1")
# # print(results)"""
    print(f"executing code: {code_snippet} ")
    result = base_manager.execute_tool(code_snippet)    
    output_value, error_value = result['output'], result['error']
    code_result_content = output_value if not error_value else error_value
    return code_result_content


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

def _llm_call_with_timeout(client, timeout_sec, **kwargs):
    def _invoke():
        return client.chat.completions.create(**kwargs)

    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(_invoke)
        try:
            return fut.result(timeout=timeout_sec)
        except FuturesTimeout:
            # Simulate a normal message object with timeout information
            return type("DummyResp", (), {
                "choices": [
                    type("DummyChoice", (), {
                        "message": {
                            "role": "assistant",
                            "content": f"⚠️ 模型调用超时（>{timeout_sec}s），请稍后重试。"
                        },
                        "finish_reason": "stop"
                    })
                ]
            })()
        except Exception as e:
            return type("DummyResp", (), {
                "choices": [
                    type("DummyChoice", (), {
                        "message": {
                            "role": "assistant",
                            "content": f"⚠️ 模型调用失败：{e}"
                        },
                        "finish_reason": "stop"
                    })
                ]
            })()

def call_model(
    system_prompt: str,
    user_prompt: str,
    tools: list = [],
    # tool_functions: Dict[str, Callable] = {},
    model_name: str = "gpt-5",
    max_tool_calls: int = 20,
    max_tokens: int = 4096,
    base_url: str = base_url,
    api_key: str = api_key,
    user_template: str = "Please answer the question:\n INFORMARION\n # Notic: - You can use the provided tools to get more information.\n - You should provide all information for answering every subqueries in the question in the last sentence and illustrate your reasoning process for these subquestions in the end, rather than a single answer.\n # Output Format: [Your subanswer to each subquestion if there is]\n [Your Final Answer]",
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
                # 清理函数名中的非打印字符
                clean_func_name = tool_call.function.name.replace('\u00a0', ' ')
                clean_func_name = ''.join(c for c in clean_func_name if c.isprintable() or c in '\t\n\r')
                code_snippest = "print("+ clean_func_name + dict_to_args_str(call_args) + ")"

                result = exec_code(code_snippest)
                print(f"Execution Results: {result}")


                # result = tool_functions[tool_call.function.name](**call_args)
            except Exception as e:
                result = traceback.format_exc()

            print(f"Tool Call: {tool_call.function.name} with arguments {call_args} -> {result}")
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
    'agent_w_multi_tool'
])
def forward(args, item:Dict[str, str]):
    query = item['query']
    tool_meta_data_path = "inference/configs/tool_metata.json"
    tool_meta_data = load_json(tool_meta_data_path)
    domain = args.domain
    if domain == "multidomain" or domain == 'all':
        selected_tools = tool_meta_data
    else:
        selected_tools = []
        for tool_item in tool_meta_data:
            if tool_item["domain"] == domain:
                selected_tools.append(tool_item)
    
    tools = convert_tools_to_schema_list(selected_tools)

    model_name = args.llm_name
    max_tool_calls = args.max_tool_calls    

    response, num_tool_calls, messages = call_model(
        system_prompt=args.system_prompt,
        user_prompt=query,
        tools=tools,
        # tool_functions=tool_functions,
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
    user_prompt = "A young child presents with growth failure, vertebral and epiphyseal skeletal dysplasia, and frequent infections. Lab studies show persistent proteinuria unresponsive to corticosteroids and decreased CD3+ T cells. Genetic analysis reveals a homozygous mutation in a SWI/SNF chromatin remodeling gene located on an autosome (non-sex chromosome) with autosomal recessive inheritance. A current Phase I trial is assessing the efficacy of sequential CAR-T cell therapy followed by dual transplantation procedures. What is the most likely diagnosis?"
    tool_meta_data_path = "./configs/tool_metata.json"
    tool_meta_data = load_json(tool_meta_data_path)



    domain = "bio"
    selected_tools = []
    for item in tool_meta_data:
        if item["domain"] == domain:
            selected_tools.append(item)
    tools = convert_tools_to_schema_list(selected_tools)

    
    result, num_tool_calls, planner_metadata = call_model(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        tools=tools,
        # tool_functions=tool_functions,
        model_name="gpt-5-2025-08-07",
        max_tool_calls=20,
    )
    print(result)
    print(num_tool_calls)
        