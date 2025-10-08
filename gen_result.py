from utils import BenchArgs, ArgparseArgs
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import model_forwards
from Bench_infer.infer import infer
from Qgen.infer_answer import infer as qgen_infer
from typing import Dict, List, Any
import yaml


bench_table = {
    "Qgen": qgen_infer,
}

def build_benchargs(api_config:Dict[str, Any], gen_answer_config:Dict[str, Any]):
    temperature, max_tokens = gen_answer_config['temperature'], gen_answer_config['max_tokens']
    model_list = gen_answer_config['model_list']
    system_prompt = gen_answer_config['system_prompt']
    timeout = gen_answer_config['timeout']
    retry = gen_answer_config['retry']

    result:List[BenchArgs] = []
    for model_name in model_list:
        try:
            model_api_config = api_config[model_name]
            parallel_size = model_api_config['parallel']
            if model_api_config['endpoints']:
                api_base, api_key = model_api_config['endpoints'][0]['api_base'],\
                      model_api_config['endpoints'][0]['api_key']
            else:
                api_base, api_key = "", "EMPTY"
            bencharg = BenchArgs(
                model_name=model_api_config['model_name'], system_prompt=system_prompt,
                parallel_size=parallel_size,
                api_base=api_base, api_key=api_key,
                max_tokens=max_tokens, temperature=temperature,
                timeout=timeout,
                retry=retry
            )
            result.append(bencharg)
        except Exception as e:
            print(f"{model_name} not support...")
            continue

    return result




if __name__ == '__main__':
    
    with open('configs/api_config.yaml', 'rb') as f:
        api_config = yaml.safe_load(f)


    with open('configs/gen_answer_config.yaml', 'rb') as f:
        gen_answer_config = yaml.safe_load(f)
    
    benchargs_list = build_benchargs(api_config, gen_answer_config)
    for bencharg in benchargs_list:
        print('='*20)
        print(f"Processing model: {bencharg.model_name}")
        print(bencharg)

        for bench in gen_answer_config['bench_list']:
            print(f"Processing bench: {bench}")
            bench_table[bench](bencharg)
            

        


    

