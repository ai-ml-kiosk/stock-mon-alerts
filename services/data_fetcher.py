from datetime import datetime
from typing import List, Optional
import re
import requests
import yfinance as yf
from core.schemas import StockArticle


def _extract_meta_description(html: str) -> Optional[str]:
    # property="og:description" content="..."
    match = re.search(
        r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE | re.DOTALL
    )
    if not match:
        # content="..." property="og:description"
        match = re.search(
            r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:description["\']',
            html,
            re.IGNORECASE | re.DOTALL
        )
    if match:
        return re.sub(r'\s+', ' ', match.group(1)).strip()

    # name="description" content="..."
    match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE | re.DOTALL
    )
    if not match:
        # content="..." name="description"
        match = re.search(
            r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description["\']',
            html,
            re.IGNORECASE | re.DOTALL
        )
    if match:
        return re.sub(r'\s+', ' ', match.group(1)).strip()

    return None


def _extract_first_paragraph(html: str) -> Optional[str]:
    """Extract the first meaningful paragraph from the article body."""
    # Try to find article content
    article_match = re.search(
        r'<article[^>]*>(.*?)</article>',
        html,
        re.IGNORECASE | re.DOTALL
    )
    if article_match:
        content = article_match.group(1)
    else:
        # Try common content containers
        content_match = re.search(
            r'<div[^>]*class=["\'][^"\']*(?:content|article|post|story)[^"\']*["\'][^>]*>(.*?)</div>',
            html,
            re.IGNORECASE | re.DOTALL
        )
        content = content_match.group(1) if content_match else html
    
    # Find first paragraph with reasonable length
    p_matches = re.findall(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    for p_text in p_matches:
        text = re.sub(r'<[^>]+>', '', p_text).strip()
        if len(text) > 50:  # Only return paragraphs with substantial content
            return text[:500]  # Limit to 500 chars
    
    return None


def _fetch_summary_from_url(url: str) -> str:
    """
    Fetch the article page and extract the summary from meta tags or content.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; NewsBot/0.1)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            # First try meta description
            desc = _extract_meta_description(resp.text)
            if desc:
                return desc
            
            # Fallback to first paragraph
            first_p = _extract_first_paragraph(resp.text)
            if first_p:
                return first_p
    except Exception:
        pass
    return ""


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
                
                # 여러 필드를 후보로 삼아 요약을 추출합니다.
                summary = (
                    news_item.get('summary')
                    or news_item.get('shortDescription')
                    or news_item.get('description')
                    or ''
                )

                # yfinance 뉴스 항목에 요약이 제공되지 않는 경우가 많으므로,
                # 원문 링크의 HTML 메타 태그(og:description / description)를 스크래핑합니다.
                if not summary and link:
                    summary = _fetch_summary_from_url(link)
                
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
