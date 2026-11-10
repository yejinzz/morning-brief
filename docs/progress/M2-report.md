# M2 완료 보고 — AI 분석 및 브리핑 생성

> 작성일 2026-11-10 · 브랜치 `dev`

## 1. 구현 범위·산출 파일

| 영역 | 산출물 |
|---|---|
| AI 어댑터 인터페이스 | `ai/base.py` — AIAdapter 프로토콜, AnalysisInput/AIResult, AIError/AIQuotaError/AIResponseError |
| 일일 상한 | `ai/limits.py` — 요청·토큰·실패 상한, 초과 시 AIQuotaError(중단) |
| Mock 어댑터 | `ai/mock.py` — 규칙 기반 결정적 분석 + 오류 경로(한도/깨진 응답) 재현 |
| **Gemini 어댑터** | `ai/gemini.py` — Flash-Lite + responseSchema, 429→AIQuotaError, 수신 후 jsonschema 재검증 (CI 미실행) |
| 프롬프트 | `ai/prompt.py` — 분류 기준 + 환각 방지 지시, 토큰 추정 |
| 사전 필터 | `pipeline/prefilter.py` — 저품질·광고·빈약 제목 제거(약한 필터) |
| 분석 오케스트레이션 | `pipeline/analyze.py` — 카테고리 묶음(D-4), 재시도 격리(failed), 한도 전파(중단), 미매칭 격리 |
| 선정 | `pipeline/select.py` — HIGH+analyzed만, 카테고리별 ≤3, 전체 ≤15, 최신 우선 |
| 브리핑 조립 | `pipeline/briefing.py` — HIGH 카드, 한 줄 브리핑, 예상 읽기 시간, ready/empty_high |
| 생성 통합 | `pipeline/generate.py` — 사전필터→분석→선정→브리핑 |
| 드라이런 | `run.py` — M1+M2 전체 흐름(Mock)으로 갱신 |

## 2. 테스트 결과 (실제 실행)

| 대상 | 결과 |
|---|---|
| ruff / mypy(strict) | ✅ / ✅ (28 files) |
| pytest | ✅ **43 passed** (M0·M1 12+19 + M2 12) |
| dry-run(M1+M2) | ✅ `collected=3 analyzed=3 selected_high=3 status=ready` + 한 줄 브리핑 생성 |

**커버 시나리오** (test-plan A·S 대응):
- AI: 정상 분석(묶음), **잘못된 응답→재시도→격리(failed)**, **무료 한도 소진(429)→중단(유료 폴백 없음)**, 요청 상한 초과→중단, 미매칭 ref→failed.
- 환각 방지: evidence_basis(title_desc_only) 플래그, 범위 제한 프롬프트, held/conflict 상태 지원.
- 선정: **HIGH만 노출**, **카테고리별 ≤3 / 전체 ≤15**, **분석 후 선정**(최신 고정 아님), MEDIUM/LOW·failed 제외.
- 브리핑: **HIGH 0건→empty_high(승격 없음)**, 한 줄 브리핑, 예상 읽기 시간, **동일 날짜 재실행 멱등**(결정적 analysis id).

## 3. 무료 운영 게이트 체크

- ✅ 기본 개발·테스트·CI는 **Mock 어댑터**(네트워크·키·비용 0).
- ✅ Gemini 어댑터는 **결제 미연결 무료 티어** 전제, 429 시 중단, **유료 폴백 코드 없음**.
- ✅ 일일 요청/토큰/실패 상한 내장 → 폭주·초과 방지.
- ✅ 원문 전문 미전송(제목+짧은 설명만) → 저작권·토큰·프라이버시 보호.

## 4. 메모 / 다음 단계 확인

- **실 Gemini 스모크 미수행**: 사용자 무료 API 키 발급 후 1회 검증 권장(PoC). 그전까지 Mock로 완전 동작.
- 한 줄 브리핑은 현재 **규칙 기반**(상위 HIGH 제목 조합). 추후 AI 생성 한 줄 요약으로 고도화 가능(선택).
- Supabase 영구 저장은 M3/M4에서 연동(현재 인메모리/계약 수준).

## 5. 다음 단계

- **M3 — 모바일 PWA**: 인증 조회, 전체+5개 탭, 카드(요약·근거·출처·링크), 상태 UI, 읽음(로컬), 테마·알림 설정 자리, PWA/오프라인.
- M3 전 사용자 작업: **Supabase 무료 프로젝트 생성**(결제 비활성) — 실 데이터 연동 시. 그전까지 Mock 데이터로 UI 구현.
- 사용자 승인 후 M3 착수.
