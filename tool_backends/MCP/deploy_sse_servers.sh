#!/bin/bash

# Initialize conda environment
echo "Initializing conda environment..."

# Check if running inside Docker container
if [ -f "/.dockerenv" ]; then
    echo "Detected running inside Docker container, using /mnt path..."
    BASE_PATH="/mnt"
else
    echo "Running on host machine, using relative path from script directory..."
    # Use relative path from script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    BASE_PATH="$SCRIPT_DIR/../.."
fi

# Function to stop all services
stop_all_services() {
    echo "Stopping all SSE services..."
    
    # Find and stop all related processes
    pkill -f "biomcp run --mode worker --port 8001"
    pkill -f "python -m src.server --sse --port 8002"
    pkill -f "python run_server.py.*serper"
    pkill -f "python run_server.py.*Youtube"
    
    echo "All SSE services have been stopped"
    exit 0
}

# Check if stop command is requested
if [ "$1" = "stop" ]; then
    stop_all_services
fi

# Activate base environment
echo "Activating base environment..."
conda activate base

# Create log directory
LOG_DIR="$BASE_PATH/MCP/logs"
mkdir -p $LOG_DIR

# Load API key configuration
CONFIG_FILE="$BASE_PATH/MCP/config/api_keys.json"
TEMPLATE_FILE="$BASE_PATH/MCP/config/api_keys.template.json"

# Check if config file exists, if not copy from template
if [ ! -f "$CONFIG_FILE" ]; then
    if [ -f "$TEMPLATE_FILE" ]; then
        echo "Config file $CONFIG_FILE does not exist, creating from template..."
        cp "$TEMPLATE_FILE" "$CONFIG_FILE"
        echo "Please edit $CONFIG_FILE and fill in your API keys before rerunning the script"
        exit 1
    else
        echo "Error: Could not find config file $CONFIG_FILE and template file $TEMPLATE_FILE"
        exit 1
    fi
fi

# Parse config file with sed and grep (based on actual deployment feedback)
echo "Warning: jq not installed, attempting to parse config file with sed and grep..."
FDA_API_KEY=$(grep -oP '"FdaApiKey":\s*"\K[^"]+' "$CONFIG_FILE")
FMP_API_KEY=$(grep -oP '"FmpApiKey":\s*"\K[^"]+' "$CONFIG_FILE")
SERPER_API_KEY=$(grep -oP '"SerperApiKey":\s*"\K[^"]+' "$CONFIG_FILE")
YOUTUBE_API_KEY=$(grep -oP '"YoutubeApiKey":\s*"\K[^"]+' "$CONFIG_FILE")
SERPAPI_KEY=$(grep -oP '"SerpapiKey":\s*"\K[^"]+' "$CONFIG_FILE")

# 1. Start biomcp server
echo "Starting biomcp server (port: 8001)..."
export FDA_API_KEY
cd $BASE_PATH/MCP/sse_server/biomcp-main
biomcp run --mode worker --port 8001 > $LOG_DIR/biomcp.log 2>&1 &
echo "biomcp server started (PID: $!)"

# 2. Start fmp server
echo "Starting fmp server (port: 8002)..."
conda deactivate
conda activate fmp
export FMP_API_KEY
cd $BASE_PATH/MCP/sse_server/fmp-mcp-server
python -m src.server --sse --port 8002 > $LOG_DIR/fmp.log 2>&1 &
echo "fmp server started (PID: $!)"

# 3. Start serper server
echo "Starting serper server (port: 8004)..."
conda deactivate
conda activate base
# Install serper dependencies
pip install aiohttp -q
export SERPER_API_KEY
cd $BASE_PATH/MCP/sse_server/serper-mcp-server-main
python run_server.py > $LOG_DIR/serper.log 2>&1 &
echo "serper server started (PID: $!)"

# 4. Start Youtube server
echo "Starting Youtube server (port: 8005)..."
# Install YouTube dependencies
pip install google-api-python-client youtube-transcript-api google-search-results -q
export YOUTUBE_API_KEY
export SERPAPI_KEY
cd $BASE_PATH/MCP/sse_server/Youtube-Server
python run_server.py > $LOG_DIR/youtube.log 2>&1 &
echo "Youtube server started (PID: $!)"

# Return to base directory
cd $BASE_PATH/MCP

# Display help information
echo ""
echo "All SSE services have been successfully started!"
echo "Service list:"
echo "- biomcp server: http://localhost:8001/sse"
echo "- fmp server: http://localhost:8002/sse"
echo "- serper server: http://localhost:8004/sse"
echo "- Youtube server: http://localhost:8005/sse"
echo ""
echo "To stop all services, run: ./deploy_sse_servers.sh stop"
echo "Log files are located at: $LOG_DIR/"

# Keep script running to display output
sleep 2