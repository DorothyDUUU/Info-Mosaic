import aiohttp
import asyncio
import os
import sys

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add necessary directories to system path to ensure correct imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))  # Add tool_backends directory
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 'api_proxy'))  # Add api_proxy directory

try:
    # Try to import fetch_web_api from api_proxy.tool_api
    from api_proxy.tool_api import fetch_web_api
except ImportError as e:
    print(f"Warning: Failed to import api_proxy.tool_api.fetch_web_api: {e}")
    
    # If import fails, define a local mock function
    async def fetch_web_api(session, url):
        print(f"Warning: Using local mock fetch_web_api function, original API call failed")
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return True, await response.text()
                else:
                    return False, f"HTTP error: {response.status}"
        except Exception as inner_e:
            return False, f"Failed to fetch web content: {str(inner_e)}" 


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
