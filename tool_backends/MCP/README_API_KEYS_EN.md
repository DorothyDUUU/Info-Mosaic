# API Key and Configuration Management Guide

## Quick Start Guide

If you just want to quickly configure the project, follow these simplest steps:

1. Copy the template file: Rename `api_keys.template.json` to `api_keys.json`
2. Edit the configuration: Fill in your actual API keys in `api_keys.json`
3. Start the project: Configuration files will be automatically loaded, no additional setup needed

For detailed information about the configuration mechanism or to troubleshoot issues, continue reading the following content.
---

This document provides detailed information about the API key and configuration management mechanism for the InfoMosaic project's tool backend services, helping you securely and conveniently configure and use various third-party services.

## 📚 Configuration Management System Overview

InfoMosaic uses the `ConfigManager` class (singleton pattern) to uniformly manage all configurations, including API keys and service configurations. This system automatically loads multiple configuration files and merges them into a unified configuration object.

### Core Configuration Files

The system loads the following configuration files (sorted by priority from highest to lowest):

1. **API Key Configuration**: `config/api_keys.json` - Stores API keys for all third-party services
2. **MCP Configuration**: `configs/mcp_config.json` - Stores basic configuration for MCP services
3. **Web Agent Configuration**: `configs/web_agent.json` - Stores configuration for web agent services
4. **LLM Call Configuration**: `configs/llm_call.json` - Stores configuration for large language model calls

## 🔑 API Key Configuration Methods

### Configuration Steps

1. **Manually Create Configuration File**
   - Copy the template file to create your configuration file:
   
   ```bash
   cp config/api_keys.template.json config/api_keys.json
   ```

2. **Edit Configuration File**
   - Open `config/api_keys.json` with your preferred editor
   - Replace the default values with your actual API keys:
   
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

## ⚙️ Configuration Loading Mechanism

The `ConfigManager` class loads and manages configurations through the following process:

1. **Initialization Phase**
   - Creates a singleton instance and determines the paths for each configuration file
   - API key configuration path: `MCP/config/api_keys.json`
   - Other configuration file paths: `tool_backends/configs/`

2. **Configuration Loading Process**
   - First loads the API key configuration (`api_keys.json`)
   - Then loads the MCP configuration (`mcp_config.json`)
   - Next loads the Web Agent configuration (`web_agent.json`), and automatically injects `SerperApiKey` into the Web Agent configuration
   - Finally loads the LLM call configuration (`llm_call.json`), and automatically injects `OpenaiApiKey` and `BaseUrl` into the LLM configuration

3. **Default Value Handling**
   - For all non-existent configuration files, the system uses built-in default values
   - Ensures the system can start normally even without configuration files

## 🔧 LLM Call Configuration Description

The `llm_call.json` configuration file is used to manage the call parameters of large language models, and the system does use it. During configuration loading, the system automatically injects `OpenaiApiKey` and `BaseUrl` from the API key configuration into the LLM configuration, overwriting empty or "EMPTY" values in the file.

Configuration example:
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

## 🕸️ Web Agent Configuration Description

The `web_agent.json` configuration file manages the parameters of the web agent service. The system automatically checks and replaces the value of the `serper_api_key` field. When it starts with "switch to", it uses the `SerperApiKey` value from the API key configuration.

## 🔐 Security Best Practices

To ensure the security of your API keys, please follow these best practices:

1. **Do not commit configuration files to version control**
   - Ensure `config/api_keys.json` is added to `.gitignore`
   - Avoid exposing your API keys in public repositories

2. **Use the principle of least privilege**
   - Assign each API key the minimum permissions required to complete the task
   - Regularly check and update the permission settings for keys

3. **Rotate keys regularly**
   - Regularly change your API keys to improve security
   - Update the `config/api_keys.json` file promptly after changing keys

4. **Restrict access permissions**
   - Ensure only necessary users and processes can access configuration files
   - Set appropriate file permissions (recommended: `chmod 600 config/api_keys.json`)

## 🛠️ Required API Keys Description

The following are the API keys used by the system and their purposes:

| Key Name | Purpose | Acquisition Method | Cost Status |
|---------|---------|-------------------|------------|
| FdaApiKey | Access data from FDA-related services | [FDA API Application](https://open.fda.gov/apis/) | Free |
| FmpApiKey | Access Financial Modeling Prep services | [FMP API Application](https://site.financialmodelingprep.com/) | Free tier available |
| SerperApiKey | Access Serper search services | [Serper API Application](https://serper.dev/) | Free tier available |
| YoutubeApiKey | Access YouTube Data API | [Google API Console](https://console.developers.google.com/) | Free |
| SerpapiKey | Access SerpAPI search engine results | [SerpAPI Application](https://serpapi.com/) | Free tier available |
| OpenaiApiKey | Access OpenAI API services | [OpenAI API Application](https://platform.openai.com/) | Paid |
| BaseUrl | Base URL for OpenAI API (for proxy or custom deployment) | According to your deployment settings | - |
| GoogleMapsApiKey | Access Google Maps API services | [Google Maps API Application](https://developers.google.com/maps) | Free |
| AmapMapsApiKey | Access Amap Maps API services | [Amap Maps API Application](https://lbs.amap.com/) | Free tier available |

## ❓ Frequently Asked Questions

### Q: How to check if the configuration is loaded correctly?
**A:** The system outputs log information at startup. You can confirm whether the configuration was successfully loaded by checking the logs.

### Q: How does the system work without configuration files?
**A:** The system uses built-in default configuration values to ensure basic functionality is available, but some services that depend on API keys may not work properly.

### Q: How to modify the default configuration?
**A:** Create the corresponding configuration file and add the configuration items you want to customize. The system will prioritize using the values in the configuration file.

### Q: How are API keys shared between different configuration files?
**A:** `ConfigManager` automatically handles configuration sharing, for example, injecting `SerperApiKey` from the API key configuration into the Web Agent configuration.

## 🤝 Contribution Guide

If you find any issues or have improvement suggestions, please feel free to submit Issues or Pull Requests.