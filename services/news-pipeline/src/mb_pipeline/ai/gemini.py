"""Gemini 무료 티어 어댑터 (M2).

무료 Flash-Lite 모델 + responseSchema(JSON 강제). 결제 계정을 연결하지 않으면 한도 초과 시
429 로 중단되고 자동 과금되지 않는다(docs/03 §2.3). 네트워크·키가 필요하므로 CI 미실행.

Gemini responseSchema 는 OpenAPI 서브셋이라 additionalProperties 를 지원하지 않는다.
→ 응답은 수신 후 ``ai_schema`` (jsonschema) 로 다시 엄격 검증한다.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from mb_pipeline.ai.base import (
    AIError,
    AIQuotaError,
    AIResponseError,
    AIResult,
    AIResultItem,
    AnalysisInput,
    DedupGroup,
    DedupInput,
)
from mb_pipeline.ai.prompt import (
    DEDUP_INSTRUCTION,
    INSTRUCTION,
    build_contents,
    build_dedup_contents,
    estimate_tokens,
)
from mb_pipeline.ai_schema import validate_ai_response
from mb_pipeline.contracts import Category

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Gemini responseSchema(OpenAPI 서브셋, additionalProperties 미지원)
_GEMINI_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "results": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "article_ref": {"type": "STRING"},
                    "impact": {"type": "STRING", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "summary": {"type": "STRING"},
                    "keywords": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "rationale": {"type": "STRING"},
                    "dev_relevance": {"type": "STRING"},
                    "evidence_basis": {"type": "STRING", "enum": ["full", "title_desc_only"]},
                    "status": {"type": "STRING", "enum": ["analyzed", "held", "conflict"]},
                },
                "required": [
                    "article_ref", "impact", "summary", "keywords",
                    "rationale", "evidence_basis", "status",
                ],
            },
        }
    },
    "required": ["results"],
}

# 교차언어 중복 판별용 responseSchema
_GEMINI_DEDUP_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "groups": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "representative_ref": {"type": "STRING"},
                    "duplicate_refs": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["representative_ref", "duplicate_refs"],
            },
        }
    },
    "required": ["groups"],
}


class GeminiAdapter:
    def __init__(
        self, api_key: str, *, model: str = "gemini-2.5-flash-lite", timeout: float = 60.0
    ):
        if not api_key:
            raise AIError("GEMINI_API_KEY 가 비어 있음")
        self._key = api_key
        self.model = model
        self._timeout = timeout

    # 일시적 서버 오류 → 백오프 재시도
    _TRANSIENT = (500, 502, 503, 504)
    _MAX_RETRY = 3

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        url = _ENDPOINT.format(model=self.model)
        data = json.dumps(body).encode("utf-8")
        last: Exception | None = None
        for attempt in range(self._MAX_RETRY):
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "x-goog-api-key": self._key},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                    parsed: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
                    return parsed
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    raise AIQuotaError("Gemini 무료 한도 초과(429)") from exc
                if exc.code == 404:
                    avail = self._list_models()  # 모델명 불일치 → 진단
                    raise AIError(
                        f"Gemini 404 model='{self.model}'. generateContent 가능: {avail}"
                    ) from exc
                if exc.code in self._TRANSIENT:
                    last = exc
                    time.sleep(2 * (attempt + 1))
                    continue
                raise AIError(f"Gemini HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last = exc
                time.sleep(2 * (attempt + 1))
                continue
        raise AIError(f"Gemini 재시도 후 실패: {last}")

    def _list_models(self) -> list[str]:
        """generateContent 를 지원하는 모델 id 목록(진단용)."""
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        req = urllib.request.Request(url, headers={"x-goog-api-key": self._key})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            return ["(목록 조회 실패)"]
        out: list[str] = []
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                out.append(str(m.get("name", "")).removeprefix("models/"))
        return out

    def analyze(self, category: Category, items: list[AnalysisInput]) -> AIResult:
        body = {
            "systemInstruction": {"parts": [{"text": INSTRUCTION}]},
            "contents": [{"role": "user", "parts": [{"text": build_contents(category, items)}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _GEMINI_SCHEMA,
                "temperature": 0.2,
            },
        }
        resp = self._post(body)
        try:
            text = resp["candidates"][0]["content"]["parts"][0]["text"]
            payload = json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise AIResponseError(f"Gemini 응답 파싱 실패: {exc}") from exc

        errors = validate_ai_response(payload)
        if errors:
            raise AIResponseError(f"스키마 위반: {errors[:3]}")

        items_out = [
            AIResultItem(
                ref=r["article_ref"],
                impact=r["impact"],
                summary=r["summary"],
                keywords=[str(k) for k in r.get("keywords", [])],
                rationale=r["rationale"],
                dev_relevance=r.get("dev_relevance", "해당 없음"),
                evidence_basis=r["evidence_basis"],
                status=r["status"],
            )
            for r in payload["results"]
        ]
        usage = resp.get("usageMetadata", {})
        tokens = int(usage.get("totalTokenCount", estimate_tokens(items)))
        return AIResult(items=items_out, model=self.model, tokens=tokens)

    def dedup_high(self, items: list[DedupInput]) -> list[DedupGroup]:
        if len(items) < 2:
            return []
        body = {
            "systemInstruction": {"parts": [{"text": DEDUP_INSTRUCTION}]},
            "contents": [{"role": "user", "parts": [{"text": build_dedup_contents(items)}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _GEMINI_DEDUP_SCHEMA,
                "temperature": 0.0,
            },
        }
        resp = self._post(body)
        try:
            text = resp["candidates"][0]["content"]["parts"][0]["text"]
            payload = json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise AIResponseError(f"Gemini dedup 응답 파싱 실패: {exc}") from exc

        valid_refs = {it.ref for it in items}
        groups: list[DedupGroup] = []
        for g in payload.get("groups", []):
            rep = g.get("representative_ref")
            dups = [str(r) for r in g.get("duplicate_refs", []) if r in valid_refs and r != rep]
            if rep in valid_refs and dups:
                groups.append(DedupGroup(representative_ref=rep, duplicate_refs=dups))
        return groups
