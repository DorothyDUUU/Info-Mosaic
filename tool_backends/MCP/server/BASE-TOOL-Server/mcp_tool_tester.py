import asyncio
import logging
import sys
import os

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("MCP_Tool_Tester")

# Get base paths and add to system path
def setup_paths():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Add MCP directory to path
    mcp_dir = os.path.join(current_dir, '..', '..', '..')  # Point to MCP directory
    if mcp_dir not in sys.path:
        sys.path.append(mcp_dir)
        logger.debug(f"Added to sys.path: {mcp_dir}")
    
    # Add web_agent directory to path
    web_agent_dir = os.path.join(current_dir, 'web_agent')
    if web_agent_dir not in sys.path:
        sys.path.append(web_agent_dir)
        logger.debug(f"Added to sys.path: {web_agent_dir}")
    
    return current_dir

# Test web_search function
async def test_web_search():
    logger.info("===== Testing web_search function ======")
    try:
        from web_agent.web_search import google_search
        logger.debug("Successfully imported google_search function")
        
        query = "What is Python programming language"
        logger.info(f"Searching for: {query}")
        result = await google_search(query, top_k=3)
        
        logger.info(f"Search result type: {type(result)}")
        if result:
            logger.info(f"Search result contains {len(result.get('results', []))} items")
            # Print first two results as example
            for i, item in enumerate(result.get('results', [])[:2]):
                logger.debug(f"Result {i+1} title: {item.get('title', 'No title')}")
                logger.debug(f"Result {i+1} URL: {item.get('url', 'No URL')}")
                logger.debug(f"Result {i+1} snippet: {item.get('snippet', 'No snippet')[:100]}...")
        else:
            logger.warning("Search returned empty result")
            
        return result
    except Exception as e:
        logger.error(f"Error in web_search test: {str(e)}", exc_info=True)
        return None

# Test web_parse function
async def test_web_parse():
    logger.info("===== Testing web_parse function ======")
    try:
        from web_agent.web_parse import parse_htmlpage
        logger.debug("Successfully imported parse_htmlpage function")
        
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        user_prompt = "What is Python programming language?"
        logger.info(f"Parsing URL: {url}")
        logger.info(f"User prompt: {user_prompt}")
        
        result = await parse_htmlpage(url, user_prompt, llm="gpt-4.1-nano-2025-04-14")
        
        logger.info(f"Parse result type: {type(result)}")
        if result:
            logger.info(f"Parse result content length: {len(result.get('content', ''))}")
            logger.info(f"Parse result score: {result.get('score', 'No score')}")
            logger.info(f"Parse result contains {len(result.get('urls', []))} URLs")
            # Print first 200 characters of content as example
            logger.debug(f"Content preview: {result.get('content', '')[:200]}...")
        else:
            logger.warning("Parse returned empty result")
            
        return result
    except Exception as e:
        logger.error(f"Error in web_parse test: {str(e)}", exc_info=True)
        return None

# Test MCP server call
async def test_mcp_server():
    logger.info("===== Testing MCP server directly ======")
    try:
        from mcp.server.fastmcp import FastMCP
        logger.debug("Successfully imported FastMCP")
        
        # Create a temporary MCP instance for testing
        temp_mcp = FastMCP("test_mcp")
        
        @temp_mcp.tool()
        async def test_tool():
            """A simple test tool"""
            return {"status": "success", "message": "Test tool works!"}
        
        # Test if tool registration is successful
        logger.debug(f"Registered tools: {temp_mcp.tool}")
        
        # If successful, return success message
        return {"status": "success", "message": "MCP server initialized successfully"}
    except Exception as e:
        logger.error(f"Error in MCP server test: {str(e)}", exc_info=True)
        return None

# Main test function
async def main():
    logger.info("Starting MCP Tool Tester...")
    
    # Set up paths
    current_dir = setup_paths()
    logger.info(f"Current directory: {current_dir}")
    
    # Test config manager
    try:
        from MCP.config_manager import config_manager
        logger.info("Successfully imported config_manager")
        logger.debug(f"Tool API URL: {config_manager.get_tool_api_url()}")
        logger.debug(f"Web agent config: {config_manager.get_web_agent_config().keys()}")
    except Exception as e:
        logger.error(f"Error importing config_manager: {str(e)}", exc_info=True)
    
    # Run individual tests
    search_result = await test_web_search()
    logger.info("\n")  # Add blank line to separate output
    parse_result = await test_web_parse()
    logger.info("\n")  # Add blank line to separate output
    mcp_result = await test_mcp_server()
    
    # Summary
    logger.info("===== Test Summary =====")
    logger.info(f"Web search test: {'PASSED' if search_result else 'FAILED'}")
    logger.info(f"Web parse test: {'PASSED' if parse_result else 'FAILED'}")
    logger.info(f"MCP server test: {'PASSED' if mcp_result else 'FAILED'}")
    
    # Provide possible fixes if tests fail
    if not search_result:
        logger.warning("Possible issues with web search:")
        logger.warning("1. Check if the search API is reachable")
        logger.warning("2. Verify serper_api_key in configuration")
        logger.warning("3. Check network connectivity")
    
    if not parse_result:
        logger.warning("Possible issues with web parse:")
        logger.warning("1. Check if the LLM API is configured correctly")
        logger.warning("2. Verify internet connectivity")
        logger.warning("3. Check HTML fetching functionality")

if __name__ == "__main__":
    asyncio.run(main())