"""AI 프롬프트 구성 (M2). 분류 기준 + 환각 방지 지시. docs/04 §6.2."""

from __future__ import annotations

from mb_pipeline.ai.base import AnalysisInput
from mb_pipeline.contracts import CATEGORY_LABELS, Category

INSTRUCTION = """\
당신은 한국어 뉴스 영향도 분석가다. 각 기사를 HIGH/MEDIUM/LOW 로 분류한다.

분류 기준:
- HIGH: 광범위한 사회·경제 영향, 중대한 정책 변화, 중요한 AI 플랫폼 변화,
  심각한 보안 취약점, 개발 실무에 직접적인 변화를 주는 소식에 한정한다.
- MEDIUM: 주목할 만하나 즉각적·광범위 영향은 아님.
- LOW: 일반·부수적 소식.

규칙:
- 제공된 제목·설명 범위 밖의 사실을 만들어내지 마라(환각 금지).
- 제목·설명만으로 판단했으면 evidence_basis="title_desc_only", 그 외 "full".
- 검증 불가/모호하면 status="held", 내용이 상충하면 "conflict", 정상 분석은 "analyzed".
- summary 는 3문장 이내의 독자적 요약(원문 문장 복붙 금지).
- rationale 은 영향도 판단 근거 1~2문장. dev_relevance 는 개발 실무 관련성(없으면 "해당 없음").
- HIGH 를 수량 때문에 억지로 만들지 마라. 없으면 없는 대로 둔다.
- article_ref 는 입력의 ref 를 그대로 사용한다. 모든 입력 기사에 대해 하나씩 결과를 낸다.
"""


def build_contents(category: Category, items: list[AnalysisInput]) -> str:
    lines = [f"카테고리: {CATEGORY_LABELS[category]}", ""]
    for it in items:
        desc = (it.description or "").strip().replace("\n", " ")
        lines.append(f"- ref={it.ref}\n  제목: {it.title}\n  설명: {desc[:300]}")
    return "\n".join(lines)


def estimate_tokens(items: list[AnalysisInput]) -> int:
    """대략적 토큰 추정(문자/4 + 지시문 상수)."""
    chars = len(INSTRUCTION) + sum(len(i.title) + len(i.description or "") for i in items)
    return chars // 4 + 256
