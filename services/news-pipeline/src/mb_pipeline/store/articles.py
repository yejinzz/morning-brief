"""기사 저장소 (M1).

``ArticleStore`` 프로토콜 + 테스트·로컬용 인메모리 구현. canonical_url 기준 upsert 로
멱등 저장(동일 기사 재수집 시 중복 생성 없음)을 보장한다. Supabase 구현은 이후 마일스톤.
"""

from __future__ import annotations

from typing import Protocol

from mb_pipeline.contracts import Article


class ArticleStore(Protocol):
    def upsert(self, articles: list[Article]) -> int:
        """canonical_url 기준 upsert. 신규 삽입 건수를 반환."""
        ...

    def get_prior_urls(self, limit_days: int) -> set[str]:
        """최근 선정 기사 canonical_url 집합(이전 브리핑 중복 검사용)."""
        ...


class InMemoryArticleStore:
    """테스트·로컬용. canonical_url → Article."""

    def __init__(self) -> None:
        self._by_url: dict[str, Article] = {}
        self._prior_urls: set[str] = set()

    def upsert(self, articles: list[Article]) -> int:
        inserted = 0
        for a in articles:
            if a.canonical_url not in self._by_url:
                inserted += 1
            self._by_url[a.canonical_url] = a
        return inserted

    def get_prior_urls(self, limit_days: int) -> set[str]:
        return set(self._prior_urls)

    # 테스트 보조
    def seed_prior(self, urls: set[str]) -> None:
        self._prior_urls |= urls

    def all(self) -> list[Article]:
        return list(self._by_url.values())
