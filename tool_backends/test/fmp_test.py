import requests
import json
from datetime import datetime, timedelta

def test_tool(method, params=None):
    """
    Test FMP tools
    
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
        
        # Use the same URL format as the original test
        url = f"http://localhost:30010/call_tool/{method}"
        
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
    # Get current date and date 30 days ago
    today = datetime.now().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Test cases list
    test_cases = [
        # Company information related
        ("income_statement", {"symbol": "AAPL"}),
        ("get_company_notes", {"symbol": "AAPL"}),
        
        # Stock quote related
        ("get_quote", {"symbol": "AAPL"}),
        ("get_quote_change", {"symbol": "AAPL"}),
        ("get_aftermarket_quote", {"symbol": "AAPL"}),
        ("get_price_change", {"symbol": "AAPL"}),
        
        # Financial statements related
        ("get_income_statement", {"symbol": "AAPL", "period": "annual", "limit": 1}),
        
        # Search related
        ("search_by_symbol", {"query": "AAPL", "limit": 5}),
        ("search_by_name", {"query": "Apple", "limit": 5}),
        
        # Analyst ratings related
        ("get_ratings_snapshot", {"symbol": "AAPL"}),
        ("get_financial_estimates", {"symbol": "AAPL", "period": "annual", "limit": 5}),
        ("get_price_target_news", {"symbol": "AAPL", "limit": 5}),
        ("get_price_target_latest_news", {"limit": 5}),
        
        # Dividends related
        ("get_company_dividends", {"symbol": "AAPL", "limit": 5}),
        ("get_dividends_calendar", {"from_date": thirty_days_ago, "to_date": today, "limit": 5}),
        
        # Index related
        ("get_index_list", {}),
        ("get_index_quote", {"symbol": "^GSPC"}),
        
        # Market performance related
        ("get_biggest_gainers", {"limit": 5}),
        ("get_biggest_losers", {"limit": 5}),
        ("get_most_active", {"limit": 5}),
        
        # Market hours
        ("get_market_hours", {"exchange": "NASDAQ"}),
        
        # Commodities related
        ("get_commodities_list", {}),
        ("get_commodities_prices", {"symbol": "GCUSD"}),
        ("get_historical_price_eod_light", {
            "symbol": "GCUSD",
            "limit": 5,
            "from_date": thirty_days_ago,
            "to_date": today
        }),
        
        # Cryptocurrency related
        ("get_crypto_list", {}),
        ("get_crypto_quote", {"symbol": "BTCUSD"}),
        
        # Forex related
        ("get_forex_list", {}),
        ("get_forex_quotes", {"symbol": "EURUSD"}),
        
        # Technical indicators
        ("get_ema", {
            "symbol": "AAPL",
            "period_length": 10,
            "timeframe": "1day",
            "from_date": thirty_days_ago,
            "to_date": today
        })
    ]
    
    print("Starting FMP tool tests...")
    print("=" * 50)
    
    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)
        
    print("\nTests completed!")

if __name__ == "__main__":
    main()