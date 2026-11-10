"""푸시 발송 인터페이스 (M4).

발송은 서명된 VAPID JWT + 암호화 페이로드를 구독 엔드포인트로 POST 하는 표준 Web Push.
전송 수단은 주입식(Protocol)이라 테스트는 네트워크 없이 MockPushSender 를 쓴다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PushSubscriptionData:
    id: str
    endpoint: str
    p256dh: str
    auth: str


class PushError(Exception):
    """일반 발송 실패(재시도 대상)."""


class PushGoneError(PushError):
    """구독 만료/무효(HTTP 404/410). 구독을 정리해야 함."""


class PushSender(Protocol):
    def send(self, sub: PushSubscriptionData, payload: str) -> None:
        """단일 구독에 발송. 만료면 PushGoneError, 그 외 실패는 PushError."""
        ...
