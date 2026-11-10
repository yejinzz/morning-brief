# M3 완료 보고 — 모바일 PWA

> 작성일 2026-11-10 · 브랜치 `dev`

## 1. 구현 범위·산출 파일

| 영역 | 산출물 |
|---|---|
| 스타일 | Tailwind v3(PostCSS, 순수 JS) — `tailwind.config.js`, `postcss.config.js`, `src/index.css`(다크 모드) |
| 라우팅 | react-router-dom v7 — `/`(오늘), `/d/:date`(지난), `/settings` |
| 데이터 계층 | `lib/briefingsRepo.ts`(인터페이스+Mock, Supabase 구현 TODO), `lib/mockData.ts`, `lib/useBriefing.ts`(로딩/오류/온라인) |
| 컴포넌트 | `ArticleCard`(제목·요약·근거·출처·시각·원문·읽음), `CategoryTabs`(전체+5, 뱃지), `BriefingParts`(헤더·한줄·통계), `StateViews`(로딩/생성중/empty_high/카테고리0/오류/오프라인/없음) |
| 화면 | `routes/HomeRoute.tsx`, `routes/SettingsRoute.tsx`(테마·알림 권한·iOS 설치 안내) |
| 읽음 상태 | `lib/readState.ts` — **로컬(localStorage)**, 결정 D-2 |
| 테마 | `lib/theme.ts` — light/dark/system, html.dark 토글 |
| 탭 로직 | `lib/tabs.ts` — 순수 필터/카운트 |
| PWA | `vite.config.ts` VitePWA — 매니페스트, 서비스워커, 오프라인 앱셸(navigateFallback) |
| 테스트 | Vitest + RTL + jsdom |

## 2. 테스트 결과 (실제 실행)

| 대상 | 결과 |
|---|---|
| tsc(strict) / eslint / prettier | ✅ / ✅ / ✅ |
| **vitest** | ✅ **8 passed** (3 파일) |
| vite build (PWA) | ✅ `sw.js`+`manifest` 생성(precache 6) |
| 비밀 노출 스캔(dist) | ✅ clean |

**커버 시나리오** (test-plan P 대응):
- 탭 필터/카운트(P-1), 카드 렌더·**읽음 토글 핸들러**(P-2), 홈 렌더·**탭 전환 필터**·**empty_high**·없음 상태(P-4).

## 3. 무료 운영 게이트 체크

- ✅ 정적 PWA — Cloudflare Pages 정적 자산 무제한 대상, 서버 키 미포함(dist 스캔 clean).
- ✅ 외부 유료 호출 없음(현재 Mock 데이터). Tailwind v3 순수 JS로 네이티브 빌드 승인 추가 없음.
- ✅ 오프라인 앱셸 캐시 → 네트워크 없이도 마지막 화면 로드.

## 4. 메모 / 확인 필요

- **Supabase 실데이터 미연동**: `briefingsRepo` 는 Mock 구현. 실제 `anon`+세션 RLS 조회(`ready/empty_high`만)와 **인증(D-3 최소 로그인)**은 Supabase 프로젝트 생성 후 M4/M5에서 연결.
- **푸시 구독 미완결**: 설정의 "알림 받기"는 **권한 요청까지만**. `pushManager.subscribe`+VAPID+서버 구독 저장은 **M4**.
- 실브라우저 설치/오프라인/iOS 수신 검증은 배포 후 **M5 수동 테스트**(P-5·P-6·P-7). 현재는 빌드 산출물(manifest/sw) 유효성까지 확인.
- CI에 **web 테스트 단계 추가**(`pnpm run test`).

## 5. 다음 단계

- **M4 — 예약 실행 및 Web Push**: GitHub Actions cron(KST 07시대)+수동 재실행, 멱등/실패 기록, VAPID·구독·만료 정리·중복 방지, **성공 후에만 발송**, 딥링크, HIGH 0건 미발송(D-1). Supabase/VAPID 연동 시작.
- M4 전 사용자 작업: **Supabase 프로젝트 생성 + VAPID 키쌍 생성**(결제 비활성).
- 사용자 승인 후 M4 착수.
