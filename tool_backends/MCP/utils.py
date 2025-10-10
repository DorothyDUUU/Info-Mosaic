import os
import asyncio
import requests

from pydantic import BaseModel
from typing import Optional, Tuple, Dict, Any
from mcp_manager import MCPManager
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pyext import RuntimeModule, _RuntimeModule

PORT = os.getenv("PORT", 30010)


class CodeRequest(BaseModel):
    """
    Represents a request body for code execution.

    :ivar code: The Python code string to be executed.
    :ivar timeout: Optional execution timeout in seconds (default is 180).
    :ivar session_id: Identifier for the current session (default is "test_id").
    """

    code: str
    # default timeout settings: 180
    timeout: Optional[int] = 180
    session_id: str = "test_id"


class CodeResponse(BaseModel):
    """
    Represents the response body after code execution.

    :ivar output: The standard output (stdout) from the code execution.
    :ivar error: Optional error message if an exception occurred.
    :ivar execution_time: The time taken for code execution in seconds.
    :ivar session_id: Identifier for the current session.
    """

    output: str
    error: Optional[str]
    execution_time: float
    session_id: str


class CodeSubmitRequest(BaseModel):
    """
    Represents a request body for submitting code (potentially for background execution).

    :ivar code: The Python code string to be submitted.
    :ivar timeout: Optional execution timeout in seconds (default is 180).
    :ivar session_id: Identifier for the current session (default is "test_id").
    """

    code: str
    timeout: Optional[int] = 180
    session_id: str = "test_id"


class CodeSubmitResponse(BaseModel):
    """
    Represents the response body after code submission.

    :ivar status: The status of the submission (e.g., "success").
    :ivar session_id: Identifier for the current session.
    """

    status: str
    session_id: str


class SandboxStreamRequest(BaseModel):
    """
    Represents a request for streaming data related to a sandbox session.

    :ivar session_id: Identifier for the current session.
    :ivar item: A dictionary containing the streaming data item.
    """

    session_id: str
    item: Dict[str, Any]


class SandboxStreamResponse(BaseModel):
    """
    Represents the response after processing a stream request.

    :ivar session_id: Identifier for the current session.
    :ivar flag: A boolean indicating success or failure of the stream operation.
    """

    session_id: str
    flag: bool


def create_lifespan(manager: MCPManager, temp_dir: str):
    """
    Creates an async context manager for the FastAPI application lifespan.
    It handles startup (e.g., manager readiness) and shutdown (e.g., client cleanup).

    :param manager: The MCPManager instance to handle client connections.
    :param temp_dir: A temporary directory path (though not used in the function body,
                     it's included in the signature).
    :return: An asynchronous context manager function for FastAPI's lifespan.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print("Lifespan startup")
        await manager.ready()
        yield
        print("Lifespan shutdown")
        for client in manager.client_list:
            await client.cleanup()

    return lifespan


agent_tools = ["browse_master", "info_master", "intern_s1"]
browse_comp_tools = ["batch_search_and_filter"]


def build_tools_functions(manager: MCPManager) -> str:
    """
    Generates a Python code string containing wrapper functions for all tools
    managed by the MCPManager. These wrappers handle argument parsing,
    inform handler calls for tool start/result, and calling the actual
    tool via 'call_tool'.

    :param manager: The MCPManager instance containing tool definitions.
    :return: A string of Python code defining the tool wrapper functions.
    """
    initial = """import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_dir)))
