"""일일 배치 오케스트레이션 (M4). docs/02 §3, 07 §4.

흐름: 동시실행 방지 → 수집 → 생성(사전필터·AI·선정·브리핑) → 저장 → (ready면) 푸시.
의존성은 모두 주입식이라 네트워크·키 없이 end-to-end 테스트 가능.

규칙:
- empty_high(HIGH 0건) → 저장하되 **푸시 미발송**(D-1).
- 무료 한도 소진(AIQuotaError) → job=failed, 푸시 없음, 마지막 정상 브리핑 유지.
- 동일 날짜 재실행 → 멱등(이미 running 이면 skip).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mb_pipeline.ai.base import AIAdapter, AIQuotaError
from mb_pipeline.contracts import BriefingStatus
from mb_pipeline.pipeline.collect import collect
from mb_pipeline.pipeline.generate import generate_briefing
from mb_pipeline.pipeline.kst import kst_date
from mb_pipeline.pipeline.stores import BriefingStore, JobStore
from mb_pipeline.push.base import PushSender
from mb_pipeline.push.send import PushSummary, send_briefing_push
from mb_pipeline.push.stores import DeliveryStore, SubscriptionStore
from mb_pipeline.sources.base import Fetcher, Source


@dataclass
class JobOutcome:
    brief_date: str
    status: str  # succeeded / failed / skipped
    briefing_status: str | None = None
    push: PushSummary | None = None
    detail: str | None = None


def run_daily(
    *,
    now: datetime,
    sources: list[Source],
    fetcher: Fetcher,
    ai_adapter: AIAdapter,
    push_sender: PushSender,
    briefing_store: BriefingStore,
    job_store: JobStore,
    subscriptions: SubscriptionStore,
    deliveries: DeliveryStore,
    prior_urls: set[str] | None = None,
) -> JobOutcome:
    brief_date = kst_date(now)

    # 동시/중복 실행 방지
    if not job_store.try_start(brief_date):
        return JobOutcome(brief_date, "skipped", detail="이미 실행 중")

    try:
        collected = collect(sources, fetcher=fetcher, now=now, prior_urls=prior_urls)
        gen = generate_briefing(
            collected.candidates, ai_adapter, brief_date=brief_date, now=now
        )
    except AIQuotaError as exc:
        # 유료 폴백 없이 중단. 마지막 정상 브리핑 유지(저장 안 함).
        job_store.finish(brief_date, "failed", {"reason": "ai_quota", "error": str(exc)})
        return JobOutcome(brief_date, "failed", detail=f"AI 한도 소진: {exc}")

    # 브리핑 저장(멱등 upsert)
    briefing_store.save(gen.briefing, gen.analyses)

    # 성공(ready) 시에만 발송. empty_high → 미발송(D-1).
    push: PushSummary | None = None
    if gen.briefing.status is BriefingStatus.READY:
        push = send_briefing_push(
            gen.briefing,
            subscriptions=subscriptions,
            deliveries=deliveries,
            sender=push_sender,
        )

    job_store.finish(
        brief_date,
        "succeeded",
        {
            "collect": collected.stage_counts,
            "generate": gen.stage_counts,
            "push": vars(push) if push else None,
        },
    )
    return JobOutcome(
        brief_date,
        "succeeded",
        briefing_status=gen.briefing.status.value,
        push=push,
    )
