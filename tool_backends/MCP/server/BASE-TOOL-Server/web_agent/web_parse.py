import json
import os
import sys
import json
import asyncio
import tiktoken
import warnings
import aiohttp

# Get the directory of the current file
current_dir = os.path.abspath(os.path.dirname(__file__))
# Add current directory to system path
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

# Get project root directory (pointing to directory containing MCP)
project_root = '/mnt'
sys.path.append(project_root)
from MCP.config_manager import config_manager
has_config_manager = True
print("Successfully loaded config manager")


# Try to import required modules
from get_html import fetch_web_content
from utils.llm_caller import llm_call
from transformers import AutoTokenizer

# Load configuration
tools_config = {}
if has_config_manager:
    try:
        tools_config = config_manager.get_web_agent_config()
        print(f"Loaded web agent config from config manager")
    except Exception as e:
        print(f"Error loading config from config manager: {e}")
        has_config_manager = False

if not has_config_manager:
    # Use default configuration or load from file
    try:
        config_path = os.path.join(current_dir, "..", "..", "..", "..", "configs", "web_agent.json")
        with open(config_path, "r") as f:
            tools_config = json.load(f)
        print(f"Loaded config from file: {config_path}")
    except Exception as e:
        print(f"Error loading config file: {e}")
        # Use hardcoded default values
        tools_config = {
            "user_prompt": {"search_conclusion": "Please analyze the provided web content..."},
            "USE_MODEL": "gpt-4o"
        }
        print("Using fallback default configuration")

# Set global variables
USE_PROMPT = tools_config.get("user_prompt", {})
USE_LLM = tools_config.get("USE_MODEL", "gpt-4o")
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
    try:
        chunks = split_chunks(text, model)
        # only select the first chunk
        chunks = chunks[:1]
        template = USE_PROMPT["search_conclusion"]
        final_prompt = template.format(user=user_prompt, info=chunks[0])
        answer = await llm_call(final_prompt, model)
        if answer is None:
            return {"content": "LLM returned no response", "urls": [], "score": -1}
        return _get_contents(answer)
    except Exception as e:
        print(f"Error in read_html: {str(e)}")
        return {"content": f"Error parsing content: {str(e)}", "urls": [], "score": -1}


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
    results = await parse_htmlpage(url, query, llm="gpt-4.1-nano")
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
