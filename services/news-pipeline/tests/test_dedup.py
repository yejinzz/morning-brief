"""중복 제거 테스트 (M1). canonical 일치, 제목 유사도, 이전 브리핑 대조."""

from __future__ import annotations

from datetime import UTC, datetime

from mb_pipeline.contracts import Article, Category
from mb_pipeline.pipeline.dedup import deduplicate, jaccard, title_tokens


def _art(
    aid: str, url: str, title: str, cat: Category = Category.DOMESTIC, hour: int = 0
) -> Article:
    return Article(
        id=aid,
        canonical_url=url,
        source="S",
        title=title,
        category=cat,
        published_at=datetime(2026, 11, 10, hour, tzinfo=UTC),
        collected_at=datetime(2026, 11, 10, 22, tzinfo=UTC),
    )


def test_jaccard_and_tokens_ignore_stopwords() -> None:
    assert "속보" not in title_tokens("속보 금리 동결")
    assert jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert jaccard({"a"}, {"b"}) == 0.0


def test_exact_canonical_duplicate_removed() -> None:
    arts = [
        _art("1", "https://ex.com/a", "금리 동결 결정"),
        _art("1", "https://ex.com/a", "금리 동결 결정"),
    ]
    res = deduplicate(arts)
    assert len(res.kept) == 1
    assert len(res.dropped_duplicate) == 1


def test_similar_titles_grouped_representative_kept() -> None:
    arts = [
        _art("1", "https://a.com/x", "한국은행 기준금리 전격 동결 결정", hour=9),
        _art("2", "https://b.com/y", "기준금리 동결 결정 한국은행", hour=8),
    ]
    res = deduplicate(arts, sim_threshold=0.5)
    assert len(res.kept) == 1
    # 더 이른 발행(8시)이 대표
    assert res.kept[0].canonical_url == "https://b.com/y"
    assert res.kept[0].dedup_group is not None


def test_cross_category_same_event_grouped() -> None:
    # 같은 사건이 여러 피드의 다른 카테고리로 들어와도 묶는다(교차-카테고리 dedup).
    arts = [
        _art("1", "https://a.com/x", "보안 취약점 패치 공개", cat=Category.DEV),
        _art("2", "https://b.com/y", "보안 취약점 패치 공개", cat=Category.TECH),
    ]
    res = deduplicate(arts, sim_threshold=0.5)
    assert len(res.kept) == 1
    assert res.kept[0].dedup_group is not None


def test_prior_briefing_urls_excluded() -> None:
    arts = [
        _art("1", "https://ex.com/old", "이미 나온 뉴스"),
        _art("2", "https://ex.com/new", "새 뉴스"),
    ]
    res = deduplicate(arts, prior_urls={"https://ex.com/old"})
    kept_urls = {a.canonical_url for a in res.kept}
    assert kept_urls == {"https://ex.com/new"}
    assert len(res.dropped_prior) == 1
