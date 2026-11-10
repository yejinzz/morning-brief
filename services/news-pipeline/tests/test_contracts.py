"""계약 모델 round-trip 및 불변식 테스트 (M0)."""

from __future__ import annotations

from mb_pipeline.contracts import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    MAX_PER_CATEGORY,
    MAX_TOTAL,
    Briefing,
    BriefingStatus,
    Category,
    Impact,
)
from mb_pipeline.mock import loader


def test_all_categories_have_labels() -> None:
    assert set(CATEGORY_LABELS) == set(Category)
    assert list(Category) == CATEGORY_ORDER


def test_raw_articles_fixture_parses() -> None:
    raw = loader.load_raw_articles()
    assert len(raw) == 3
    cats = {a.category for a in raw}
    assert cats == {Category.AI, Category.ECONOMY, Category.DEV}


def test_briefing_round_trip() -> None:
    briefing = loader.load_briefing()
    dumped = briefing.model_dump_json()
    again = Briefing.model_validate_json(dumped)
    assert again == briefing


def test_briefing_only_high_exposed() -> None:
    briefing = loader.load_briefing()
    assert briefing.status is BriefingStatus.READY
    assert all(a.impact is Impact.HIGH and a.is_high for a in briefing.articles)
    assert briefing.high_count == len(briefing.articles)


def test_selection_limits_respected() -> None:
    briefing = loader.load_briefing()
    assert len(briefing.articles) <= MAX_TOTAL
    per_cat: dict[Category, int] = {}
    for a in briefing.articles:
        per_cat[a.category] = per_cat.get(a.category, 0) + 1
    assert all(n <= MAX_PER_CATEGORY for n in per_cat.values())
