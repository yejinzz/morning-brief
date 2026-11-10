"""정규화 테스트 (M1). URL canonical 화, 결정적 id, Article 변환."""

from __future__ import annotations

from datetime import UTC, datetime

from mb_pipeline.contracts import Category, RawArticle
from mb_pipeline.pipeline.normalize import article_id, canonicalize_url, to_article


def test_strip_tracking_params() -> None:
    url = "https://ex.com/a?utm_source=news&id=5&fbclid=xyz&gclid=q"
    assert canonicalize_url(url) == "https://ex.com/a?id=5"


def test_lowercase_host_and_scheme() -> None:
    assert canonicalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"


def test_strip_trailing_slash_and_fragment() -> None:
    assert canonicalize_url("https://ex.com/a/b/#sec") == "https://ex.com/a/b"
    # 루트 슬래시는 유지
    assert canonicalize_url("https://ex.com/") == "https://ex.com/"


def test_id_is_deterministic_for_same_canonical() -> None:
    a = canonicalize_url("https://ex.com/x?utm_medium=rss")
    b = canonicalize_url("https://ex.com/x")
    assert a == b
    assert article_id(a) == article_id(b)


def test_to_article_sets_fields() -> None:
    raw = RawArticle(
        source="S",
        title="  제목  ",
        url="https://ex.com/post?utm_source=x",
        category=Category.AI,
        published_at=datetime(2026, 11, 10, tzinfo=UTC),
    )
    now = datetime(2026, 11, 10, 22, 0, tzinfo=UTC)
    art = to_article(raw, collected_at=now)
    assert art.canonical_url == "https://ex.com/post"
    assert art.title == "제목"
    assert art.collected_at == now
    assert art.category is Category.AI
