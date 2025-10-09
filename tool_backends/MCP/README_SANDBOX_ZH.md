# MCP 沙盒工具服务器说明
这个readme主要是介绍沙盒的用法和代码，我们参考https://github.com/sjtu-sai-agents/mcp_sandbox，对齐进行了一定的修改。以下是详细的功能和使用介绍，如果你需要对沙盒或者工具进行改造的话，你可以参考下面的说明，如果你只是需要使用，可以跳过这部分说明。

## 沙盒工作逻辑

MCP (Modular Computing Platform) 沙盒是一个模块化的工具执行平台，提供了统一的工具调用、会话管理和结果流式返回机制。

### 核心工作原理

1. **会话隔离机制**
   - 每个会话ID对应独立的代码执行空间，保留历史函数和变量
   - 支持手动关闭会话以释放内存资源

2. **工具执行流程**
   - 客户端通过StreamToolManager提交代码任务
   - 服务器执行代码并流式返回结果
   - 支持直接调用工具和嵌套调用其他agent作为工具

3. **流式结果返回**
   - 通过main_stream_type、sub_stream_type、stream_state等字段标识返回内容类型和状态
   - 工具调用结果包含在other_info字段中

### 部署架构

- 推荐在Docker容器中运行，提供更好的隔离性和资源控制
- 支持多CPU核心分配，提升并发处理能力
- 通过HTTP API提供工具调用接口

## 如何增加工具

MCP支持两种工具导入方式：本地client导入和SSE client导入。

### 本地client导入

1. 在server目录下创建新的子目录
2. 在该目录中创建Python文件，使用`@mcp.tool()`装饰器定义工具函数
3. 在`./MCP/config/server_list.json`中注册该Python文件的路径

**示例：**

创建文件 `./MCP/server/hello/hello.py`：
```python
@mcp.tool()
def hello_world() -> str:
    # 在这里添加自定义逻辑和工具
    return "Hello world!"
```

在`server_list.json`中添加：
```json
[
    "server/hello/hello.py"
]
```

注意：简单的MCP服务也可以直接在mcp_server.py文件中定义，系统会默认从中导入。

### SSE client导入

对于需要通过SSE协议连接的外部工具服务，只需在`config/server_list.json`中添加对应的SSE链接即可。

**示例：**
```json
[
    "http://localhost:8001/sse",
    "http://localhost:8002/sse",
    "http://localhost:8004/sse",
    "http://localhost:8005/sse",
    "server/Google_Map_server/new_server.py"
]
```

## 运行服务

### Docker部署（推荐）
参考这里的启动代码：中文/data/yaxindu/InfoMosaic/tool_backends/README_zh.md
英文：/data/yaxindu/InfoMosaic/tool_backends/REAMDE.md

### 调用服务

#### 方法1：使用Agent框架自带的tool manager（推荐）

```python
class StreamToolManager(BaseToolManager):
    def __init__(self, url, session_id:str = None, timeout:int=180):
        super().__init__(url)
        self.session_id = str(uuid4()) if not session_id else session_id
        self.timeout = timeout

    async def submit_task(self, code:str):
        # 提交代码任务的实现
        ...

    async def recieve_task_process(self, ):
        # 接收处理结果的实现
        ...
                
    async def execute_code_async_stream(self, tool_call: str,):
        submit_status = await self.submit_task(tool_call)
        if submit_status["status"] == "fail":
            yield {"output":""}
            return
        
        async for item in self.recieve_task_process():
            yield item

    async def close_session(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.server_url}/del_session",
                params={"session_id": self.session_id}
            )
            return resp.json()
```

**使用注意事项：**
- 每个会话需要维护自己的tool manager实例
- 会话结束后调用`close_session()`释放资源
- 调用`execute_code_async_stream`执行代码，结果会流式返回

#### 方法2：直接HTTP请求调用execute端点

```python
import requests
import time
url = "http://127.0.0.1:30004"

test_code = f"""
from tools import *
link = "https://www2.census.gov/library/publications/2001/demo/p60-214.html"
query = "Does this document mention any towns with 0% poverty rate for 65+ population and the specified income figures?"
result = web_parse_qwen(link, query)
print(result)
"""

headers = {
    "Content-Type": "application/json"
}

def code_tool(code:str):
    start_time = time.time()  # 记录开始时间
    payload = {
        "code": code
    }
    resp = requests.post(
        f"{url}/execute",
        headers=headers,
        json=payload
    )
    response = resp.json()
    elapsed = time.time() - start_time  # 计算总耗时
    response['total_time'] = elapsed
    response['server_time'] = resp.elapsed.total_seconds()
    
    return response

code_tool(test_code)
```

## 工具结果返回格式

### 情况1：直接调用工具

工具返回时，结果会包含在other_info字段中，格式如下：

```json
{
    "main_stream_type": "tool_result",
    "sub_stream_type": "",
    "content": "",
    "from_sandbox": true,
    "stream_state": "running",
    "other_info": {
        "web_search": {
            "tool_result": {
                "organic": [/*搜索结果条目*/],
                "peopleAlsoAsk": [/*相关问题*/],
                "relatedSearches": [/*相关搜索*/]
            },
            "tool_elapsed_time": 2.11
        }
    }
}
```

### 情况2：调用其他agent作为工具

当调用其他agent作为工具时，会流式返回其他agent的text和工具调用结果：

```json
{
    "main_stream_type": "tool_result",
    "sub_stream_type": "text",
    "content": ">\n\n",
    "from_sandbox": true,
    "stream_state": "running",
    "other_info": {}
}
```

## 项目结构

MCP工具服务器的核心组件包括：
- `server/`: 存放本地工具客户端的目录
- `config/`: 配置文件目录，包含server_list.json等
- `mcp_manager.py`: 管理工具调用和会话的核心模块
- `tool_server.py`: 工具服务器的主入口
- `proxy_service.py`: 代理服务组件

## 配置文件说明

主要配置文件包括：
- `config/server_list.json`: 定义要加载的工具服务列表
- `config/llm_call.json`: LLM模型调用配置
- `config/mcp_config.json`: MCP服务器基本配置

## 常见问题排查

1. **工具无法加载**
   - 检查server_list.json中的文件路径是否正确
   - 确保工具函数使用了@mcp.tool()装饰器

2. **会话资源释放**
   - 确保在会话结束后调用close_session()函数
   - 长时间运行的服务应定期清理闲置会话

3. **性能优化**
   - 使用Docker部署并分配足够的CPU资源
   - 对于高并发场景，可增加服务器实例数量
