"""푸시 발송 오케스트레이션 (M4). docs/07 §5, 02.4.

브리핑 정상 완료(ready) 후에만 호출. 날짜·기기별 중복 방지, 제한 재시도,
만료 구독(410/404) 정리. 저장 성공과 발송 실패를 분리(상위에서 브리핑은 이미 저장됨).
"""

from __future__ import annotations

from dataclasses import dataclass

from mb_pipeline.contracts import Briefing
from mb_pipeline.push.base import PushError, PushGoneError, PushSender
from mb_pipeline.push.payload import build_payload
from mb_pipeline.push.stores import DeliveryStore, SubscriptionStore


@dataclass
class PushSummary:
    sent: int = 0
    skipped: int = 0
    failed: int = 0
    gone: int = 0


def send_briefing_push(
    briefing: Briefing,
    *,
    subscriptions: SubscriptionStore,
    deliveries: DeliveryStore,
    sender: PushSender,
    retries: int = 2,
) -> PushSummary:
    payload = build_payload(briefing)
    summary = PushSummary()

    for sub in subscriptions.list_active():
        # 날짜·기기 중복 방지(멱등)
        if deliveries.already_sent(briefing.brief_date, sub.id):
            summary.skipped += 1
            continue

        last: Exception | None = None
        for _ in range(retries + 1):
            try:
                sender.send(sub, payload)
                deliveries.record(briefing.brief_date, sub.id, "sent")
                summary.sent += 1
                last = None
                break
            except PushGoneError:
                # 만료 구독 → 정리하고 재시도 안 함
                subscriptions.deactivate(sub.id)
                deliveries.record(briefing.brief_date, sub.id, "skipped")
                summary.gone += 1
                last = None
                break
            except PushError as exc:
                last = exc
        if last is not None:
            deliveries.record(briefing.brief_date, sub.id, "failed")
            summary.failed += 1

    return summary
