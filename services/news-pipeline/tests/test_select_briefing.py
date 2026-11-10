"""선정·브리핑 테스트 (M2): HIGH만, ≤3/≤15, 분석후선정, empty_high, 멱등, 읽기시간."""

from __future__ import annotations

from conftest import make_article
from mb_pipeline.ai.limits import UsageTracker
from mb_pipeline.ai.mock import MockAIAdapter
from mb_pipeline.contracts import (
    Analysis,
    AnalysisStatus,
    BriefingStatus,
    Category,
    EvidenceBasis,
    Impact,
)
from mb_pipeline.pipeline.generate import generate_briefing
from mb_pipeline.pipeline.select import select

NOW = make_article("x", "y").collected_at


def _analysis(
    aid: str, impact: Impact, status: AnalysisStatus = AnalysisStatus.ANALYZED
) -> Analysis:
    return Analysis(
        id=f"{aid}:d:m",
        article_id=aid,
        brief_date="2026-11-10",
        model="m",
        impact=impact,
        summary="요약",
        rationale="근거",
        dev_relevance="해당 없음",
        evidence_basis=EvidenceBasis.TITLE_DESC_ONLY,
        status=status,
        analyzed_at=NOW,
    )


def test_select_only_high_analyzed() -> None:
    arts = {a.id: a for a in [make_article(str(i), f"기사{i}") for i in range(4)]}
    analyses = [
        _analysis("0", Impact.HIGH),
        _analysis("1", Impact.MEDIUM),
        _analysis("2", Impact.HIGH, AnalysisStatus.FAILED),
        _analysis("3", Impact.LOW),
    ]
    sel = select(analyses, arts)
    assert {s.article.id for s in sel} == {"0"}  # HIGH + analyzed 만


def test_max_three_per_category() -> None:
    arts = {}
    analyses = []
    for i in range(5):
        a = make_article(f"a{i}", f"AI 기사 {i}", category=Category.AI, hour=i)
        arts[a.id] = a
        analyses.append(_analysis(a.id, Impact.HIGH))
    sel = select(analyses, arts)
    assert len(sel) == 3  # 카테고리별 최대 3


def test_generate_high_only_ready() -> None:
    arts = [
        make_article("1", "심각한 보안 취약점 공개", category=Category.DEV),
        make_article("2", "평범한 일상 소식", category=Category.AI),
    ]
    res = generate_briefing(arts, MockAIAdapter(), brief_date="2026-11-10", now=NOW)
    assert res.briefing.status is BriefingStatus.READY
    assert res.briefing.high_count == 1
    assert all(c.impact is Impact.HIGH for c in res.briefing.articles)
    assert res.briefing.est_read_minutes is not None and res.briefing.est_read_minutes >= 1
    assert res.briefing.headline


def test_generate_empty_high_when_no_high() -> None:
    arts = [make_article("1", "평범한 소식입니다", category=Category.AI)]
    res = generate_briefing(arts, MockAIAdapter(), brief_date="2026-11-10", now=NOW)
    assert res.briefing.status is BriefingStatus.EMPTY_HIGH
    assert res.briefing.high_count == 0
    assert res.briefing.headline is None


def test_generate_idempotent_same_analysis_ids() -> None:
    arts = [make_article("1", "보안 취약점 패치", category=Category.DEV)]
    r1 = generate_briefing(arts, MockAIAdapter(), brief_date="2026-11-10", now=NOW)
    r2 = generate_briefing(arts, MockAIAdapter(), brief_date="2026-11-10", now=NOW)
    assert [a.id for a in r1.analyses] == [a.id for a in r2.analyses]
    assert r1.briefing.model_dump() == r2.briefing.model_dump()


def test_usage_snapshot_tracks_requests() -> None:
    arts = [make_article("1", "보안 취약점", category=Category.DEV)]
    tracker = UsageTracker()
    generate_briefing(arts, MockAIAdapter(), brief_date="2026-11-10", now=NOW, tracker=tracker)
    assert tracker.snapshot()["requests"] >= 1
