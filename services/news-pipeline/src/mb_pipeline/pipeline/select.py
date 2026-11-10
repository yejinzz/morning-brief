"""선정 (M2). docs/04 §7. 분석 후 선정: HIGH 우선, 카테고리별 ≤3, 전체 ≤15.

기본 노출은 HIGH 만. MEDIUM/LOW·실패 분석은 저장되지만 선정/노출하지 않는다.
HIGH 가 없으면 억지로 승격하지 않는다(빈 선정 허용).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from mb_pipeline.contracts import (
    MAX_PER_CATEGORY,
    MAX_TOTAL,
    Analysis,
    AnalysisStatus,
    Article,
    Category,
    Impact,
)


@dataclass(frozen=True)
class Selected:
    article: Article
    analysis: Analysis
    category: Category
    display_order: int


def _recency_key(article: Article) -> tuple[int, float]:
    if article.published_at is None:
        return (1, 0.0)
    return (0, -article.published_at.timestamp())


def select(
    analyses: list[Analysis],
    articles_by_id: dict[str, Article],
    *,
    max_per_category: int = MAX_PER_CATEGORY,
    max_total: int = MAX_TOTAL,
) -> list[Selected]:
    # HIGH + analyzed 만 노출 후보
    by_cat: dict[Category, list[tuple[Article, Analysis]]] = defaultdict(list)
    for an in analyses:
        if an.impact is not Impact.HIGH or an.status is not AnalysisStatus.ANALYZED:
            continue
        art = articles_by_id.get(an.article_id)
        if art is None:
            continue
        by_cat[art.category].append((art, an))

    selected: list[Selected] = []
    # 카테고리 순서 고정(docs/01 탭 순서)
    for cat in Category:
        pairs = by_cat.get(cat, [])
        pairs.sort(key=lambda p: _recency_key(p[0]))
        for order, (art, an) in enumerate(pairs[:max_per_category], start=1):
            selected.append(Selected(article=art, analysis=an, category=cat, display_order=order))

    # 전체 상한(카테고리별 ≤3 이면 ≤15 이지만 방어적으로 컷)
    return selected[:max_total]
