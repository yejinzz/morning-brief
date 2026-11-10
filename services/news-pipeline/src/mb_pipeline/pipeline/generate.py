"""브리핑 생성 오케스트레이션 (M2).

수집 후보(candidates) → 사전필터 → AI 분석 → 분석 후 선정 → 브리핑 조립.
무료 한도 소진(AIQuotaError)은 전파하여 상위에서 '중단 + 마지막 정상 브리핑 유지'로 처리한다.
동일 날짜 재실행은 결정적 analysis id 로 멱등하다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mb_pipeline.ai.base import AIAdapter
from mb_pipeline.ai.limits import DailyLimits, UsageTracker
from mb_pipeline.contracts import Analysis, Article, Briefing
from mb_pipeline.pipeline import prefilter as prefilter_mod
from mb_pipeline.pipeline.analyze import analyze_candidates
from mb_pipeline.pipeline.briefing import build_briefing
from mb_pipeline.pipeline.select import select


@dataclass
class GenerateResult:
    briefing: Briefing
    analyses: list[Analysis]
    stage_counts: dict[str, object]


def generate_briefing(
    candidates: list[Article],
    adapter: AIAdapter,
    *,
    brief_date: str,
    now: datetime,
    tracker: UsageTracker | None = None,
    limits: DailyLimits | None = None,
    retries: int = 1,
) -> GenerateResult:
    tracker = tracker or UsageTracker(limits)
    collected_count = len(candidates)

    # ④ 사전 필터
    filtered, dropped = prefilter_mod.prefilter(candidates)

    # ⑤ AI 분석 (AIQuotaError 는 전파 → 중단)
    analyses = analyze_candidates(
        filtered, adapter, tracker, brief_date=brief_date, now=now, retries=retries
    )

    # ⑥ 분석 후 선정 · ⑦ HIGH 만 브리핑
    articles_by_id = {a.id: a for a in filtered}
    selected = select(analyses, articles_by_id)
    briefing = build_briefing(
        brief_date, collected_count=collected_count, selected=selected, now=now
    )

    return GenerateResult(
        briefing=briefing,
        analyses=analyses,
        stage_counts={
            "collected": collected_count,
            "prefiltered_out": dropped,
            "analyzed": len(analyses),
            "selected_high": briefing.high_count,
            "status": briefing.status.value,
            "usage": tracker.snapshot(),
        },
    )
