import yfinance as yf
import pprint

def check_yahoo_news_schema():
    ticker_symbol = "AAPL"
    print(f"🔄 Fetching fresh live news data layout for '{ticker_symbol}'...")
    
    ticker = yf.Ticker(ticker_symbol)
    news_list = ticker.news
    
    if not news_list:
        print("❌ No news items returned. Yahoo might be throttling requests.")
        return

    print(f"✅ Successfully retrieved {len(news_list)} news items.\n")
    print("================== FIRST NEWS ITEM RAW SCHEMA ==================")
    # Pretty-print the entire first item so we can inspect every key-value pair clearly
    pprint.pprint(news_list[0])
    print("================================================================")

if __name__ == "__main__":
    check_yahoo_news_schema()