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

def get_data_paths(current_dir, sub_path="multi_domain/critic_master_slave", filename="QA_0910.jsonl"):
    """获取数据路径的通用函数"""
    generation_path = os.path.join(current_dir, '..', 'output', 'generation', sub_path, filename)
    answer_generation_path = os.path.join(current_dir, '..', 'output', 'answer_generation', sub_path)
    return generation_path, answer_generation_path

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
    if len(item['testcase']) == 0 or subanswer is None:
        passrate = -1
    else:
        num_passed = 0
        formated_subquestion = json.dumps(item['testcase'], ensure_ascii=False, indent=2)
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

    item['passrate'] = passrate
    return item



def load_judge_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    judge_config_path = os.path.join(current_dir, '..', 'configs', 'judge_config.yaml')
    
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


def score(data_path:str):

    data_dir = os.path.dirname(data_path)
    model_name = os.path.basename(data_path).split('.')[0]

    with open(data_path, 'rb') as f:
        data = f.readlines()

    infer_data = [json.loads(obj) for obj in data]
    lookup_table = {json.loads(obj)['query']:0 for obj in data}

    # 保存评分结果到相同的answer_generation目录
    output_jsonl_path = os.path.join(data_dir, f"{model_name}_eval.jsonl")

    if os.path.exists(output_jsonl_path):
        with open(output_jsonl_path, 'rb') as f:
            processed_data = f.readlines()
        for obj in processed_data:
            lookup_table[json.loads(obj)['query']] = 1 
    
    need_process_infer_data = [item for item in infer_data if not lookup_table[item['query']]]
    print(f"==> processing {model_name}, {len(need_process_infer_data)} need to process...")

    judge_config = load_judge_config()
    model_config = judge_config['judge_model']
    max_worker = int(model_config['parallel_size'] * len(model_config['api_base']))

    # for item in tqdm(need_process_infer_data, desc="processing"):
    #     result = eval_llm(item, judge_config)
    #     if result:
    #         with open(output_jsonl_path, 'a') as f:
    #             f.write(json.dumps(result) + '\n')
    #             f.flush()

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(eval_llm, item, judge_config) for item in need_process_infer_data]

        for future in tqdm(as_completed(futures), total=len(need_process_infer_data), desc="processing"):
            result = future.result()
            if result:  # 确保 result 不是 None
                with open(output_jsonl_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    f.flush()  # 强制刷新缓冲区

    print(f"==> {model_name} eval done, saved to {output_jsonl_path}")

    with open(output_jsonl_path, 'rb') as f:
        processed_data = f.readlines()
    
    num_correct = sum([json.loads(obj)['score']==2 for obj in processed_data])
    print(f"==> {model_name} eval done, {num_correct} / {len(processed_data)} correct")
    print(f"==> {model_name} eval done, {num_correct / len(processed_data) * 100:.2f}% correct")
    
    # calculate passrate
    passrate_ls = [json.loads(obj)['passrate'] for obj in processed_data if json.loads(obj)['passrate'] != -1]
    print(f"Accuracy: {num_correct / len(processed_data) * 100:.2f}%")
    if passrate_ls:
        print(f"=> number of samples that has testcase: {len(passrate_ls)}")
        print(f"Pass rate: {sum(passrate_ls) / len(passrate_ls) * 100:.2f}%")
    else:
        print(f"Pass rate: 0%")
    


if __name__ == '__main__':
    
    json_path = '/data/yaxindu/ToolArena/AI-Researcher-dev/evaluation/output/answer_generation/multi_domain/critic_master_slave_env2/naive_forward_testcase.jsonl'

    score(json_path)