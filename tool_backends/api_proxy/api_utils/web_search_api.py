import aiohttp
import asyncio
import traceback
import json
import os
import sys

# 检测是否在Docker容器中运行并设置正确的路径
def get_config_path():
    # 检查是否在Docker容器中运行
    is_docker = os.path.exists('/.dockerenv')
    
    if is_docker:
        # Docker容器中使用/mnt路径
        base_dir = '/mnt'
    else:
        # 宿主机上使用相对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))  # 指向tool_backends目录
    
    # 添加到Python路径确保模块可被导入
    if base_dir not in sys.path:
        sys.path.append(base_dir)
    
    return base_dir

# 获取基础路径
base_dir = get_config_path()

# 加载web_agent配置
with open(os.path.join(base_dir, "configs/web_agent.json"), "r") as f:
    config = json.load(f)


async def serper_google_search(
    query: str, serper_api_key: str, top_k: int, region: str, lang: str, depth: int = 0
):
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": top_k,
        "gl": region,
        "hl": lang,
        "location": "United States",
    }

    headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise Exception(f"API Error: {response.status}")
                data = await response.json()

                data.pop("searchParameters", None)
                data.pop("credits", None)

                if not data:
                    raise Exception(
                        "The google search API is temporarily unavailable, please try again later."
                    )
                return data

    except Exception as e:
        if depth < 3:
            await asyncio.sleep(1)
            return await serper_google_search(
                query, serper_api_key, top_k, region, lang, depth=depth + 1
            )
        print(f"search failed: {e}")
        print(traceback.format_exc())
        return []


async def main():
    query = "[Merrill et al. Transformers are Hard-Attention Automata]"
    result = await serper_google_search(
        query=query,
        serper_api_key=config["serper_api_key"],
        top_k=10,
        region=config["search_region"],
        lang=config["search_lang"],
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
