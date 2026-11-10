"""AI 응답 스키마 검증 테스트 (M0).

정상 JSON / 깨진 JSON / enum 경계 / 환각 방지 플래그를 커버한다. (test-plan A-1, A-2)
"""

from __future__ import annotations

import copy

from mb_pipeline.ai_schema import is_valid_ai_response, validate_ai_response
from mb_pipeline.mock import loader


def test_valid_response_passes() -> None:
    payload = loader.load_ai_response()
    assert validate_ai_response(payload) == []
    assert is_valid_ai_response(payload)


def test_missing_required_field_fails() -> None:
    payload = copy.deepcopy(loader.load_ai_response())
    del payload["results"][0]["impact"]  # required
    errors = validate_ai_response(payload)
    assert errors
    assert not is_valid_ai_response(payload)


def test_invalid_impact_enum_fails() -> None:
    payload = copy.deepcopy(loader.load_ai_response())
    payload["results"][0]["impact"] = "CRITICAL"  # not in enum
    assert not is_valid_ai_response(payload)


def test_unknown_property_rejected() -> None:
    payload = copy.deepcopy(loader.load_ai_response())
    payload["results"][0]["hallucinated_field"] = "x"
    assert not is_valid_ai_response(payload)


def test_not_an_object_fails() -> None:
    assert not is_valid_ai_response("not json object")
    assert not is_valid_ai_response({"results": "should be array"})


def test_evidence_basis_flag_present() -> None:
    payload = loader.load_ai_response()
    # 제목·설명만으로 분석한 항목은 title_desc_only 로 표시되어 근거 한계를 드러낸다.
    bases = {r["evidence_basis"] for r in payload["results"]}
    assert bases <= {"full", "title_desc_only"}
    assert "title_desc_only" in bases
