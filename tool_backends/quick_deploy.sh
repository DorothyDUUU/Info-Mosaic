#!/bin/bash

# Quick deployment script - One-line command to complete all deployment steps and deploy different services in separate tmux windows

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <container_name>"
    echo "Example: $0 backend_server"
    exit 1
fi

CONTAINER_NAME=$1

# Enter container and execute all deployment steps
docker exec -it $CONTAINER_NAME /bin/bash -c "
    # Create tmux session
    cd /mnt/
    tmux new -d -s server
    
    # Create window 1: SSE Servers
    tmux rename-window -t server:0 'SSE Servers'
    tmux send-keys -t server:SSE\ Servers 'echo "Starting SSE servers deployment..." && \' C-m
    tmux send-keys -t server:SSE\ Servers 'bash /mnt/MCP/deploy_sse_servers.sh && \' C-m
    tmux send-keys -t server:SSE\ Servers 'echo "SSE servers deployment completed!"' C-m
    
    # Create window 2: API Proxy
    tmux new-window -t server -n 'API Proxy'
    tmux send-keys -t server:API\ Proxy 'echo "Starting API proxy..." && \' C-m
    tmux send-keys -t server:API\ Proxy 'cd /mnt/api_proxy && \' C-m
    tmux send-keys -t server:API\ Proxy 'conda deactivate && \' C-m
    tmux send-keys -t server:API\ Proxy 'python api_server.py' C-m
    
    # Create window 3: Main Server
    tmux new-window -t server -n 'Main Server'
    tmux send-keys -t server:Main\ Server 'echo "Starting main server deployment..." && \' C-m
    tmux send-keys -t server:Main\ Server 'sleep 30 && \' C-m  # Give other services some startup time
    tmux send-keys -t server:Main\ Server 'unset http_proxy && \' C-m
    tmux send-keys -t server:Main\ Server 'unset https_proxy && \' C-m
    tmux send-keys -t server:Main\ Server 'conda deactivate && \' C-m
    tmux send-keys -t server:Main\ Server 'pip install google-search-results && \' C-m
    tmux send-keys -t server:Main\ Server 'cd /mnt/MCP/ && \' C-m
    tmux send-keys -t server:Main\ Server 'sh deploy_server.sh && \' C-m
    tmux send-keys -t server:Main\ Server 'echo "Main server deployment completed!"' C-m
    
    # Select first window and attach to session
    echo "All services have been started in different windows of tmux session, attaching to session..."
    tmux select-window -t server:SSE\ Servers
    tmux attach -t server
    
    # Prompt user how to switch between windows
    echo "\nTip: In tmux session, you can use the following shortcuts:"
    echo "- Ctrl+b 0: Switch to SSE Servers window"
    echo "- Ctrl+b 1: Switch to API Proxy window"
    echo "- Ctrl+b 2: Switch to Main Server window"
    echo "- Ctrl+b d: Detach from session"
"

echo "Deployment script execution completed!"

echo "Tip: Your services have been deployed in different windows of the tmux session inside the Docker container."
echo "You can use 'docker exec -it $CONTAINER_NAME /bin/bash tmux attach -t server' to reconnect to the session."