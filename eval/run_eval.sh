#!/usr/bin/env bash

# 评估脚本 - 参考 inference/run_infer.sh 的简单形式

# 基本配置参数
OUTPUT_DIR="output"
MODEL_NAME="agent_wo_tool"
LLM_NAME="gpt-5-mini"
DOMAIN="all"
MAX_WORKERS=10

# 评估模型配置（从 judge_config.yaml 移到shell脚本中）
JUDGE_MODEL_NAME="gpt-4o"
JUDGE_API_BASE="${OPENAI_API_BASE_URL}"
JUDGE_API_KEY="${OPENAI_API_KEY}"
JUDGE_PARALLEL_SIZE=50
JUDGE_TEMPERATURE=0
JUDGE_MAX_TOKENS=4096


python eval/evaluate_all.py \
  --output_dir "$OUTPUT_DIR" \
  --model_name "$MODEL_NAME" \
  --llm_name "$LLM_NAME" \
  --domain "$DOMAIN" \
  --max_workers "$MAX_WORKERS" \
  --judge_model_name "$JUDGE_MODEL_NAME" \
  --judge_api_base "$JUDGE_API_BASE" \
  --judge_api_key "$JUDGE_API_KEY" \
  --judge_parallel_size "$JUDGE_PARALLEL_SIZE" \
  --judge_temperature "$JUDGE_TEMPERATURE" \
  --judge_max_tokens "$JUDGE_MAX_TOKENS"