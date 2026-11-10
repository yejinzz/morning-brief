"""AI 어댑터 인터페이스 (M2).

교체 가능한 최소 계약. 입력은 기사 메타(제목·짧은 설명·카테고리)뿐이며 원문 전문은
전송하지 않는다(저작권·토큰·프라이버시). 출력은 ``ai_schema`` 를 따르는 구조화 결과.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mb_pipeline.contracts import Category


@dataclass(frozen=True)
class AnalysisInput:
    ref: str  # 기사 식별자(= Article.id). 응답의 article_ref 와 매칭.
    title: str
    description: str | None
    category: Category


@dataclass(frozen=True)
class AIResultItem:
    ref: str
    impact: str  # HIGH/MEDIUM/LOW
    summary: str
    rationale: str
    dev_relevance: str
    evidence_basis: str  # full/title_desc_only
    status: str  # analyzed/held/conflict


@dataclass(frozen=True)
class AIResult:
    items: list[AIResultItem]
    model: str
    tokens: int = 0


class AIError(Exception):
    """AI 호출 일반 오류."""


class AIQuotaError(AIError):
    """무료 한도 소진(429 등). 유료 폴백 없이 즉시 중단 신호."""


class AIResponseError(AIError):
    """응답 형식/스키마 오류(제한적 재시도 대상)."""


class AIAdapter(Protocol):
    model: str

    def analyze(self, category: Category, items: list[AnalysisInput]) -> AIResult:
        """한 카테고리 후보 묶음을 분석. 실패 시 AIError 계열 raise."""
        ...
