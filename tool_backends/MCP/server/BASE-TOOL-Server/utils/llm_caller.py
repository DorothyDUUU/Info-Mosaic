import asyncio
import openai
import re
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(os.path.dirname(os.path.abspath(f"./{os.path.relpath(current_dir)}")))

# Import config_manager from MCP
try:
    from MCP.config_manager import config_manager
    use_config_manager = True
except ImportError:
    use_config_manager = False
    from configs.common_config import CommonConfig


async def llm_call(query: str, model_name: str = "qwen-72b", max_retries: int = 3):
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Use config_manager if available, otherwise fall back to CommonConfig
            if use_config_manager:
                llm_config = config_manager.get_llm_config()
                model_config = llm_config.get(model_name)
            else:
                config = CommonConfig()
                model_config = config[model_name]
            
            if model_config is None:
                raise ValueError(f"Model '{model_name}' not found in configuration")
            
            api_key = model_config.get("authorization", "EMPTY")
            base_url = model_config.get("url")
            
            if not base_url:
                raise ValueError(f"No URL configured for model '{model_name}'")
            
            client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            response = await client.chat.completions.create(
                model=model_name, messages=[{"role": "user", "content": query}]
            )
            
            if not response or not response.choices or len(response.choices) == 0:
                raise ValueError("Empty response from LLM API")
            
            content = response.choices[0].message.content
            if isinstance(content, str) and content.strip():
                return content
            else:
                raise ValueError("Invalid content received, not a non-empty string")

        except Exception as e:
            retry_count += 1
            print(f"Attempt {retry_count} failed: {e}")
            if retry_count == max_retries:
                raise RuntimeError(
                    f"llm_call_async failed after {max_retries} retries."
                ) from e
            await asyncio.sleep(1)
    return None


async def conclude_abstract(abstract, question):
    query = f"Please conclude the abstract of the following paper according to the question: {question}. Your answer should be concise and to the point, and should not be too long. You can conclude it in different aspects, such as the problem, the solution, the result, the limitation, etc. Wrap your conclusion using <conclusion> and </conclusion> tags. Abstract: {abstract}."
    response = await llm_call(query, model_name="gpt-4o")
    match = re.search(
        r"<conclusion>(.*?)</conclusion>", response, re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    else:
        return ""


if __name__ == "__main__":
    print(asyncio.run(llm_call("What is the Nerf?", model_name="qwen-32b")))
