"""AI 분석 오케스트레이션 테스트 (M2): 묶음, 재시도 격리, 한도 중단, 미매칭."""

from __future__ import annotations

import pytest

from conftest import make_article
from mb_pipeline.ai.base import AIQuotaError, AIResult, AIResultItem, AnalysisInput
from mb_pipeline.ai.limits import DailyLimits, UsageTracker
from mb_pipeline.ai.mock import MockAIAdapter
from mb_pipeline.contracts import AnalysisStatus, Category, Impact
from mb_pipeline.pipeline.analyze import analyze_candidates

NOW = make_article("x", "y").collected_at


def _run(articles, adapter, tracker=None, retries=1):
    return analyze_candidates(
        articles, adapter, tracker or UsageTracker(),
        brief_date="2026-11-10", now=NOW, retries=retries,
    )


def test_batch_analyzes_all_with_mock() -> None:
    arts = [
        make_article("1", "심각한 보안 취약점 발견", category=Category.DEV),
        make_article("2", "새 제품 출시 발표", category=Category.DEV),
        make_article("3", "일상적인 소식", category=Category.AI),
    ]
    out = _run(arts, MockAIAdapter())
    by_id = {a.article_id: a for a in out}
    assert by_id["1"].impact is Impact.HIGH
    assert by_id["2"].impact is Impact.MEDIUM
    assert by_id["3"].impact is Impact.LOW
    assert all(a.status is AnalysisStatus.ANALYZED for a in out)


def test_keywords_mapped_from_adapter() -> None:
    arts = [make_article("1", "심각한 보안 취약점 발견", category=Category.DEV)]
    out = _run(arts, MockAIAdapter())
    # Mock 은 제목 앞 토큰을 키워드로 반환 → Analysis.keywords 로 매핑
    assert out[0].keywords == ["심각한", "보안", "취약점"]


def test_quota_error_propagates_and_stops() -> None:
    arts = [make_article("1", "아무 기사나")]
    with pytest.raises(AIQuotaError):
        _run(arts, MockAIAdapter(raise_quota=True))


def test_bad_response_isolated_as_failed() -> None:
    arts = [make_article("1", "기사 하나", category=Category.AI)]
    out = _run(arts, MockAIAdapter(bad_response=True), retries=1)
    assert len(out) == 1
    assert out[0].status is AnalysisStatus.FAILED


def test_unmatched_ref_marked_failed() -> None:
    class DropOneAdapter:
        model = "drop-1"

        def analyze(self, category: Category, items: list[AnalysisInput]) -> AIResult:
            # 두 번째 기사 결과를 누락시킨다
            first = items[0]
            return AIResult(
                items=[
                    AIResultItem(first.ref, "HIGH", "요약", "근거", "해당 없음",
                                 "title_desc_only", "analyzed")
                ],
                model=self.model,
            )

    arts = [make_article("1", "첫째"), make_article("2", "둘째")]
    out = _run(arts, DropOneAdapter())
    by_id = {a.article_id: a for a in out}
    assert by_id["1"].status is AnalysisStatus.ANALYZED
    assert by_id["2"].status is AnalysisStatus.FAILED


def test_request_cap_triggers_quota() -> None:
    # 요청 상한 0 → 첫 요청에서 중단
    tracker = UsageTracker(DailyLimits(max_requests=0))
    with pytest.raises(AIQuotaError):
        _run([make_article("1", "기사")], MockAIAdapter(), tracker=tracker)
