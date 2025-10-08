import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from new_new_server import mcp
import logging
import requests
import sys

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def check_environment():
    """检查环境变量和API密钥"""
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    if not youtube_api_key:
        logger.error("❌ YOUTUBE_API_KEY 环境变量未设置!")
        return False
    logger.info("✅ YOUTUBE_API_KEY 已设置")
    return True

def check_youtube_api():
    """检查 YouTube API 的连接和密钥有效性"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    test_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&maxResults=1&key={api_key}"
    
    try:
        logger.info("正在检查 YouTube API 连接...")
        response = requests.get(test_url, timeout=5)
        
        if response.status_code == 200:
            logger.info("✅ YouTube API 连接成功")
            return True
        elif response.status_code == 403:
            logger.error(f"❌ API 密钥无效或没有权限: {response.json().get('error', {}).get('message', '未知错误')}")
            return False
        else:
            logger.error(f"❌ YouTube API 连接失败: HTTP {response.status_code}")
            if response.content:
                try:
                    error_message = response.json().get('error', {}).get('message', '未知错误')
                    logger.error(f"错误信息: {error_message}")
                except:
                    logger.error(f"响应内容: {response.text[:200]}")
            return False
            
    except requests.exceptions.SSLError as e:
        logger.error(f"❌ SSL 错误: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ 连接错误: {e}")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"❌ 连接超时: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    logger.info("正在启动 YouTube MCP SSE 服务器...")
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查 YouTube API
    if not check_youtube_api():
        logger.warning("⚠️ YouTube API 检查失败，服务可能无法正常工作")
        response = input("是否仍然继续启动服务？(y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    try:
        # 创建 Starlette app 并挂载 MCP 服务
        app = Starlette(
            routes=[
                Mount("/", app=mcp.sse_app()),
            ]
        )
        
        # 运行服务器
        logger.info("启动 SSE 服务器在端口 8005...")
        uvicorn.run(app, host="0.0.0.0", port=8005)
    except Exception as e:
        logger.exception(f"❌ 运行 MCP SSE 服务器时出错: {e}")