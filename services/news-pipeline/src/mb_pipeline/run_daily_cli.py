"""일일 배치 CLI 엔트리 (M4). GitHub Actions 예약 실행이 호출.

MB_MODE:
- mock(기본): 실 RSS 수집 + Mock AI + Mock 푸시 + 인메모리 저장. 키·비용 없이 흐름 검증(스모크).
- live: Gemini + Supabase + 실 Web Push. Supabase 저장 어댑터 연동(M5)까지 미완 → 안내 후 종료.

실제 운영(영구 저장·실 푸시) 연동은 Supabase 클라이언트 구현 시점(M5)에 완성한다.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

from mb_pipeline.ai.mock import MockAIAdapter
from mb_pipeline.pipeline.run_daily import run_daily
from mb_pipeline.pipeline.stores import InMemoryBriefingStore, InMemoryJobStore
from mb_pipeline.push.base import PushSubscriptionData
from mb_pipeline.push.mock import MockPushSender
from mb_pipeline.push.stores import InMemoryDeliveryStore, InMemorySubscriptionStore
from mb_pipeline.sources.base import http_fetcher
from mb_pipeline.sources.registry import all_sources


def _run_mock() -> int:
    now = datetime.now(UTC)
    sub = PushSubscriptionData(
        id="demo", endpoint="https://push.example/demo", p256dh="x", auth="y"
    )
    outcome = run_daily(
        now=now,
        sources=all_sources(),
        fetcher=http_fetcher,
        ai_adapter=MockAIAdapter(),
        push_sender=MockPushSender(),
        briefing_store=InMemoryBriefingStore(),
        job_store=InMemoryJobStore(),
        subscriptions=InMemorySubscriptionStore([sub]),
        deliveries=InMemoryDeliveryStore(),
    )
    print(
        f"[run_daily:mock] date={outcome.brief_date} job={outcome.status} "
        f"briefing={outcome.briefing_status} push={vars(outcome.push) if outcome.push else None}"
    )
    return 0


def main() -> int:
    mode = os.environ.get("MB_MODE", "mock")
    if mode == "mock":
        return _run_mock()
    print(
        "[run_daily:live] 실 운영(Supabase 저장 + 실 Web Push) 연동은 M5에서 완성됩니다. "
        "현재는 MB_MODE=mock 스모크만 지원합니다.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
