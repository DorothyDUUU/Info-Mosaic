import aiohttp
import asyncio
from api_proxy.tool_api import fetch_web_api


async def fetch_web_content(url: str):
    async with aiohttp.ClientSession() as session:
        result = await fetch_web_api(session, url)
        return result


async def main():
    url = "https://www.sciencedirect.com/"
    is_ok, html = await fetch_web_content(url)
    if is_ok:
        print(html)
    else:
        print("❌Error for response")


if __name__ == "__main__":
    asyncio.run(main())
