"""푸시 페이로드·발송 테스트 (M4): 중복 방지, 만료 정리, 실패 격리, 4KB."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from mb_pipeline.contracts import ArticleCard, Briefing, BriefingStatus
from mb_pipeline.pipeline.kst import kst_date
from mb_pipeline.push.base import PushSubscriptionData
from mb_pipeline.push.mock import MockPushSender
from mb_pipeline.push.payload import MAX_PAYLOAD_BYTES, build_payload
from mb_pipeline.push.send import send_briefing_push
from mb_pipeline.push.stores import InMemoryDeliveryStore, InMemorySubscriptionStore


def _card(cat: str) -> ArticleCard:
    return ArticleCard(
        id=f"c-{cat}",
        category=cat,  # type: ignore[arg-type]
        title="제목",
        source="S",
        url="https://ex.com",
        impact="HIGH",
        evidence_basis="full",
        display_order=1,
        is_high=True,
    )


def _briefing(n_high: int = 2) -> Briefing:
    cats = ["ai", "dev", "economy"][:n_high]
    return Briefing(
        brief_date="2026-11-10",
        headline="h",
        collected_count=10,
        high_count=n_high,
        est_read_minutes=3,
        status=BriefingStatus.READY,
        articles=[_card(c) for c in cats],
    )


def _sub(sid: str) -> PushSubscriptionData:
    return PushSubscriptionData(id=sid, endpoint=f"https://push/{sid}", p256dh="p", auth="a")


# ── 페이로드 ──────────────────────────────────────────────────


def test_payload_has_title_body_url_and_fits() -> None:
    payload = build_payload(_briefing(2))
    data = json.loads(payload)
    assert data["title"] == "오늘의 주요 뉴스 2건"
    assert data["url"] == "/d/2026-11-10"
    assert "AI·LLM 1" in data["body"]
    assert len(payload.encode("utf-8")) <= MAX_PAYLOAD_BYTES


def test_kst_date_crosses_midnight() -> None:
    # 2026-11-10 22:30 UTC = 2026-11-11 07:30 KST
    assert kst_date(datetime(2026, 11, 10, 22, 30, tzinfo=UTC)) == "2026-11-11"
    assert kst_date(datetime(2026, 11, 10, 10, 0, tzinfo=UTC)) == "2026-11-10"


# ── 발송 ──────────────────────────────────────────────────────


def _stores(subs):
    return InMemorySubscriptionStore(subs), InMemoryDeliveryStore()


def _send(subs, deliveries, sender):
    return send_briefing_push(
        _briefing(), subscriptions=subs, deliveries=deliveries, sender=sender
    )


def test_sends_to_all_active() -> None:
    subs, deliveries = _stores([_sub("1"), _sub("2")])
    sender = MockPushSender()
    summary = _send(subs, deliveries, sender)
    assert summary.sent == 2
    assert len(sender.sent) == 2


def test_duplicate_send_skipped() -> None:
    subs, deliveries = _stores([_sub("1")])
    sender = MockPushSender()
    _send(subs, deliveries, sender)
    again = _send(subs, deliveries, sender)  # 같은 날짜 재발송 → 멱등 skip
    assert again.sent == 0
    assert again.skipped == 1


def test_gone_subscription_cleaned() -> None:
    subs, deliveries = _stores([_sub("1"), _sub("2")])
    summary = _send(subs, deliveries, MockPushSender(gone={"2"}))
    assert summary.sent == 1
    assert summary.gone == 1
    assert {s.id for s in subs.list_active()} == {"1"}  # 2 는 정리됨


def test_failed_send_isolated() -> None:
    subs, deliveries = _stores([_sub("1"), _sub("2")])
    summary = _send(subs, deliveries, MockPushSender(fail={"1"}))
    assert summary.sent == 1
    assert summary.failed == 1
