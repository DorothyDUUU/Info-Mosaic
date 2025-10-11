from tenacity import retry, wait_exponential, stop_after_attempt
import random
from openai import OpenAI
import os
import yaml
from typing import Dict, List, Any, Optional, Tuple
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import argparse

def extract_answer(text: str) -> Tuple[str, Optional[str]]:
    """
    返回 (json_block_str, final_answer)
    - json_block_str: 首个 ```json ... ``` 代码块内部的原始字符串；若没有则为空串
    - final_answer: <final_answer>...</final_answer> 的内容；若没有则为 None
    """
    # 1) 抓取首个 ``` 代码块
    m = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        json_block_str = m.group(1).strip()
    else:
        # 可选回退：若没有标注 json 的围栏，就抓第一个 ``` ... ```
        m2 = re.search(r"```+\s*([\s\S]*?)\s*```+", text)
        json_block_str = m2.group(1).strip() if m2 else ""

    # 2) 抓取 <final_answer>...</final_answer>
    fm = re.search(r"<final_answer>\s*([\s\S]*?)\s*</final_answer>", text, re.IGNORECASE)
    final_answer = fm.group(1).strip() if fm else None

    return json_block_str, final_answer

def eval_llm(item, judge_config:Dict[str, Any]):
    model_config = judge_config['judge_model']
    
    ################ 提取答案
    subquestions = '\n'.join([f"Subquestion {index + 1}: {it['condition']}" for index, it in enumerate(item['testcase'])])
    extract_answer_prompt = judge_config['testcase_answer_template'].format(task=item['query'], operated_text=item['response'], testcase=subquestions)

    try:
        answer = call_llm(extract_answer_prompt, model_config)
    except Exception as e:
        answer = None
    
    subanswer, final_answer = extract_answer(answer)

    ################# 评估最终答案
    final_answer_evaluation_prompt = judge_config['eval_prompt_template'].format(task=item['query'], operated_text=final_answer, ground_truth=item['GT'])

    try:
        final_answer_response = call_llm(final_answer_evaluation_prompt, model_config)
    except Exception as e:
        final_answer_response = 'calling llm error'

    if "The answer is correct" in final_answer_response:
        score = 2
    elif "The answer is approximated but should be correct" in final_answer_response:
        score = 1
    else:
        score = 0


    item['extracted_response'] = answer
    item['final_answer_evaluation'] = final_answer_response
    item['score'] = score

    ################### 评估每个testcase
    # 如果没有testcase
    if len(item['testcase']) == 0 or subanswer is None:
        passrate = -1

    # 如果是testcase没有GT
    elif item['testcase'][0]['ground_truth']==None:
        num_passed = 0
        formated_subquestion = '\n'.join([f"Testcase {index + 1}: {it['condition']}" for index, it in enumerate(item['testcase'])])
        eval_testcase_prompt = judge_config['eval_testcase_prompt_template'].format(task=formated_subquestion, subanswer=subanswer)

        try:
            testcase_response = call_llm(eval_testcase_prompt, model_config)
        except Exception as e:
            testcase_response = 'calling llm error'

        testcase_results, _ = extract_answer(testcase_response)
        try:
            num_passed = sum([1 for it in json.loads(testcase_results).values() if it == 'CORRECT'])
        except json.JSONDecodeError:
            item['passrate'] = -1
            return item
        
        num_testcase = len(item['testcase'])
        passrate = num_passed / num_testcase if num_testcase > 0 else 0

    # 如果testcase有GT，也就是subquestion: subanswer的形式
    else:
        num_passed = 0
        formated_subquestion = json.dumps(item['testcase'], ensure_ascii=False, indent=2)
        eval_testcase_prompt = judge_config['eval_subquestion_prompt_template'].format(task=item['query'], testcase=formated_subquestion, operated_text=subanswer)

        try:
            testcase_response = call_llm(eval_testcase_prompt, model_config)
        except Exception as e:
            testcase_response = 'calling llm error'
       
        testcase_results, _ = extract_answer(testcase_response)
        try:
            num_passed = sum([1 for it in json.loads(testcase_results).values() if it == 'CORRECT'])
        except json.JSONDecodeError:
            item['passrate'] = -1
            return item
        
        num_testcase = len(item['testcase'])
        passrate = num_passed / num_testcase if num_testcase > 0 else 0

    item['passrate'] = passrate
    return item



def load_judge_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    judge_config_path = os.path.join(current_dir, 'judge_config.yaml')
    
    with open(judge_config_path, 'rb') as f:
        judge_config = yaml.safe_load(f)
    # print(judge_config)
    return judge_config


def handle_retry_error(retry_state):
    # print('here ')
    return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5), retry_error_callback=handle_retry_error)
