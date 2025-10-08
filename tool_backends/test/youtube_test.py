import requests
import json

def test_tool(method, params=None):
    """
    测试 YouTube 工具
    
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
        
        # 使用 YouTube MCP 服务的 URL
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
                    print("✅ 测试成功")
                    print(f"响应数据: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)}...")
                else:
                    print(f"⚠️ 请求成功但返回状态为失败: {result.get('result')}")
            except json.JSONDecodeError:
                print(f"⚠️ 响应不是有效的JSON格式: {response.text}")
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")

def main():
    # 使用一个示例视频 ID 和频道 ID 进行测试
    test_video_id = "QtIlD6uxwwk" #"dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    test_channel_id = "UCuAXFkgsw1L7xaCfnd5JJOw"  # Rick Astley's channel
    
    # 测试用例列表
    test_cases = [
        # 视频搜索
        ("search_videos", {
            "query": "Rick Astley Never Gonna Give You Up",
            "max_results": 5,
            "order": "relevance"
        }),
        
        # # 获取视频详情
        # ("get_video_details", {
        #     "video_id": test_video_id
        # }),
        
        # # 获取频道详情
        # ("get_channel_details", {
        #     "channel_id": test_channel_id
        # }),
        
        # # 获取视频评论
        # ("get_video_comments", {
        #     "video_id": test_video_id,
        #     "max_results": 5,
        #     "order": "relevance",
        #     "include_replies": True
        # }),
        
        # 获取视频字幕
        ("get_video_transcript", {
            "video_id": test_video_id,
            "language": "en"  # 英文字幕
        }),
        
        # # 获取相关视频
        # ("get_related_videos", {
        #     "video_id": test_video_id,
        #     "max_results": 5
        # }),
        
        # # 获取热门视频
        # ("get_trending_videos", {
        #     "region_code": "US",
        #     "max_results": 5
        # }),
        
        # # 获取增强字幕
        # ("get_video_enhanced_transcript", {
        #     "video_ids": [test_video_id],
        #     "language": "en",
        #     "format": "timestamped",
        #     "include_metadata": True,
        #     "segment_method": "equal",
        #     "segment_count": 2
        # })
    ]
    
    print("开始 YouTube 工具测试...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\n测试完成!")

if __name__ == "__main__":
    main()
