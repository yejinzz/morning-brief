"""공유 데이터 계약 (M0).

이 모듈은 파이프라인 전 단계와 PWA가 공유하는 데이터 형태를 Python(pydantic)으로 고정한다.
동일한 형태가 TypeScript 쪽 ``apps/web/src/types/contracts.ts`` 에 미러링되어 있으므로,
한쪽을 바꾸면 반드시 다른 쪽도 함께 갱신한다.

설계 근거: docs/05-database.md, docs/04-news-pipeline.md §6.3
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Category(StrEnum):
    """뉴스 카테고리 (안정 키 ↔ 표시명)."""

    DOMESTIC = "domestic"  # 국내 시사
    ECONOMY = "economy"  # 경제·국제
    AI = "ai"  # AI·LLM
    DEV = "dev"  # 개발·인프라
    TECH = "tech"  # 기타 테크


CATEGORY_LABELS: dict[Category, str] = {
    Category.DOMESTIC: "국내 시사",
    Category.ECONOMY: "경제·국제",
    Category.AI: "AI·LLM",
    Category.DEV: "개발·인프라",
    Category.TECH: "기타 테크",
}

# PWA 탭 순서 (전체는 UI 전용, 여기서는 카테고리 순서만)
CATEGORY_ORDER: list[Category] = [
    Category.DOMESTIC,
    Category.ECONOMY,
    Category.AI,
    Category.DEV,
    Category.TECH,
]


class Impact(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EvidenceBasis(StrEnum):
    """분석 근거 범위 (환각 방지 표시)."""

    FULL = "full"
    TITLE_DESC_ONLY = "title_desc_only"


class AnalysisStatus(StrEnum):
    ANALYZED = "analyzed"
    HELD = "held"  # 검증 불가 → 보류
    CONFLICT = "conflict"  # 출처 충돌
    FAILED = "failed"  # 분석 실패(격리)


class BriefingStatus(StrEnum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    EMPTY_HIGH = "empty_high"  # 정상 완료, HIGH 0건


class JobStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"


# ── 수집/저장 단계 모델 ────────────────────────────────────────


class RawArticle(BaseModel):
    """소스 어댑터가 반환하는 정규화 전 원본 (M1)."""

    source: str
    source_feed: str | None = None
    title: str
    url: str  # http(s) URL. 소스 파서가 scheme 를 검증한다.
    description: str | None = None
    published_at: datetime | None = None
    category: Category
    lang: str = "ko"


class Article(BaseModel):
    """정규화·중복제거 후 저장 대상 (news_articles)."""

    id: str
    canonical_url: str
    source: str
    source_feed: str | None = None
    title: str
    description: str | None = None
    category: Category
    published_at: datetime | None = None
    collected_at: datetime
    dedup_group: str | None = None
    lang: str = "ko"


class Analysis(BaseModel):
    """기사별 AI 분석 결과 (news_analyses). MEDIUM/LOW 포함 모두 저장."""

    id: str
    article_id: str
    brief_date: str  # KST ISO date (YYYY-MM-DD)
    model: str
    impact: Impact
    summary: str | None = None  # 3문장 이내 독자적 요약
    rationale: str | None = None
    dev_relevance: str | None = None
    evidence_basis: EvidenceBasis
    status: AnalysisStatus
    analyzed_at: datetime


# ── PWA 읽기(조회) 계약 ────────────────────────────────────────


class ArticleCard(BaseModel):
    """PWA 카드 1건 (briefing_articles + 조인). 기본 노출은 HIGH 만."""

    id: str
    category: Category
    title: str
    summary: str | None = None
    rationale: str | None = None
    dev_relevance: str | None = None
    source: str
    published_at: datetime | None = None
    url: str
    impact: Impact
    evidence_basis: EvidenceBasis
    display_order: int
    is_high: bool = True


class Briefing(BaseModel):
    """날짜별 브리핑 응답 (daily_briefings + cards). PWA가 소비하는 최상위 계약."""

    brief_date: str  # KST ISO date
    headline: str | None = None  # 오늘의 한 줄 브리핑
    collected_count: int = 0
    high_count: int = 0
    est_read_minutes: int | None = None
    status: BriefingStatus
    generated_at: datetime | None = None
    articles: list[ArticleCard] = Field(default_factory=list)


# ── 선정 규칙 상수 (docs/04 §7) ────────────────────────────────

MAX_PER_CATEGORY = 3
MAX_TOTAL = 15
