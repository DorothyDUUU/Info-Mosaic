import requests
import json

def test_tool(method, params=None):
    """
    Test Serper tools
    
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
        data = params  # Send only the parameter part
        
        # Use Serper SSE service URL
        url = f"http://localhost:30010/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10  # Serper API may require longer timeout
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == True:
                    print("✅ Test succeeded")
                    print(f"Response data: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)[:500]}...")
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
        # Basic search
        ("google_search", {
            "q": "OpenAI latest news",
            "num": 5  # Number type
        }),
        
        # Image search
        ("google_search_images", {
            "q": "cute cats",
            "num": 5  # Number type
        }),
        
        # News search
        ("google_search_news", {
            "q": "artificial intelligence news",
            "num": 5  # Number type
        }),
        
        # Places search
        ("google_search_places", {
            "q": "restaurants in New York"
        }),
        
        # Video search
        ("google_search_videos", {
            "q": "python programming tutorials",
            "num": 5  # Number type
        }),
        
        # Patent search
        ("google_search_patents", {
            "q": "artificial intelligence machine learning patent",
            "num": 5  # Number type
        }),
        
        # Webpage scraping
        ("webpage_scrape", {
            "url": "https://www.example.com"
        })
    ]
    
    print("Starting Serper tool tests...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\nTests completed!")

if __name__ == "__main__":
    main()