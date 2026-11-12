"""중복 제거 (M1). docs/04-news-pipeline.md §4.

1차: canonical_url 완전 일치 제거.
2차: 제목 유사도(토큰 자카드) → 동일 사건 dedup_group, 대표 1건 유지.
     카테고리 무관(같은 사건이 여러 피드의 다른 카테고리로 들어오므로 교차 비교).
3차: 이전 브리핑에 선정된 canonical_url 과 대조 → 재노출 제거.

주의: 토큰 자카드는 같은 언어 내 중복에만 유효하다(엔비디아↔Nvidia 교차언어는 못 잡음).
교차언어 중복은 분석 후 LLM 단계(pipeline/dedup_llm.py)에서 추가로 제거한다.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from mb_pipeline.contracts import Article

_WORD_RE = re.compile(r"[0-9a-z가-힣]+")
# 유사도 비교에서 무시할 흔한 토큰(노이즈)
_STOPWORDS = {"속보", "종합", "단독", "the", "a", "an", "to", "of", "and", "뉴스"}


def normalize_title(title: str) -> str:
    text = unicodedata.normalize("NFKC", title).lower()
    return " ".join(_WORD_RE.findall(text))


def title_tokens(title: str) -> set[str]:
    return {t for t in normalize_title(title).split() if t not in _STOPWORDS}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass
class DedupResult:
    kept: list[Article]
    dropped_duplicate: list[Article] = field(default_factory=list)
    dropped_prior: list[Article] = field(default_factory=list)


def _representative_sort_key(a: Article) -> tuple[int, float]:
    # 발행 시각이 있는 것을 우선, 더 이른 것을 대표로(최초 보도).
    if a.published_at is None:
        return (1, 0.0)
    return (0, a.published_at.timestamp())


def deduplicate(
    articles: list[Article],
    *,
    prior_urls: set[str] | None = None,
    sim_threshold: float = 0.55,
) -> DedupResult:
    prior_urls = prior_urls or set()
    result = DedupResult(kept=[])

    # 3차: 이전 브리핑 중복 선제거
    survivors: list[Article] = []
    for a in articles:
        if a.canonical_url in prior_urls:
            result.dropped_prior.append(a)
        else:
            survivors.append(a)

    # 1차: canonical_url 완전 일치 제거(최초 등장 유지)
    seen_urls: set[str] = set()
    unique: list[Article] = []
    for a in survivors:
        if a.canonical_url in seen_urls:
            result.dropped_duplicate.append(a)
            continue
        seen_urls.add(a.canonical_url)
        unique.append(a)

    # 2차: 제목 유사도 클러스터(카테고리 무관 — 같은 사건이 여러 피드로 들어옴)
    groups: list[list[Article]] = []
    token_cache: dict[str, set[str]] = {}
    for a in unique:
        toks = title_tokens(a.title)
        token_cache[a.id] = toks
        placed = False
        for group in groups:
            rep = group[0]
            if jaccard(token_cache[rep.id], toks) >= sim_threshold:
                group.append(a)
                placed = True
                break
        if not placed:
            groups.append([a])

    for idx, group in enumerate(groups):
        if len(group) == 1:
            result.kept.append(group[0])
            continue
        group.sort(key=_representative_sort_key)
        rep = group[0]
        gid = f"grp-{idx}-{rep.id[:8]}"
        rep_tagged = rep.model_copy(update={"dedup_group": gid})
        result.kept.append(rep_tagged)
        result.dropped_duplicate.extend(group[1:])

    return result
