"""수집 오케스트레이션 (M1). docs/04-news-pipeline.md §1-§5.

흐름: 소스별 fetch+parse(재시도·격리) → 정규화 → 중복제거 → 24→72h 윈도우(부족 시 확장)
→ 카테고리별 후보 상한. 반환은 후보 목록 + 단계별 건수 + 소스 실패 목록(collection_jobs 로그용).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from mb_pipeline.contracts import Article, Category
from mb_pipeline.pipeline import dedup, normalize
from mb_pipeline.sources.base import Fetcher, Source, SourceError
from mb_pipeline.sources.rss import parse_feed

# 기본 파라미터 (docs/02.3.1, 04 §5)
DEFAULT_WINDOWS_H = (24, 48, 72)
DEFAULT_MIN_PER_CATEGORY = 10
DEFAULT_CAP_PER_CATEGORY = 20


@dataclass(frozen=True)
class SourceFailure:
    source: str
    category: Category
    error: str


@dataclass
class CollectResult:
    candidates: list[Article]
    failures: list[SourceFailure] = field(default_factory=list)
    stage_counts: dict[str, object] = field(default_factory=dict)


def collect(
    sources: list[Source],
    *,
    fetcher: Fetcher,
    now: datetime,
    retries: int = 1,
    windows_h: tuple[int, ...] = DEFAULT_WINDOWS_H,
    min_per_category: int = DEFAULT_MIN_PER_CATEGORY,
    cap_per_category: int = DEFAULT_CAP_PER_CATEGORY,
    prior_urls: set[str] | None = None,
) -> CollectResult:
    # ① 수집(소스 격리) ──────────────────────────────────────
    raw_articles: list[Article] = []
    failures: list[SourceFailure] = []
    for source in sources:
        if not source.enabled:
            continue
        last: Exception | None = None
        parsed = None
        for _ in range(retries + 1):
            try:
                parsed = parse_feed(fetcher(source.url), source)
                break
            except SourceError as exc:
                last = exc
        if parsed is None:
            failures.append(SourceFailure(source.name, source.category, str(last)))
            continue
        raw_articles.extend(normalize.to_article(r, collected_at=now) for r in parsed)

    fetched_count = len(raw_articles)

    # ② 중복 제거 ────────────────────────────────────────────
    dd = deduplicate_result = dedup.deduplicate(raw_articles, prior_urls=prior_urls)
    kept = dd.kept

    # ③ 카테고리별 윈도우(24→72h) + 상한 ─────────────────────
    by_cat: dict[Category, list[Article]] = defaultdict(list)
    for a in kept:
        by_cat[a.category].append(a)

    candidates: list[Article] = []
    per_cat_counts: dict[str, int] = {}
    window_used: dict[str, int] = {}

    for cat, items in by_cat.items():
        chosen: list[Article] = items
        for w in windows_h:
            cutoff = now - timedelta(hours=w)
            fresh = [a for a in items if a.published_at is None or a.published_at >= cutoff]
            chosen = fresh
            window_used[cat.value] = w
            if len(fresh) >= min_per_category:
                break
        chosen.sort(key=_recency_key)
        chosen = chosen[:cap_per_category]
        per_cat_counts[cat.value] = len(chosen)
        candidates.extend(chosen)

    return CollectResult(
        candidates=candidates,
        failures=failures,
        stage_counts={
            "sources": len([s for s in sources if s.enabled]),
            "fetched": fetched_count,
            "deduped": len(kept),
            "dropped_duplicate": len(deduplicate_result.dropped_duplicate),
            "dropped_prior": len(deduplicate_result.dropped_prior),
            "candidates": len(candidates),
            "per_category": per_cat_counts,
            "window_hours": window_used,
            "failures": len(failures),
        },
    )


def _recency_key(a: Article) -> tuple[int, float]:
    # 최신 우선(발행 시각 내림차순), 미상은 뒤로.
    if a.published_at is None:
        return (1, 0.0)
    return (0, -a.published_at.timestamp())
