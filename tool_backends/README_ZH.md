# InfoMosaic 工具后端服务

⚡⚡ **部署超省心，轻松上手**

InfoMosaic 工具后端服务提供了极其简单的一键部署方案！只需一个命令，即可完成所有服务的配置和启动，无需复杂的手动操作。即使是初次接触的用户，也能在几分钟内完成整个部署流程。

---

## 📚 项目简介

InfoMosaic 工具后端服务是 InfoMosaic 框架的核心组件，提供了多种工具服务支持，包括网络搜索、地图查询、文档解析等功能。工具沙盒经过测试可以实现500次的并发请求。

## 🐳 Docker 部署 (三步设置好你的工具沙盒)

### 1. 拉取Docker镜像

```bash
docker pull dorothyduuu/infomosaic:latest
docker tag dorothyduuu/infomosaic:latest backend_server_image:v1
```

### 2. 运行容器

将`tool_backends/`挂载到容器的`/mnt`路径下，container的名字为backend_server，端口为30010：

```bash
cd tool_backends/
bash run_docker.sh backend_server backend_server_image:v1
```

## 🚀 快速部署

对于快速部署，可以直接使用快速部署脚本：

```bash
cd tool_backends/
bash quick_deploy.sh backend_server
```

## 🛠️ 服务管理

### 进入容器查看部署情况

```bash
docker exec -it backend_server /bin/bash
tmux attach -t server
```

### 停止容器

```bash
# 停止容器
docker stop backend_server
# 删除容器
docker rm backend_server
```

## 🔑 API 密钥配置

使用前需要配置各工具的API密钥，详细步骤请参考：

- [API 密钥与配置管理指南](MCP/README_API_KEYS_ZH.md)

## 🧪 测试工具

`test/`目录下包含了各种工具的测试脚本，您可以使用它们来验证工具是否正常工作。