def call_llm(prompt, model_config:Dict[str, Any]):
    
    model_url_list = model_config['api_base']
    model_name = model_config['model_name']
    temperature, max_tokens = model_config['temperature'], model_config['max_tokens']

    model_url = random.choice(model_url_list)
    llm = OpenAI(base_url=f"{model_url}", api_key=model_config['api_key'])
    completion = llm.chat.completions.create(
        model=f"{model_name}",
        messages=[{"role": "user", "content": prompt}],
        stop=['<|eot_id|>'],
        temperature=temperature,
        max_tokens=max_tokens
    )
    response = completion.choices[0].message.content

    return response


def score(domain: str, model_name: str, llm_name: str, output_dir: str, max_workers: int, 
          judge_model_name: str, judge_api_base: str, judge_api_key: str, 
          judge_parallel_size: int = 10, judge_temperature: float = 0.0, judge_max_tokens: int = 4096):
    """评估函数 - 参考inference的数据加载方式"""
    # 使用统一的输入数据文件
    input_data_path = os.path.join(output_dir, model_name, llm_name, f'{domain}.jsonl')
    
    # 检查输入文件是否存在
    if not os.path.exists(input_data_path):
        raise FileNotFoundError(f"Error: Input data file {input_data_path} not found")
    
    # 读取所有数据
    total_data = []
    with open(input_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                total_data.append(json.loads(line))
    
    # 根据domain过滤数据
    if domain == 'all':
        data = total_data
    else:
        data = [item for item in total_data if item['domain'] == domain]
    
    # 构建输出路径
    output_jsonl_path = os.path.join(output_dir, model_name, llm_name, f'{domain}_eval.jsonl')
    
    # 断点续传逻辑
    print(f"Save to {output_jsonl_path}")
    os.makedirs(os.path.dirname(output_jsonl_path), exist_ok=True)
    
    lookup_table = {item['query']: 0 for item in data}
    
    if os.path.exists(output_jsonl_path):
        with open(output_jsonl_path, 'r', encoding='utf-8') as f:
            processed_data = f.readlines()
        for obj in processed_data:
            try:
                processed_item = json.loads(obj)
                lookup_table[processed_item['query']] = 1
            except json.JSONDecodeError:
                continue
    
    need_process_data = [item for item in data if not lookup_table[item['query']]]
    
    if not need_process_data:
        print(f"==> {domain} already fully processed")
        # 计算已处理数据的统计信息
        with open(output_jsonl_path, 'r', encoding='utf-8') as f:
            processed_data = [json.loads(line) for line in f]
        
        # 如果是'all'，需要分别计算每个domain的统计信息
        if domain == 'all':
            domain_stats = {}
            for item in processed_data:
                item_domain = item['domain']
                if item_domain not in domain_stats:
                    domain_stats[item_domain] = {'items': [], 'correct': 0, 'total': 0, 'passrate_items': []}
                
                domain_stats[item_domain]['items'].append(item)
                domain_stats[item_domain]['total'] += 1
                if item['score'] == 2:
                    domain_stats[item_domain]['correct'] += 1
                if item['passrate'] != -1:
                    domain_stats[item_domain]['passrate_items'].append(item['passrate'])
            
            # 打印每个domain的统计信息
            print(f"==> Detailed statistics for 'all' domain:")
            for domain_name, stats in domain_stats.items():
                domain_accuracy = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
                domain_passrate = sum(stats['passrate_items']) / len(stats['passrate_items']) * 100 if stats['passrate_items'] else 0
                print(f"  {domain_name}: Accuracy={domain_accuracy:.2f}%, Pass Rate={domain_passrate:.2f}%")
        
        num_correct = sum([item['score'] == 2 for item in processed_data])
        accuracy = num_correct / len(processed_data) * 100 if processed_data else 0
        
        passrate_ls = [item['passrate'] for item in processed_data if item['passrate'] != -1]
        passrate = sum(passrate_ls) / len(passrate_ls) * 100 if passrate_ls else 0
        
        return accuracy, passrate
    
    print(f"==> processing {domain}, {len(need_process_data)} items to process...")

    # 构建评估模型配置
    judge_config = load_judge_config()
    # 更新模型配置为传入的参数
    judge_config['judge_model'] = {
        'model_name': judge_model_name,
        'api_base': [judge_api_base],  # 转换为列表格式
        'api_key': judge_api_key,
        'parallel_size': judge_parallel_size,
        'temperature': judge_temperature,
        'max_tokens': judge_max_tokens
    }

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(eval_llm, item, judge_config) for item in need_process_data]

        for future in tqdm(as_completed(futures), total=len(need_process_data), desc="processing"):
            result = future.result()
            if result:  # 确保 result 不是 None
                with open(output_jsonl_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f.flush()  # 强制刷新缓冲区

    print(f"==> {domain} eval done, saved to {output_jsonl_path}")

    # 计算统计信息
    with open(output_jsonl_path, 'r', encoding='utf-8') as f:
        processed_data = [json.loads(line) for line in f]
    
    # 如果是'all'，需要分别计算每个domain的统计信息
    if domain == 'all':
        domain_stats = {}
        for item in processed_data:
            item_domain = item['domain']
            if item_domain not in domain_stats:
                domain_stats[item_domain] = {'items': [], 'correct': 0, 'total': 0, 'passrate_items': []}
            
            domain_stats[item_domain]['items'].append(item)
            domain_stats[item_domain]['total'] += 1
            if item['score'] == 2:
                domain_stats[item_domain]['correct'] += 1
            if item['passrate'] != -1:
                domain_stats[item_domain]['passrate_items'].append(item['passrate'])
        
        # 打印每个domain的统计信息
        print(f"==> Detailed statistics for 'all' domain:")
        for domain_name, stats in domain_stats.items():
            domain_accuracy = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
            domain_passrate = sum(stats['passrate_items']) / len(stats['passrate_items']) * 100 if stats['passrate_items'] else 0
            print(f"  {domain_name}: Accuracy={domain_accuracy:.2f}%, Pass Rate={domain_passrate:.2f}%")
    
    num_correct = sum([item['score'] == 2 for item in processed_data])
    accuracy = num_correct / len(processed_data) * 100 if processed_data else 0
    
    print(f"==> {domain} eval done, {num_correct} / {len(processed_data)} correct")
    print(f"==> {domain} eval done, {accuracy:.2f}% correct")
    
    # calculate passrate
    passrate_ls = [item['passrate'] for item in processed_data if item['passrate'] != -1]
    
    if passrate_ls:
        passrate = sum(passrate_ls) / len(passrate_ls) * 100
        print(f"==> {domain} eval done, {accuracy:.2f}% correct, pass rate: {passrate:.2f}%")
        print(f"=> number of samples that has testcase: {len(passrate_ls)}")
    else:
        passrate = 0
        print(f"==> {domain} eval done, pass rate: 0%")

    return accuracy, passrate



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, required=True, help='path to the data file')
    parser.add_argument('--model_name', type=str, required=True, help='model name')
    parser.add_argument('--llm_name', type=str, required=True, help='llm name')
    parser.add_argument('--domain', type=str, nargs='+', required=True, help='domain，支持输入多个值，以空格分隔')
    parser.add_argument('--max_workers', type=int, default=10, help='max workers')
    
    # 评估模型配置参数
    parser.add_argument('--judge_model_name', type=str, required=True, help='judge model name')
    parser.add_argument('--judge_api_base', type=str, required=True, help='judge model API base URL')
    parser.add_argument('--judge_api_key', type=str, required=True, help='judge model API key')
    parser.add_argument('--judge_parallel_size', type=int, default=10, help='judge model parallel size')
    parser.add_argument('--judge_temperature', type=float, default=0.0, help='judge model temperature')
    parser.add_argument('--judge_max_tokens', type=int, default=4096, help='judge model max tokens')
    
    args = parser.parse_args()
    
    # 如果domain包含'all'，只处理'all'这个domain
    if 'all' in args.domain:
        domain_list = ['all']
        print("==> Processing 'all' domain")
    else:
        domain_list = args.domain
    
    acc_ls, passrate_ls = [], []
    domain_results = []  # 存储每个domain的结果
    
    for domain in domain_list:
        accuracy, passrate = score(
            domain, args.model_name, args.llm_name, args.output_dir, 
            max_workers=args.max_workers,
            judge_model_name=args.judge_model_name,
            judge_api_base=args.judge_api_base,
            judge_api_key=args.judge_api_key,
            judge_parallel_size=args.judge_parallel_size,
            judge_temperature=args.judge_temperature,
            judge_max_tokens=args.judge_max_tokens
        )
        acc_ls.append(accuracy)
        passrate_ls.append(passrate)
        domain_results.append((domain, accuracy, passrate))

    print(f"==> {args.model_name} {args.llm_name} eval results:")
    print(f"| Domain | Accuracy | Pass Rate |")
    print(f"| --- | --- | --- |")
    for domain, acc, passrate in domain_results:
        # 以表格的形式输出
        print(f"| {domain} | {acc:.2f}% | {passrate:.2f}% |")
    
    # 如果包含'all'，计算总体统计信息
    if 'all' in args.domain:
        # 读取all_eval.jsonl文件计算总体统计
        all_eval_path = os.path.join(args.output_dir, args.model_name, args.llm_name, 'all_eval.jsonl')
        if os.path.exists(all_eval_path):
            with open(all_eval_path, 'r', encoding='utf-8') as f:
                all_data = [json.loads(line) for line in f]
            
            total_correct = sum([item['score'] == 2 for item in all_data])
            total_accuracy = total_correct / len(all_data) * 100 if all_data else 0
            
            total_passrate_items = [item['passrate'] for item in all_data if item['passrate'] != -1]
            total_passrate = sum(total_passrate_items) / len(total_passrate_items) * 100 if total_passrate_items else 0
            
            print(f"\n==> Overall statistics for 'all':")
            print(f"| Domain | Accuracy | Pass Rate |")
            print(f"| --- | --- | --- |")
            print(f"| all | {total_accuracy:.2f}% | {total_passrate:.2f}% |")
