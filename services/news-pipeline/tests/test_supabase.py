"""Supabase 저장소 contract 테스트 (M5). 가짜 transport 로 호출 내용 검증(네트워크 없음)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from conftest import make_article
from mb_pipeline.contracts import (
    Analysis,
    AnalysisStatus,
    ArticleCard,
    Briefing,
    BriefingStatus,
    Category,
    EvidenceBasis,
    Impact,
)
from mb_pipeline.supabase.client import PostgrestClient
from mb_pipeline.supabase.stores import (
    SupabaseBriefingStore,
    SupabaseDeliveryStore,
    SupabaseJobStore,
    SupabaseSubscriptionStore,
)

NOW = datetime(2026, 11, 10, tzinfo=UTC)


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []
        self.responses: dict[tuple[str, str], tuple[int, str]] = {}

    def __call__(self, method, url, headers, body):
        table = url.split("/rest/v1/")[1].split("?")[0]
        self.calls.append((method, table, body.decode() if body else None))
        return self.responses.get((method, table), (201, ""))

    def tables(self, method: str) -> list[str]:
        return [t for (m, t, _) in self.calls if m == method]


def _client(t: FakeTransport) -> PostgrestClient:
    return PostgrestClient("https://x.supabase.co", "sb_secret_test", transport=t)


def test_job_try_start_ok_and_conflict() -> None:
    t = FakeTransport()
    assert SupabaseJobStore(_client(t)).try_start("2026-11-10") is True
    assert "collection_jobs" in t.tables("POST")

    t2 = FakeTransport()
    t2.responses[("POST", "collection_jobs")] = (409, "duplicate")
    assert SupabaseJobStore(_client(t2)).try_start("2026-11-10") is False


def _briefing() -> tuple[Briefing, list[Analysis], list]:
    art = make_article("a1", "보안 패치", category=Category.DEV)
    an = Analysis(
        id="an-1",
        article_id="a1",
        brief_date="2026-11-10",
        model="m",
        impact=Impact.HIGH,
        summary="s",
        rationale="r",
        dev_relevance="d",
        evidence_basis=EvidenceBasis.FULL,
        status=AnalysisStatus.ANALYZED,
        analyzed_at=NOW,
    )
    card = ArticleCard(
        id="a1",
        category=Category.DEV,
        title="보안 패치",
        source="S",
        url="https://ex.com/a1",
        impact=Impact.HIGH,
        evidence_basis=EvidenceBasis.FULL,
        display_order=1,
        is_high=True,
    )
    briefing = Briefing(
        brief_date="2026-11-10",
        headline="h",
        collected_count=1,
        high_count=1,
        est_read_minutes=1,
        status=BriefingStatus.READY,
        generated_at=NOW,
        articles=[card],
    )
    return briefing, [an], [art]


def test_briefing_save_hits_all_tables() -> None:
    t = FakeTransport()
    briefing, analyses, articles = _briefing()
    SupabaseBriefingStore(_client(t)).save(briefing, analyses, articles)
    posts = t.tables("POST")
    assert "news_articles" in posts
    assert "news_analyses" in posts
    assert "daily_briefings" in posts
    assert "briefing_articles" in posts
    assert "briefing_articles" in t.tables("DELETE")  # 선정 교체 전 삭제
    # briefing_articles 가 분석 id 로 연결되는지
    ba_body = next(b for (m, tbl, b) in t.calls if m == "POST" and tbl == "briefing_articles")
    assert json.loads(ba_body)[0]["analysis_id"] == "an-1"


def test_subscription_list_active_maps_rows() -> None:
    t = FakeTransport()
    t.responses[("GET", "push_subscriptions")] = (
        200,
        json.dumps([{"id": "s1", "endpoint": "https://p/1", "p256dh": "p", "auth": "a"}]),
    )
    subs = SupabaseSubscriptionStore(_client(t)).list_active()
    assert [s.id for s in subs] == ["s1"]
    assert subs[0].endpoint == "https://p/1"


def test_delivery_already_sent() -> None:
    t = FakeTransport()
    store = SupabaseDeliveryStore(_client(t))
    t.responses[("GET", "notification_deliveries")] = (200, "[]")
    assert store.already_sent("2026-11-10", "s1") is False
    t.responses[("GET", "notification_deliveries")] = (200, json.dumps([{"id": "x"}]))
    assert store.already_sent("2026-11-10", "s1") is True
