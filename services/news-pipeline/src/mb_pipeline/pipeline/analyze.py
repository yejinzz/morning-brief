"""AI 분석 오케스트레이션 (M2). docs/04 §6.

카테고리 묶음 분석(D-4). 깨진 응답은 제한 재시도 후 격리(status=failed),
무료 한도 소진(AIQuotaError)은 유료 폴백 없이 **중단**(상위로 전파).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime

from mb_pipeline.ai.base import (
    AIAdapter,
    AIResponseError,
    AnalysisInput,
)
from mb_pipeline.ai.limits import UsageTracker
from mb_pipeline.ai.prompt import estimate_tokens
from mb_pipeline.contracts import (
    Analysis,
    AnalysisStatus,
    Article,
    Category,
    EvidenceBasis,
    Impact,
)

# 결정적 analysis id(= DB uuid). 동일 기사·날짜·모델 → 동일 id → 멱등 upsert.
_ANALYSIS_NS = uuid.UUID("b2c3d4e5-6f70-5182-93a4-b5c6d7e8f901")


def analysis_id(article_id: str, brief_date: str, model: str) -> str:
    return str(uuid.uuid5(_ANALYSIS_NS, f"{article_id}:{brief_date}:{model}"))


def _to_analysis(
    *, article_id: str, brief_date: str, model: str, now: datetime,
    impact: Impact, summary: str | None, rationale: str | None,
    dev_relevance: str | None, evidence: EvidenceBasis, status: AnalysisStatus,
) -> Analysis:
    return Analysis(
        id=analysis_id(article_id, brief_date, model),
        article_id=article_id,
        brief_date=brief_date,
        model=model,
        impact=impact,
        summary=summary,
        rationale=rationale,
        dev_relevance=dev_relevance,
        evidence_basis=evidence,
        status=status,
        analyzed_at=now,
    )


def _failed(article_id: str, brief_date: str, model: str, now: datetime) -> Analysis:
    return _to_analysis(
        article_id=article_id, brief_date=brief_date, model=model, now=now,
        impact=Impact.LOW, summary=None, rationale=None, dev_relevance=None,
        evidence=EvidenceBasis.TITLE_DESC_ONLY, status=AnalysisStatus.FAILED,
    )


def analyze_candidates(
    articles: list[Article],
    adapter: AIAdapter,
    tracker: UsageTracker,
    *,
    brief_date: str,
    now: datetime,
    retries: int = 1,
) -> list[Analysis]:
    by_cat: dict[Category, list[Article]] = defaultdict(list)
    for a in articles:
        by_cat[a.category].append(a)

    analyses: list[Analysis] = []
    for cat, items in by_cat.items():
        inputs = [
            AnalysisInput(ref=a.id, title=a.title, description=a.description, category=cat)
            for a in items
        ]
        # 요청 직전 상한 확인(초과 시 AIQuotaError 전파 → 중단)
        tracker.before_request(estimated_tokens=estimate_tokens(inputs))

        result = None
        for _ in range(retries + 1):
            try:
                result = adapter.analyze(cat, inputs)
                break
            except AIResponseError:
                continue
        if result is None:
            # 카테고리 전체 격리(다른 카테고리는 계속)
            tracker.add_failure()
            analyses.extend(_failed(a.id, brief_date, adapter.model, now) for a in items)
            continue

        tracker.add_tokens(result.tokens)
        by_ref = {r.ref: r for r in result.items}
        for a in items:
            r = by_ref.get(a.id)
            if r is None:
                analyses.append(_failed(a.id, brief_date, adapter.model, now))
                continue
            analyses.append(
                _to_analysis(
                    article_id=a.id, brief_date=brief_date, model=adapter.model, now=now,
                    impact=Impact(r.impact), summary=r.summary, rationale=r.rationale,
                    dev_relevance=r.dev_relevance, evidence=EvidenceBasis(r.evidence_basis),
                    status=AnalysisStatus(r.status),
                )
            )
    return analyses
