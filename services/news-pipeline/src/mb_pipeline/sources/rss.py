"""RSS/Atom 파싱 (M1). feedparser 로 다양한 피드를 RawArticle 로 변환."""

from __future__ import annotations

from datetime import UTC, datetime
from time import struct_time

import feedparser

from mb_pipeline.contracts import RawArticle
from mb_pipeline.sources.base import Source, SourceError


def _to_datetime(parsed: struct_time | None) -> datetime | None:
    """feedparser 의 *_parsed(struct_time, UTC) → tz-aware datetime."""
    if parsed is None:
        return None
    return datetime(*parsed[:6], tzinfo=UTC)


def parse_feed(content: str, source: Source) -> list[RawArticle]:
    """피드 본문 텍스트를 RawArticle 목록으로. 제목/링크 없는 항목은 건너뜀."""
    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        raise SourceError(f"피드 파싱 실패: {source.name}: {feed.get('bozo_exception')}")

    articles: list[RawArticle] = []
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link.startswith(("http://", "https://")):
            continue
        published = _to_datetime(entry.get("published_parsed") or entry.get("updated_parsed"))
        articles.append(
            RawArticle(
                source=source.name,
                source_feed=source.url,
                title=title,
                url=link,
                description=entry.get("summary"),
                published_at=published,
                category=source.category,
            )
        )
    return articles
