import streamlit as st
from datetime import datetime, timedelta
from typing import List
from src.schemas import StockArticle
from services.data_fetcher import fetch_stock_news
from services.article_filter import filter_by_window



# Time frame mapping to days
TIME_FRAME_DAYS = {
    "Today": 0,
    "Last 3 days": 3,
    "Last 7 days": 7,
    "Last 30 days": 30,
}

st.title("📈 Stock Information & News Monitor")

# Text input for ticker symbol
ticker = st.text_input("Enter stock ticker symbol", value="AAPL")

# Select box for news filter window
time_frame = st.selectbox(
    "Select news filter window",
    options=["Today", "Last 3 days", "Last 7 days", "Last 30 days"]
)

# Convert selected time frame to days
window_days = TIME_FRAME_DAYS[time_frame]

# Search button
if st.button("Search"):
    try:
        # Fetch stock data and news
        result = fetch_stock_news(ticker)
        current_price = result.get('current_price')
        articles = result.get('articles', [])
        
        # Filter articles
        filtered_articles = filter_by_window(articles, window_days)
        
        # Display current price
        if current_price is not None:
            st.metric(label="Current Price", value=f"{current_price} USD")
        else:
            st.metric(label="Current Price", value="N/A")
        
        # Display filtered articles
        if filtered_articles:
            st.subheader("Filtered News Articles")
            for article in filtered_articles:
                st.markdown(f"[{article.title}]({article.link})")
                st.write(f"Published: {article.published_date}")
                if article.summary and article.summary.strip():
                    st.write(f"Summary: {article.summary}")
                else:
                    st.write("*Summary unavailable. Click the link above to read the full story on the publisher's site.*")
                st.write("---")
        else:
            st.write("No articles found for the selected time frame.")
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
