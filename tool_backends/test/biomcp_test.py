import requests
import json
from datetime import datetime


def test_tool(method, params=None):
    """
    测试 BioMCP 工具

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

        # 构建请求数据（仅发送参数部分）
        data = params

        # 统一的工具调用服务
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
                if result.get('status') is True:
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
    today = datetime.now().strftime("%Y-%m-%d")

    # 选择一些常见的、易命中的示例参数
    example_pmid = "31452104"  # 示例PMID
    example_nct = "NCT04280705"  # 示例NCT ID
    # 使用更稳定的标识：基因组坐标（优先）与 rsID
    example_variant_hgvs = "chr7:g.140453136A>T"  # BRAF V600E (GRCh37)
    example_variant_rsid = "rs113488022"  # 常见 rsID 映射到 BRAF V600E

    test_cases = [
        # 文献检索与获取
        ("article_searcher", {"query": "BRAF mutations in melanoma"}),
        ("article_getter", {"pmid": example_pmid}),

        # 临床试验检索与分项获取
        ("trial_searcher", {"query": "melanoma"}),
        ("trial_getter", {"nct_id": example_nct}),
        ("trial_protocol_getter", {"nct_id": example_nct}),
        ("trial_locations_getter", {"nct_id": example_nct}),
        ("trial_outcomes_getter", {"nct_id": example_nct}),
        ("trial_references_getter", {"nct_id": example_nct}),

        # 变异检索与获取
        ("variant_searcher", {"query": "BRAF V600E"}),
        ("variant_getter", {"variant_id": example_variant_hgvs}),
        ("variant_getter", {"variant_id": example_variant_rsid}),
    ]

    print("开始 BioMCP 工具测试...")
    print("=" * 50)

    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)

    print("\n测试完成!")


if __name__ == "__main__":
    main()


