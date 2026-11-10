"""기사 저장소 멱등성 테스트 (M1)."""

from __future__ import annotations

from datetime import UTC, datetime

from mb_pipeline.contracts import Article, Category
from mb_pipeline.store.articles import InMemoryArticleStore


def _art(url: str) -> Article:
    return Article(
        id="x",
        canonical_url=url,
        source="S",
        title="제목",
        category=Category.AI,
        collected_at=datetime(2026, 11, 10, tzinfo=UTC),
    )


def test_upsert_is_idempotent_by_canonical_url() -> None:
    store = InMemoryArticleStore()
    assert store.upsert([_art("https://ex.com/a"), _art("https://ex.com/b")]) == 2
    # 동일 canonical 재삽입은 신규 0
    assert store.upsert([_art("https://ex.com/a")]) == 0
    assert len(store.all()) == 2
