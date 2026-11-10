"""Mock fixture 로더 (M0).

``tests/fixtures`` 의 JSON 을 읽어 계약 모델로 역직렬화한다.
외부 네트워크/AI/DB 없이 파이프라인 골격과 PWA 조회 계약을 검증하는 데 쓴다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mb_pipeline.contracts import Briefing, RawArticle

_FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


def _load(name: str) -> Any:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def load_raw_articles() -> list[RawArticle]:
    return [RawArticle.model_validate(a) for a in _load("raw_articles.json")]


def load_ai_response() -> dict[str, Any]:
    data: dict[str, Any] = _load("ai_response.json")
    return data


def load_briefing() -> Briefing:
    return Briefing.model_validate(_load("briefing.json"))
