# This file is aimed to ensemble the qurey from huggingface and GT from the github repo, which is used to avoid data leakage.
import json
import os
from datasets import load_dataset
import requests

# check if you could connet to huggingface
print("Connected to Hugging Face!" if requests.get("https://huggingface.co", timeout=5).status_code == 200 else "Could not connect to Hugging Face.")

# download huggingface dataset
try:
    query_data = load_dataset('Dorothydu/InfoMosaic_Bench')['test']
    assert len(query_data) == 1000
except:
    # wget the parquet file
    os.system("wget https://huggingface.co/datasets/Dorothydu/InfoMosaic_Bench/resolve/main/data/test-00000-of-00001.parquet")
    query_data = load_dataset("parquet", data_files="test-00000-of-00001.parquet")["train"]


# load jsonl file
gt_data = []
script_dir = os.path.dirname(os.path.abspath(__file__))
gt_file_path = os.path.join(script_dir, 'info_mosaic_gt_answer.jsonl')
with open(gt_file_path, 'r', encoding='utf-8') as f:
    for line in f:
        item = json.loads(line)
        gt_data.append(item)

if len(query_data) != len(gt_data):
    print(f"len(query_data): {len(query_data)}")
    print(f"len(gt_data): {len(gt_data)}")
    raise ValueError("The length of query_data and gt_data should be the same.")

# ensemble the query and gt data
ensemble_data = []
for query_item, gt_item in zip(query_data, gt_data):
    if query_item['id'] != gt_item['id']:
        raise ValueError("The id of query_item and gt_item should be the same.")
    ensemble_item = {**query_item, **gt_item}
    ensemble_data.append(ensemble_item)

# save to jsonl file
with open('data/info_mosaic_w_gt.jsonl', 'w', encoding='utf-8') as f:
    for item in ensemble_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')