from tool_caller import call_tool\n"""
    code = ""
    for tool in manager.get_tools():
        schema = tool.get("input_schema")
        arg = ""
        arg_dict = "    tool_args = {"
        if schema:
            for in_arg in schema.get("properties").keys():
                default = ""
                if not (in_arg in schema.get("required", [])):

                    value = schema["properties"][in_arg].get("default")
                    if isinstance(value, str):
                        default = f"='{value}'"
                    else:
                        default = "=" + str(value)
                arg += f"{in_arg}{default},"
                arg_dict += f"'{in_arg}':{in_arg},"
        arg = arg.rstrip(",")
        arg_dict = arg_dict.rstrip(",") + "}"

        # Standard tool function definition
        if (tool["name"] not in agent_tools) and (
            tool["name"] not in browse_comp_tools
        ):
            code += f"def {tool['name']}({arg}):\n{arg_dict}\n    inform_handler.post_tool_start('{tool['name']}')\n    result = call_tool('{tool['name']}', tool_args, inform_handler.session_id)\n    inform_handler.post_tool_result('{tool['name']}', result)\n    return result\n"

        # Browse completion tool function definition (requires session_id in args)
        elif tool["name"] in browse_comp_tools:
            code += f"def {tool['name']}({arg}):\n{arg_dict}\n    tool_args['session_id']=inform_handler.session_id\n    inform_handler.post_tool_start('{tool['name']}')\n    result = call_tool('{tool['name']}', tool_args, inform_handler.session_id)\n    inform_handler.post_tool_result('{tool['name']}', result)\n    return result\n"

        # Agent-specific tool function definition (requires stream_id in args)
        else:
            code += f"def {tool['name']}({arg}):\n{arg_dict}\n    tool_args['stream_id']=inform_handler.session_id\n    inform_handler.post_tool_start('{tool['name']}')\n    result = call_tool('{tool['name']}', tool_args, inform_handler.session_id)\n    inform_handler.post_tool_result('{tool['name']}', result)\n    return result\n"
    return initial + code


def form_item(main_stream_type: str, content: str, stream_state: str) -> Dict[str, Any]:
    """
    Creates a standard dictionary structure for a stream item.

    :param main_stream_type: The main category of the stream item (e.g., "tool_result").
    :param content: The primary content of the item.
    :param stream_state: The current state of the stream (e.g., "running", "finished").
    :return: A dictionary representing the formatted stream item.
    """
    default = {
        "main_stream_type": main_stream_type,
        "sub_stream_type": "",
        "content": content,
        "from_sandbox": True,
        "stream_state": stream_state,
        "other_info": {},
    }
    return default


def post_item_info(session_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends a stream item to the designated endpoint via an HTTP POST request.

    :param session_id: The session identifier.
    :param item: The stream item dictionary to post.
    :return: The JSON response from the server.
    """
    url = f"http://127.0.0.1:{PORT}"
    headers = {"Content-Type": "application/json"}
    payload = {"session_id": session_id, "item": item}
    resp = requests.post(f"{url}/put_item", headers=headers, json=payload)
    response = resp.json()

    return response


class SessionInformHandler:
    """
    Handles posting real-time information (e.g., tool start/result)
    from the sandbox environment back to the main server.

    :ivar session_id: The identifier for the current session.
    :ivar async_inform_queue: An asyncio.Queue for potentially asynchronous
                              information handling (though currently unused in methods).
    """

    def __init__(self, session_id: str):
        """
        Initializes the SessionInformHandler with a specific session ID.
        """
        self.session_id = session_id
        self.async_inform_queue = asyncio.Queue()

    def post_tool_start(
        self,
        tool_name: str,
    ):
        """
        Posts an item indicating that a tool execution has started.

        :param tool_name: The name of the tool that is starting.
        """
        print(f"-----------{self.session_id}---------------")
        formated_item = form_item("tool_result", "", "running")
        formated_item["other_info"]["tool_name"] = tool_name

        response = post_item_info(self.session_id, formated_item)

    def post_tool_result(self, tool_name: str, item: Any):
        """
        Posts an item containing the result of a completed tool execution.

        :param tool_name: The name of the tool that finished execution.
        :param item: The result or output from the tool execution.
        """
        print(f"-----------{self.session_id}---------------")
        # print(item)

        formated_item = form_item("tool_result", "", "running")
        formated_item["other_info"][tool_name] = item

        response = post_item_info(self.session_id, formated_item)


class SessionManager:
    """
    Manages runtime modules for different execution sessions.
    Each session is associated with a pyext.RuntimeModule, which
    can execute code in an isolated, repeatable environment with access
    to dynamically built tool functions.

    :ivar sessions: A dictionary mapping session IDs to their RuntimeModule instances.
    :ivar mcp_manager: The MCPManager instance used to retrieve tool information.
    """

    def __init__(self, mcp_manager: MCPManager):
        """
        Initializes the SessionManager.
        """
        self.sessions: Dict[str, _RuntimeModule] = {}
        self.mcp_manager = mcp_manager

    def build_lib(self) -> str:
        """
        Wrapper around build_tools_functions to generate the library code.

        :return: A string of Python code defining tool wrapper functions.
        """
        return build_tools_functions(self.mcp_manager)

    def get_session(self, session_id: str) -> _RuntimeModule:
        """
        Retrieves an existing session's RuntimeModule or creates a new one
        if the session ID is not found. The new module is initialized with
        the tool functions and a SessionInformHandler.

        :param session_id: The ID of the session to retrieve or create.
        :return: The pyext._RuntimeModule instance for the session.
        """
        if session_id not in self.sessions:
            # Use pyext.RuntimeModule to create a repeatable execution module
            code_string = self.build_lib()
            # print(code_string)
            self.sessions[session_id] = RuntimeModule.from_string(
                f"session_{session_id}", "", ""
            )
            
            # First add the inform_handler to the session
            self.sessions[session_id].__dict__["inform_handler"] = SessionInformHandler(session_id=session_id)
            
            # Then execute the tool functions code to inject them into the session
            exec(code_string, self.sessions[session_id].__dict__)

        return self.sessions[session_id]

    def clear_session(self, session_id: str):
        """
        Clears a specific session's RuntimeModule from the manager.

        :param session_id: The ID of the session to clear.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
