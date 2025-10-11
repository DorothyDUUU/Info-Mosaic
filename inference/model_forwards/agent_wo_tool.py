import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import register_forward, BenchArgs
from typing import Dict
from openai import OpenAI

@register_forward("agent_wo_tool")
def forward(args: BenchArgs, item: Dict[str, str]):
    # Use the custom call_model function to perform a simple model call without using any tools
    api_key = args.api_key
    base_url = args.api_base
    model = args.llm_name
    max_tokens = args.max_tokens

    query = item["query"]
    response = call_model(api_key, base_url, model, query, max_tokens)
    item['response'] = response
    return item

def call_model(api_key: str, base_url: str, model: str, query: str, max_tokens: int):
    client = OpenAI(api_key=api_key, base_url=base_url)
    user_prompt = f"Please answer the following question: {query}, you should also give the conditions of the question."
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_prompt}],
        response_format={"type": "text"},  # 👈 force text output
        max_tokens=max_tokens,
        temperature=1,  # modify to a value supported by the model
    )
    response_content = response.choices[0].message.content
    print(response_content)
    return response_content
