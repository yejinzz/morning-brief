"""교차언어 LLM dedup 테스트: 대표 유지·비대표 제외, HIGH 한정, best-effort."""

from __future__ import annotations

from datetime import UTC, datetime

from conftest import make_article
from mb_pipeline.ai.base import AIError, DedupGroup, DedupInput
from mb_pipeline.contracts import (
    Analysis,
    AnalysisStatus,
    Category,
    EvidenceBasis,
    Impact,
)
from mb_pipeline.pipeline.dedup_llm import dedup_high_llm

NOW = datetime(2026, 11, 12, tzinfo=UTC)


def _an(
    article_id: str,
    *,
    impact: Impact = Impact.HIGH,
    status: AnalysisStatus = AnalysisStatus.ANALYZED,
) -> Analysis:
    return Analysis(
        id=f"an-{article_id}",
        article_id=article_id,
        brief_date="2026-11-12",
        model="m",
        impact=impact,
        evidence_basis=EvidenceBasis.FULL,
        status=status,
        analyzed_at=NOW,
    )


class _StubAdapter:
    model = "stub"

    def __init__(self, *, groups: list[DedupGroup] | None = None, error: bool = False) -> None:
        self._groups = groups or []
        self._error = error
        self.seen: list[DedupInput] | None = None

    def analyze(self, category, items):  # pragma: no cover - dedup 경로 미사용
        raise NotImplementedError

    def dedup_high(self, items: list[DedupInput]) -> list[DedupGroup]:
        self.seen = items
        if self._error:
            raise AIError("stub 실패")
        return self._groups


def test_drops_cross_lingual_duplicates() -> None:
    arts = {
        "a1": make_article("a1", "Nvidia to oust Jensen Huang", category=Category.DEV),
        "a2": make_article("a2", "엔비디아 젠슨 황 해임", category=Category.TECH),
        "a3": make_article("a3", "한국은행 금리 동결", category=Category.ECONOMY),
    }
    analyses = [_an("a1"), _an("a2"), _an("a3")]
    adapter = _StubAdapter(groups=[DedupGroup(representative_ref="a1", duplicate_refs=["a2"])])
    drop = dedup_high_llm(analyses, arts, adapter)
    assert drop == {"a2"}  # 대표(a1) 유지, 비대표(a2) 제외
    assert adapter.seen is not None
    assert {i.ref for i in adapter.seen} == {"a1", "a2", "a3"}  # HIGH+analyzed 만 전달


def test_only_high_analyzed_considered() -> None:
    arts = {"a1": make_article("a1", "t1"), "a2": make_article("a2", "t2")}
    analyses = [_an("a1", impact=Impact.MEDIUM), _an("a2", status=AnalysisStatus.FAILED)]
    adapter = _StubAdapter()
    drop = dedup_high_llm(analyses, arts, adapter)
    assert drop == set()
    assert adapter.seen is None  # HIGH 후보 <2 → 호출조차 안 함


def test_best_effort_on_error() -> None:
    arts = {"a1": make_article("a1", "t1"), "a2": make_article("a2", "t2")}
    analyses = [_an("a1"), _an("a2")]
    adapter = _StubAdapter(error=True)
    drop = dedup_high_llm(analyses, arts, adapter)
    assert drop == set()  # 호출 실패 → 아무것도 버리지 않음(토큰 dedup 결과 유지)
