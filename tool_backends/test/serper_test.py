import requests
import json

def test_tool(method, params=None):
    """
    测试 Serper 工具
    
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
        
        # 使用 Serper SSE 服务的 URL
        url = f"http://localhost:30010/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10  # Serper API 可能需要更长的超时时间
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

def main():
    # 测试用例列表
    test_cases = [
        # # 基本搜索
        # ("google_search", {
        #     "q": "OpenAI latest news",
        #     "num": 5  # 数字类型
        # }),
        
        # # 图片搜索
        # ("google_search_images", {
        #     "q": "cute cats",
        #     "num": 5  # 数字类型
        # }),
        
        # 新闻搜索
        # ("google_search_news", {
        #     "q": "artificial intelligence news",
        #     "num": 5  # 数字类型
        # }),
        
        # 地点搜索
        ("google_search_places", {
            "q": "restaurants in New York"
        }),
        
        # # 视频搜索
        # ("google_search_videos", {
        #     "q": "python programming tutorials",
        #     "num": 5  # 数字类型
        # }),
        
        # # 专利搜索
        # ("google_search_patents", {
        #     "q": "artificial intelligence machine learning patent",
        #     "num": 5  # 数字类型
        # }),
        
        # # 网页抓取
        # ("webpage_scrape", {
        #     "url": "https://www.example.com"
        # })
    ]
    
    print("开始 Serper 工具测试...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\n测试完成!")

if __name__ == "__main__":
    main()