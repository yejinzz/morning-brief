"""수집 오케스트레이션 테스트 (M1): 격리, 24→72h 윈도우, 상한, 이전 브리핑 대조."""

from __future__ import annotations

from datetime import UTC, datetime

from conftest import fake_fetcher, rss
from mb_pipeline.contracts import Category
from mb_pipeline.pipeline.collect import collect
from mb_pipeline.sources.base import Source

NOW = datetime(2026, 11, 10, 22, 0, tzinfo=UTC)


def test_source_failure_isolated() -> None:
    good = Source("good", Category.AI, "feed://good")
    bad = Source("bad", Category.AI, "feed://bad")
    good_feed = rss([("정상 기사", "https://ex.com/g", "Mon, 10 Nov 2026 20:00:00 +0000")])
    fetcher = fake_fetcher({"feed://good": good_feed}, fail={"feed://bad"})
    res = collect([good, bad], fetcher=fetcher, now=NOW, retries=1, min_per_category=1)
    assert len(res.candidates) == 1
    assert len(res.failures) == 1
    assert res.failures[0].source == "bad"
    assert res.stage_counts["failures"] == 1


def test_window_expands_24_to_72() -> None:
    src = Source("dev", Category.DEV, "feed://dev")
    # 두 기사 모두 24h 밖, 72h 안 (now-30h, now-50h). 서로 다른 사건(중복 아님).
    items = [
        ("쿠버네티스 릴리스", "https://ex.com/a", "Sun, 09 Nov 2026 16:00:00 +0000"),
        ("파이썬 보안 패치", "https://ex.com/b", "Sat, 08 Nov 2026 20:00:00 +0000"),
    ]
    fetcher = fake_fetcher({"feed://dev": rss(items)})
    res = collect([src], fetcher=fetcher, now=NOW, min_per_category=2)
    assert len(res.candidates) == 2
    assert res.stage_counts["window_hours"][Category.DEV.value] == 72


def test_24h_priority_excludes_old_when_enough_fresh() -> None:
    src = Source("ai", Category.AI, "feed://ai")
    fetcher = fake_fetcher(
        {
            "feed://ai": rss(
                [
                    ("최신1", "https://ex.com/1", "Mon, 10 Nov 2026 20:00:00 +0000"),
                    ("최신2", "https://ex.com/2", "Mon, 10 Nov 2026 12:00:00 +0000"),
                    ("오래됨", "https://ex.com/old", "Fri, 07 Nov 2026 00:00:00 +0000"),
                ]
            )
        }
    )
    res = collect([src], fetcher=fetcher, now=NOW, min_per_category=2)
    urls = {a.canonical_url for a in res.candidates}
    assert urls == {"https://ex.com/1", "https://ex.com/2"}
    assert res.stage_counts["window_hours"][Category.AI.value] == 24


def test_per_category_cap() -> None:
    src = Source("ai", Category.AI, "feed://ai")
    items = [
        (f"기사 {i}", f"https://ex.com/{i}", "Mon, 10 Nov 2026 20:00:00 +0000") for i in range(10)
    ]
    fetcher = fake_fetcher({"feed://ai": rss(items)})
    res = collect([src], fetcher=fetcher, now=NOW, min_per_category=1, cap_per_category=5)
    assert len(res.candidates) == 5
    assert res.stage_counts["per_category"][Category.AI.value] == 5


def test_prior_urls_excluded_in_collect() -> None:
    src = Source("ai", Category.AI, "feed://ai")
    fetcher = fake_fetcher(
        {
            "feed://ai": rss(
                [
                    ("이전", "https://ex.com/seen", "Mon, 10 Nov 2026 20:00:00 +0000"),
                    ("신규", "https://ex.com/fresh", "Mon, 10 Nov 2026 20:00:00 +0000"),
                ]
            )
        }
    )
    res = collect(
        [src], fetcher=fetcher, now=NOW, min_per_category=1, prior_urls={"https://ex.com/seen"}
    )
    urls = {a.canonical_url for a in res.candidates}
    assert urls == {"https://ex.com/fresh"}
    assert res.stage_counts["dropped_prior"] == 1
