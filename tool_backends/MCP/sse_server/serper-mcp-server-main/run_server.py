from src.serper_mcp_server.core import google, scape, SERPER_API_KEY
from src.serper_mcp_server.enums import SerperTools
from src.serper_mcp_server.schemas import (
    SearchRequest,
    WebpageRequest
)
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP
import json

# 创建一个新的 FastMCP 实例
mcp = FastMCP("Serper", port=8004, host="0.0.0.0")

@mcp.tool()
async def google_search(q: str, num: int = 10) -> str:
    """Search Google for results"""
    request = SearchRequest(q=q, num=num)
    result = await google(SerperTools.GOOGLE_SEARCH, request)
    return json.dumps(result, indent=2)

@mcp.tool()
async def google_search_images(q: str, num: int = 10) -> str:
    """Search Google Images"""
    request = SearchRequest(q=q, num=num)
    result = await google(SerperTools.GOOGLE_SEARCH_IMAGES, request)
    return json.dumps(result, indent=2)

@mcp.tool()
async def google_search_news(q: str, num: int = 10) -> str:
    """Search Google News"""
    request = SearchRequest(q=q, num=num)
    result = await google(SerperTools.GOOGLE_SEARCH_NEWS, request)
    return json.dumps(result, indent=2)

@mcp.tool()
async def google_search_places(q: str) -> str:
    """Search Google Places"""
    request = SearchRequest(q=q)
    result = await google(SerperTools.GOOGLE_SEARCH_PLACES, request)
    return json.dumps(result, indent=2)

@mcp.tool()
async def google_search_videos(q: str, num: int = 10) -> str:
    """Search Google Videos"""
    request = SearchRequest(q=q, num=num)
    result = await google(SerperTools.GOOGLE_SEARCH_VIDEOS, request)
    return json.dumps(result, indent=2)

@mcp.tool()
async def google_search_patents(q: str, num: int = 10) -> str:
    """Search Google Patents"""
    request = SearchRequest(q=q, num=num)
    result = await google(SerperTools.GOOGLE_SEARCH_PATENTS, request)
    return json.dumps(result, indent=2)

@mcp.tool()
async def webpage_scrape(url: str) -> str:
    """Scrape webpage by url"""
    request = WebpageRequest(url=url)
    result = await scape(request)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    # 创建 Starlette app 并挂载 MCP 服务
    app = Starlette(
        routes=[
            Mount("/", app=mcp.sse_app()),
        ]
    )
    
    # 运行服务器
    uvicorn.run(app, host="0.0.0.0", port=8004)