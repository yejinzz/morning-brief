# M5 완료 보고 — 배포·연동·운영 (라이브)

> 작성일 2026-11-11 · 브랜치 `main`(배포)/`dev`(작업) · **라이브 동작 확인 완료**
> 사이트: https://yejinzz.github.io/morning-brief/

M5를 검증 가능한 단계로 나눠 진행, **전 구간 라이브 동작을 실제로 확인**했다.

## 확정된 결정 (M5)
- 호스팅 Cloudflare Pages → **GitHub Pages**(관리 통일, SPA 404 폴백).
- Supabase 키 레거시 anon/service_role → **publishable/secret**(신규).
- **D-3 변경: 로그인 없음** — anon이 `ready` 브리핑만 RLS로 읽기, 쓰기는 secret key.
- AI는 **Mock**으로 검증(사용자 선택). `MB_AI=gemini`로 전환 가능.

## 단계별 결과
| 단계 | 내용 | 상태 |
|---|---|---|
| M5-1 | GitHub Pages 배포(서브경로·404 SPA·deploy 워크플로) | ✅ 라이브 |
| M5-2 | Supabase 연동(배치 쓰기 secret / PWA 읽기 anon·RLS) + 신규 키 네이밍 | ✅ |
| M5-3 | 실 배포 → 실 Supabase 쓰기/읽기 → **실 Web Push 수신(iOS)** → E2E | ✅ 확인 |
| M5-4 | 데이터 보관 정리, 잘못된 구독 자동 정리, README·런북, 설계문서 네이밍 | ✅ |

## 라이브 검증 (실제 확인됨)
- 배치(수동 dispatch) `db=supabase ai=Mock push=WebPush` → `job=succeeded briefing=ready push sent:1`.
- 실 RSS 100건 수집 → 선정 5건(HIGH) → Supabase 저장 → **anon 임베디드 조회**로 PWA 카드 렌더(웹/폰).
- **iOS 설치형 PWA에서 실제 푸시 알림 수신 확인.** 멱등(재실행 중복 푸시 없음), 날짜별 중복 방지 동작.
- 잘못된 키 구독 → `gone` 자동 비활성화. stuck job → 자가 복구.

## 라이브 디버깅으로 해결한 이슈
1. `SUPABASE_URL` 시크릿에 `/rest/v1/` 꼬리 → client(py)·web(ts) URL을 scheme+host로 **정규화**.
2. anon에 SELECT 정책 없어 `ON CONFLICT` upsert가 RLS로 차단 → 구독 저장을 **plain INSERT + 409 PATCH**로.
3. 잘못된 키 구독이 pywebpush에서 예외 → **예외 격리**(배치 중단 방지) + ValueError는 **gone 처리**.
4. 크래시로 남은 `running` job → **try/finally 마감 + stale(5분) 자가 복구**.

## 검증 (코드)
| 대상 | 결과 |
|---|---|
| Python ruff/mypy/pytest | ✅ **60 passed** |
| Web tsc/eslint/prettier/vitest/build | ✅ **12 passed** |
| CI(main/dev) · Deploy Pages | ✅ green |

## 무료 운영 게이트
✅ 호스팅·DB·Actions·푸시 전부 무료 · ✅ secret은 Actions Secret(dist 미노출) · ✅ AI 기본 Mock(비용0), 실 Gemini도 429 중단 · ✅ 표준 러너.

## 알려진 한계 (수용)
- **정확한 07:00 보장 불가** — 실제로 당일 예약 실행이 누락되어 **수동 재실행으로 복구**함(런북 §2). 무료 cron 한계.
- **영구 0원 보장 불가**(정책 변경 위험, 현재 검증 통과).

## 남은(선택) 작업
- 실 Gemini 분석 전환(`MB_AI=gemini`) — 요약 품질 향상 원할 때.
- 정시성 개선(외부 핑어/Workers Cron) — 예약 누락이 잦으면(런북 §9).
- 비선정 기사 30일 조기 정리(DB 함수) — 용량 증가 시.

## 운영 문서
- [`README.md`](../../README.md) · [`docs/13-runbook.md`](../13-runbook.md) · 설계문서 02/03/05/07/12에 M5 구현 반영 배너.

**결론: Morning Brief MVP 라이브 운영 상태. 핵심 요구(기기 독립 클라우드 배치·조회·푸시·0원·안전 중단) 충족.**
