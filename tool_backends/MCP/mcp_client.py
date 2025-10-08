import os, sys
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client


class MCPClient:
    """
    A client for connecting to a Multi-Content Protocol (MCP) server,
    which can be a local Python/Node script via stdio or a remote server via SSE.

    It manages the connection, initialization, tool listing, and tool calling
    using asyncio and an AsyncExitStack for resource cleanup.
    """

    def __init__(self, venv_path: Optional[str] = None, server: str = ""):
        """
        Initializes the MCPClient.

        :param venv_path: Optional path to a Python virtual environment to use
                          when running a local Python server.
        :type venv_path: Optional[str]
        :param server: The server endpoint. Can be a path to a local '.py' or
                       '.js' script, or an 'http'/'https' link for an SSE server.
                       If empty, it defaults to 'mcp_server.py' in the current directory.
        :type server: str
        """
        self.venv_path = venv_path
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.server = server
        if not self.server:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.server = os.path.join(current_dir, "mcp_server.py")

    async def connect_to_server(self) -> str:
        """
        Establishes a connection to the configured MCP server.

        Depending on the `server` string, it initializes either an SSE client
        (for http/https links) or an Stdio client (for local .py or .js scripts).
        It then initializes the ClientSession and lists the available tools.

        :raises ValueError: If the server string is not a supported file type (.py, .js)
                            or a valid sse link (http/https), or if the Python executable
                            is not found in the virtual environment path.
        :raises Exception: Catches and re-raises any connection or initialization errors.
        :return: The name of the connected server.
        :rtype: str
        """
        is_python = self.server.endswith(".py")
        is_js = self.server.endswith(".js")
        is_sse = self.server.startswith("http")
        if not (is_python or is_js or is_sse):
            raise ValueError("Server script must be a .py or .js file or a sse link")

        if is_sse:
            try:
                print(self.server)
                streams = await self.exit_stack.enter_async_context(
                    sse_client(self.server)
                )

                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(*streams)
                )
                result = await self.session.initialize()

                response = await self.session.list_tools()
                tools = response.tools
                print(
                    "\nConnected to server with tools:", [tool.name for tool in tools]
                )
                return result.serverInfo.name

            except Exception as e:
                print(f"An error occurred while connecting to the server: {e}")
                raise

        command = "python" if is_python else "node"
        env = os.environ.copy()
        if is_python:
            if self.venv_path:
                if sys.platform == "win32":
                    python_executable = os.path.join(
                        self.venv_path, "Scripts", "python.exe"
                    )
                    env["PATH"] = (
                        os.path.join(self.venv_path, "Scripts")
                        + os.pathsep
                        + env["PATH"]
                    )
                else:
                    python_executable = os.path.join(self.venv_path, "bin", "python")
                    env["PATH"] = (
                        os.path.join(self.venv_path, "bin") + os.pathsep + env["PATH"]
                    )
                if not os.path.exists(python_executable):
                    raise ValueError(
                        f"Python interpreter not found in virtual environment: {python_executable}"
                    )
                command = python_executable
            else:
                command = "python"
        else:
            command = "node"

        server_params = StdioServerParameters(
            command=command, args=[self.server], env=env
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            stdio, write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(stdio, write)
            )
            result = await self.session.initialize()

            response = await self.session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])
            return result.serverInfo.name

        except Exception as e:
            print(f"An error occurred while connecting to the server: {e}")
            raise

    async def get_tools(self) -> list:
        """
        Retrieves the list of tools available on the connected server.

        :raises RuntimeError: If the session is not initialized.
        :return: A list of dictionaries, each describing an available tool
                 with its name, description, and input schema.
        :rtype: list
        """
        if not self.session:
            # This case should ideally be covered by a proper type-checking or a check
            # but raising an error here makes sense if the method is called before connect_to_server.
            raise RuntimeError("Client is not connected to a server. Call connect_to_server first.")

        response = await self.session.list_tools()
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]
        return available_tools

    async def use_tools(self, response_content: list) -> str:
        """
        Processes a list of mixed content (text and tool_use) and executes
        any tool calls found.

        This method iterates through the content, appending text and executing
        tool calls via `self.session.call_tool()`.

        :param response_content: A list of content objects, potentially including
                                 objects with 'tool_use' type.
        :type response_content: list
        :return: A concatenated string of all text content and tool call results,
                 interspersed with information about the tool call itself.
        :rtype: str
        """
        final_text = []

        for content in response_content:
            if content.type == "text":
                final_text.append(content.text)
            elif content.type == "tool_use":
                tool_name = content.name
                tool_args = content.input

                result = await self.session.call_tool(tool_name, tool_args)

                # Appends text content *before* the tool call result, if present
                if hasattr(content, "text") and content.text:
                    final_text.append(content.text)
                
                # Print information about the tool call
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Append the raw result content from the tool call
                final_text.append(result.content)
        return "\n".join(final_text)

    async def call_tool(self, tool_name: str, tool_args: dict) -> list:
        """
        Calls a specific tool on the connected server and processes the results.

        This method is a more structured way to call tools compared to `use_tools`.
        It expects a single tool call and processes its various content types.

        :param tool_name: The name of the tool to call.
        :type tool_name: str
        :param tool_args: A dictionary of arguments for the tool call.
        :type tool_args: dict
        :raises RuntimeError: If the tool call results in an error.
        :return: A list of tool results, with different types (text, image data, resource URI)
                 depending on the server's response content.
        :rtype: list
        """
        result = await self.session.call_tool(tool_name, tool_args)
        if result.isError:
            raise RuntimeError(str(result.content))
        else:
            results = []
            for r in result.content:
                # Use model_dump to convert the Pydantic object to a dictionary
                r_dict = r.model_dump(mode="json", by_alias=True) 
                
                # Extract content based on type
                match r_dict.get("type"):
                    case "text":
                        results.append(r_dict.get("text"))
                    case "image":
                        results.append(r_dict.get("data")) # Assuming 'data' field holds image payload/bytes
                    case "resource":
                        results.append(r_dict.get("resource")) # Assuming 'resource' field holds URI/identifier
            return results

    async def cleanup(self):
        """
        Performs asynchronous cleanup by closing the AsyncExitStack,
        which in turn closes the client session and terminates any
        associated subprocess (for stdio connections).
        """
        await self.exit_stack.aclose()


# Test
async def create_client() -> MCPClient:
    """
    Asynchronously creates an MCPClient, connects it to the server (with default
    parameters), and handles cleanup on failure.

    :raises Exception: Re-raises any error that occurred during client creation or connection.
    :return: An initialized and connected MCPClient instance.
    :rtype: MCPClient
    """
    # The default constructor call MCPClient() will use default venv_path=None 
    # and default server="" (which resolves to "mcp_server.py")
    client = MCPClient() 
    try:
        await client.connect_to_server()
        return client
    except Exception as e:
        print(f"An error occurred while create client: {e}")
        await client.cleanup()
        raise


async def test():
    """
    A simple test function to demonstrate client creation, connection, and cleanup.
    It uses the default server settings.
    """
    client = MCPClient()
    await client.connect_to_server()
    await client.cleanup()


if __name__ == "__main__":
    asyncio.run(test())