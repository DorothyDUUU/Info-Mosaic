import requests
import json
from datetime import datetime, timedelta

BASE


def test_tool(method, params=None):
    """
    测试FMP工具

    Args:
        method: 工具方法名
        params: 请求参数（可选）
    """
    if params is None:
        params = {}

    print(f"\n测试工具: {method}")
    print(f"参数: {params}")

    try:
        headers = {"Content-Type": "application/json"}
        data = params 

        url = f"http://localhost:30010/call_tool/{method}"

        response = requests.post(url, headers=headers, json=data, timeout=5)

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == True:
                    print("✅ 测试成功")
                    print(
                        f"响应数据: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)[:500]}..."
                    )
                else:
                    print(f"⚠️ 请求成功但返回状态为失败: {result.get('result')}")
            except json.JSONDecodeError:
                print(f"⚠️ 响应不是有效的JSON格式: {response.text[:200]}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text[:200]}")

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")


def main():
    # 获取当前日期和30天前的日期
    today = datetime.now().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    test_cases = [
        # 经纬度与位置互转
        ("maps_get_from_coordinates", {"coordinates": "118.7965,32.0584"}),
        ("maps_get_from_location", {"address": "南京秦淮河", "city": "南京"}),
        # 模糊搜索与地点详情
        ("maps_get_structured_location", {"address": "夫子庙"}),
        ("maps_get_structured_location", {"address": "夫子庙", "city": "南京"}),
        # 天气查询
        ("maps_weather", {"city": "南京市"}),
        ("maps_weather", {"city": "上海闵行"}),
        # 行政区划代码查询
        ("maps_get_adcode", {"address": "江苏南京"}),
        # 路径规划
        (
            "maps_bicycling_by_address",
            {"origin_address": "南京夫子庙", "destination_address": "南京新街口"},
        ),
        (
            "maps_walking_by_address",
            {"origin_address": "南京夫子庙", "destination_address": "南京新街口"},
        ),
        (
            "maps_driving_by_address",
            {"origin_address": "南京夫子庙", "destination_address": "南京新街口"},
        ),
        # 综合路径规划
        (
            "maps_direction",
            {
                "origin_address": "南京夫子庙",
                "destination_address": "南京新街口",
                "origin_city": "南京",
                "destination_city": "南京",
            },
        ),
        # 距离计算
        ("maps_distance", {"origin": "南京夫子庙", "destination": "南京新街口"}),
        # POI 搜索
        ("maps_input_prompt", {"keywords": "仙林"}),
        ("maps_poi_search", {"keywords": "仙林", "city": "南京"}),
        # 周边搜索
        (
            "maps_around_search",
            {"keywords": "服装店", "location": "南京夫子庙", "radius": "2000"},
        ),
    ]

    test_for_googlemap = [
        ("googlemap_search_places", {"query": "High Schools in NanJing Gulou"}),
        ("google_map_get_place_details", {"query": "Shanghai Jiao Tong University"}),
        ("google_map_get_place_id", {"query": "Shanghai Jiao Tong University"}),
        (
            "google_map_get_map_direction",
            {
                "start": "Shanghai Jiao Tong University",
                "end": "Fudan University",
                "travel_mode": 2,
            },
        ),
    ]

    print("开始FMP工具测试...")
    print("=" * 50)

    for method, params in test_for_googlemap:
        test_tool(method, params)
        print("=" * 50)

    print("\n测试完成!")


if __name__ == "__main__":
    main()
