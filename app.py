import os
from dotenv import load_dotenv
# Load environment variables first
load_dotenv()

import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import List
from streamlit_searchbox import st_searchbox

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

# 1. Define the live ticker autocomplete search function with fix for case/types
def search_tickers(search_term: str) -> list[tuple[str, str]]:
    """
    Yahoo Finance Autocomplete API를 호출하여 검색어에 매칭되는
    (화면 표시용 이름, 실제 티커 기호) 튜플 리스트를 실시간으로 리턴합니다.
    """
    # Fix AttributeError: Ensure search_term is always a clean string
    if search_term is None:
        term_str = ""
    else:
        term_str = str(search_term).strip()

    # Fixed: Case-insensitive fallback check + allows 1-character typing to hit the API
    if not term_str:
        return [
            ("AAPL - Apple Inc.", "AAPL"),
            ("TSLA - Tesla Inc.", "TSLA"),
            ("NVDA - NVIDIA Corporation", "NVDA"),
            ("ORCL - Oracle Corporation", "ORCL")
        ]
    
    try:
        # Lowercase the query for safety, though Yahoo's API handles it natively
        clean_query = term_str.lower()
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={clean_query}&quotesCount=6&newsCount=0"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=3)
        
        if response.status_code == 200:
            results = response.json().get("quotes", [])
            
            # Formulate results dynamically based on what the user typed
            suggestions = [
                (f"{item['symbol']} - {item.get('shortname', item.get('longname', 'Unknown Company'))}", item['symbol'])
                for item in results if 'symbol' in item
            ]
            
            if suggestions:
                return suggestions
                
    except Exception:
        pass
        
    # Final safety fallback if API fails or drops
    return [
        ("AAPL - Apple Inc.", "AAPL"),
        ("TSLA - Tesla Inc.", "TSLA"),
        ("NVDA - NVIDIA Corporation", "NVDA"),
        ("ORCL - Oracle Corporation", "ORCL")
    ]

# App Interface Config
st.set_page_config(page_title="Stock Information & News Monitor", page_icon="📈", layout="wide")
st.title("📈 Stock Information & News Monitor")

# Sidebar for Filters to clean up main content area
with st.sidebar:
    st.subheader("⚙️ Configuration")
    time_frame = st.selectbox(
        "Select news filter window",
        options=["Today", "Last 3 days", "Last 7 days", "Last 30 days"],
        index=1  # Default to 'Last 3 days'
    )
    window_days = TIME_FRAME_DAYS[time_frame]
    max_articles = st.selectbox(
        "Max articles to display",
        options=[5, 10, 20, 30, 50],
        index=1  # Default to 10
    )

st.write("### 🔍 Search Global Equities")

# 2. Render the Predictive Search box component securely
ticker = st_searchbox(
    search_tickers,
    key="ticker_searchbox",
    placeholder="Type company name or ticker (e.g., Apple, TSLA, ORCL)...",
)

# 3. Handle data rendering automatically when a selection is loaded
if ticker:
    try:
        with st.spinner(f"Fetching real-time analytics for {ticker}..."):
            # Fetch stock data and news
            result = fetch_stock_news(ticker)
            current_price = result.get('current_price')
            articles = result.get('articles', [])
            
            # Filter articles based on window
            filtered_articles = filter_by_window(articles, window_days)
            filtered_articles = filtered_articles[:max_articles]
            
            # UI Layout Split: Left for Price Metrics, Right for Summary Details
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.write(f"#### Market Value ({ticker})")
                if current_price and current_price > 0:
                    st.metric(label="Current Price", value=f"{current_price:,.2f} USD")
                else:
                    st.metric(label="Current Price", value="N/A")
            
            with col2:
                # Display filtered articles
                if filtered_articles:
                    st.subheader(f"📰 Filtered News Articles ({time_frame})")
                    for article in filtered_articles:
                        st.markdown(f"#### [{article.title}]({article.link})")
                        st.caption(f"📍 Source: {article.source} | 🕒 Published: {article.published_date}")
                        
                        if article.summary and article.summary.strip():
                            st.write(f"**Summary:** {article.summary}")
                        else:
                            st.write("*Summary unavailable. Click the link above to read the full story on the publisher's site.*")
                        st.write("---")
                else:
                    st.info(f"No recent articles found matching '{ticker}' within the selected frame ({time_frame}).")
                    
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
else:
    st.info("💡 Please start typing above to search for a company name or stock ticker symbol.")