"""파이프라인 엔트리 (Mock 드라이런). 외부 호출 없이 전체 흐름을 통과시킨다.

M0: 계약·스키마. M1: 정규화. M2: 사전필터→AI 분석(Mock)→선정→브리핑.
실제 소스/AI/DB 연동은 각 마일스톤의 어댑터로 대체된다.

실행:
    python -m mb_pipeline.run
"""

from __future__ import annotations

from datetime import UTC, datetime

from mb_pipeline.ai.mock import MockAIAdapter
from mb_pipeline.contracts import MAX_PER_CATEGORY, MAX_TOTAL, BriefingStatus
from mb_pipeline.mock import loader
from mb_pipeline.pipeline import normalize
from mb_pipeline.pipeline.generate import generate_briefing


def dry_run() -> None:
    now = datetime(2026, 11, 10, 22, 0, tzinfo=UTC)

    # ① 수집(Mock) → ② 정규화
    raw = loader.load_raw_articles()
    articles = [normalize.to_article(r, collected_at=now) for r in raw]

    # ④ 사전필터 → ⑤ AI 분석(Mock) → ⑥ 선정 → ⑦ 브리핑
    res = generate_briefing(articles, MockAIAdapter(), brief_date="2026-11-10", now=now)
    b = res.briefing

    # 불변식 점검
    assert b.high_count == sum(1 for a in b.articles if a.is_high)
    assert len(b.articles) <= MAX_TOTAL
    per_cat: dict[str, int] = {}
    for a in b.articles:
        per_cat[a.category.value] = per_cat.get(a.category.value, 0) + 1
    assert all(n <= MAX_PER_CATEGORY for n in per_cat.values())
    assert b.status in {BriefingStatus.READY, BriefingStatus.EMPTY_HIGH}

    print(f"[dry-run] {res.stage_counts}")
    print(f"[dry-run] headline={b.headline}")
    for a in b.articles:
        print(f"   - [{a.category.value}] {a.impact.value} {a.title[:48]}")


if __name__ == "__main__":
    dry_run()
