"""실 Web Push 발송 (M4). pywebpush 사용(선택 의존성 `.[push]`). CI 미실행.

VAPID 서명 + 페이로드 암호화는 pywebpush 가 처리한다. 404/410 → PushGoneError(구독 정리).
키·네트워크가 필요하므로 테스트는 MockPushSender 를 쓴다.
"""

from __future__ import annotations

from mb_pipeline.push.base import PushError, PushGoneError, PushSubscriptionData


class WebPushSender:
    def __init__(self, vapid_private_key: str, vapid_subject: str, *, ttl: int = 3600) -> None:
        if not vapid_private_key or not vapid_subject:
            raise PushError("VAPID 개인키/subject 가 비어 있음")
        self._key = vapid_private_key
        self._subject = vapid_subject
        self._ttl = ttl

    def send(self, sub: PushSubscriptionData, payload: str) -> None:
        # 선택 의존성은 지연 import (CI/테스트 기본 환경에 미설치)
        from pywebpush import WebPushException, webpush

        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=self._key,
                vapid_claims={"sub": self._subject},
                ttl=self._ttl,
            )
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)
            if status in (404, 410):
                raise PushGoneError(f"구독 만료: {status}") from exc
            raise PushError(f"푸시 실패: {status}") from exc
        except ValueError as exc:
            # 잘못된 키/형식(base64 디코딩 실패 등) → 영구 무효 → 정리(deactivate)
            raise PushGoneError(f"잘못된 구독(키 형식): {exc}") from exc
        except Exception as exc:
            # 그 외 예기치 못한 오류는 격리(배치 전체 중단 방지), 재시도 대상
            raise PushError(f"푸시 발송 오류: {exc}") from exc
