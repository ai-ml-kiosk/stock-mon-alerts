from datetime import datetime, timedelta, timezone
import pytest
from src.schemas import StockArticle
from services.article_filter import filter_by_window


def test_filter_by_window():
    """Test that filter_by_window correctly filters articles by time window."""
    # Get current timezone-aware datetime
    now = datetime.now(timezone.utc)
    
    # Create mock StockArticle objects with different dates
    article_today = StockArticle(
        title="Today's Article",
        source="Source A",
        published_date=now,
        link="https://example.com/today",
        summary="Summary for today's article"
    )
    
    article_5_days_ago = StockArticle(
        title="Article from 5 days ago",
        source="Source B",
        published_date=now - timedelta(days=5),
        link="https://example.com/5days",
        summary="Summary for 5 days ago article"
    )
    
    article_15_days_ago = StockArticle(
        title="Article from 15 days ago",
        source="Source C",
        published_date=now - timedelta(days=15),
        link="https://example.com/15days",
        summary="Summary for 15 days ago article"
    )
    
    # Create list of articles
    articles = [article_today, article_5_days_ago, article_15_days_ago]
    
    # Filter with window_days=7 (should return articles from last 7 days)
    filtered = filter_by_window(articles, 7)
    
    # Assert that only the first two articles are returned
    assert len(filtered) == 2
    assert article_today in filtered
    assert article_5_days_ago in filtered
    assert article_15_days_ago not in filtered
