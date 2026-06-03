import pytest
from unittest.mock import patch, MagicMock
from services.data_fetcher import fetch_stock_news
from core.schemas import StockArticle


@pytest.fixture
def mock_yfinance_response():
    """yfinance Ticker 객체를 모킹하는 픽스처"""
    with patch('services.data_fetcher.yf.Ticker') as MockTicker:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            'regularMarketPrice': 175.0
        }
        mock_ticker.news = [
            {"title": "AAPL 주가 상승", "publisher": "Tech News", "link": "https://example.com/aapl"},
            {"title": "AAPL 출시", "publisher": "Apple", "link": "https://example.com/aapl-release"},
        ]
        MockTicker.return_value = mock_ticker
        yield MockTicker


def test_fetch_stock_news_aapl(mock_yfinance_response):
    """AAPL 주식 뉴스를 가져오는 테스트."""
    result = fetch_stock_news('AAPL')
    assert result['current_price'] == 175.0
    assert len(result['articles']) == 2
    assert result['articles'][0].title == "AAPL 주가 상승"
    assert result['articles'][1].title == "AAPL 출시"
