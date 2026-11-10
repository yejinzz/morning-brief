"""Mock 푸시 전송 (M4). 네트워크·키 없이 발송 로직 테스트.

특정 구독 id 에 대해 만료(410)/실패를 재현할 수 있다.
"""

from __future__ import annotations

from mb_pipeline.push.base import PushError, PushGoneError, PushSubscriptionData


class MockPushSender:
    def __init__(self, *, gone: set[str] | None = None, fail: set[str] | None = None) -> None:
        self._gone = gone or set()
        self._fail = fail or set()
        self.sent: list[tuple[str, str]] = []  # (subscription_id, payload)

    def send(self, sub: PushSubscriptionData, payload: str) -> None:
        if sub.id in self._gone:
            raise PushGoneError(f"mock: 만료 구독 {sub.id}")
        if sub.id in self._fail:
            raise PushError(f"mock: 발송 실패 {sub.id}")
        self.sent.append((sub.id, payload))
