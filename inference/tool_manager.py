from uuid import uuid4
import requests
import asyncio
import aiohttp
import httpx
import json
import threading



class BaseToolManager:
    def __init__(self, url:str, session_id:str = None, timeout:int=180):
        self.server_url = url
        self.headers = {
            "Content-Type": "application/json"
        }
        self.session_id = str(uuid4()) if not session_id else session_id
        self.headers['session_id'] = session_id
        # self.session_id = str("test_id2")
        self.timeout = timeout

    def execute_tool(self, tool_call:str):
        
        payload = {
            "code":tool_call,
            "session_id":self.session_id,
            "timeout": self.timeout
        }
        # print("execution...")
        resp = requests.post(
            f"{self.server_url}/execute",
            headers=self.headers,
            json=payload
        )
        # print(resp)
        return resp.json()
    
    def del_session(self):
        print(self.session_id)
        url = f"{self.server_url}/del_session"
        params = {"session_id": self.session_id}
        headers = self.headers

        resp = requests.post(url, params=params, headers=headers)
        
        return resp.json()


class AsyncToolManager(BaseToolManager):
    def __init__(self, url):
        super().__init__(url)

    async def execute_tool_async(self, tool_call: str):
        # tool_call = "from tools import *\n" + tool_call
        payload = {
            "code": tool_call
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.server_url}/execute",
                    headers=self.headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": "Request failed", "status_code": resp.status}
            except Exception as e:
                return {"error": str(e)}    


class StreamToolManager(BaseToolManager):
    def __init__(self, url, session_id:str = None, timeout:int=180):
        super().__init__(url)
        self.session_id = str(uuid4()) if not session_id else session_id
        self.headers['session_id'] = session_id
        # self.session_id = str("test_id2")
        self.timeout = timeout

    async def submit_task(self, code:str):
        submit_url = f"{self.server_url}/submit"

        payload = {
            "code":code,
            "session_id":self.session_id,
            "timeout": self.timeout
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    submit_url,
                    headers=self.headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"status": "fail", "status_code": resp.status}
            except Exception as e:
                return {"status": "fail", "error":f"{e}"}


    async def recieve_task_process(self, ):
        recieve_url = f"{self.server_url}/get_mcp_result/{self.session_id}"
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", recieve_url, headers=self.headers) as response:
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    # print("Received:", data)
                    # print(data['content'], end="", flush=True)
                    # print(data['content'], data['stream_state'])


                    if (not data.get("sub_stream_type")) and (data.get("stream_state") == "end"):
                        yield data
                        break    
                    else:
                        yield data
                        
    async def execute_code_async_stream(self, tool_call: str,):
        submit_status = await self.submit_task(tool_call)
        if submit_status["status"] == "fail":
            yield {"output":""}
            return
        
        # await self.recieve_task_process()
        # print('start recieve')
        async for item in self.recieve_task_process():
            yield item

    async def execute_code_async_resonly(self, tool_call:str):
        submit_status = await self.submit_task(tool_call)
        if submit_status["status"] == "fail":
            return {"output":"code submit fail"}
        
        # await self.recieve_task_process()
        async for item in self.recieve_task_process():
            if item["main_stream_type"] == "code_result":
                return_value = {"output":item['content']}
            
             
        return return_value

    async def close_session(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.server_url}/del_session",
                params={"session_id": self.session_id},
                headers=self.headers
            )
            return resp.json()



if __name__ == '__main__':


    tool_manager = BaseToolManager(url="http://127.0.0.1:30010", session_id="hahahha")
    
    test_code = f"""# test code
def sum(a, b):
    return a+b
output = sum(1,2)
print(output)

# test tool
result = web_search(query="what is google?")
print(result)
# # print(search_r1(queries=["What is Python?", "Tell me about neural networks."]))
# """

    res = tool_manager.execute_tool(test_code)
    print(res)
    print(tool_manager.del_session())
