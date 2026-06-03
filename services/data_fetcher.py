from datetime import datetime
from typing import List, Optional
import re
import requests
import yfinance as yf
from core.schemas import StockArticle
import os  # 추가: 환경 변수 접근을 위한 모듈

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


def _generate_ai_summary(title: str, publisher: str) -> str:
    """
    OpenRouter LLM을 사용하여 AI 요약을 생성합니다.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "요약 생성 실패: API 키 미설정"
    
    url = "https://api.openrouter.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai-gpt-3.5-turbo",
        "messages": [{"role": "user", "content": f"You are a financial analyst agent. Write a 1-sentence summary of what this stock news headline is about. Headline: '{title}'"}],
        "max_tokens": 50,
        "temperature": 0.3,
        "timeout": 5
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        # 응답 구조에 따라 요약 텍스트 추출
        summary = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return summary if summary else "요약 생성 실패"
    except Exception as e:
        return f"요약 생성 실패: {str(e)}"


def _fetch_summary_from_url(url: str) -> str:
    """
    URL에서 요약을 스크래핑하거나 AI 요약을 생성합니다.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; NewsBot/0.1)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            # 메타 설명 먼저 시도
            desc = _extract_meta_description(resp.text)
            if desc:
                return desc
            
            # 첫 번째 단락 시도
            first_p = _extract_first_paragraph(resp.text)
            if first_p:
                return first_p
            
            # AI 요약 생성
            return _generate_ai_summary("뉴스 제목 없음", "미 known")
    except Exception:
        return "요약 생성 실패"


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
