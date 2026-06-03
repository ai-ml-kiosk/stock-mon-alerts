from datetime import datetime, timedelta
from typing import List
from src.schemas import StockArticle


def filter_by_window(articles: List[StockArticle], window_days: int) -> List[StockArticle]:
    """
    주어진 기사 목록에서 지정된 기간 내에 발행된 기사만 필터링합니다.
    
    Args:
        articles: StockArticle 객체 목록
        window_days: 현재 날짜로부터 뒤로 계산할 일수
        
    Returns:
        window_days 이후에 발행된 기사 목록
    """
    # 현재 날짜에서 window_days를 뺀 임계 날짜 계산
    threshold_date = datetime.now() - timedelta(days=window_days)
    
    # 임계 날짜 이후에 발행된 기사만 필터링
    filtered_articles = [
        article for article in articles 
        if article.published_date >= threshold_date
    ]
    
    return filtered_articles
