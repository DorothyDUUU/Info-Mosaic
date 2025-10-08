#!/bin/bash
# 用法: ./run_container.sh <container_name> <image_name>
# 示例: ./run_container.sh my_container my_image:latest

# 参数检查
if [ $# -lt 2 ]; then
  echo "用法: $0 <container_name> <image_name>"
  exit 1
fi

CONTAINER_NAME=$1
IMAGE_NAME=$2
CURRENT_DIR=$(pwd)

# 运行容器
docker run -d \
  --name "${CONTAINER_NAME}" \
  --cpuset-cpus="0-63" \
  -p 30010:30010 \
  -v ${CURRENT_DIR}/:/mnt \
  "${IMAGE_NAME}" \
  tail -f /dev/null
