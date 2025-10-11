#!/usr/bin/env bash

MODEL_NAME=agent_wo_tool # agent name ['agent_wo_tool', 'agent_w_web_tool', 'agent_w_multi_tool']
NUM_TOOLCALLS=20
PARALLEL_SIZE=10
DOMAIN=all # ['map', 'bio', 'financial', 'web', 'video', 'multidomain', 'all']
LLM_NAME=gpt-5-mini # LLM name

# basic settings usually not need set
API_BASE="${OPENAI_API_BASE_URL}"
API_KEY="${OPENAI_API_KEY}"
SERPER_API_KEY="${SERPER_API_KEY}"  # An effective Serper API key needs to be set to implement web search.
TEMPERATURE=0.0
MAX_TOKENS=4096
TIMEOUT=1800
SYSTEM_PROMPT="You are a helpful assistant"
USER_TEMPLATE="Please answer the question:\n INFORMARION\n # Notic: - You can use the web_search tool to get more information.\n - You should provide all information for answering every subqueries in the question in the last sentence and illustrate your reasoning process for these subquestions in the end, rather than a single answer.\n # Output Format: [Your subanswer to each subquestion if there is]\n [Your Final Answer]"
FINISH_TEMPLATE="You have reached the maximum number of tool calls. Please provide your final answer according to the above tool usage results and answer the question anyway.\n Remember you should provide all information for answering every subqueries in the question rather than a single answer."


python inference/run_infer.py \
  --model_name "$MODEL_NAME" \
  --max_tool_calls "$NUM_TOOLCALLS" \
  --system_prompt "$SYSTEM_PROMPT" \
  --user_template "$USER_TEMPLATE" \
  --finish_template "$FINISH_TEMPLATE" \
  --parallel_size "$PARALLEL_SIZE" \
  --api_base "$API_BASE" \
  --api_key "$API_KEY" \
  --temperature "$TEMPERATURE" \
  --max_tokens "$MAX_TOKENS" \
  --timeout "$TIMEOUT" \
  --domain "$DOMAIN" \
  --llm_name "$LLM_NAME"
