"""사전 필터 테스트 (M2)."""

from __future__ import annotations

from conftest import make_article
from mb_pipeline.pipeline.prefilter import prefilter


def test_drops_short_title_and_ads() -> None:
    arts = [
        make_article("1", "정상적인 뉴스 제목입니다"),
        make_article("2", "짧다"),  # < 6자
        make_article("3", "[광고] 특가 분양 정보"),
    ]
    kept, dropped = prefilter(arts)
    assert {a.id for a in kept} == {"1"}
    assert dropped == 2
