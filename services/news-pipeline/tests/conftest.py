"""테스트 공용 헬퍼 (M1): RSS 빌더 + 가짜 fetcher."""

from __future__ import annotations

from collections.abc import Iterable

from mb_pipeline.sources.base import Fetcher, SourceError


def rss(items: Iterable[tuple[str, str, str]], *, title: str = "Feed") -> str:
    """(제목, 링크, RFC822 pubDate) 목록으로 RSS 2.0 문자열 생성."""
    entries = "".join(
        f"<item><title>{t}</title><link>{u}</link><pubDate>{d}</pubDate></item>"
        for (t, u, d) in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<rss version=\"2.0\"><channel><title>{title}</title>{entries}</channel></rss>"
    )


def atom(items: Iterable[tuple[str, str, str]], *, title: str = "Feed") -> str:
    entries = "".join(
        f"<entry><title>{t}</title><link href=\"{u}\"/><updated>{d}</updated></entry>"
        for (t, u, d) in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<feed xmlns="http://www.w3.org/2005/Atom"><title>{title}</title>{entries}</feed>'
    )


def fake_fetcher(mapping: dict[str, str], *, fail: set[str] | None = None) -> Fetcher:
    """url→본문 매핑 기반 가짜 fetcher. ``fail`` 에 든 url 은 SourceError."""
    fail = fail or set()

    def _fetch(url: str) -> str:
        if url in fail:
            raise SourceError(f"의도된 실패: {url}")
        if url not in mapping:
            raise SourceError(f"매핑 없음: {url}")
        return mapping[url]

    return _fetch
