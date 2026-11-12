"""일일 배치 CLI 엔트리 (M5). GitHub Actions 예약 실행이 호출.

환경에 따라 자동 구성(유료 전환·과금 경로 없음):
- 저장: SUPABASE_URL + SUPABASE_SECRET_KEY 있으면 Supabase, 없으면 인메모리.
- 푸시: VAPID_PRIVATE_KEY + VAPID_SUBJECT 있으면 실 Web Push, 없으면 Mock.
- AI: MB_AI=gemini + GEMINI_API_KEY 면 Gemini, 아니면 Mock(기본, 비용 0).

실 RSS 수집은 항상 수행(무료·키 불필요). 라이브 저장/푸시 검증은 배포 환경에서.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from mb_pipeline.ai.base import AIAdapter
from mb_pipeline.ai.mock import MockAIAdapter
from mb_pipeline.pipeline.run_daily import run_daily
from mb_pipeline.pipeline.stores import (
    BriefingStore,
    InMemoryBriefingStore,
    InMemoryJobStore,
    JobStore,
)
from mb_pipeline.push.base import PushSender, PushSubscriptionData
from mb_pipeline.push.mock import MockPushSender
from mb_pipeline.push.stores import (
    DeliveryStore,
    InMemoryDeliveryStore,
    InMemorySubscriptionStore,
    SubscriptionStore,
)
from mb_pipeline.sources.base import http_fetcher
from mb_pipeline.sources.registry import all_sources
from mb_pipeline.supabase.client import PostgrestClient
from mb_pipeline.supabase.stores import cleanup_retention


def _ai_adapter() -> AIAdapter:
    if os.environ.get("MB_AI") == "gemini" and os.environ.get("GEMINI_API_KEY"):
        from mb_pipeline.ai.gemini import GeminiAdapter

        model = os.environ.get("MB_GEMINI_MODEL", "gemini-2.5-flash-lite")
        return GeminiAdapter(os.environ["GEMINI_API_KEY"], model=model)
    return MockAIAdapter()


def _push_sender() -> PushSender:
    priv = os.environ.get("VAPID_PRIVATE_KEY")
    sub = os.environ.get("VAPID_SUBJECT")
    if priv and sub:
        from mb_pipeline.push.webpush import WebPushSender

        return WebPushSender(priv, sub)
    return MockPushSender()


def _stores() -> tuple[
    BriefingStore, JobStore, SubscriptionStore, DeliveryStore, PostgrestClient | None
]:
    url = os.environ.get("SUPABASE_URL")
    secret = os.environ.get("SUPABASE_SECRET_KEY")
    if url and secret:
        from mb_pipeline.supabase.stores import (
            SupabaseBriefingStore,
            SupabaseDeliveryStore,
            SupabaseJobStore,
            SupabaseSubscriptionStore,
        )

        client = PostgrestClient(url, secret)
        return (
            SupabaseBriefingStore(client),
            SupabaseJobStore(client),
            SupabaseSubscriptionStore(client),
            SupabaseDeliveryStore(client),
            client,
        )
    # 인메모리(로컬 스모크): 데모 구독 1건으로 푸시 경로도 통과
    demo = PushSubscriptionData(
        id="demo", endpoint="https://push.example/demo", p256dh="x", auth="y"
    )
    return (
        InMemoryBriefingStore(),
        InMemoryJobStore(),
        InMemorySubscriptionStore([demo]),
        InMemoryDeliveryStore(),
        None,
    )


def main() -> int:
    now = datetime.now(UTC)
    briefing_store, job_store, subscriptions, deliveries, client = _stores()
    sender = _push_sender()
    ai = _ai_adapter()

    # MB_FORCE=1 → 성공 이력 무시하고 강제 재생성(수동 실행). 예약 실행은 미설정 → 중복 스킵.
    force = os.environ.get("MB_FORCE") == "1"

    outcome = run_daily(
        now=now,
        sources=all_sources(),
        fetcher=http_fetcher,
        ai_adapter=ai,
        push_sender=sender,
        briefing_store=briefing_store,
        job_store=job_store,
        subscriptions=subscriptions,
        deliveries=deliveries,
        force=force,
    )

    # 데이터 보관 정리(live 전용, 베스트에포트 — 실패해도 배치는 성공 처리)
    if client is not None:
        try:
            cleanup_retention(client, now)
        except Exception as exc:  # noqa: BLE001
            print(f"[run_daily] 보관 정리 건너뜀: {exc}")

    mode = (
        f"db={'supabase' if client else 'memory'} "
        f"ai={type(ai).__name__} push={type(sender).__name__}"
    )
    print(
        f"[run_daily] {mode} | date={outcome.brief_date} job={outcome.status} "
        f"briefing={outcome.briefing_status} push={vars(outcome.push) if outcome.push else None}"
    )
    return 0 if outcome.status != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
