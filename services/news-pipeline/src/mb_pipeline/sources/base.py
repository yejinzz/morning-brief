"""소스 정의와 네트워크 fetcher (M1).

``Fetcher`` 는 URL→본문 텍스트 콜러블로 주입된다. 테스트는 fixture 기반 fetcher 를
주입해 네트워크 없이 동작하며, 운영은 ``http_fetcher`` (urllib) 를 쓴다.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from mb_pipeline.contracts import Category

# 폴링 매너: 식별 가능한 UA (docs/04 §9 — 과도 폴링/차단 방지)
USER_AGENT = "MorningBriefBot/0.1 (+personal news briefing; contact via VAPID_SUBJECT)"
DEFAULT_TIMEOUT = 10.0

Fetcher = Callable[[str], str]


class SourceKind(StrEnum):
    RSS = "rss"  # feedparser 가 RSS/Atom 모두 처리
    GOOGLE_NEWS = "google_news"


class SourceError(Exception):
    """소스 fetch/parse 실패. 개별 소스 격리에 사용(전체 중단 아님)."""


@dataclass(frozen=True)
class Source:
    name: str
    category: Category
    url: str
    kind: SourceKind = SourceKind.RSS
    enabled: bool = True
    # 1차 소스 장애 시 폴백(카테고리 공통 안전망, 보통 Google News)
    is_fallback: bool = False


def http_fetcher(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """운영용 HTTP fetcher. 실패 시 SourceError."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            charset = resp.headers.get_content_charset() or "utf-8"
            data: bytes = resp.read()
        return data.decode(charset, errors="replace")
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SourceError(f"fetch 실패: {url}: {exc}") from exc
