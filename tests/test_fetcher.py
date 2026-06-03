import pytestfrom unittest.mock import patch
from services.data_fetcher import fetch_stock_news
from core.schemas import StockArticle

@pytest.mark.usefixtures("mock_yfinance_response")
def test_fetch_stock_news_aapl():
    """AAPL 주식 뉴스를 가져오는 테스트."""
    mock_response = {
        "currentPrice": 175.32,
        "news": [
            {"title": "AAPL 주가 상승", "publisher": "Tech News", "link": "https://example.com/aapl"},
            {"title": "AAPL 출시", "publisher": "Apple", "link": "https://example.com/aapl-release"},
        ]
    }
    with patch('services.data_fetcher.yfinance.Ticker') as MockTicker:
        mock_ticker = MockTicker.return_value
        mock_ticker.info = mock_response
        result = fetch_stock_news('AAPL')
        assert result['current_price'] == 175.32
        assert len(result['articles']) == 2        assert result['articles'][0].title == "AAPL 주가 상승"
        assert result['articles'][1].title == "AAPL 출시"
