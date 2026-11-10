"""일일 배치 오케스트레이션 테스트 (M4): end-to-end, empty_high 미발송, 한도 중단, 멱등."""

from __future__ import annotations

from datetime import UTC, datetime

from conftest import fake_fetcher, rss
from mb_pipeline.ai.mock import MockAIAdapter
from mb_pipeline.contracts import Category
from mb_pipeline.pipeline.run_daily import run_daily
from mb_pipeline.pipeline.stores import InMemoryBriefingStore, InMemoryJobStore
from mb_pipeline.push.base import PushSubscriptionData
from mb_pipeline.push.mock import MockPushSender
from mb_pipeline.push.stores import InMemoryDeliveryStore, InMemorySubscriptionStore
from mb_pipeline.sources.base import Source

NOW = datetime(2026, 11, 10, 22, 30, tzinfo=UTC)  # KST 2026-11-11 07:30
RECENT = "Mon, 10 Nov 2026 22:00:00 +0000"


def _sub() -> PushSubscriptionData:
    return PushSubscriptionData(id="s1", endpoint="https://push/s1", p256dh="p", auth="a")


def _deps(feed_items, *, ai=None, subs=None):
    src = Source("dev", Category.DEV, "feed://dev")
    fetcher = fake_fetcher({"feed://dev": rss(feed_items)})
    return {
        "now": NOW,
        "sources": [src],
        "fetcher": fetcher,
        "ai_adapter": ai or MockAIAdapter(),
        "push_sender": MockPushSender(),
        "briefing_store": InMemoryBriefingStore(),
        "job_store": InMemoryJobStore(),
        "subscriptions": InMemorySubscriptionStore(subs if subs is not None else [_sub()]),
        "deliveries": InMemoryDeliveryStore(),
    }


def test_ready_briefing_sends_push() -> None:
    deps = _deps([("심각한 보안 취약점 공개", "https://ex.com/sec", RECENT)])
    out = run_daily(**deps)
    assert out.status == "succeeded"
    assert out.brief_date == "2026-11-11"  # KST
    assert out.briefing_status == "ready"
    assert out.push is not None and out.push.sent == 1
    assert deps["briefing_store"].get("2026-11-11") is not None


def test_empty_high_does_not_send() -> None:
    # HIGH 키워드 없는 기사 → empty_high → 미발송(D-1)
    deps = _deps([("평범한 일상 소식입니다", "https://ex.com/x", RECENT)])
    sender: MockPushSender = deps["push_sender"]
    out = run_daily(**deps)
    assert out.briefing_status == "empty_high"
    assert out.push is None
    assert sender.sent == []


def test_ai_quota_stops_without_push() -> None:
    deps = _deps([("보안 취약점", "https://ex.com/x", RECENT)], ai=MockAIAdapter(raise_quota=True))
    sender: MockPushSender = deps["push_sender"]
    out = run_daily(**deps)
    assert out.status == "failed"
    assert out.push is None
    assert sender.sent == []
    # 브리핑 저장 안 됨(마지막 정상 브리핑 유지)
    assert deps["briefing_store"].get("2026-11-11") is None


def test_concurrent_run_skipped() -> None:
    deps = _deps([("보안 취약점", "https://ex.com/x", RECENT)])
    deps["job_store"].try_start("2026-11-11")  # 이미 실행 중으로 표시
    out = run_daily(**deps)
    assert out.status == "skipped"


def test_rerun_same_date_idempotent_push() -> None:
    # 저장소를 공유해 두 번 실행 → 두 번째는 푸시 중복 방지(skip)
    deps = _deps([("보안 취약점 발견", "https://ex.com/x", RECENT)])
    run_daily(**deps)
    # job 은 finish 로 running 해제됨 → 재실행 가능. 하지만 delivery 멱등으로 재발송 안 함.
    out2 = run_daily(**deps)
    assert out2.status == "succeeded"
    assert out2.push is not None and out2.push.sent == 0 and out2.push.skipped == 1
