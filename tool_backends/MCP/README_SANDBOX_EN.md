# MCP Sandbox Tool Server Documentation
This README mainly introduces the usage and code of the sandbox. We have referenced https://github.com/sjtu-sai-agents/mcp_sandbox and made some modifications. Below is a detailed introduction to the features and usage. If you need to modify the sandbox or tools, you can refer to the following instructions. If you just need to use it, you can skip this part.

## Sandbox Working Logic

MCP (Modular Computing Platform) sandbox is a modular tool execution platform that provides unified tool calling, session management, and streaming result return mechanisms.

### Core Working Principles

1. **Session Isolation Mechanism**
   - Each session ID corresponds to an independent code execution space, preserving historical functions and variables
   - Supports manual closing of sessions to release memory resources

2. **Tool Execution Flow**
   - Clients submit code tasks through StreamToolManager
   - The server executes the code and streams the results back
   - Supports direct tool calls and nested calls to other agents as tools

3. **Streaming Result Return**
   - Uses fields like main_stream_type, sub_stream_type, and stream_state to identify the type and status of returned content
   - Tool call results are included in the other_info field

### Deployment Architecture

- Recommended to run in Docker containers for better isolation and resource control
- Supports multi-CPU core allocation to improve concurrent processing capabilities
- Provides tool calling interfaces through HTTP API

## How to Add Tools

MCP supports two ways of tool import: local client import and SSE client import.

### Local Client Import

1. Create a new subdirectory under the server directory
2. Create a Python file in this directory and define tool functions using the `@mcp.tool()` decorator
3. Register the path of this Python file in `./MCP/config/server_list.json`

**Example:**

Create file `./MCP/server/hello/hello.py`:
```python
@mcp.tool()
def hello_world() -> str:
    # Add custom logic and tools here
    return "Hello world!"
```

Add in `server_list.json`:
```json
[
    "server/hello/hello.py"
]
```

Note: Simple MCP services can also be defined directly in the mcp_server.py file, which will be imported by default.

### SSE Client Import

For external tool services that need to connect via SSE protocol, simply add the corresponding SSE links in `config/server_list.json`.

**Example:**
```json
[
    "http://localhost:8001/sse",
    "http://localhost:8002/sse",
    "http://localhost:8004/sse",
    "http://localhost:8005/sse",
    "server/Google_Map_server/new_server.py"
]
```

## Running the Service

### Docker Deployment (Recommended)
Refer to the startup code here: Chinese /data/yaxindu/InfoMosaic/tool_backends/README_zh.md
English: /data/yaxindu/InfoMosaic/tool_backends/REAMDE.md

### Calling the Service

#### Method 1: Using the tool manager built into the Agent framework (Recommended)

```python
class StreamToolManager(BaseToolManager):
    def __init__(self, url, session_id:str = None, timeout:int=180):
        super().__init__(url)
        self.session_id = str(uuid4()) if not session_id else session_id
        self.timeout = timeout

    async def submit_task(self, code:str):
        # Implementation of submitting code tasks
        ...

    async def recieve_task_process(self, ):
        # Implementation of receiving processing results
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

**Usage Notes:**
- Each session needs to maintain its own tool manager instance
- Call `close_session()` to release resources after the session ends
- Call `execute_code_async_stream` to execute code, and results will be streamed back

#### Method 2: Direct HTTP Request to Call the execute Endpoint

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
    start_time = time.time()  # Record start time
    payload = {
        "code": code
    }
    resp = requests.post(
        f"{url}/execute",
        headers=headers,
        json=payload
    )
    response = resp.json()
    elapsed = time.time() - start_time  # Calculate total time consumed
    response['total_time'] = elapsed
    response['server_time'] = resp.elapsed.total_seconds()
    
    return response

code_tool(test_code)
```

## Tool Result Return Format

### Case 1: Direct Tool Call

When a tool returns, the result is included in the other_info field in the following format:

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
                "organic": [/*Search result entries*/],
                "peopleAlsoAsk": [/*Related questions*/],
                "relatedSearches": [/*Related searches*/]
            },
            "tool_elapsed_time": 2.11
        }
    }
}
```

### Case 2: Calling Other Agents as Tools

When calling other agents as tools, the text and tool call results of the other agent are streamed back:

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

## Project Structure

The core components of the MCP tool server include:
- `server/`: Directory for local tool clients
- `config/`: Directory for configuration files, including server_list.json, etc.
- `mcp_manager.py`: Core module for managing tool calls and sessions
- `tool_server.py`: Main entry point for the tool server
- `proxy_service.py`: Proxy service component

## Configuration File Description

Main configuration files include:
- `config/server_list.json`: Defines the list of tool services to load
- `config/llm_call.json`: LLM model call configuration
- `config/mcp_config.json`: Basic configuration for the MCP server

## Troubleshooting Common Issues

1. **Tool Cannot Be Loaded**
   - Check if the file path in server_list.json is correct
   - Ensure the tool function uses the @mcp.tool() decorator

2. **Session Resource Release**
   - Ensure to call the close_session() function after the session ends
   - Long-running services should regularly clean up idle sessions

3. **Performance Optimization**
   - Use Docker deployment and allocate sufficient CPU resources
   - For high concurrency scenarios, increase the number of server instances