import requests
import json

def test_tool(method, params=None):
    """
    Test YouTube tools
    
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
        
        # Use YouTube MCP service URL
        url = f"http://localhost:30010/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=300
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == True:
                    print("✅ Test succeeded")
                    print(f"Response data: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)}...")
                else:
                    print(f"⚠️ Request succeeded but returned failure status: {result.get('result')}")
            except json.JSONDecodeError:
                print(f"⚠️ Response is not valid JSON format: {response.text}")
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            print(f"Response content: {response.text}")
            
    except Exception as e:
        print(f"❌ Error occurred during testing: {str(e)}")

def main():
    # Use a sample video ID and channel ID for testing
    test_video_id = "QtIlD6uxwwk" #"dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    test_channel_id = "UCuAXFkgsw1L7xaCfnd5JJOw"  # Rick Astley's channel
    
    # List of test cases
    test_cases = [
        # Search videos
        ("search_videos", {
            "query": "Rick Astley Never Gonna Give You Up",
            "max_results": 5,
            "order": "relevance"
        }),
        
        # Get video details
        ("get_video_details", {
            "video_id": test_video_id
        }),
        
        # Get channel details
        ("get_channel_details", {
            "channel_id": test_channel_id
        }),
        
        # Get video comments
        ("get_video_comments", {
            "video_id": test_video_id,
            "max_results": 5,
            "order": "relevance",
            "include_replies": True
        }),
        
        # Get video transcript
        ("get_video_transcript", {
            "video_id": test_video_id,
            "language": "en"  # English subtitles
        }),
        
        # Get related videos
        ("get_related_videos", {
            "video_id": test_video_id,
            "max_results": 5
        }),
        
        # Get trending videos
        ("get_trending_videos", {
            "region_code": "US",
            "max_results": 5
        }),
        
        # Get enhanced transcript
        ("get_video_enhanced_transcript", {
            "video_ids": [test_video_id],
            "language": "en",
            "format": "timestamped",
            "include_metadata": True,
            "segment_method": "equal",
            "segment_count": 2
        })
    ]
    
    print("Starting YouTube tool tests...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\nTests completed!")

if __name__ == "__main__":
    main()
