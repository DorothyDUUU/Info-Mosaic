import aiohttp
import asyncio
import os
import sys

# Get the directory of the current file
script_dir = os.path.dirname(os.path.abspath(__file__))
# Add current directory to system path
sys.path.append(script_dir)
# If relative import fails, import tool_api module directly
import tool_api

web_search_api = tool_api.web_search_api


async def google_search(query: str, top_k: int = 10):
    async with aiohttp.ClientSession() as session:
        result = await web_search_api(session, query, top_k)
        return result


if __name__ == "__main__":
    print(asyncio.run(google_search("what is google")))
