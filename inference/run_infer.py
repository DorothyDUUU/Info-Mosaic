import os
import argparse
from uuid import uuid4
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from openai import OpenAI
import traceback
from typing import List, Dict
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import ArgparseArgs, BenchArgs, filter_think, forward
import model_forwards

def load_data(domain, model_name, llm_name, output_data_path):
    input_data_path = 'data/info_mosaic_w_gt.jsonl'

    total_data = []
    with open(input_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                total_data.append(json.loads(line))

    # filter data
    if domain == 'all':
        data = total_data
    else:
        data = [item for item in total_data if item['domain'] == domain]

    # resume data
    print(f"Save to {output_data_path}")
    os.makedirs(os.path.dirname(output_data_path), exist_ok=True)

    if os.path.exists(output_data_path):
        with open(output_data_path, 'r', encoding='utf-8') as f:
            processed_data = f.readlines()
        processed_queries = {json.loads(obj)['query']: 1 for obj in processed_data}
        print(f"==> {args.model_name} has processed {len(processed_data)} items")
        data = [item for item in data if item['query'] not in processed_queries]
    return data

def infer(args:BenchArgs):
    output_data_path = f'output/{args.model_name}/{args.llm_name}/{args.domain}.jsonl'
    data = load_data(args.domain, args.model_name, args.llm_name, output_data_path)
    lookup_table = {obj['query']:0 for obj in data}
   
    need_process_data = [item for item in data if not lookup_table[item['query']]]
    print(f"==> processing {args.model_name}_{args.llm_name}, {len(need_process_data)} need to process...")

    with ThreadPoolExecutor(max_workers=args.parallel_size) as executor:
        futures = [executor.submit(forward, args.model_name, args, item) for item in need_process_data]

        for future in tqdm(as_completed(futures), total=len(need_process_data), desc="processing"):
            result = future.result()
            if result:  # check result is not None
                with open(output_data_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--model_name', type=str, default=f'NQ-TEST-{uuid4()}')
    parser.add_argument('--system_prompt', type=str, default="You are a helpful assistant")
    parser.add_argument('--user_template', type=str, default="You are a helpful assistant. Please answer the question based on the following information: $information$\n You can use the web_search tool to get more information.\n You should provide all information for answering every subqueries in the question and illustrate your reasoning process for these subquestions in the end, rather than a single answer.")
    parser.add_argument('--finish_template', type=str, default="You have reached the maximum number of tool calls. Please provide your final answer according to the above tool usage results and answer the question anyway.\n Remember you should provide all information for answering every subqueries in the question rather than a single answer.")
    parser.add_argument('--parallel_size', type=int, default=1)
    parser.add_argument('--api_base', type=str, default='')
    parser.add_argument('--api_key', type=str, default='EMPTY')
    parser.add_argument('--max_tokens', type=int, default=4096)
    parser.add_argument('--temperature', type=float, default=0.0)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--max_tool_calls', type=int, default=20)
    parser.add_argument('--domain', type=str, default='multidomain')
    parser.add_argument('--llm_name', type=str, default='gpt-5-2025-08-07')
    parser.add_argument('--retry', type=int, default=3)
    parser.add_argument('--filter_think', type=bool, default=False)
    
    args = parser.parse_args()

    infer(args=args)
