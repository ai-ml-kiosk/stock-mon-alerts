# services/data_fetcher.py
import os
import requests
from typing import List, Optional
import re
from core.schemas import StockArticle
import datetime

# OpenRouter API 호출 시 호스트를 명시적으로 설정
OPENROUTER_HOST = "api.openrouter.ai"

def _extract_meta_description(html: str) -> Optional[str]:
    # ... (기존 코드 유지) ...

def _generate_ai_summary(title: str, publisher: str) -> str:
    # ... (기존 코드 유지) ...

def _fetch_summary_from_url(url: str) -> str:
    """
    URL에서 요약을 스크래핑하거나 AI 요약을 생성합니다.
    """
    headers = {
        "Host": OPENROUTER_HOST,
        "User-Agent": "Mozilla/5.0 (compatible; NewsBot/0.1)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    resp = requests.get(url, timeout=10, headers=headers)
    if resp.status_code == 200:
        # ... (기존 코드 유지) ...
    return ""

def fetch_stock_news(ticker: str) -> dict:
    """
    주식 티커(ticker)를 사용하여 현재 시장 가격과 최근 뉴스 데이터를 가져옵니다.
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
                
                # 요약 생성
                summary = (
                    news_item.get('summary')
                    or news_item.get('shortDescription')
                    or news_item.get('description')
                    or ''
                )
                
                # 요약이 비어 있으면 AI 요약 생성
                if not summary or not summary.strip():
                    summary = _generate_ai_summary(title, source)
                
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
