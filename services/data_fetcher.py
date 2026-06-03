from datetime import datetime
from typing import List, Optional
import yfinance as yf
from core.schemas import StockArticle


def fetch_stock_news(ticker: str) -> dict:
    """
    주식 티커(ticker)를 사용하여 현재 시장 가격과 최근 뉴스 데이터를 가져옵니다.
    
    Args:
        ticker: 주식 티커 심볼 (예: "AAPL", "GOOGL")
        
    Returns:
        {'current_price': float, 'articles': list[StockArticle]} 형태의 딕셔너리
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        # 현재 가격 가져오기
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0.0
        
        # 뉴스 데이터 가져오기
        news_list = ticker_obj.news or []
        
        articles: List[StockArticle] = []
        
        for news_item in news_list:
            try:
                title = news_item.get('title', '')
                source = news_item.get('publisher', '')
                link = news_item.get('link', '')
                
                # 발행일 변환
                published_date: datetime
                if 'providerPublishTime' in news_item:
                    published_date = datetime.fromtimestamp(news_item['providerPublishTime'])
                else:
                    published_date = datetime.now()
                
                summary = news_item.get('summary', news_item.get('shortDescription', ''))
                
                article = StockArticle(
                    title=title,
                    source=source,
                    published_date=published_date,
                    link=link,
                    summary=summary
                )
                articles.append(article)
            except Exception:
                continue
        
        return {
            'current_price': float(current_price),
            'articles': articles
        }
        
    except Exception:
        return {
            'current_price': 0.0,
            'articles': []
        }
