import argparse
from typing import Callable, Any, Dict, Union
from functools import wraps
from openai import OpenAI
import traceback
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from concurrent.futures import Future
import traceback

class ArgparseArgs(argparse.Namespace):
    model_name:str 
    system_prompt:str
    parallel_size:int
    api_base:str
    api_key:str
    max_tokens:int
    temperature:float
    timeout:int
    retry:int
    filter_think:bool


class BenchArgs:
    def __init__(self, 
            model_name:str=None, system_prompt:str=None, parallel_size:int=None,
            api_base:str=None, api_key:str=None, max_tokens:int=None, 
            temperature:float=None, timeout:int=None, retry:int=None,
            filter_think:bool=True, domain:str=None
        ):
        self.model_name:str =  model_name
        self.system_prompt:str = system_prompt
        self.parallel_size:int = parallel_size
        self.api_base:str = api_base
        self.api_key:str = api_key
        self.max_tokens:int = max_tokens
        self.temperature:float = temperature
        self.timeout:int = timeout
        self.retry:int = retry
        self.filter_think:bool = filter_think
        self.domain:str = domain
    def load_param(self, args:ArgparseArgs):
        self.model_name:str =  args.model_name
        self.system_prompt:str = args.system_prompt
        self.parallel_size:int = args.parallel_size
        self.api_base:str = args.api_base
        self.api_key:str = args.api_key
        self.max_tokens:int = args.max_tokens
        self.temperature:float = args.temperature
        self.timeout:int = args.timeout
        self.retry:int = args.retry
        self.filter_think:bool = args.filter_think
        self.domain:str = args.domain
    def __str__(self):
        return (f"BenchArgs(\n"
                f"  model_name={self.model_name},\n"
                f"  system_prompt={self.system_prompt},\n"
                f"  parallel_size={self.parallel_size},\n"
                f"  api_base={self.api_base},\n"
                f"  api_key={self.api_key},\n"
                f"  max_tokens={self.max_tokens},\n"
                f"  temperature={self.temperature},\n"
                f"  timeout={self.timeout},\n"
                f"  retry={self.retry},\n"
                f"  filter_think={self.filter_think}\n"
                f"  domain={self.domain}\n"
                f")")


class JudgeArgs:
    def __init__(self):
        pass

def filter_think(response:str):
    end_pos = response.find('</think>')
    if end_pos != -1:
        response = response[end_pos + len('</think>'):].strip()
    else:
        response = response.strip()
    return response

def call_model(args:BenchArgs, item:Dict[str, str]):
    client = OpenAI(base_url=args.api_base, api_key=args.api_key)

    try:
        response = client.chat.completions.create(
            model=args.model_name,
            messages=[
                {"role": "system", "content": args.system_prompt},
                {"role": "user", "content": f"{item['query']}"},
            ],
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout
        )
        response = response.choices[0].message.content
        if args.filter_think:  # 根据全局参数决定是否过滤
            response = filter_think(response)
    except Exception as e:
        print(f"{e}\n\n{traceback.format_exc()}")
        response = ""

    item['response'] = response
    return item


# 存储模型与 forward 函数的映射
_forward_registry = {}
_reward_registry = {}

# 注册函数的装饰器
def register_forward(model_name: Union[str, Iterable[str]]):
    
    def decorator(func: Callable):
        names = [model_name] if isinstance(model_name, str) else model_name
        if not names or not all(isinstance(name, str) for name in names):
            raise ValueError("model_names must be a non-empty string or iterable of strings")
        for name in names:
            _forward_registry[name] = func
        return func
    return decorator

def forward(model_name: str, args: BenchArgs, item: Dict[str, str]) -> Any:
    timeout = args.timeout
    max_retry = args.retry

    def call_with_timeout():
        if model_name not in _forward_registry:
            print(f"DEBUG: Model {model_name} not found in registry, using call_model (SINGLE DOMAIN)")
            return call_model(args, item)
        
        print(f"DEBUG: Found model {model_name} in registry, calling registered function (MULTI DOMAIN)")
        tmp_item = _forward_registry[model_name](args, item)
        if args.filter_think:  # 根据全局参数决定是否过滤
            response = filter_think(tmp_item['response'])
            tmp_item['response'] = response
        return tmp_item
        
            
    # print(timeout, max_retry)
    for attempt in range(1, max_retry + 1):
        # print(f"attempt {attempt}")
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call_with_timeout)
            try:
                tmp_item = future.result(timeout=timeout)
                return tmp_item
            except FuturesTimeoutError:
                err_msg = f"timeout on attempt {attempt}, detail: {traceback.format_exc()}"
                print(f"ERROR: {err_msg}")
                # 即使超时也返回超时内容
                item['response'] = f"Timeout on attempt {attempt}: Request exceeded the time limit of {timeout} seconds"
                raise FuturesTimeoutError(err_msg)
                # return item
            except Exception as e:
                err_msg = f"error on attempt {attempt}: {e}, detail: {traceback.format_exc()}"
                print(f"ERROR: {err_msg}")
                raise FuturesError(err_msg)

    item['response'] = f"there is some error after {max_retry} retries: {err_msg}"
    return item   



def register_reward(model_name: Union[str, Iterable[str]]):
    
    def decorator(func: Callable):
        names = [model_name] if isinstance(model_name, str) else model_name
        if not names or not all(isinstance(name, str) for name in names):
            raise ValueError("model_names must be a non-empty string or iterable of strings")
        for name in names:
            _reward_registry[name] = func
        return func
    return decorator

def reward(reward_name: str, item: Dict[str, str], judge_config:Dict[str, Any]) -> Any:

    timeout = judge_config['timeout']
    max_retry = judge_config['retry']

    # print(_reward_registry)

    def call_with_timeout():
        if reward_name not in _reward_registry:
            # return call_model(args, item)
            func = _reward_registry['default']
        else:
            func = _reward_registry[reward_name]
        
        tmp_item = func(item, judge_config)
        
        return tmp_item
        
            
    # print(timeout, max_retry)
    for attempt in range(1, max_retry + 1):
        # print(f"attempt {attempt}")
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call_with_timeout)
            try:
                tmp_item = future.result(timeout=timeout)
                return tmp_item
            except FuturesTimeoutError:
                err_msg = f"timeout on attempt {attempt}, detail: {traceback.format_exc()}"
            except Exception as e:
                err_msg = f"error on attempt {attempt}: {e}, detail: {traceback.format_exc()}"

    item['evaluation'] = f"there is some error after {max_retry} retries: {err_msg}"
    return item
