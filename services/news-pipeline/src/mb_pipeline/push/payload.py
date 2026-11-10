"""푸시 페이로드 구성 (M4). docs/02.4, 06 §5. 4KB 이내.

알림: "오늘의 주요 뉴스 N건" + 카테고리별 HIGH 건수 + 예상 읽기 시간. 탭 시 해당 날짜 딥링크.
"""

from __future__ import annotations

import json

from mb_pipeline.contracts import CATEGORY_LABELS, Briefing, Category

MAX_PAYLOAD_BYTES = 4096


def build_payload(briefing: Briefing) -> str:
    counts: dict[Category, int] = {}
    for card in briefing.articles:
        counts[card.category] = counts.get(card.category, 0) + 1
    parts = [f"{CATEGORY_LABELS[c]} {n}" for c, n in counts.items()]
    if briefing.est_read_minutes:
        parts.append(f"약 {briefing.est_read_minutes}분")

    data = {
        "title": f"오늘의 주요 뉴스 {briefing.high_count}건",
        "body": " · ".join(parts) if parts else "오늘의 브리핑이 준비되었습니다.",
        "url": f"/d/{briefing.brief_date}",
        "date": briefing.brief_date,
    }
    encoded = json.dumps(data, ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        # 본문 축약 폴백(안전)
        data["body"] = f"HIGH {briefing.high_count}건"
        encoded = json.dumps(data, ensure_ascii=False)
    return encoded
