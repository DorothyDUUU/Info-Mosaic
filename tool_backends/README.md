# InfoMosaic Tool Backend Services

[中文文档](README_ZH.md)


⚡⚡ **Super Easy Deployment**

InfoMosaic Tool Backend Services provides an extremely simple one-click deployment solution! Just one command to complete all service configuration and startup, no complex manual operations required. Even users with no prior experience can complete the entire deployment process in just a few minutes.

---

## 📚 Project Introduction

InfoMosaic Tool Backend Services are the core components of the InfoMosaic framework, providing support for various tools including web search, map query, document parsing, and more. This directory contains all tool implementations and deployment configurations, supporting quick deployment and usage via Docker.

## 📁 Directory Structure

```
tool_backends/
├── MCP/                     # Modular Computing Platform, tool execution platform
│   ├── config/              # Configuration files directory
│   ├── server/              # Implementation of various tool services
│   ├── sse_server/          # SSE server implementation
│   ├── README_API_KEYS_EN.md # API key configuration guide
│   ├── README_SANDBOX_EN.md # Sandbox usage guide
│   ├── deploy_server.sh     # MCP server deployment script
│   └── deploy_sse_servers.sh # SSE servers deployment script
├── api_proxy/               # API proxy service
├── configs/                 # Global configuration files
│   ├── llm_call.json        # LLM call configuration
│   ├── mcp_config.json      # MCP configuration
│   └── web_agent.json       # Web agent configuration
├── test/                    # Tool test scripts
├── run_docker.sh            # Docker run script
├── quick_deploy.sh          # Quick deployment script
└── README_EN.md             # English documentation
```

## 🔑 API Key Configuration

Before using, you need to configure API keys for each tool. For detailed steps, please refer to:

- [API Key and Configuration Management Guide](MCP/README_API_KEYS_EN.md)

Brief steps:
1. Copy the template file: `cp MCP/config/api_keys.template.json MCP/config/api_keys.json`
2. Edit the `api_keys.json` file and fill in your actual API keys
3. The configuration will be loaded automatically, no additional settings needed

## 🐳 Docker Deployment

### 1. Pull Docker Image

```bash
docker pull dorothyduuu/infomosaic:latest
docker tag dorothyduuu/infomosaic:latest backend_server_image:v1
```

### 2. Run Container

Mount `tool_backends/` to the `/mnt` path in the container, with container name `backend_server` and port `30010`:

```bash
cd tool_backends/
bash run_docker.sh backend_server backend_server_image:v1
```

## 🚀 Quick Deployment

For quick deployment, you can directly use the quick deployment script:

```bash
cd tool_backends/
bash quick_deploy.sh backend_server
```

## 🛠️ Service Management

### Enter Container to Check Deployment Status

```bash
docker exec -it backend_server /bin/bash
tmux attach -t server
```

### Start Services

Inside the container, you can manually start each service:

1. Start SSE servers:
   ```bash
   cd /mnt/MCP
   bash deploy_sse_servers.sh
   ```

2. Start API proxy service:
   ```bash
   cd /mnt/api_proxy
   python api_server.py
   ```

3. Start MCP server:
   ```bash
   cd /mnt/MCP
   sh deploy_server.sh
   ```

### Stop Container

```bash
# Stop container
docker stop backend_server
# Remove container
docker rm backend_server
```

## 🧪 Test Tools

The `test/` directory contains test scripts for various tools. You can use them to verify if the tools are working properly:

```bash
cd tool_backends/test
python test_all.py  # Test all tools
```

Or test individual tools:

```bash
python websearch_test.py  # Test web search tool
python googlemap_test.py  # Test Google Maps tool
```

## 📖 Detailed Documentation

- [Sandbox Working Logic and Usage Guide](MCP/README_SANDBOX_EN.md) - Learn about tool execution mechanisms and how to add new tools
- [API Key and Configuration Management Guide](MCP/README_API_KEYS_EN.md) - Detailed API key configuration instructions

## ❓ FAQ

**Q: What to do if encountering API key errors when starting services?**
A: Please check if the API keys in `MCP/config/api_keys.json` are correct and ensure the file format complies with JSON standards.

**Q: How to add new tools?**
A: Please refer to the "How to Add Tools" section in [Sandbox Working Logic and Usage Guide](MCP/README_SANDBOX_EN.md).

**Q: What to do if services consume too much memory?**
A: You can limit container resource usage through Docker or shut down unnecessary SSE services.

## 🔗 Related Links

- [InfoMosaic Main Project Documentation](../README.md)
- [InfoMosaic Paper](https://arxiv.org/pdf/2510.02271)
- [InfoMosaic_Bench Dataset](https://huggingface.co/datasets/Dorothydu/InfoMosaic_Bench)