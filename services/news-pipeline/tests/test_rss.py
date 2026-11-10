"""RSS/Atom 파싱 테스트 (M1)."""

from __future__ import annotations

from datetime import UTC, datetime

from conftest import atom, rss
from mb_pipeline.contracts import Category
from mb_pipeline.sources.base import Source, SourceError
from mb_pipeline.sources.rss import parse_feed

SRC = Source("테스트", Category.AI, "https://feed.example/rss")


def test_parse_rss_fields_and_timestamp() -> None:
    content = rss(
        [
            ("첫 번째 기사", "https://ex.com/1", "Mon, 10 Nov 2026 00:00:00 +0000"),
            ("두 번째 기사", "https://ex.com/2", "Mon, 10 Nov 2026 09:00:00 +0900"),
        ]
    )
    arts = parse_feed(content, SRC)
    assert [a.title for a in arts] == ["첫 번째 기사", "두 번째 기사"]
    assert arts[0].published_at == datetime(2026, 11, 10, 0, 0, tzinfo=UTC)
    # +0900 → UTC 00:00
    assert arts[1].published_at == datetime(2026, 11, 10, 0, 0, tzinfo=UTC)
    assert all(a.category is Category.AI for a in arts)


def test_parse_atom() -> None:
    content = atom([("Atom 글", "https://ex.com/a", "2026-11-10T01:00:00Z")])
    arts = parse_feed(content, SRC)
    assert len(arts) == 1
    assert arts[0].published_at == datetime(2026, 11, 10, 1, 0, tzinfo=UTC)


def test_skip_entries_without_title_or_link() -> None:
    content = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<item><title></title><link>https://ex.com/x</link></item>"
        "<item><title>링크없음</title></item>"
        "<item><title>정상</title><link>https://ex.com/ok</link></item>"
        "</channel></rss>"
    )
    arts = parse_feed(content, SRC)
    assert [a.title for a in arts] == ["정상"]


def test_garbage_raises_source_error() -> None:
    try:
        parse_feed("this is not xml at all <<<", SRC)
    except SourceError:
        return
    raise AssertionError("SourceError 가 발생해야 함")
