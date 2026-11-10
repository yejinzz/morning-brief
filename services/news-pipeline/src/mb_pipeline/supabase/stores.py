"""Supabase 저장소 구현 (M5). 배치가 secret key 로 쓰는 live 저장소.

Protocol(pipeline/stores.py, push/stores.py)을 PostgREST 호출로 구현한다.
HTTP 전송은 주입식이라 contract 테스트로 호출 내용을 검증(라이브 검증은 배포 시).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from mb_pipeline.contracts import Analysis, Article, Briefing
from mb_pipeline.push.base import PushSubscriptionData
from mb_pipeline.supabase.client import ConflictError, PostgrestClient

_BA_NS = uuid.UUID("c3d4e5f6-7081-5293-a4b5-c6d7e8f90123")


def _briefing_article_id(brief_date: str, article_id: str) -> str:
    return str(uuid.uuid5(_BA_NS, f"{brief_date}:{article_id}"))


class SupabaseJobStore:
    def __init__(self, client: PostgrestClient) -> None:
        self._c = client

    # 이 시간보다 오래된 running 은 크래시로 남은 것으로 간주(배치는 수 분 내 완료)
    STALE_MINUTES = 5

    def try_start(self, brief_date: str) -> bool:
        try:
            # 동일 날짜 running 1건 부분 unique → 두 번째는 409.
            self._c.insert("collection_jobs", [{"brief_date": brief_date, "status": "running"}])
            return True
        except ConflictError:
            # stale running(크래시 잔존) 정리 후 1회 재시도
            threshold = (datetime.now(UTC) - timedelta(minutes=self.STALE_MINUTES)).isoformat()
            self._c.update(
                "collection_jobs",
                filters={
                    "brief_date": f"eq.{brief_date}",
                    "status": "eq.running",
                    "started_at": f"lt.{threshold}",
                },
                patch={"status": "failed", "error": "stale (auto-recovered)"},
            )
            try:
                self._c.insert(
                    "collection_jobs", [{"brief_date": brief_date, "status": "running"}]
                )
                return True
            except ConflictError:
                return False  # 최근 running 존재 → 실제 동시 실행

    def finish(self, brief_date: str, status: str, counts: dict[str, object]) -> None:
        self._c.update(
            "collection_jobs",
            filters={"brief_date": f"eq.{brief_date}", "status": "eq.running"},
            patch={"status": status, "stage_counts": counts, "finished_at": "now()"},
        )


class SupabaseBriefingStore:
    def __init__(self, client: PostgrestClient) -> None:
        self._c = client

    def save(
        self, briefing: Briefing, analyses: list[Analysis], articles: list[Article]
    ) -> None:
        # ① 후보 기사(FK 대상) upsert
        self._c.upsert(
            "news_articles",
            [a.model_dump(mode="json") for a in articles],
            on_conflict="id",
        )
        # ② 분석 결과(모두) upsert
        self._c.upsert(
            "news_analyses",
            [a.model_dump(mode="json") for a in analyses],
            on_conflict="id",
        )
        # ③ 브리핑 헤더 upsert(날짜 멱등)
        self._c.upsert(
            "daily_briefings",
            [
                {
                    "brief_date": briefing.brief_date,
                    "headline": briefing.headline,
                    "collected_count": briefing.collected_count,
                    "high_count": briefing.high_count,
                    "est_read_minutes": briefing.est_read_minutes,
                    "status": briefing.status.value,
                    "generated_at": briefing.generated_at.isoformat()
                    if briefing.generated_at
                    else None,
                }
            ],
            on_conflict="brief_date",
        )
        # ④ 선정 결과 교체(기존 삭제 후 삽입)
        self._c.delete("briefing_articles", filters={"brief_date": f"eq.{briefing.brief_date}"})
        analysis_by_article = {
            a.article_id: a.id for a in analyses if a.status.value == "analyzed"
        }
        rows = [
            {
                "id": _briefing_article_id(briefing.brief_date, card.id),
                "brief_date": briefing.brief_date,
                "article_id": card.id,
                "analysis_id": analysis_by_article.get(card.id),
                "category": card.category.value,
                "display_order": card.display_order,
                "is_high": card.is_high,
            }
            for card in briefing.articles
        ]
        if rows:
            self._c.insert("briefing_articles", rows)

    def get(self, brief_date: str) -> Briefing | None:
        rows = self._c.select(
            "daily_briefings", query=f"brief_date=eq.{brief_date}&limit=1"
        )
        if not rows:
            return None
        r = rows[0]
        return Briefing(
            brief_date=r["brief_date"],
            headline=r.get("headline"),
            collected_count=r.get("collected_count", 0),
            high_count=r.get("high_count", 0),
            est_read_minutes=r.get("est_read_minutes"),
            status=r["status"],
            generated_at=r.get("generated_at"),
        )


class SupabaseSubscriptionStore:
    def __init__(self, client: PostgrestClient) -> None:
        self._c = client

    def list_active(self) -> list[PushSubscriptionData]:
        rows = self._c.select(
            "push_subscriptions",
            query="active=eq.true&select=id,endpoint,p256dh,auth",
        )
        return [
            PushSubscriptionData(
                id=r["id"], endpoint=r["endpoint"], p256dh=r["p256dh"], auth=r["auth"]
            )
            for r in rows
        ]

    def deactivate(self, subscription_id: str) -> None:
        self._c.update(
            "push_subscriptions",
            filters={"id": f"eq.{subscription_id}"},
            patch={"active": False},
        )


class SupabaseDeliveryStore:
    def __init__(self, client: PostgrestClient) -> None:
        self._c = client

    def already_sent(self, brief_date: str, subscription_id: str) -> bool:
        rows = self._c.select(
            "notification_deliveries",
            query=(
                f"brief_date=eq.{brief_date}"
                f"&subscription_id=eq.{subscription_id}"
                "&status=eq.sent&select=id&limit=1"
            ),
        )
        return len(rows) > 0

    def record(self, brief_date: str, subscription_id: str, status: str) -> None:
        self._c.upsert(
            "notification_deliveries",
            [{"brief_date": brief_date, "subscription_id": subscription_id, "status": status}],
            on_conflict="brief_date,subscription_id",
        )
