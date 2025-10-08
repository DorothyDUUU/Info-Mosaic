import requests
import json

def test_tool(method, params=None):
    """
    测试 Google Maps 工具
    
    Args:
        method: 工具方法名
        params: 请求参数（可选）
    """
    if params is None:
        params = {}
        
    print(f"\n测试工具: {method}")
    print(f"参数: {params}")
    
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 构建请求数据
        data = params  # 只发送参数部分
        
        # 使用 Google Maps SSE 服务的 URL
        url = f"http://localhost:30009/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30  # Google Maps API 可能需要更长的超时时间
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == True:
                    print("✅ 测试成功")
                    print(f"响应数据: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)[:500]}...")
                else:
                    print(f"⚠️ 请求成功但返回状态为失败: {result.get('result')}")
            except json.JSONDecodeError:
                print(f"⚠️ 响应不是有效的JSON格式: {response.text[:200]}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")

def test_place_details_workflow():
    """
    测试获取地点详情的完整流程：先搜索地点，再获取详情
    """
    print("\n" + "="*60)
    print("测试地点详情获取流程")
    print("="*60)
    
    # 第一步：搜索地点获取place_id
    search_result = test_tool("find_place", {
        "input": "Starbucks near Times Square New York",
        "input_type": "textquery"
    })
    
    # 注意：这里只是演示流程，实际需要解析返回结果获取place_id
    print("提示：要获取地点详情，需要从find_place的结果中提取place_id")
    print("然后使用该place_id调用place_details工具")

def main():
    # 测试用例列表
    test_cases = [
        # 获取路线规划 - 使用英文地址
        ("get_directions", {
            "origin": "Tiananmen Square, Beijing, China",
            "destination": "Beijing Capital International Airport, China",
            "mode": "driving"
        }),
        
        # 步行路线
        ("get_directions", {
            "origin": "People's Square, Shanghai, China",
            "destination": "The Bund, Shanghai, China",
            "mode": "walking"
        }),
        
        # 公交路线
        ("get_directions", {
            "origin": "Times Square, New York, NY",
            "destination": "JFK Airport, New York, NY",
            "mode": "transit"
        }),
        
        # 获取距离和时间
        ("get_distance", {
            "origin": "Central Park, New York, NY",
            "destination": "Brooklyn Bridge, New York, NY",
            "mode": "driving"
        }),
        
        # 步行距离
        ("get_distance", {
            "origin": "Eiffel Tower, Paris, France",
            "destination": "Louvre Museum, Paris, France",
            "mode": "walking"
        }),
        
        # 地理编码 - 著名地标
        ("get_geocode", {
            "address": "Times Square, New York, NY"
        }),
        
        # 地理编码 - 地标建筑
        ("get_geocode", {
            "address": "Eiffel Tower, Paris, France"
        }),
        
        # 查找地点 - 使用英文搜索
        ("find_place", {
            "input": "Pizza restaurant in New York",
            "input_type": "textquery"
        }),
        
        # 查找酒店
        ("find_place", {
            "input": "Hotel near Times Square New York",
            "input_type": "textquery"
        }),
        
        # 查找附近餐厅 - 使用纽约坐标
        ("place_nearby", {
            "location": {
                "lat": 40.7589,
                "lng": -73.9851
            },
            "radius": 1000,
            "place_type": "restaurant"
        }),
        
        # 查找附近银行 - 使用巴黎坐标
        ("place_nearby", {
            "location": {
                "lat": 48.8566,
                "lng": 2.3522
            },
            "radius": 500,
            "place_type": "bank"
        }),
        
        # 注意：place_details 需要有效的 place_id，建议先运行 find_place 获取
        # ("place_details", {
        #     "place_id": "需要先通过find_place获取有效的place_id",
        #     "fields": ["name", "formatted_address", "formatted_phone_number", "website", "rating"]
        # })
    ]
    
    print("开始 Google Maps 工具测试...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
    
    # 测试地点详情获取流程
    test_place_details_workflow()
        
    print("\n测试完成!")

if __name__ == "__main__":
    main()
