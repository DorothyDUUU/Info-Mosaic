import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ConfigManager')

class ConfigManager:
    _instance = None
    _config = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(current_dir)
        
        # Define configuration file paths - Fixed API key path
        self.api_keys_path = os.path.join(current_dir, 'config', 'api_keys.json')
        self.mcp_config_path = os.path.join(self.root_dir, 'configs', 'mcp_config.json')
        self.web_agent_config_path = os.path.join(self.root_dir, 'configs', 'web_agent.json')
        self.llm_call_config_path = os.path.join(self.root_dir, 'configs', 'llm_call.json')
        
        # Load all configurations
        self._load_all_configs()
        
    def _load_all_configs(self):
        """Load all configuration files into a unified configuration object"""
        self._config = {}
        
        # 1. Load API key configuration
        try:
            if os.path.exists(self.api_keys_path):
                with open(self.api_keys_path, 'r', encoding='utf-8') as f:
                    api_keys = json.load(f)
                    self._config.update(api_keys)
                    logger.info(f"Loaded API key configuration: {self.api_keys_path}")
            else:
                logger.warning(f"API key configuration file not found: {self.api_keys_path}")
        except Exception as e:
            logger.error(f"Failed to load API key configuration: {str(e)}")
        
        # 2. Load MCP configuration
        try:
            if os.path.exists(self.mcp_config_path):
                with open(self.mcp_config_path, 'r', encoding='utf-8') as f:
                    mcp_config = json.load(f)
                    self._config.update(mcp_config)
                    logger.info(f"Loaded MCP configuration: {self.mcp_config_path}")
            else:
                # Use default values
                mcp_config = {
                    "tool_api_url": "http://127.0.0.1:1234",
                    "mcp_server_url": "http://127.0.0.1:30010"
                }
                self._config.update(mcp_config)
                logger.info(f"Using default MCP configuration")
        except Exception as e:
            logger.error(f"Failed to load MCP configuration: {str(e)}")
        
        # 3. Load Web Agent configuration
        try:
            if os.path.exists(self.web_agent_config_path):
                with open(self.web_agent_config_path, 'r', encoding='utf-8') as f:
                    web_agent_config = json.load(f)
                    # Merge values from api_keys into web_agent configuration
                    if 'serper_api_key' in web_agent_config and web_agent_config['serper_api_key'].startswith('switch to'):
                        web_agent_config['serper_api_key'] = self._config.get('SerperApiKey', web_agent_config['serper_api_key'])
                    self._config['web_agent'] = web_agent_config
                    logger.info(f"Loaded Web Agent configuration: {self.web_agent_config_path}")
            else:
                # Use default values
                web_agent_config = {
                    "serper_api_key": self._config.get('SerperApiKey', 'your_serper_api_key'),
                    "search_region": "us",
                    "search_lang": "en",
                    "USE_MODEL": "gpt-4o",
                    "BASE_MODEL": "qwen-32b",
                    "user_prompt": {
                        "search_conclusion": "Please analyze the provided web content and extract the information most relevant to the user's question: 1. Reformat the web page into human readable version, provide the raw data, do not miss any useful information. 2. Ensure no fabrication. 3. Give some urls which are related to the user's question. Return the result in JSON format, e.g., {{'content': content,'urls': [{{'url':url,'description':description}},{{'url':url,'description':description}},...],'score': score}}, where 'content' is the core content related to the user's question, url must be related to the user's question. It can be web url or image url. If it is an image URL, you can roughly judge the content of the image based on the text near this URL. If the image is relevant to the search query, you can return this image URL. You must return some image urls. 'description' is the description of the url. If there is no related url, return empty list. 'score' is the relevance score between 0 and 1, indicating how relevant the web content is to the user's question. Limit the overall response to within 500 words, and provide only the most important URLs, no more than 2. The user's question is: {user}, and the web content is: {info}."
                    }
                }
                self._config['web_agent'] = web_agent_config
                logger.info(f"Using default Web Agent configuration")
        except Exception as e:
            logger.error(f"Failed to load Web Agent configuration: {str(e)}")
        
        # 4. Load LLM call configuration
        try:
            if os.path.exists(self.llm_call_config_path):
                with open(self.llm_call_config_path, 'r', encoding='utf-8') as f:
                    llm_config = json.load(f)
                    # Merge values from environment variables
                    for model_name, model_config in llm_config.items():
                        if 'url' in model_config and not model_config['url']:
                            model_config['url'] = self._config.get('BaseUrl', '')
                        if 'authorization' in model_config and (not model_config['authorization'] or model_config['authorization'] == 'EMPTY'):
                            model_config['authorization'] = self._config.get('OpenaiApiKey', '')
                    self._config['llm_call'] = llm_config
                    logger.info(f"Loaded LLM call configuration: {self.llm_call_config_path}")
            else:
                # Use default values
                base_url = self._config.get('BaseUrl', '')
                openai_key = self._config.get('OpenaiApiKey', '')
                llm_config = {
                    "gpt-4o": {
                        "url": base_url,
                        "authorization": openai_key,
                        "retry_time": 3
                    },
                    "gpt-4.1-nano-2025-04-14": {
                        "url": base_url,
                        "authorization": openai_key,
                        "retry_time": 3
                    },
                    "qwen-32b": {
                        "url": "",
                        "authorization": openai_key,
                        "retry_time": 3,
                        "tool_link": ""
                    },
                    "qwen-72b": {
                        "url": "",
                        "authorization": openai_key,
                        "stream_api_base": "",
                        "retry_time": 3
                    }
                }
                self._config['llm_call'] = llm_config
                logger.info(f"Using default LLM call configuration")
        except Exception as e:
            logger.error(f"Failed to load LLM call configuration: {str(e)}")
            
    def get(self, key, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
        
    def get_web_agent_config(self):
        """Get Web Agent configuration"""
        return self._config.get('web_agent', {})
        
    def get_llm_config(self):
        """Get LLM configuration"""
        return self._config.get('llm_call', {})
        
    def get_tool_api_url(self):
        """Get tool API URL"""
        return self._config.get('tool_api_url', 'http://127.0.0.1:1234')

# Create global configuration manager instance
config_manager = ConfigManager.get_instance()

if __name__ == "__main__":
    config_manager = ConfigManager.get_instance()
