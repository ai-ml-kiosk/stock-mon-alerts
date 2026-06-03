from datetime import datetime, timedelta, timezone
from src.schemas import StockArticle


def filter_by_window(articles: list[StockArticle], window_days: int) -> list[StockArticle]:
    """
    주어진 기사 목록에서 지정된 기간 내에 발행된 기사만 필터링합니다.
    
    Args:
        articles: StockArticle 객체 목록
        window_days: 현재 날짜로부터 뒤로 계산할 일수
        
    Returns:
        window_days 이후에 발행된 기사 목록
    """
    # 현재 timezone-aware UTC 날짜에서 window_days를 뺀 임계 날짜 계산
    threshold_date = datetime.now(timezone.utc) - timedelta(days=window_days)
    
    # 임계 날짜 이후에 발행된 기사만 필터링
    # published_date가 timezone-naive인 경우 UTC로 강제 변환
    filtered_articles = []
    for article in articles:
        published_date = article.published_date
        # timezone 정보가 없으면 UTC로 설정
        if published_date.tzinfo is None:
            published_date = published_date.replace(tzinfo=timezone.utc)
        
        if published_date >= threshold_date:
            filtered_articles.append(article)
    
    return filtered_articles
