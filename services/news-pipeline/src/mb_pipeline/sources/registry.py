"""소스 카탈로그 (M1). docs/04-news-pipeline.md §2 검증 소스 + Google News 폴백.

각 카테고리는 1차 소스 + 공통 안전망(Google News 검색 RSS)을 가진다.
1차 소스 장애 시 폴백으로 카테고리당 후보를 확보한다.
"""

from __future__ import annotations

import urllib.parse

from mb_pipeline.contracts import Category
from mb_pipeline.sources.base import Source, SourceKind

_GN_BASE = "https://news.google.com/rss"
_GN_SUFFIX = "hl=ko&gl=KR&ceid=KR:ko"


def google_news_search(query: str, category: Category, *, name: str | None = None) -> Source:
    """Google News 검색 RSS 소스(카테고리별 쿼리). 제목+링크만 → 저작권 최안전."""
    q = urllib.parse.quote(query)
    return Source(
        name=name or f"Google News ({category})",
        category=category,
        url=f"{_GN_BASE}/search?q={q}&{_GN_SUFFIX}",
        kind=SourceKind.GOOGLE_NEWS,
        is_fallback=True,
    )


# 카테고리별 폴백(공통 안전망) 쿼리
_FALLBACK_QUERY: dict[Category, str] = {
    Category.DOMESTIC: "정부정책 OR 법안 OR 공공기관 OR 사회현안",
    Category.ECONOMY: "금리 OR 환율 OR 인플레이션 OR 거시경제 OR 국제정세",
    Category.AI: "인공지능 OR LLM OR AI에이전트 OR OpenAI OR Anthropic OR Gemini",
    Category.DEV: "Spring Boot OR Docker OR Kubernetes OR React OR 오픈소스 보안",
    Category.TECH: "반도체 OR 모바일 OR 하드웨어 OR 신기술",
}


def fallback_source(category: Category) -> Source:
    name = f"Google News 폴백 ({category})"
    return google_news_search(_FALLBACK_QUERY[category], category, name=name)


# 1차 소스(검증된 무료 RSS). 봇 차단 소스는 운영 fetcher 에서 UA 로 대응.
_PRIMARY: dict[Category, list[Source]] = {
    Category.DOMESTIC: [
        Source("연합뉴스 종합", Category.DOMESTIC, "https://www.yna.co.kr/rss/news.xml"),
    ],
    Category.ECONOMY: [
        Source("연합뉴스 경제", Category.ECONOMY, "https://www.yna.co.kr/rss/economy.xml"),
        Source("연합뉴스 국제", Category.ECONOMY, "https://www.yna.co.kr/rss/international.xml"),
    ],
    Category.AI: [
        Source("OpenAI 블로그", Category.AI, "https://openai.com/blog/rss.xml"),
        Source("Google AI 블로그", Category.AI, "https://blog.google/technology/ai/rss/"),
        Source("Hugging Face", Category.AI, "https://huggingface.co/blog/feed.xml"),
    ],
    Category.DEV: [
        Source("Hacker News", Category.DEV, "https://hnrss.org/newest?points=100"),
        Source("Lobsters", Category.DEV, "https://lobste.rs/rss"),
    ],
    Category.TECH: [
        Source("전자신문 ETNews", Category.TECH, "http://rss.etnews.com/Section901.xml"),
        Source("Ars Technica", Category.TECH, "https://arstechnica.com/ai/feed/"),
    ],
}


def sources_for(category: Category) -> list[Source]:
    """카테고리의 1차 소스 + 폴백."""
    return [*_PRIMARY.get(category, []), fallback_source(category)]


def all_sources() -> list[Source]:
    out: list[Source] = []
    for cat in Category:
        out.extend(sources_for(cat))
    return out
