Preparing~
not ready yet.

# load docker
docker load -i  /data/shuotang/backend_server_image_v1.tar

# 部署docker
运行容器
cd tool_backends/
bash run_docker.sh <container_name> <image_name>
<container_name> backend_server_yaxin
<image_name> backend_server_image:v1

bash run_docker.sh backend_server_yaxin backend_server_image:v1


## 进入容器
docker exec -it backend_server /bin/bash
tmux new -s server
tmux attach -t server

1. 新建sse
bash /mnt/MCP/deploy_sse_servers.sh
2. 启动proxy
cd /mnt/api_proxy
conda deactivate
python api_server.py
3. 运行server
unset http_proxy
unset https_proxy
conda deactivate
pip install google-search-results
cd /mnt/MCP/
sh deploy_server.sh