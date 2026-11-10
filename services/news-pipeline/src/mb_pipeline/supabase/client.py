"""PostgREST 클라이언트 (M5). Supabase REST API를 urllib 로 호출(의존성 최소).

secret key 로 인증(RLS 우회). HTTP 전송은 주입식(Transport)이라 테스트는 네트워크 없이
호출 내용을 검증한다. 라이브 검증은 배포 시 실제 Supabase 로 수행한다.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# (method, url, headers, body) -> (status_code, response_text)
Transport = Callable[[str, str, dict[str, str], bytes | None], tuple[int, str]]


class SupabaseError(Exception):
    pass


class ConflictError(SupabaseError):
    """409 (고유 제약 충돌). 예: 동일 날짜 running job."""


def urllib_transport(
    method: str, url: str, headers: dict[str, str], body: bytes | None
) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SupabaseError(f"요청 실패: {exc}") from exc


@dataclass
class PostgrestClient:
    url: str  # https://xxx.supabase.co
    secret_key: str
    transport: Transport = urllib_transport

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {
            "apikey": self.secret_key,
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def _origin(self) -> str:
        # URL 에 경로(/rest/v1 등)·슬래시·공백이 섞여도 scheme+host 만 사용(PGRST125 방지).
        p = urllib.parse.urlsplit(self.url.strip())
        if p.scheme and p.netloc:
            return f"{p.scheme}://{p.netloc}"
        return self.url.strip().rstrip("/")

    def _rest(self, table: str, query: str = "") -> str:
        base = f"{self._origin()}/rest/v1/{table}"
        return f"{base}?{query}" if query else base

    def insert(self, table: str, rows: list[dict[str, Any]]) -> None:
        body = json.dumps(rows).encode("utf-8")
        status, text = self.transport("POST", self._rest(table), self._headers(), body)
        if status == 409:
            raise ConflictError(text)
        if status >= 300:
            raise SupabaseError(f"insert {table} 실패 {status}: {text}")

    def upsert(self, table: str, rows: list[dict[str, Any]], *, on_conflict: str) -> None:
        if not rows:
            return
        query = urllib.parse.urlencode({"on_conflict": on_conflict})
        headers = self._headers({"Prefer": "resolution=merge-duplicates"})
        body = json.dumps(rows).encode("utf-8")
        status, text = self.transport("POST", self._rest(table, query), headers, body)
        if status >= 300:
            raise SupabaseError(f"upsert {table} 실패 {status}: {text}")

    def update(self, table: str, *, filters: dict[str, str], patch: dict[str, Any]) -> None:
        query = urllib.parse.urlencode(filters)
        body = json.dumps(patch).encode("utf-8")
        status, text = self.transport("PATCH", self._rest(table, query), self._headers(), body)
        if status >= 300:
            raise SupabaseError(f"update {table} 실패 {status}: {text}")

    def delete(self, table: str, *, filters: dict[str, str]) -> None:
        query = urllib.parse.urlencode(filters)
        status, text = self.transport("DELETE", self._rest(table, query), self._headers(), None)
        if status >= 300:
            raise SupabaseError(f"delete {table} 실패 {status}: {text}")

    def select(self, table: str, *, query: str) -> list[dict[str, Any]]:
        status, text = self.transport("GET", self._rest(table, query), self._headers(), None)
        if status >= 300:
            raise SupabaseError(f"select {table} 실패 {status}: {text}")
        data: list[dict[str, Any]] = json.loads(text) if text else []
        return data
