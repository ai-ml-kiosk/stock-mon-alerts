import streamlitas st
from datetime import datetime, timedeltafrom typing import List
from src.schemas import StockArticle
from services.data_fetcher import get_stock_info_with_news
from services.article_filter import filter_by_window

# Time frame mapping to days
TIME_FRAME_DAYS = {
    "Today": 0,
    "Last 3 days": 3,
    "Last 7 days": 7,
    "Last 30 days": 30,
}

st.title("Stock News Viewer")

# Text input for ticker symbol
ticker = st.text_input("Enter stock ticker symbol", value="AAPL")

# Dropdown for time frame selection
time_frame = st.selectbox(
    "Select time frame for filtering news",
    options=["Today", "Last 3 days", "Last 7 days", "Last 30 days"]
)

# Convert selected time frame to number of days
window_days = TIME_FRAME_DAYS[time_frame]

# Button to fetch dataif st.button("Fetch Data"):
    # Fetch stock data and news articles
    result = get_stock_info_with_news(ticker)
    stock_data = result.get("stock_data", {})
    news_articles: List[StockArticle] = result.get("news_articles", [])
    
    # Filter articles based on selected window    filtered_articles = filter_by_window(news_articles, window_days)
    
    # Display current price information
    current_price = stock_data.get("current_price")
    currency = stock_data.get("currency", "USD")
    name = stock_data.get("name", ticker)
    
    if current_price:
        st.write(f"### {name} ({ticker})")
        st.write(f"Current price: **{current_price} {currency}**")
    else:
        st.write(f"### {name} ({ticker})")
        st.write("Current price: **N/A**")
        # Display filtered news articles
    if filtered_articles:
        st.subheader("Filtered News Articles")
        for article in filtered_articles:
            st.markdown(f"**Title:** {article.title}")
            st.write(f"Source: {article.source}")
            st.write(f"Published Date: {article.published_date}")
            st.write(f"[Read article]({article.link})")
            st.write(f"Summary: {article.summary}")
            st.write("---")
    else:
        st.write("No news articles found for the selected time frame.")
