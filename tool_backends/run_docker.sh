#!/bin/bash
# Usage: ./run_container.sh <container_name> <image_name>
# Example: ./run_container.sh my_container my_image:latest

# Check arguments
if [ $# -lt 2 ]; then
  echo "Usage: $0 <container_name> <image_name>"
  exit 1
fi

CONTAINER_NAME=$1
IMAGE_NAME=$2
CURRENT_DIR=$(pwd)

# Run container
docker run -d \
  --name "${CONTAINER_NAME}" \
  --cpuset-cpus="0-63" \
  -p 30010:30010 \
  -v ${CURRENT_DIR}/:/mnt \
  "${IMAGE_NAME}" \
  tail -f /dev/null
