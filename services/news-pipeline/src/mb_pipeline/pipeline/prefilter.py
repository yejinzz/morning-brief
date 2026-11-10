"""사전 필터 (M2). AI 호출 전 저품질·무관 기사 제거로 비용 절감. docs/04 §5.

과도 제거 금지(약한 필터). 명백한 저품질/광고/빈약한 제목만 제외한다.
"""

from __future__ import annotations

from mb_pipeline.contracts import Article

_MIN_TITLE_LEN = 6
_AD_MARKERS = ("[광고]", "[ad]", "분양", "프로모션", "쿠폰", "할인코드", "sponsored")


def is_low_quality(article: Article) -> bool:
    title = article.title.strip()
    if len(title) < _MIN_TITLE_LEN:
        return True
    low = title.lower()
    return any(m in low for m in _AD_MARKERS)


def prefilter(articles: list[Article]) -> tuple[list[Article], int]:
    """(통과 기사, 제외 건수)."""
    kept = [a for a in articles if not is_low_quality(a)]
    return kept, len(articles) - len(kept)
