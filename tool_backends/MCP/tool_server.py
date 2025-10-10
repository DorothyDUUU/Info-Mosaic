import json
import os
import sys
import asyncio
import uvicorn
import threading
import time
import builtins
import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse


# setting log
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
sys.path.append("..")
current_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(current_dir, "temp")
os.makedirs(temp_dir, exist_ok=True)
sys.path.append(temp_dir)


from mcp_manager import MCPManager

from io_manage import ThreadOutputManager
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from MCP.utils import (
    CodeRequest,
    CodeResponse,
    SandboxStreamRequest,
    SandboxStreamResponse,
    SessionInformHandler,
    CodeSubmitRequest,
    CodeSubmitResponse,
    SessionManager,
    post_item_info,
    form_item,
    create_lifespan,
)

executor = ThreadPoolExecutor(max_workers=1000)
output_manager = ThreadOutputManager()
manager = MCPManager()
session_manager = SessionManager(manager)


# Load agent tools configuration
def load_agent_tools() -> Dict[str, Any]:
    """Loads the agent tools configuration from the local JSON file."""
    config_path = os.path.join(current_dir, "config/agent_tools.json")
    try:
        with open(config_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from: {config_path}")
        return {}


agent_tools = load_agent_tools()
app = FastAPI(lifespan=create_lifespan(manager, temp_dir))

# --- Utility Functions ---


async def put_item_with_session_id(session_id: str, item: Dict[str, Any]) -> bool:
    """
    Puts an item into the asynchronous queue associated with a specific session.

    Args:
        session_id: The unique identifier for the session.
        item: The data item (e.g., tool result, code output) to be queued.

    Returns:
        True if the item was successfully put into the queue, False otherwise.
    """
    try:
        inform_handler: SessionInformHandler = session_manager.sessions[
            session_id
        ].__dict__["inform_handler"]
        await inform_handler.async_inform_queue.put(item)
        return True
    except KeyError:
        logger.error(f"Session ID {session_id} not found when attempting to put item.")
        return False
    except Exception as e:
        logger.error(f"Failed to put item into session queue: {e}", exc_info=True)
        return False


def _execute_code_safely(
    code: str, session_id: str, timeout: int
) -> Tuple[float, Optional[str], Optional[str]]:
    """
    Safely executes Python code within a sandboxed environment in a worker thread.

    This function handles I/O redirection, limits access to file writing,
    and manages execution timeout within the thread.

    Args:
        code: The Python code string to execute.
        session_id: The ID of the session context (for variable persistence).
        timeout: The maximum execution time in seconds.

    Returns:
        A tuple containing (execution_time, stdout_output, error_output).
    """
    logger.info(
        f"Executing in thread {threading.current_thread().ident}, process {os.getpid()} for session {session_id}"
    )

    module = session_manager.get_session(session_id)
    capture = output_manager.get_capture()

    # Define the sandboxed environment dictionary for execution
    sandbox_globals = {
        "print": lambda *args, **kwargs: capture.write(
            " ".join(str(arg) for arg in args)
            + (kwargs.get("end", "\n") if kwargs.get("end") is not None else "\n")
        ),
        "open": restricted_open,
        "__builtins__": builtins,
        "sys": type(
            "sys",
            (),
            {
                "stdout": capture,
                "stderr": capture,
                "stdin": None,
            },
        )(),
    }

    # Update module dictionary with sandbox globals, preserving existing tools
    # This ensures tool functions injected by session manager are not overwritten
    for key, value in sandbox_globals.items():
        if key not in module.__dict__:  # Only add if not already present (preserve tools)
            module.__dict__[key] = value

    error_value = None
    output_value = None
    start_time = time.time()

    # Use a single dedicated executor for the code execution within the worker thread
    single_executor = ThreadPoolExecutor(max_workers=1)

    def run_code():
        """The actual function executed by the sub-thread."""
        start_item = form_item("tool_result", "", "start")
        post_item_info(session_id, start_item)

        cleaned_code = code.replace('\u00a0', ' ').replace('\xa0', ' ')
        
        try:
            compile(cleaned_code, '<string>', 'exec')
            print("Code compilation successful")
        except Exception as e:
            print(f"Code compilation error: {e}")
            raise
        
        # Execute the cleaned code string within the session module's dictionary
        exec(cleaned_code, module.__dict__)

        return capture.get_stdout(), capture.get_stderr()

    try:
        # Submit the code execution task with the timeout
        future = single_executor.submit(run_code)
        output_value, error_value = future.result(timeout=timeout)

    except FutureTimeoutError:
        error_value = f"Execution timed out after {timeout} seconds"
        logger.warning(f"Code execution timeout: {timeout}s")

    except SystemExit as se:
        error_value = f"Code called sys.exit({se.code})"
        if capture.stderr:
            capture.stderr.write(error_value)
        logger.warning(f"Code triggered SystemExit: {error_value}\n\n-----\n{code}")

    except Exception as e:
        # Capture full traceback and clean it for presentation
        error = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        error = error.replace(
            """Traceback (most recent call last):\n  File "<string>", line 1, in <module>\n""",
            "",
        )
        if capture.stderr:
            capture.stderr.write(error)
        logger.warning(f"Code execution error: {error}\n\n-----\n{code}")
        error_value = error

    finally:
        execution_time = time.time() - start_time

        # Ensure output is captured even if an error occurred
        output_value = (
            output_value if output_value is not None else capture.get_stdout()
        )
        error_value = error_value if error_value is not None else capture.get_stderr()

        # Post results back to the session stream
        code_result_content = output_value if not error_value else error_value
        code_result_item = form_item("code_result", code_result_content, "running")
        post_item_info(session_id, code_result_item)

        end_item = form_item("tool_result", "", "end")
        post_item_info(session_id, end_item)

        logger.info(
            f"Execution finished in {execution_time:.2f}s for thread {threading.current_thread().ident}"
        )

    # Return output and error without the execution time from this inner thread
    return execution_time, output_value, error_value if error_value else None


async def execute_python_code(
    code: str, session_id: str, timeout: int
) -> Tuple[str, Optional[str], float]:
    """
    Asynchronously executes Python code by submitting the task to the shared ThreadPoolExecutor.

    Args:
        code: The Python code string to execute.
        session_id: The ID of the session context.
        timeout: The maximum execution time in seconds.

    Returns:
        A tuple containing (stdout_output, error_output, total_execution_time).
    """
    loop = asyncio.get_event_loop()
    start_time = loop.time()

    # Use a semaphore to limit the total number of concurrent code execution tasks
    execution_semaphore = asyncio.Semaphore(2000)

    async with execution_semaphore:
        try:
            # Run the synchronous, blocking code execution function in the thread pool
            execution_time, output, error = await loop.run_in_executor(
                executor, _execute_code_safely, code, session_id, timeout
            )
        except Exception as e:
            error = f"Execution failed in executor: {str(e)}"
            output = ""
            logger.error(f"Unexpected executor error: {error}", exc_info=True)
            execution_time = loop.time() - start_time

    total_exec_time = loop.time() - start_time
    # Note: The `execution_time` returned by `_execute_code_safely` is only the thread's wall time.
    # We use the time measured in the async context for total time.
    return output, error, total_exec_time


def restricted_open(*args, **kwargs):
    """
    A wrapper around builtins.open to restrict file write operations (w, a, +).
    """
    mode = args[1] if len(args) > 1 else kwargs.get("mode", "r")
    if any(m in mode.lower() for m in ("w", "a", "+")):
        raise IOError("File write operations are disabled in this sandbox environment.")
    return builtins.open(*args, **kwargs)


# --- FastAPI Endpoints ---


@app.get("/health")
async def health():
    """Returns a simple status check for the service."""
    return {"status": "ok"}


@app.get("/get_tool")
async def get_tools_all():
    """Returns a list of all available tools managed by MCPManager."""
    return manager.get_tools()


@app.get("/get_tool/{agent_name}")
async def get_tools_by_agent(agent_name: str):
    """
    Returns the tools specific to a named agent, or all tools if the agent is unknown
    or has no specific tools configured.
    """
    if not agent_tools.get(agent_name):
        return manager.get_tools()
    return agent_tools[agent_name]


@app.post("/del_session")
async def del_session(session_id: str):
    """Deletes and clears a specific session context."""
    try:
        session_manager.clear_session(session_id)
        return {"status": "success", "message": f"Session {session_id} cleared."}
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {e}", exc_info=True)
        return {"status": "failed", "message": str(e)}


@app.post("/put_item", response_model=SandboxStreamResponse)
async def put_item(request: SandboxStreamRequest):
    """
    Receives a single item and puts it into the session's stream queue.
    """
    flag = await put_item_with_session_id(request.session_id, request.item)
    return SandboxStreamResponse(session_id=request.session_id, flag=flag)


@app.post("/stream_put_item")
async def stream_put_item(request: Request):
    """
    Receives a stream of newline-separated JSON objects and queues each item
    into its corresponding session.
    """
    buffer = ""
    total_count = 0
    errors = []

    try:
        async for chunk in request.stream():
            text_chunk = chunk.decode("utf-8")
            buffer += text_chunk

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    session_id = data.get("session_id")
                    item = data.get("item", {})

                    if not session_id:
                        raise ValueError("Missing session_id in payload.")

                    await put_item_with_session_id(session_id, item)
                    total_count += 1

                except json.JSONDecodeError:
                    errors.append(
                        {
                            "line": line,
                            "error": "JSONDecodeError - Invalid JSON format.",
                        }
                    )
                except Exception as e:
                    errors.append({"line": line, "error": str(e)})

        return JSONResponse(
            {"status": "ok", "processed_items": total_count, "errors": errors}
        )

    except Exception as e:
        logger.error(f"Error during streaming put item: {e}", exc_info=True)
        return JSONResponse(
            {"error": f"Internal stream error: {str(e)}"}, status_code=500
        )


@app.get("/get_mcp_result/{session_id}")
async def get_mcp_result(session_id: str, request: Request):
    """
    Establishes a StreamingResponse (Server-Sent Events style) to stream
    results from the session's asynchronous queue back to the client.
    """
    try:
        inform_handler: SessionInformHandler = session_manager.sessions[
            session_id
        ].__dict__["inform_handler"]
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Session ID '{session_id}' not found"
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Error retrieving session handler.")

    async def event_generator():
        """Generator function to yield queued items."""
        while True:
            try:
                # Wait for the next item in the queue
                item = await inform_handler.async_inform_queue.get()

                # Yield the item as a JSON string followed by a newline separator
                yield json.dumps(item) + "\n"

                # Check for the 'end' signal to close the stream
                if (not item.get("sub_stream_type")) and (
                    item.get("stream_state") == "end"
                ):
                    break

            except asyncio.CancelledError:
                # The client closed the connection
                logger.info(f"Stream cancelled by client for session {session_id}")
                break
            except Exception as e:
                logger.error(f"Error yielding item for session {session_id}: {e}")
                break  # Exit the loop on unexpected error

    return StreamingResponse(event_generator(), media_type="application/json")


@app.post("/call_tool/{tool_name}")
async def create_tool_task(tool_name: str, tool_args: Dict[str, Any]):
    """
    Calls a registered tool synchronously and returns the result.
    """
    logger.info(f"Calling tool: {tool_name} with args: {tool_args}")

    if tool_name not in manager.get_toolnames():
        raise HTTPException(404, detail=f"Tool '{tool_name}' not found")

    result = None
    status = False

    try:
        raw_results = await manager.call_tool(tool_name, tool_args)
        status = True

        # Attempt to parse results that might be JSON strings
        final_result = []
        for item in raw_results:
            try:
                final_result.append(json.loads(item))
            except Exception:
                final_result.append(item)
        result = final_result

    except Exception as e:
        error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}\n\ntool name: {tool_name}\n\ntool args: {tool_args}"
        logger.error(error_msg)
        result = error_msg
        status = False

    # The original code returns only the first item of the result list,
    # maintaining that behavior:
    final_response_result = result[0] if isinstance(result, list) and result else result

    return {"status": status, "result": final_response_result}


