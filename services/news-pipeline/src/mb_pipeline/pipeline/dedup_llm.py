"""교차언어 LLM 중복 제거 (분석 후). docs/04 §4 보강.

토큰 자카드 dedup(pipeline/dedup.py)는 같은 언어 내에서만 동작한다.
엔비디아↔Nvidia, 젠슨 황↔Jensen Huang 처럼 언어가 다른 같은 사건은 못 잡으므로,
HIGH 후보에 한해 LLM 에게 "같은 실제 사건" 그룹핑을 맡겨 대표 1건만 남긴다.

- 대상: HIGH + analyzed 분석만(보통 10~20건) → Gemini 1콜, 무료 티어 내.
- best-effort: 호출 실패(429/503/타임아웃/파싱)면 아무것도 버리지 않고 토큰 dedup 결과 유지.
- 반환: 선정에서 제외할 article_id 집합(분석 저장은 전부 유지, 노출만 대표 1건).
"""

from __future__ import annotations

from mb_pipeline.ai.base import AIAdapter, AIError, DedupInput
from mb_pipeline.contracts import Analysis, AnalysisStatus, Article, Impact


def dedup_high_llm(
    analyses: list[Analysis],
    articles_by_id: dict[str, Article],
    adapter: AIAdapter,
) -> set[str]:
    """HIGH 후보 교차언어 중복의 비대표 article_id 집합을 반환(best-effort)."""
    high: list[Article] = [
        art
        for an in analyses
        if an.impact is Impact.HIGH
        and an.status is AnalysisStatus.ANALYZED
        and (art := articles_by_id.get(an.article_id)) is not None
    ]
    if len(high) < 2:
        return set()

    items = [
        DedupInput(ref=a.id, title=a.title, source=a.source, category=a.category) for a in high
    ]
    try:
        groups = adapter.dedup_high(items)
    except AIError as exc:  # best-effort: 실패 시 아무것도 버리지 않음
        print(f"[dedup_llm] 교차언어 dedup 건너뜀(격리): {exc}")
        return set()

    drop: set[str] = set()
    for g in groups:
        for ref in g.duplicate_refs:
            if ref != g.representative_ref:
                drop.add(ref)
    return drop
