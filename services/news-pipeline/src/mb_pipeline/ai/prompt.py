"""AI 프롬프트 구성 (M2). 분류 기준 + 환각 방지 지시. docs/04 §6.2."""

from __future__ import annotations

from mb_pipeline.ai.base import AnalysisInput, DedupInput
from mb_pipeline.contracts import CATEGORY_LABELS, Category

INSTRUCTION = """\
당신은 한국어 뉴스 영향도 분석가다. 각 기사를 HIGH/MEDIUM/LOW 로 분류한다.

분류 기준:
- HIGH: 광범위한 사회·경제 영향, 중대한 정책 변화, 중요한 AI 플랫폼 변화,
  심각한 보안 취약점, 개발 실무에 직접적인 변화를 주는 소식에 한정한다.
- MEDIUM: 주목할 만하나 즉각적·광범위 영향은 아님.
- LOW: 일반·부수적 소식.

규칙:
- **출력 언어는 항상 한국어다.** 입력 기사가 영어 등 외국어여도
  summary·rationale·dev_relevance 는 반드시 한국어 문장으로 쓴다.
  고유명사·브랜드·제품명·약어(Nvidia, WSJ, C++ 등)는 원문 표기를 허용하되 문장 자체는 한국어다.
  keywords 도 한국어 위주로 뽑되 고유명사는 원문 표기 가능.
- 제공된 제목·설명 범위 밖의 사실을 만들어내지 마라(환각 금지).
- 제목·설명만으로 판단했으면 evidence_basis="title_desc_only", 그 외 "full".
- 검증 불가/모호하면 status="held", 내용이 상충하면 "conflict", 정상 분석은 "analyzed".
- summary 는 3~4문장 독자적 요약. **구체적 사실 위주**로 써라:
  누가·무엇을·언제·수치(금액·비율·기한 등)·고유명사를 반드시 담아라.
  "중대한 영향을 미친다" 같은 **막연한 상투어·일반론은 금지**.
  제공된 정보에 수치가 없으면 지어내지 말고 사실만 쓴다.
- keywords 는 핵심 용어·인물·회사·수치 3~5개(짧은 명사구). 요약의 뼈대가 되는 단어를 뽑아라.
- rationale 은 영향도 판단 근거 1~2문장. dev_relevance 는 개발 실무 관련성(없으면 "해당 없음").
- HIGH 를 수량 때문에 억지로 만들지 마라. 없으면 없는 대로 둔다.
- article_ref 는 입력의 ref 를 그대로 사용한다. 모든 입력 기사에 대해 하나씩 결과를 낸다.
"""

DEDUP_INSTRUCTION = """\
당신은 뉴스 중복 판별기다. 아래 기사들 중 "같은 실제 사건·발표"를 다루는 것끼리 그룹으로 묶어라.

규칙:
- 언어가 달라도 같은 사건이면 같은 그룹이다(예: '엔비디아'=Nvidia, '젠슨 황'=Jensen Huang).
- 확실히 같은 사건일 때만 묶어라. 주제만 비슷하고 사건이 다르면 묶지 마라.
- 각 그룹에서 가장 포괄적이고 정보량 많은 기사 1건을 representative_ref 로 고르고,
  나머지 ref 를 duplicate_refs 에 넣어라.
- 중복이 없는 기사는 어떤 그룹에도 넣지 마라. groups 에는 2건 이상 묶인 그룹만 담는다.
- ref 는 입력의 ref 를 그대로 사용한다.
"""


def build_dedup_contents(items: list[DedupInput]) -> str:
    lines: list[str] = []
    for it in items:
        label = CATEGORY_LABELS[it.category]
        lines.append(f"- ref={it.ref} [{label}] ({it.source}) 제목: {it.title}")
    return "\n".join(lines)


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
