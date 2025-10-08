import aiohttp
import asyncio
from .tool_api import web_search_api


async def google_search(query: str, top_k: int = 10):
    async with aiohttp.ClientSession() as session:
        result = await web_search_api(session, query, top_k)
        return result


if __name__ == "__main__":
    print(asyncio.run(google_search("what is google")))
