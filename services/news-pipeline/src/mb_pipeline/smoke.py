"""실 RSS 수동 스모크 (M1). CI 에서 실행하지 않는다(네트워크 사용).

실행:
    python -m mb_pipeline.smoke            # 전 카테고리
    python -m mb_pipeline.smoke ai dev     # 특정 카테고리
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from mb_pipeline.contracts import Category
from mb_pipeline.pipeline.collect import collect
from mb_pipeline.sources.base import http_fetcher
from mb_pipeline.sources.registry import sources_for


def main(argv: list[str]) -> int:
    cats = [Category(c) for c in argv] if argv else list(Category)
    now = datetime.now(UTC)
    for cat in cats:
        res = collect(sources_for(cat), fetcher=http_fetcher, now=now)
        print(f"[{cat.value}] {res.stage_counts}")
        for a in res.candidates[:3]:
            when = a.published_at.isoformat() if a.published_at else "?"
            print(f"   - ({when}) {a.title[:60]} · {a.source}")
        if res.failures:
            for f in res.failures:
                print(f"   ! 실패: {f.source}: {f.error[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
