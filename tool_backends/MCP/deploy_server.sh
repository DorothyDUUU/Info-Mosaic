#!/bin/bash

export START_PORT=40001
export NUM_WORKERS=1
export END_PORT=$((START_PORT + NUM_WORKERS - 1))
export WOLFRAM_API_KEY=E846LLHVGE
export OPENAI_API_KEY="your api key here"
export BASE_URL="your base url"
export GOOGLE_MAPS_API_KEY="your google maps api key"
export AMAP_MAPS_API_KEY="your amaps api key"
export SERPAPI_API_KEY="your serpapi api key"

# start proxy service
# ! attention, change the port to your own
python proxy_service.py &
echo "Starting Proxy Service in $START_PORT"

# starting working instance...
for port in $(seq $START_PORT $END_PORT); do
  PORT=$port python tool_server.py &
  echo "starting working instance...(pid:$!) port:$port"
  sleep 0.1 
done

wait
