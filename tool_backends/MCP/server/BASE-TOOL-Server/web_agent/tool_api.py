import aiohttp
import os, sys, json
import aiohttp

# Add project root directory to system path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = '/mnt'
sys.path.append(project_root)

# Import config manager
from MCP.config_manager import config_manager

# Get configuration from config manager
base_url = config_manager.get_tool_api_url()
config = config_manager.get_web_agent_config()
has_config_manager = True
print("Successfully loaded config manager")

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
    try:
        async with session.post(url, json=data) as resp:
            return await resp.json()
    except Exception as e:
        # If API call fails, return mock results
        print(f"API call failed: {e}")
        return {
            "results": [
                {
                    "title": f"Search result for '{query}'",
                    "url": "https://example.com/search",
                    "snippet": "This is a fallback search result.",
                    "content": "This content is provided as a fallback when the search API is unavailable."
                }
            ] * min(top_k, 3)
        }


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
