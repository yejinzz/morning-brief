"""정규화 (M1): URL canonical 화 + RawArticle→Article.

docs/04-news-pipeline.md §3. 추적 파라미터 제거, 호스트 소문자, fragment/말미 슬래시 정리.
Google News 리다이렉트 URL 의 실제 원문 해석은 네트워크가 필요하므로 M1 범위 밖(링크는 보존).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from mb_pipeline.contracts import Article, RawArticle

# 제거할 추적 쿼리 파라미터(접두 매칭 포함)
_TRACKING_EXACT = {"fbclid", "gclid", "igshid", "ref", "ref_src", "spm", "cmpid"}
_TRACKING_PREFIX = ("utm_",)

# canonical URL → 결정적 UUID (멱등 저장 키)
_NS = uuid.UUID("6f1a2b3c-4d5e-6f70-8192-a3b4c5d6e7f8")


def _keep_param(key: str) -> bool:
    k = key.lower()
    if k in _TRACKING_EXACT:
        return False
    return all(not k.startswith(p) for p in _TRACKING_PREFIX)


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if _keep_param(k)])
    path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    # fragment 제거
    return urlunsplit((scheme, netloc, path, query, ""))


def article_id(canonical_url: str) -> str:
    return str(uuid.uuid5(_NS, canonical_url))


def to_article(raw: RawArticle, *, collected_at: datetime) -> Article:
    canonical = canonicalize_url(raw.url)
    return Article(
        id=article_id(canonical),
        canonical_url=canonical,
        source=raw.source,
        source_feed=raw.source_feed,
        title=raw.title.strip(),
        description=raw.description,
        category=raw.category,
        published_at=raw.published_at,
        collected_at=collected_at,
        dedup_group=None,
        lang=raw.lang,
    )
