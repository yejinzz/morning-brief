"""Mock AI 어댑터 (M2). 네트워크·키 없이 결정적 분석. 개발·테스트용.

규칙 기반 분류(키워드)로 재현 가능한 결과를 낸다. 오류 경로(한도/깨진 응답)도
플래그로 재현할 수 있다.
"""

from __future__ import annotations

from mb_pipeline.ai.base import (
    AIQuotaError,
    AIResponseError,
    AIResult,
    AIResultItem,
    AnalysisInput,
)
from mb_pipeline.contracts import Category

# HIGH 로 올릴 키워드(데모용 규칙)
_HIGH_KEYWORDS = (
    "보안", "취약점", "해킹", "금리", "표준", "규제", "장애", "유출",
    "security", "vulnerability", "cve", "breaking", "outage",
)
_MEDIUM_KEYWORDS = ("출시", "발표", "업데이트", "release", "update", "launch")


def _classify(title: str) -> str:
    low = title.lower()
    if any(k in low for k in _HIGH_KEYWORDS):
        return "HIGH"
    if any(k in low for k in _MEDIUM_KEYWORDS):
        return "MEDIUM"
    return "LOW"


class MockAIAdapter:
    model = "mock-1"

    def __init__(self, *, raise_quota: bool = False, bad_response: bool = False) -> None:
        self._raise_quota = raise_quota
        self._bad_response = bad_response

    def analyze(self, category: Category, items: list[AnalysisInput]) -> AIResult:
        if self._raise_quota:
            raise AIQuotaError("mock: 무료 한도 소진(429)")
        if self._bad_response:
            raise AIResponseError("mock: 스키마 위반 응답")
        out: list[AIResultItem] = []
        for it in items:
            impact = _classify(it.title)
            out.append(
                AIResultItem(
                    ref=it.ref,
                    impact=impact,
                    summary=f"{it.title} 관련 요약(모의).",
                    rationale="모의 판단 근거.",
                    dev_relevance="해당 없음" if category is not Category.DEV else "개발 관련.",
                    evidence_basis="title_desc_only",
                    status="analyzed",
                )
            )
        return AIResult(items=out, model=self.model, tokens=len(items) * 50)
