import requests
import json
from datetime import datetime, timedelta

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
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 构建请求数据
        data = params  # 只发送参数部分
        
        # 使用与原始测试相同的URL格式
        url = f"http://localhost:30009/call_tool/{method}"
        
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=5
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
    # 获取当前日期和30天前的日期
    today = datetime.now().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 测试用例列表
    test_cases = [
        # 公司信息相关
        ("income_statement", {"symbol": "AAPL"}),
        ("get_company_notes", {"symbol": "AAPL"}),
        
        # 股票报价相关
        ("get_quote", {"symbol": "AAPL"}),
        ("get_quote_change", {"symbol": "AAPL"}),
        ("get_aftermarket_quote", {"symbol": "AAPL"}),
        ("get_price_change", {"symbol": "AAPL"}),
        
        # 财务报表相关
        ("get_income_statement", {"symbol": "AAPL", "period": "annual", "limit": 1}),
        
        # 搜索相关
        ("search_by_symbol", {"query": "AAPL", "limit": 5}),
        ("search_by_name", {"query": "Apple", "limit": 5}),
        
        # 分析师评级相关
        ("get_ratings_snapshot", {"symbol": "AAPL"}),
        ("get_financial_estimates", {"symbol": "AAPL", "period": "annual", "limit": 5}),
        ("get_price_target_news", {"symbol": "AAPL", "limit": 5}),
        ("get_price_target_latest_news", {"limit": 5}),
        
        # 股息相关
        ("get_company_dividends", {"symbol": "AAPL", "limit": 5}),
        ("get_dividends_calendar", {"from_date": thirty_days_ago, "to_date": today, "limit": 5}),
        
        # 指数相关
        ("get_index_list", {}),
        ("get_index_quote", {"symbol": "^GSPC"}),
        
        # 市场表现相关
        ("get_biggest_gainers", {"limit": 5}),
        ("get_biggest_losers", {"limit": 5}),
        ("get_most_active", {"limit": 5}),
        
        # 市场时间
        ("get_market_hours", {"exchange": "NASDAQ"}),
        
        # 商品相关
        ("get_commodities_list", {}),
        ("get_commodities_prices", {"symbol": "GCUSD"}),
        ("get_historical_price_eod_light", {
            "symbol": "GCUSD",
            "limit": 5,
            "from_date": thirty_days_ago,
            "to_date": today
        }),
        
        # 加密货币相关
        ("get_crypto_list", {}),
        ("get_crypto_quote", {"symbol": "BTCUSD"}),
        
        # 外汇相关
        ("get_forex_list", {}),
        ("get_forex_quotes", {"symbol": "EURUSD"}),
        
        # 技术指标
        ("get_ema", {
            "symbol": "AAPL",
            "period_length": 10,
            "timeframe": "1day",
            "from_date": thirty_days_ago,
            "to_date": today
        })
    ]
    
    print("开始FMP工具测试...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\n测试完成!")

if __name__ == "__main__":
    main()