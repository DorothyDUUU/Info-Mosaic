import requests
import json

def test_tool(method, params=None):
    """
    测试Web搜索和解析工具
    
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
        data = params
        
        url = f"http://localhost:30010/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30  # 增加超时时间，因为网页搜索和解析可能需要更长时间
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == True:
                    print("✅ 测试成功")
                    print(f"响应数据: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)[:1000]}...")
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
        # Web搜索测试用例
        ("web_search", {
            "query": "OpenAI ChatGPT latest news",
            "top_k": 10  # 添加可选参数
        }),
        
        # Web解析测试用例
        ("web_parse", {
            "link": "https://www.python.org/about/",
            "user_prompt": "What is Python programming language?"
        })

    ]
    
    print("开始Web搜索和解析工具测试...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\n测试完成!")

if __name__ == "__main__":
    main()