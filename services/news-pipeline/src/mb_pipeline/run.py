"""파이프라인 엔트리 (M0: Mock 드라이런 골격).

단계 순서(docs/04 §1)를 코드로 고정한다. M0 에서는 각 단계가 Mock/placeholder 이며,
M1(수집)·M2(AI·선정)·M4(푸시) 에서 실제 구현으로 대체된다. 외부 호출은 없다.

실행:
    python -m mb_pipeline.run
"""

from __future__ import annotations

from mb_pipeline.ai_schema import validate_ai_response
from mb_pipeline.contracts import MAX_PER_CATEGORY, MAX_TOTAL, Briefing, BriefingStatus
from mb_pipeline.mock import loader


def dry_run() -> Briefing:
    """Mock 데이터로 단계 순서를 통과시키고 브리핑 계약을 반환한다."""
    # ① 후보 수집 (M1 에서 실제 소스 어댑터로 대체)
    raw = loader.load_raw_articles()

    # ② 정규화 · ③ 중복제거 · ④ 사전 필터 (M1)  — M0 은 건수만 통과
    collected_count = len(raw)

    # ⑤ AI 영향도 분석 (M2). 여기서는 Mock 응답을 스키마로 검증만.
    ai_payload = loader.load_ai_response()
    errors = validate_ai_response(ai_payload)
    if errors:
        raise ValueError(f"AI 응답 스키마 위반: {errors}")

    # ⑥ 선정 (M2) · ⑦ HIGH 만 노출 브리핑 (M2)  — M0 은 Mock 브리핑 로드
    briefing = loader.load_briefing()

    # 불변식 점검 (선정 규칙)
    assert briefing.high_count == sum(1 for a in briefing.articles if a.is_high)
    assert len(briefing.articles) <= MAX_TOTAL
    per_cat: dict[str, int] = {}
    for a in briefing.articles:
        per_cat[a.category.value] = per_cat.get(a.category.value, 0) + 1
    assert all(n <= MAX_PER_CATEGORY for n in per_cat.values())

    print(
        f"[dry-run] collected={collected_count} "
        f"high={briefing.high_count} status={briefing.status.value} "
        f"read={briefing.est_read_minutes}min articles={len(briefing.articles)}"
    )
    return briefing


if __name__ == "__main__":
    b = dry_run()
    if b.status is not BriefingStatus.READY:
        raise SystemExit(f"브리핑이 ready 아님: {b.status}")
