# API 密钥与配置管理指南

## 快速开始指南

如果您只想快速配置项目，请按照以下最简单的步骤操作：

1. 复制模板文件：将 `api_keys.template.json` 重命名为 `api_keys.json`
2. 编辑配置：在 `api_keys.json` 中填写您的实际 API 密钥
3. 启动项目：配置文件会被自动加载，无需额外设置

如需详细了解配置机制或解决问题，请继续阅读以下内容。
---

本文档详细介绍了 InfoMosaic 项目中工具后端服务的 API 密钥和配置管理机制，帮助您安全、便捷地配置和使用各种第三方服务。

## 📚 配置管理系统概述

InfoMosaic 使用 `ConfigManager` 类（单例模式）统一管理所有配置，包括 API 密钥和各服务配置。该系统会自动加载多个配置文件，并将它们合并为一个统一的配置对象。

### 核心配置文件

系统会加载以下配置文件（按优先级从高到低排序）：

1. **API 密钥配置**：`config/api_keys.json` - 存储所有第三方服务的 API 密钥
2. **MCP 配置**：`configs/mcp_config.json` - 存储 MCP 服务的基础配置
3. **Web Agent 配置**：`configs/web_agent.json` - 存储 Web 代理服务的配置
4. **LLM 调用配置**：`configs/llm_call.json` - 存储大语言模型的调用配置

## 🔑 API 密钥配置方法

### 配置步骤

1. **手动创建配置文件**
   - 复制模板文件创建您的配置文件：
   
   ```bash
   cp config/api_keys.template.json config/api_keys.json
   ```

2. **编辑配置文件**
   - 使用您喜欢的编辑器打开 `config/api_keys.json`
   - 将其中的默认值替换为您的实际 API 密钥：
   
   ```json
   {
     "FdaApiKey": "your_fda_api_key",
     "FmpApiKey": "your_fmp_api_key",
     "SerperApiKey": "your_serper_api_key",
     "YoutubeApiKey": "your_youtube_api_key",
     "SerpapiKey": "your_serpapi_key",
     "OpenaiApiKey": "your_openai_api_key",
     "BaseUrl": "your_base_url",
     "GoogleMapsApiKey": "your_google_maps_api_key",
     "AmapMapsApiKey": "your_amaps_api_key"
   }
   ```

## ⚙️ 配置加载机制

`ConfigManager` 类通过以下流程加载和管理配置：

1. **初始化阶段**
   - 创建单例实例并确定各配置文件的路径
   - API 密钥配置路径：`MCP/config/api_keys.json`
   - 其他配置文件路径：`tool_backends/configs/`

2. **配置加载流程**
   - 首先加载 API 密钥配置 (`api_keys.json`)
   - 然后加载 MCP 配置 (`mcp_config.json`)
   - 接着加载 Web Agent 配置 (`web_agent.json`)，并自动将 `SerperApiKey` 注入到 Web Agent 配置中
   - 最后加载 LLM 调用配置 (`llm_call.json`)，并自动将 `OpenaiApiKey` 和 `BaseUrl` 注入到 LLM 配置中

3. **默认值处理**
   - 对于所有不存在的配置文件，系统会使用内置的默认值
   - 确保即使没有配置文件，系统也能正常启动

## 🔧 LLM 调用配置说明

`llm_call.json` 配置文件用于管理大语言模型的调用参数，系统确实会使用它。配置加载时，系统会自动将 `OpenaiApiKey` 和 `BaseUrl` 从 API 密钥配置注入到 LLM 配置中，覆盖文件中的空值或 "EMPTY" 值。

配置示例：
```json
{
    "gpt-4o": {
        "url": "",
        "authorization": "",
        "retry_time": 3
    },
    "qwen-32b": {
        "url": "",
        "authorization": "EMPTY",
        "retry_time": 3,
        "tool_link": ""
    }
}
```

## 🕸️ Web Agent 配置说明

`web_agent.json` 配置文件管理 Web 代理服务的参数。系统会自动检查并替换 `serper_api_key` 字段的值，当它以 "switch to" 开头时，会使用 API 密钥配置中的 `SerperApiKey` 值。

## 🔐 安全最佳实践

为了保障您的 API 密钥安全，请遵循以下最佳实践：

1. **不要将配置文件提交到版本控制系统**
   - 确保 `config/api_keys.json` 已添加到 `.gitignore` 中
   - 避免在公共仓库中暴露您的 API 密钥

2. **使用最小权限原则**
   - 为每个 API 密钥分配完成任务所需的最小权限
   - 定期检查和更新密钥的权限设置

3. **定期轮换密钥**
   - 定期更换您的 API 密钥以提高安全性
   - 更换后及时更新 `config/api_keys.json` 文件

4. **限制访问权限**
   - 确保只有必要的用户和进程可以访问配置文件
   - 设置适当的文件权限（推荐：`chmod 600 config/api_keys.json`）

## 🛠️ 所需的 API 密钥说明

以下是系统使用的各项 API 密钥及其用途：

| 密钥名称 | 用途 | 获取途径 | 费用状态 |
|---------|------|---------|---------|
| FdaApiKey | 访问 FDA 相关服务的数据 | [FDA API 申请](https://open.fda.gov/apis/) | 免费 |
| FmpApiKey | 访问 Financial Modeling Prep 服务 | [FMP API 申请](https://site.financialmodelingprep.com/) | 有免费额度 |
| SerperApiKey | 访问 Serper 搜索服务 | [Serper API 申请](https://serper.dev/) | 有免费额度 |
| YoutubeApiKey | 访问 YouTube 数据 API | [Google API Console](https://console.developers.google.com/) | 免费 |
| SerpapiKey | 访问 SerpAPI 搜索引擎结果 | [SerpAPI 申请](https://serpapi.com/) | 有免费额度 |
| OpenaiApiKey | 访问 OpenAI API 服务 | [OpenAI API 申请](https://platform.openai.com/) | 付费 |
| BaseUrl | OpenAI API 的基础 URL（用于代理或自定义部署） | 根据您的部署设置 | - |
| GoogleMapsApiKey | 访问 Google Maps API 服务 | [Google Maps API 申请](https://developers.google.com/maps) | 免费 |
| AmapMapsApiKey | 访问高德地图 API 服务 | [高德地图 API 申请](https://lbs.amap.com/) | 有免费额度 |

## ❓ 常见问题解答

### Q: 如何检查配置是否正确加载？
**A:** 系统在启动时会输出日志信息，您可以通过查看日志来确认配置是否成功加载。

### Q: 没有配置文件时系统会如何工作？
**A:** 系统会使用内置的默认配置值，确保基本功能可用，但某些依赖 API 密钥的服务可能无法正常工作。

### Q: 如何修改默认配置？
**A:** 创建相应的配置文件并添加您想要自定义的配置项，系统会优先使用配置文件中的值。

### Q: API 密钥如何在不同配置文件之间共享？
**A:** `ConfigManager` 会自动处理配置共享，例如将 `SerperApiKey` 从 API 密钥配置注入到 Web Agent 配置中。

## 🤝 贡献指南

如果您发现任何问题或有改进建议，请随时提交 Issue 或 Pull Request。