@app.post("/execute", response_model=CodeResponse)
async def execute_code_handler(request: CodeRequest):
    """
    Handles immediate, synchronous execution of Python code in a sandboxed environment.
    The response waits for the code execution to complete.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    logger.info(
        f"Synchronously executing code (timeout: {request.timeout}s) for session: {request.session_id}"
    )

    try:
        output, error, exec_time = await execute_python_code(
            request.code, request.session_id, request.timeout
        )

        logger.info(
            f"Code execution completed in {exec_time:.2f}s. " f"Error: {bool(error)}"
        )

        return CodeResponse(
            output=output,
            error=error,
            execution_time=exec_time,
            session_id=request.session_id,
        )

    except Exception as e:
        logger.error(
            f"Unexpected server error during /execute: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/submit", response_model=CodeSubmitResponse)
async def submit_code_handler(
    request: CodeSubmitRequest, background_tasks: BackgroundTasks
):
    """
    Handles asynchronous code execution by running the task in a background thread
    without blocking the response. Results are streamed back via /get_mcp_result.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    logger.info(
        f"Submitting code for background execution (timeout: {request.timeout}s) for session: {request.session_id}"
    )

    try:
        # Add the code execution task to be run in the background
        background_tasks.add_task(
            execute_python_code, request.code, request.session_id, request.timeout
        )
        logger.info(f"Task submitted to background tasks.")
        return CodeSubmitResponse(status="success", session_id=request.session_id)

    except Exception as e:
        logger.error(f"Unexpected server error during /submit: {str(e)}", exc_info=True)
        # Return a failure response model
        return CodeSubmitResponse(
            status="fail", session_id=request.session_id, message=str(e)
        )


if __name__ == "__main__":
    # Ensure correct structure for uvicorn run when using FastAPI
    PORT = os.getenv("PORT", 40001)

    # Note: When running this file directly, the `tool_server:app` string
    # works because the file is named `tool_server.py` and the FastAPI instance
    # is named `app`.
    uvicorn.run(
        "tool_server:app",
        host="0.0.0.0",
        port=int(PORT),
        lifespan="on",
        workers=1,
    )
