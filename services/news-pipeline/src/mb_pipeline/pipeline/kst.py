"""KST 시간대 유틸 (M4). docs/02 §6. 배치는 UTC로 돌지만 브리핑 날짜는 Asia/Seoul 기준."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def kst_date(now_utc: datetime) -> str:
    """UTC(또는 tz-aware) 시각 → KST 기준 'YYYY-MM-DD' 멱등 키."""
    return now_utc.astimezone(KST).strftime("%Y-%m-%d")
