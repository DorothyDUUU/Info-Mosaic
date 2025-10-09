import requests
import json

def test_tool(method, params=None):
    """
    Test Web search and parsing tools
    
    Args:
        method: Tool method name
        params: Request parameters (optional)
    """
    if params is None:
        params = {}
        
    print(f"\nTesting tool: {method}")
    print(f"Parameters: {params}")
    
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Construct request data
        data = params
        
        url = f"http://localhost:30010/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30  # Increased timeout as web search and parsing may take longer
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == True:
                    print("✅ Test succeeded")
                    print(f"Response data: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)[:1000]}...")
                else:
                    print(f"⚠️ Request succeeded but returned failure status: {result.get('result')}")
            except json.JSONDecodeError:
                print(f"⚠️ Response is not valid JSON format: {response.text[:200]}")
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            print(f"Response content: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error occurred during testing: {str(e)}")

def main():
    # Test cases list
    test_cases = [
        # Web search test cases
        ("web_search", {
            "query": "OpenAI ChatGPT latest news",
            "top_k": 10  # Adding optional parameter
        }),
        
        # Web parsing test cases
        ("web_parse", {
            "link": "https://www.python.org/about/",
            "user_prompt": "What is Python programming language?"
        })

    ]
    
    print("Starting Web search and parsing tool tests...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\nTests completed!")

if __name__ == "__main__":
    main()