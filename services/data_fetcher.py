from datetime import datetime
from typing import List, Optional
import yfinance as yf
from core.schemas import StockArticle


def fetch_stock_data(symbol: str) -> dict:
    """
    주식 티커(symbol)를 사용하여 현재 주가 정보를 가져옵니다.
    
    Args:
        symbol: 주식 티커 심볼 (예: "AAPL", "GOOGL")
        
    Returns:
        현재 주가 정보를 담은 딕셔너리
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
    
    return {
        'symbol': symbol,
        'current_price': current_price,
        'name': info.get('longName', ''),
        'currency': info.get('currency', 'USD')
    }


def fetch_news_articles(symbol: str) -> List[StockArticle]:
    """
    주식 티커(symbol)를 사용하여 뉴스 기사를 가져오고 StockArticle 객체로 매핑합니다.
    
    Args:
        symbol: 주식 티커 심볼 (예: "AAPL", "GOOGL")
        
    Returns:
        StockArticle 객체 목록
    """
    ticker = yf.Ticker(symbol)
    news_list = ticker.news
    
    articles: List[StockArticle] = []
    
    if not news_list:
        return articles
    
    for news_item in news_list:
        try:
            # 뉴스 항목에서 필요한 필드 추출
            title = news_item.get('title', '')
            source = news_item.get('publisher', '')
            link = news_item.get('link', '')
            
            # 발행일 변환 (Unix 타임스탬프 또는 문자열)
            published_date: datetime
            if 'providerPublishTime' in news_item:
                published_date = datetime.fromtimestamp(news_item['providerPublishTime'])
            else:
                published_date = datetime.now()
            
            # 요약 생성 (설명이나 요약 필드 사용)
            summary = news_item.get('summary', news_item.get('shortDescription', ''))
            
            article = StockArticle(
                title=title,
                source=source,
                published_date=published_date,
                link=link,
                summary=summary
            )
            articles.append(article)
        except Exception as e:
            # 개별 뉴스 항목 처리 중 오류 발생 시 건너뛰기
            continue
    
    return articles


def get_stock_info_with_news(symbol: str) -> dict:
    """
    주식 정보와 뉴스 기사를 함께 가져옵니다.
    
    Args:
        symbol: 주식 티커 심볼
        
    Returns:
        주식 정보와 뉴스 기사 목록을 담은 딕셔너리
    """
    stock_data = fetch_stock_data(symbol)
    news_articles = fetch_news_articles(symbol)
    
    return {
        'stock_data': stock_data,
        'news_articles': news_articles
    }
