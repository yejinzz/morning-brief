# M5 진행 보고 — 배포·연동·운영 (진행 중)

> 작성일 2026-11-10 · 브랜치 `dev` · **배포 미실행(사용자 요청)**, 라이브 검증은 배포 시

M5는 외부 계정·배포가 필요해 검증 가능한 단계로 분할. **M5-1·M5-2 코드 완료**(로컬/Mock 검증), 실 배포·라이브 E2E는 보류.

## 확정된 결정 (M5)
- **호스팅**: Cloudflare Pages → **GitHub Pages**(관리 통일). SPA는 404.html 폴백.
- **Supabase 키**: 레거시 anon/service_role → **publishable/secret**(신규). 환경변수·문서 반영.
- **D-3 변경**: 최소 로그인 → **로그인 없음**(anon이 `ready` 브리핑만 RLS로 읽기, 쓰기는 secret key만).
- **AI**: 배포 검증은 **Mock 분석**부터(사용자 선택). `MB_AI=gemini`로 전환 가능.

## M5-1 — GitHub Pages 배포 (코드 완료, 미배포)
- `deploy-pages.yml`(main 전용 트리거) + Vite `base`(/morning-brief/) + 라우터 basename + SPA 404 폴백.
- 로컬 빌드 검증: 서브경로 asset 경로·manifest scope 정상.
- 배포는 `dev→main` fast-forward 병합 후 가능(보류 중).

## M5-2 — Supabase 연동 (코드 완료, 라이브 검증 대기)
| 영역 | 산출물 |
|---|---|
| RLS 개정 | `0002_rls.sql` — anon이 `ready/empty_high`만 읽기, push_subscriptions 자가 등록, 그 외 차단 |
| PostgREST 클라이언트 | `supabase/client.py` — secret key, urllib, transport 주입식(테스트 가능) |
| 배치 저장소(live) | `supabase/stores.py` — Briefing/Job/Subscription/Delivery (멱등 upsert·running 충돌·만료 정리) |
| 배치 자동 구성 | `run_daily_cli.py` — Supabase/VAPID/Gemini 있으면 live, 없으면 인메모리/Mock |
| PWA 읽기(anon) | `briefingsRepoSupabase.ts` — PostgREST 임베디드 조회 → Briefing 매핑, 환경 구성 시 자동 선택 |
| 네이밍 정리 | `.env.example`·`SECRETS.md`·`vite-env.d.ts`·`daily-brief.yml` 신규 키 기준 |
| 멱등 보강 | analysis id를 결정적 UUID로(저장 upsert 안전) |

## 검증 (실제 실행)
| 대상 | 결과 |
|---|---|
| Python ruff/mypy/pytest | ✅ **58 passed** |
| Web tsc/eslint/prettier/vitest/build | ✅ **12 passed** + build |
| CLI 스모크(memory/mock) | ✅ `job=succeeded briefing=ready push sent:1` |
| dist 비밀 스캔 | ✅ clean |

> ⚠ **라이브 미검증**: 실제 Supabase 쓰기/읽기·실 푸시·GitHub Pages 배포는 배포 환경에서만 검증 가능. 로컬엔 키가 없어 contract/Mock 테스트로 로직만 검증했다. 배포 시 PostgREST 임베딩·upsert 충돌 등 세부 조정 가능성 있음.

## 무료 운영 게이트
✅ 호스팅·DB·Actions·푸시 전부 무료 · ✅ secret은 Actions Secret(빌드 미노출, dist clean) · ✅ AI 기본 Mock(비용0), live도 429 중단 · ✅ 표준 러너

## 남은 M5 작업
- **M5-3**: 실 배포(dev→main) → 라이브 Supabase 쓰기/읽기 검증 → 실 Web Push 수신(iOS 설치형) → E2E.
- **M5-4**: 운영·복구 문서, README, 설계문서 prose 갱신(Cloudflare→GitHub Pages·키 네이밍), 데이터 보관 잡.

## 현재 `dev`
M5-1·M5-2 커밋 포함(CI green). 배포·라이브 검증은 사용자 준비/승인 후.
