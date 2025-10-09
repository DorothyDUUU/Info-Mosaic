import requests
import json

def test_tool(method, params=None):
    """
    Test Google Maps tools
    
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
        
        # Use Google Maps SSE service URL
        url = f"http://localhost:30010/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30  # Google Maps API may require longer timeout
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == True:
                    print("✅ Test succeeded")
                    print(f"Response data: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)[:500]}...")
                    return result.get('result')  # Return result for use in workflow tests
                else:
                    print(f"⚠️ Request succeeded but returned failure status: {result.get('result')}")
            except json.JSONDecodeError:
                print(f"⚠️ Response is not valid JSON format: {response.text[:200]}")
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            print(f"Response content: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error occurred during testing: {str(e)}")
    return None

def test_place_details_workflow():
    """
    Test complete workflow for obtaining place details: first search for place, then get details
    """
    print("\n" + "="*60)
    print("Testing place details retrieval workflow")
    print("="*60)
    
    # Step 1: Search for place to get place_id
    print("1. Using google_map_get_place_id tool to obtain place ID")
    place_ids_result = test_tool("google_map_get_place_id", {
        "query": "Starbucks near Times Square New York",
        "max_results": 1
    })
    
    if place_ids_result and isinstance(place_ids_result, list) and len(place_ids_result) > 0:
        place_id = place_ids_result[0].get("place_id")
        print(f"Found place_id: {place_id}")
        
        # Step 2: Use place_id to get place details
        print("\n2. Using obtained place_id to call google_map_get_place_details tool")
        test_tool("google_map_get_place_details", {
            "query": place_id,
            "is_accurate_id": True
        })
    else:
        print("Unable to obtain valid place_id, workflow test failed")

    # Test getting place details directly through query
    print("\n3. Calling google_map_get_place_details tool directly with query term")
    test_tool("google_map_get_place_details", {
        "query": "Eiffel Tower, Paris, France",
        "is_accurate_id": False
    })

def main():
    # Test cases list - corresponding to tools actually implemented in the server
    test_cases = [
        # 1. google_map_get_map_direction - Get route planning
        ("google_map_get_map_direction", {
            "start": "Tiananmen Square, Beijing, China",
            "end": "Beijing Capital International Airport, China",
            "travel_mode": 0  # 0 = Driving
        }),
        
        # Walking route
        ("google_map_get_map_direction", {
            "start": "People's Square, Shanghai, China",
            "end": "The Bund, Shanghai, China",
            "travel_mode": 2  # 2 = Walking
        }),
        
        # Transit route
        ("google_map_get_map_direction", {
            "start": "Times Square, New York, NY",
            "end": "JFK Airport, New York, NY",
            "travel_mode": 3  # 3 = Transit
        }),
        
        # 2. googlemap_search_places - Search places (return formatted text)
        ("googlemap_search_places", {
            "query": "Pizza restaurant in New York",
            "max_results": 5,
            "structured": False
        }),
        
        # Search places (return structured data)
        ("googlemap_search_places", {
            "query": "Hotel near Times Square New York",
            "max_results": 3,
            "structured": True
        }),
        
        # Search landmarks
        ("googlemap_search_places", {
            "query": "Tourist attractions in Paris",
            "max_results": 5,
            "structured": False
        }),
        
        # 3. google_map_get_place_id - Get place ID
        ("google_map_get_place_id", {
            "query": "Starbucks in San Francisco",
            "max_results": 3
        }),
        
        # Get landmark building's place_id
        ("google_map_get_place_id", {
            "query": "Eiffel Tower, Paris",
            "max_results": 1
        }),
        
        # 4. google_map_get_place_details - Get place details through query term
        ("google_map_get_place_details", {
            "query": "Empire State Building, New York",
            "is_accurate_id": False
        })
    ]
    
    print("Starting Google Maps tool tests...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
    
    # Test place details retrieval workflow
    test_place_details_workflow()
        
    print("\nTests completed!")

if __name__ == "__main__":
    main()
