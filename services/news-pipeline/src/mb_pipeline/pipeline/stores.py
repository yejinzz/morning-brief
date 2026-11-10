"""브리핑·실행(Job) 저장소 (M4). Protocol + 인메모리. Supabase 구현은 이후.

Job 은 동일 날짜 동시/중복 실행 방지(멱등). 브리핑 저장은 upsert(동일 날짜 덮어쓰기).
"""

from __future__ import annotations

from typing import Protocol

from mb_pipeline.contracts import Analysis, Article, Briefing


class BriefingStore(Protocol):
    def save(
        self, briefing: Briefing, analyses: list[Analysis], articles: list[Article]
    ) -> None: ...
    def get(self, brief_date: str) -> Briefing | None: ...


class JobStore(Protocol):
    def try_start(self, brief_date: str) -> bool:
        """실행 시작 등록. 이미 running 이면 False(중복 실행 방지)."""
        ...

    def finish(self, brief_date: str, status: str, counts: dict[str, object]) -> None: ...


class InMemoryBriefingStore:
    def __init__(self) -> None:
        self._briefings: dict[str, Briefing] = {}
        self._analyses: dict[str, list[Analysis]] = {}
        self._articles: dict[str, list[Article]] = {}

    def save(
        self, briefing: Briefing, analyses: list[Analysis], articles: list[Article]
    ) -> None:
        self._briefings[briefing.brief_date] = briefing  # upsert(멱등)
        self._analyses[briefing.brief_date] = analyses
        self._articles[briefing.brief_date] = articles

    def get(self, brief_date: str) -> Briefing | None:
        return self._briefings.get(brief_date)


class InMemoryJobStore:
    def __init__(self) -> None:
        self._running: set[str] = set()
        self.records: list[dict[str, object]] = []

    def try_start(self, brief_date: str) -> bool:
        if brief_date in self._running:
            return False
        self._running.add(brief_date)
        return True

    def finish(self, brief_date: str, status: str, counts: dict[str, object]) -> None:
        self._running.discard(brief_date)
        self.records.append({"brief_date": brief_date, "status": status, **counts})
