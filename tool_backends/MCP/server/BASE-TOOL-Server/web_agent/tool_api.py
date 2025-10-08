import aiohttp
import os, sys, json

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_dir)))
with open(os.path.join(current_dir, "../../../../configs/mcp_config.json"), "r") as f:
    mcp_config = json.load(f)

base_url = mcp_config["tool_api_url"]


with open(os.path.join(current_dir, "../../../../configs/web_agent.json"), "r") as f:
    config = json.load(f)


async def web_search_api(session: aiohttp.ClientSession, query: str, top_k: int = 10):
    url = f"{base_url}/search"
    data = {
        "query": query,
        "serper_api_key": config["serper_api_key"],
        "top_k": top_k,
        "region": config["search_region"],
        "lang": config["search_lang"],
        "depth": 0,
    }
    async with session.post(url, json=data) as resp:
        return await resp.json()


async def read_pdf_api(session: aiohttp.ClientSession, url: str):
    server_url = f"{base_url}/read_pdf"
    data = {"url": url}
    async with session.post(server_url, json=data) as resp:
        return await resp.json()


async def fetch_web_api(session: aiohttp.ClientSession, url: str):
    server_url = f"{base_url}/fetch_web"
    data = {"url": url}
    async with session.post(server_url, json=data) as resp:
        return await resp.json()
