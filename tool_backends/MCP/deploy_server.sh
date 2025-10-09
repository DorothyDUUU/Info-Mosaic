#!/bin/bash

# Load API key configuration
# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$SCRIPT_DIR/config/api_keys.json"
TEMPLATE_FILE="$SCRIPT_DIR/config/api_keys.template.json"

# Set default port configuration
export START_PORT=40001
export NUM_WORKERS=1
export END_PORT=$((START_PORT + NUM_WORKERS - 1))

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

# Check if config file contains actual API keys (not template values)
if grep -q "your_" "$CONFIG_FILE"; then
    echo "Warning: Config file $CONFIG_FILE contains unreplaced default API key template values"
    echo "Please edit $CONFIG_FILE and replace all 'your_*_api_key' with your actual API keys"
fi

# Read API keys from config file
if command -v jq >/dev/null 2>&1; then
    echo "Parsing config file with jq..."
    export OPENAI_API_KEY=$(jq -r '.OpenaiApiKey' "$CONFIG_FILE")
    export BASE_URL=$(jq -r '.BaseUrl' "$CONFIG_FILE")
    export GOOGLE_MAPS_API_KEY=$(jq -r '.GoogleMapsApiKey' "$CONFIG_FILE")
    export AMAP_MAPS_API_KEY=$(jq -r '.AmapMapsApiKey' "$CONFIG_FILE")
    export SERPAPI_API_KEY=$(jq -r '.SerpapiKey' "$CONFIG_FILE")
else
    echo "Warning: jq not installed, attempting to parse config file with sed and grep..."
    export OPENAI_API_KEY=$(grep -oP '"OpenaiApiKey":\s*"\K[^"]+' "$CONFIG_FILE")
    export BASE_URL=$(grep -oP '"BaseUrl":\s*"\K[^"]+' "$CONFIG_FILE")
    export GOOGLE_MAPS_API_KEY=$(grep -oP '"GoogleMapsApiKey":\s*"\K[^"]+' "$CONFIG_FILE")
    export AMAP_MAPS_API_KEY=$(grep -oP '"AmapMapsApiKey":\s*"\K[^"]+' "$CONFIG_FILE")
    export SERPAPI_API_KEY=$(grep -oP '"SerpapiKey":\s*"\K[^"]+' "$CONFIG_FILE")
fi

# Start proxy service
# ! Attention: change the port to your own
echo "Starting Proxy Service on port $START_PORT"
python proxy_service.py &

# Starting working instances...
for port in $(seq $START_PORT $END_PORT); do
  echo "Starting working instance...(pid:$!) on port:$port"
  PORT=$port python tool_server.py &
  sleep 0.1 
done

wait
