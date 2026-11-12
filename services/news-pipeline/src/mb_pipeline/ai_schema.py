"""AI 영향도 분석 응답 JSON Schema (M0).

Gemini ``responseSchema`` 로 강제하고, 수신 응답을 ``jsonschema`` 로 재검증한다.
설계 근거: docs/04-news-pipeline.md §6.3

환각 방지 규칙:
- 모델은 제공된 제목/요약/링크 범위 밖 사실을 생성하지 않는다.
- 제목·설명만으로 분석했으면 ``evidence_basis = "title_desc_only"``.
- 검증 불가/출처 충돌은 ``status = "held" | "conflict"``.
모델명·버전·분석 시각은 모델이 아니라 서버가 기록한다(스키마에 없음).
"""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

# Gemini responseSchema 겸 수신 검증 스키마
AI_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "article_ref": {
                        "type": "string",
                        "description": "입력 기사 식별자(배치 내 참조)",
                    },
                    "impact": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "summary": {
                        "type": "string",
                        "description": "3~4문장(약 3~4줄) 독자적 요약(원문 복붙 금지)",
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "핵심 용어·인물·수치 3~5개(명사 위주, 짧게)",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "영향도 판단 근거 1~2문장",
                    },
                    "dev_relevance": {
                        "type": "string",
                        "description": "개발 실무 관련성(없으면 '해당 없음')",
                    },
                    "evidence_basis": {
                        "type": "string",
                        "enum": ["full", "title_desc_only"],
                    },
                    "status": {
                        "type": "string",
                        "enum": ["analyzed", "held", "conflict"],
                    },
                },
                "required": [
                    "article_ref",
                    "impact",
                    "summary",
                    "rationale",
                    "evidence_basis",
                    "status",
                ],
            },
        }
    },
    "required": ["results"],
}

_validator = Draft202012Validator(AI_RESPONSE_SCHEMA)


def validate_ai_response(payload: Any) -> list[str]:
    """스키마 위반 메시지 목록을 반환한다. 빈 리스트면 유효."""
    return [
        f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
        for e in sorted(_validator.iter_errors(payload), key=lambda e: list(e.path))
    ]


def is_valid_ai_response(payload: Any) -> bool:
    return bool(_validator.is_valid(payload))
