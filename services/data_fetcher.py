import os
import requests
from typing import List, Optional
import re
import datetime
import yfinance as yf
import email.utils
from core.schemas import StockArticle

OPENROUTER_IP = "172.67.209.117"
OPENROUTER_HOST = "api.openrouter.ai"

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")

def _extract_meta_description(html: str) -> Optional[str]:
    match = re.search(
        r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        match = re.search(
            r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:description["\']',
            html,
            re.IGNORECASE | re.DOTALL,
        )
    if match:
        return re.sub(r'\s+', ' ', match.group(1)).strip()

    match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return re.sub(r'\s+', ' ', match.group(1)).strip()

    return None


def _extract_first_paragraph(html: str) -> Optional[str]:
    """Extract the first meaningful paragraph from the article body."""
    article_match = re.search(
        r'<article[^>]*>(.*?)</article>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if article_match:
        content = article_match.group(1)
    else:
        content_match = re.search(
            r'<div[^>]*class=["\'][^"\']*(?:content|article|post|story)[^"\']*["\'][^>]*>(.*?)</div>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        content = content_match.group(1) if content_match else html

    p_matches = re.findall(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    for p_text in p_matches:
        text = re.sub(r'<[^>]+>', '', p_text).strip()
        if len(text) > 50:
            return text[:500]

    return None


def _generate_ai_summary(title: str, publisher: str) -> str:
    """
    Groq LLM을 사용하여 AI 요약을 생성합니다.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "요약 생성 실패: GROQ_API_KEY 미설정"

    model_name = "llama-3.1-8b-instant"
    url = f"{LLM_BASE_URL}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model_name,
        "messages": [{
            "role": "user", 
            "content": f"You are a financial analyst agent. Write a 1-sentence summary of what this stock news headline is about. Headline: '{title}'"
        }],
        "max_tokens": 50,
        "temperature": 0.3,
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        summary = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return summary if summary else "요약 생성 실패"
    except Exception as e:
        return f"요약 생성 실패: {str(e)}"


def _fetch_summary_from_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsBot/0.1)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            desc = _extract_meta_description(resp.text)
            if desc:
                return desc

            first_p = _extract_first_paragraph(resp.text)
            if first_p:
                return first_p

            return _generate_ai_summary("뉴스 제목 없음", "알 수 없음")
    except Exception:
        return "요약 생성 실패"

    return ""


def fetch_stock_news(ticker: str) -> dict:
    """
    주식 티커(ticker)를 사용하여 현재 시장 가격과 최근 뉴스 데이터를 가져옵니다.
    최신 yfinance 구조의 중첩된 'content' 키를 완벽히 파싱합니다.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0.0
        news_list = ticker_obj.news or []
        articles: List[StockArticle] = []

        for news_item in news_list:
            try:
                # Sandbox 검증 결과 반영: 모든 데이터는 'content' 노드 하위에 존재합니다.
                content_data = news_item.get('content', {})
                if not content_data:
                    continue
                
                title = content_data.get('title') or ''
                source = content_data.get('provider', {}).get('displayName') or ''
                link = content_data.get('canonicalUrl', {}).get('url') or ''

                # ISO 날짜 파싱 ('2026-06-03T19:59:14Z' 포맷 대응)
                pub_date_str = content_data.get('pubDate')
                if pub_date_str:
                    published_date = datetime.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                else:
                    published_date = datetime.datetime.now()

                # 기본 요약문 매핑 추출
                summary = content_data.get('summary') or content_data.get('description') or ''

                # 기본 요약이 없거나 공백일 때만 Groq AI 엔진을 작동시킵니다.
                if not summary or not summary.strip():
                    summary = _generate_ai_summary(title, source)

                article = StockArticle(
                    title=title,
                    source=source,
                    published_date=published_date,
                    link=link,
                    summary=summary,
                )
                articles.append(article)
            except Exception:
                continue

        return {
            'current_price': float(current_price),
            'articles': articles,
        }

    except Exception:
        return {
            'current_price': 0.0,
            'articles': [],
        }