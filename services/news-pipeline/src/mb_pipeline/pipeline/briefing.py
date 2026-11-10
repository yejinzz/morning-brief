"""브리핑 조립 (M2). docs/04 §7, 02.3.1.

선정 결과(HIGH)로 PWA 노출 계약(Briefing)을 만든다. 한 줄 브리핑·예상 읽기 시간 포함.
HIGH 0건이면 status=empty_high(임의 승격 없음).
"""

from __future__ import annotations

from datetime import datetime

from mb_pipeline.contracts import (
    ArticleCard,
    Briefing,
    BriefingStatus,
)
from mb_pipeline.pipeline.select import Selected

_WPM = 400  # 한국어 분당 읽기(대략). 요약이 짧으므로 보수적.


def _est_read_minutes(cards: list[ArticleCard]) -> int:
    if not cards:
        return 0
    chars = sum(len(c.title) + len(c.summary or "") + len(c.rationale or "") for c in cards)
    words = chars / 2  # 한국어 어절 근사
    return max(1, round(words / _WPM))


def _headline(cards: list[ArticleCard]) -> str | None:
    if not cards:
        return None
    top = cards[0].title
    if len(cards) == 1:
        return f"오늘의 주요 소식: {top}"
    return f"오늘은 '{top}' 등 HIGH {len(cards)}건이 주요 소식입니다."


def build_briefing(
    brief_date: str,
    *,
    collected_count: int,
    selected: list[Selected],
    now: datetime,
) -> Briefing:
    cards = [
        ArticleCard(
            id=s.article.id,
            category=s.category,
            title=s.article.title,
            summary=s.analysis.summary,
            rationale=s.analysis.rationale,
            dev_relevance=s.analysis.dev_relevance,
            source=s.article.source,
            published_at=s.article.published_at,
            url=s.article.canonical_url,
            impact=s.analysis.impact,
            evidence_basis=s.analysis.evidence_basis,
            display_order=s.display_order,
            is_high=True,
        )
        for s in selected
    ]
    status = BriefingStatus.READY if cards else BriefingStatus.EMPTY_HIGH
    return Briefing(
        brief_date=brief_date,
        headline=_headline(cards),
        collected_count=collected_count,
        high_count=len(cards),
        est_read_minutes=_est_read_minutes(cards),
        status=status,
        generated_at=now,
        articles=cards,
    )
