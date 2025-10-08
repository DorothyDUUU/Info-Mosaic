import httpx
import hashlib
import os, sys
import uvicorn
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, Optional


START_PORT = int(os.getenv("START_PORT", 30010))
NUM_WORKERS = int(os.getenv("NUM_WORKERS", 1))

# Initialize the FastAPI application
app = FastAPI(
    title="Session-Sticky Proxy",
    description="A load balancer that uses consistent hashing on 'session_id' for sticky routing.",
)

BACKEND_PORTS = range(START_PORT, START_PORT + NUM_WORKERS)
PROXY_TIMEOUT = 36000


def get_port_by_session_id(session_id: str) -> int:
    """
    Calculates the target backend port using consistent hashing based on the session ID.

    This ensures that requests with the same session ID are consistently routed
    to the same backend worker (session stickiness).

    :param session_id: The unique identifier for the user session.
    :return: The target port number for the backend worker.
    """
    # Use MD5 hash of the session_id to deterministically select a worker port
    hash_value = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
    worker_index = hash_value % NUM_WORKERS
    target_port = START_PORT + worker_index
    return target_port


@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(path: str, request: Request):
    """
    A universal API route acting as a session-sticky proxy to backend workers.

    It extracts the 'session_id' from headers, calculates the target port,
    and forwards the request. GET requests are handled as streams, while
    other methods (like POST) return a standard JSON response.

    :param path: The URL path requested by the client.
    :param request: The incoming FastAPI Request object.
    :return: A FastAPI response (JSONResponse or StreamingResponse).
    """
    session_id: str = request.headers.get("session_id")
    print(f"!!!!!!!!!!!!!!!!!!!!{session_id}!!!!!!!!!!!!!!!!!!!!!!!!!")

    if not session_id:
        session_id = str(uuid4())

    port = get_port_by_session_id(session_id)
    target_url = f"http://127.0.0.1:{port}/{path}"

    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        try:
            headers = dict(request.headers)

            if request.method == "POST":
                body = await request.body()
                response = await client.post(target_url, content=body, headers=headers)
                return JSONResponse(
                    status_code=response.status_code, content=response.json()
                )

            elif request.method == "GET":

                async def stream_response():
                    """Generator function to stream raw chunks from the backend response."""
                    async with httpx.AsyncClient(
                        timeout=PROXY_TIMEOUT
                    ) as stream_client:
                        async with stream_client.stream(
                            "GET",
                            target_url,
                            headers=headers,
                            params=request.query_params,
                        ) as response:
                            #! Forward necessary headers and then stream the content
                            for header, value in response.headers.items():
                                if header.lower() not in (
                                    "content-length",
                                    "transfer-encoding",
                                ):
                                    yield f"{header}: {value}\n".encode("utf-8")

                            async for chunk in response.aiter_raw():
                                yield chunk

                return StreamingResponse(
                    stream_response(),
                    media_type=request.headers.get("Accept") or "application/json",
                )

            # Handle all other methods (PUT, DELETE, etc.)
            else:
                response = await client.request(
                    request.method,
                    target_url,
                    headers=headers,
                    params=request.query_params,
                    content=await request.body(),
                )

                return JSONResponse(
                    status_code=response.status_code, content=response.json()
                )

        except Exception as e:
            error_message = f"Proxy error communicating with backend: {e}"
            print(error_message)
            return JSONResponse(status_code=500, content={"error": error_message})


if __name__ == "__main__":
    # Runs the main proxy application using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=30010)
