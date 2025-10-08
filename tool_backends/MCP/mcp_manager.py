import os, sys
import json
from typing import List, Dict, Any
from mcp_client import MCPClient

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


def load_serverlist() -> List[str]:
    """
    Loads the list of server endpoints from the 'config/server_list.json' file.

    The configuration file is expected to be a JSON array of strings, where
    each string is a server path (local file) or an SSE URL (http/https link).

    :raises FileNotFoundError: If the configuration file is missing.
    :raises json.JSONDecodeError: If the configuration file content is invalid JSON.
    :return: A list of server configuration strings.
    :rtype: List[str]
    """
    config_path = os.path.join(current_dir, "config/server_list.json")
    with open(config_path, "r") as file:
        return json.load(file)


class MCPManager:
    """
    Manages connections to multiple Multi-Content Protocol (MCP) servers
    and aggregates their available tools.

    It handles initialization, connection, tool renaming (converting 'tool-name'
    to 'tool_name'), and routing tool calls to the correct MCPClient instance.
    """

    def __init__(self):
        """
        Initializes the MCPManager with empty lists and dictionaries to store
        clients, tools, and the mapping between original tool names and
        sanitized function names.
        """
        self.client_list: List[MCPClient] = []
        # Maps sanitized tool function name (e.g., 'search_papers_enhanced') to its client
        self.tool_client: Dict[str, MCPClient] = {}
        # List of aggregated tool descriptions, with names sanitized for use in Python
        self.tool_list: List[Dict[str, Any]] = []
        self.is_ready: bool = False

        # Maps original tool name (e.g., 'search-papers-enhanced') to sanitized function name
        self.tool_to_func: Dict[str, str] = {}
        # Maps sanitized function name to original tool name
        self.func_to_tool: Dict[str, str] = {}

    async def ready(self) -> List[str]:
        """
        Connects to all servers specified in the server list and aggregates their tools.

        This method attempts to connect each server, retrieves its tools, and maps
        them to the correct `MCPClient`. It also performs a name sanitization
        (replacing hyphens '-' with underscores '_') for easier use in Python
        function calls. It filters tools for specific servers (like 'openapi-mcp-server').

        :return: A list of names of the successfully connected servers.
        :rtype: List[str]
        """
        self.is_ready = False
        server_list: List[str] = load_serverlist()

        # Normalize local server paths relative to the current directory
        tmp = []
        for server in server_list:
            is_sse = server.startswith("http")
            if not is_sse:
                tmp.append(os.path.join(current_dir, server))
            else:
                tmp.append(server)

        server_list = tmp
        ready_server = []

        # sys.prefix points to the active virtual environment root directory
        venv_path = sys.prefix if hasattr(sys, "real_prefix") else None

        for server in server_list:
            client = MCPClient(venv_path=venv_path, server=server)
            try:
                name = await client.connect_to_server()

                # Apply tool filtering rules based on server name
                if name == "openapi-mcp-server":
                    allowed_tools = ["search-papers-enhanced", "search-scholars"]
                else:
                    allowed_tools = "all"

                tools = await client.get_tools()
                self.client_list.append(client)

                tool_list_tmp = []

                for tool in tools:
                    # Apply filtering
                    if allowed_tools != "all" and (tool["name"] not in allowed_tools):
                        continue

                    # Sanitize tool name: "tool-name" -> "tool_name"
                    func_name = tool["name"].replace("-", "_")

                    self.tool_to_func[tool["name"]] = func_name
                    self.func_to_tool[func_name] = tool["name"]

                    # Update tool name in the exposed list
                    tool["name"] = func_name

                    self.tool_client[tool["name"]] = client
                    tool_list_tmp.append(tool)

                self.tool_list.extend(tool_list_tmp)

                ready_server.append(name)
                print(f"Server {name} ready.")
            except Exception as e:
                print(
                    f"An error occurred while creating client: {e}. For server {server}."
                )
                await client.cleanup()
                continue

        if ready_server:
            self.is_ready = True
        return ready_server

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Returns the aggregated list of all available tools from all connected servers.

        The tool names in this list are sanitized (using underscores instead of hyphens).

        :return: A list of tool descriptions (dictionaries).
        :rtype: List[Dict[str, Any]]
        """
        return self.tool_list

    def get_toolnames(self) -> List[str]:
        """
        Returns a list of the sanitized names of all available tools.

        :return: A list of tool names (e.g., ['search_papers_enhanced']).
        :rtype: List[str]
        """
        return list(self.tool_client.keys())

    def get_status(self) -> bool:
        """
        Returns the readiness status of the manager.

        The manager is ready if at least one server connected successfully.

        :return: True if the manager has successfully connected to at least one server, False otherwise.
        :rtype: bool
        """
        return self.is_ready

    async def call_tool(self, tool_name: str, tool_args: Dict[str, Any] = None) -> list:
        """
        Calls a specific tool using the appropriate underlying MCPClient.

        It automatically maps the sanitized tool name (e.g., 'search_papers_enhanced')
        back to the original tool name required by the server, and routes the call
        to the correct client instance.

        :param tool_name: The sanitized name of the tool to call (e.g., 'tool_name').
        :type tool_name: str
        :param tool_args: A dictionary of arguments for the tool call. Defaults to None (empty dict).
        :type tool_args: Dict[str, Any], optional
        :raises KeyError: If the provided `tool_name` is not found in the available tools.
        :raises RuntimeError: If the tool call on the server fails.
        :return: The processed result content from the tool call.
        :rtype: list
        """
        if tool_args is None:
            tool_args = {}

        if not self.tool_client.get(tool_name):
            raise KeyError(f"Tool '{tool_name}' not found in tool list.")

        # try:
        # Get the original tool name for the server
        call_tool_name = self.func_to_tool[tool_name]

        # Route the call to the correct client
        result = await self.tool_client[tool_name].call_tool(
            call_tool_name, tool_args
        )
        return result
        # except Exception as e:
        #     # Re-raise as a RuntimeError to signify a tool execution failure
        #     raise RuntimeError(e)

    async def close(self):
        """
        Cleans up all resources by calling `cleanup()` on every managed `MCPClient`.
        """
        for client in self.client_list:
            await client.cleanup()
