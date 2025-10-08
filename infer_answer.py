import os
import argparse
from uuid import uuid4
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from openai import OpenAI
import traceback
from typing import List, Dict
from utils import ArgparseArgs, BenchArgs, filter_think, forward




def get_data_paths(current_dir, sub_path="", filename="critic_master_slave_en_advance.jsonl"):
    """获取数据路径的通用函数"""
    generation_path = os.path.join(current_dir, '..', 'output', 'generation', sub_path, filename)
    answer_generation_path = os.path.join(current_dir, '..', 'output', 'answer_generation', sub_path)
    return generation_path, answer_generation_path

def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 使用通用函数获取路径
    browse_json_path, _ = get_data_paths(current_dir)
    
    data = []
    with open(browse_json_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def infer(args:BenchArgs):

    data = load_data()
    lookup_table = {obj['query']:0 for obj in data}

    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 使用通用函数获取路径
    _, output_jsonl_dir = get_data_paths(current_dir)
    os.makedirs(output_jsonl_dir, exist_ok=True)
    output_jsonl_path = os.path.join(output_jsonl_dir, f"{args.model_name}.jsonl")
    print(f"Save to {output_jsonl_path}")

    if os.path.exists(output_jsonl_path):
        with open(output_jsonl_path, 'r', encoding='utf-8') as f:
            processed_data = f.readlines()
        for obj in processed_data:
            lookup_table[json.loads(obj)['query']] = 1 
    
    need_process_data = [item for item in data if not lookup_table[item['query']]]
    print(f"==> processing {args.model_name}, {len(need_process_data)} need to process...")

    # for item in tqdm(need_process_data, desc="processing"):
    #     result = forward(args.model_name, args, item)
    #     if result:
    #         with open(output_jsonl_path, 'a', encoding='utf-8') as f:
    #             f.write(json.dumps(result, ensure_ascii=False) + '\n')
    #             f.flush()

    with ThreadPoolExecutor(max_workers=args.parallel_size) as executor:
        futures = [executor.submit(forward, args.model_name, args, item) for item in need_process_data]

        for future in tqdm(as_completed(futures), total=len(need_process_data), desc="processing"):
            result = future.result()
            if result:  # 确保 result 不是 None
                with open(output_jsonl_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f.flush()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--model_name', type=str, default=f'NQ-TEST-{uuid4()}')
    parser.add_argument('--system_prompt', type=str, default="You are a helpful assistant")
    parser.add_argument('--parallel_size', type=int, default=1)
    parser.add_argument('--api_base', type=str, default='')
    parser.add_argument('--api_key', type=str, default='EMPTY')
    parser.add_argument('--max_tokens', type=int, default=4096)
    parser.add_argument('--temperature', type=float, default=0.0)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--retry', type=int, default=3)
    parser.add_argument('--user_template', type=str, default="")
    parser.add_argument('--filter_think', type=bool, default=False)
    parser.add_argument('--domain', type=str, default="web")


    args:ArgparseArgs = parser.parse_args(namespace=ArgparseArgs())

    bench_args = BenchArgs()
    bench_args.load_param(args)

    infer(args=bench_args)
