"""AI 일일 상한 추적 (M2). docs/04 §6.1, 설계 요청서 §4.2.

요청 수·토큰 수·실패 횟수에 일일 상한. 초과 시 AIQuotaError 로 **중단**(유료 폴백 없음).
"""

from __future__ import annotations

from dataclasses import dataclass

from mb_pipeline.ai.base import AIQuotaError


@dataclass(frozen=True)
class DailyLimits:
    max_requests: int = 300
    max_tokens: int = 500_000
    max_failures: int = 20


class UsageTracker:
    def __init__(self, limits: DailyLimits | None = None) -> None:
        self.limits = limits or DailyLimits()
        self.requests = 0
        self.tokens = 0
        self.failures = 0

    def before_request(self, *, estimated_tokens: int = 0) -> None:
        """요청 직전 상한 확인. 초과면 AIQuotaError."""
        if self.requests + 1 > self.limits.max_requests:
            raise AIQuotaError(f"일일 요청 상한 초과: {self.limits.max_requests}")
        if self.tokens + estimated_tokens > self.limits.max_tokens:
            raise AIQuotaError(f"일일 토큰 상한 초과: {self.limits.max_tokens}")
        self.requests += 1

    def add_tokens(self, n: int) -> None:
        self.tokens += n

    def add_failure(self) -> None:
        self.failures += 1
        if self.failures > self.limits.max_failures:
            raise AIQuotaError(f"일일 실패 상한 초과: {self.limits.max_failures}")

    def snapshot(self) -> dict[str, int]:
        return {"requests": self.requests, "tokens": self.tokens, "failures": self.failures}
