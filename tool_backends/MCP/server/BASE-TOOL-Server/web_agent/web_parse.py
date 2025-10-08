import json
import os
import sys
import asyncio
import tiktoken
import warnings

current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, ".."))
sys.path.append(os.path.join(current_dir))
from get_html import fetch_web_content
from utils.llm_caller import llm_call
from transformers import AutoTokenizer

with open(
    os.path.join(current_dir, "..", "..", "..", "..", "configs", "web_agent.json"), "r"
) as f:
    tools_config = json.load(f)

USE_PROMPT = tools_config["user_prompt"]
USE_LLM = tools_config["USE_MODEL"]
warnings.filterwarnings("ignore")


def split_chunks(text: str, model: str):
    if "gpt" in model:
        tokenizer = tiktoken.encoding_for_model("gpt-4o")
        chunk_token_limit = 120000
    elif model == "deepseek-r1":
        tokenizer = AutoTokenizer.from_pretrained(
            "deepseek-ai/deepseek-r1", trust_remote_code=True
        )
        chunk_token_limit = 120000
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen-72B", trust_remote_code=True
        )
        chunk_token_limit = 30000

    all_tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    while start < len(all_tokens):
        end = min(start + chunk_token_limit, len(all_tokens))
        chunk_tokens = all_tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end
    return chunks


async def read_html(text, user_prompt, model=None):
    chunks = split_chunks(text, model)
    # only select the first chunk
    chunks = chunks[:1]
    template = USE_PROMPT["search_conclusion"]
    final_prompt = template.format(user=user_prompt, info=chunks[0])
    answer = await llm_call(final_prompt, model)
    return _get_contents(answer)


async def parse_htmlpage(url: str, user_prompt: str = "", llm: str = None):
    try:
        is_fetch, text = await fetch_web_content(url)
        if not is_fetch:
            return {"content": "failed to fetch web content", "urls": [], "score": -1}

        model_to_use = llm if llm else USE_LLM
        try:
            print(f"Using {model_to_use} to parse web pages...")
            result = await read_html(text, user_prompt, model=model_to_use)
            return result
        except Exception as e:
            USE_LLM = tools_config["BASE_MODEL"]
            print(f"Using {USE_LLM} for parsing: {e}")
            result = await read_html(text, user_prompt, model=USE_LLM)
            return result

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"content": "failed to parse web content", "urls": [], "score": -1}


def _get_contents(response: str):
    try:
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        json_str = response[json_start:json_end]
        json_str = json_str.replace("\\(", "\\\\(").replace("\\)", "\\\\)")
        try:
            data = json.loads(json_str)
        except Exception as e:
            print(f"\033[91mError Response Format: {e}\033[0m")
            think_end = response.rfind("</think>")
            if think_end != -1:
                return {
                    "content": response[think_end + len("</think>") :].strip(),
                    "urls": [],
                    "score": -1,
                }
            else:
                return {"content": response, "urls": [], "score": -1}
        return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"content": "failed to parse web content", "urls": [], "score": -1}


async def main():
    query = "Was Chris Wilder a youth player at the club he managed in 2001? Also, when and where did he meet his spouse?"
    url = "https://en.wikipedia.org/wiki/Chris_Wilder"
    results = await parse_htmlpage(url, query, llm="gpt-4.1-nano-2025-04-14")
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
