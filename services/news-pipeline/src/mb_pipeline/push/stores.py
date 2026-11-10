"""구독·발송이력 저장소 (M4). Protocol + 인메모리. Supabase 구현은 이후.

날짜·기기별 중복 발송 방지(notification_deliveries unique)와 만료 구독 정리를 담당.
"""

from __future__ import annotations

from typing import Protocol

from mb_pipeline.push.base import PushSubscriptionData


class SubscriptionStore(Protocol):
    def list_active(self) -> list[PushSubscriptionData]: ...
    def deactivate(self, subscription_id: str) -> None: ...


class DeliveryStore(Protocol):
    def already_sent(self, brief_date: str, subscription_id: str) -> bool: ...
    def record(self, brief_date: str, subscription_id: str, status: str) -> None: ...


class InMemorySubscriptionStore:
    def __init__(self, subs: list[PushSubscriptionData] | None = None) -> None:
        self._subs = {s.id: s for s in (subs or [])}
        self._active = set(self._subs)

    def add(self, sub: PushSubscriptionData) -> None:
        self._subs[sub.id] = sub
        self._active.add(sub.id)

    def list_active(self) -> list[PushSubscriptionData]:
        return [self._subs[i] for i in self._subs if i in self._active]

    def deactivate(self, subscription_id: str) -> None:
        self._active.discard(subscription_id)


class InMemoryDeliveryStore:
    def __init__(self) -> None:
        self._sent: dict[tuple[str, str], str] = {}

    def already_sent(self, brief_date: str, subscription_id: str) -> bool:
        key = (brief_date, subscription_id)
        return self._sent.get(key) == "sent"

    def record(self, brief_date: str, subscription_id: str, status: str) -> None:
        self._sent[(brief_date, subscription_id)] = status
