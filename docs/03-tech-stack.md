# 03 · 기술 스택 (Tech Stack)

> Morning Brief · 설계 문서 3/8 · 작성일 2026-11-10 · 상태: 초안(승인 대기)
>
> ⚠️ **M5 구현 반영**: 호스팅 Cloudflare Pages→**GitHub Pages**, Supabase 키 anon/service_role→**publishable/secret**, 인증 D-3 '최소 로그인'→**'로그인 없음(anon이 ready만 읽기)'**. 실제 구성·운영은 [`README`](../README.md)·[`13-runbook`](13-runbook.md) 참조.
> 무료 조건은 2026-11-10 공식 문서 기준 검증. 무료 플랜 정책은 변동될 수 있으므로 **영구 0원 보장 불가**(위험은 `08-risks.md`).

---

## 1. 최종 추천 스택 (요약)

| 레이어 | 추천 | 핵심 이유 | 무료 검증 |
|---|---|---|---|
| 프론트엔드 | **React + Vite + TypeScript + Tailwind + vite-plugin-pwa** | 설계 요청 스택, PWA 성숙, 모바일 경량 | 빌드 도구(무료) |
| 정적 호스팅 | **Cloudflare Pages** | 정적 자산 무제한·무료 HTTPS·자동과금 없음 | ✅ |
| 뉴스 파이프라인 | **Python** (feedparser, httpx) | RSS/HTTP 생태계, Actions 실행 | 런타임(무료) |
| AI | **Google Gemini API — Flash-Lite 무료 티어** (교체 가능 어댑터) | JSON Schema 지원, 하루 100건 충분, 카드 불필요 | ✅ |
| DB·인증 | **Supabase Free (Postgres + Auth + RLS)** | DB+Auth 일체, RLS, 카드 불필요 | ✅ |
| 예약 실행 | **GitHub Actions (Public repo)** | 표준 러너 무료·무제한, Secret 관리 | ✅ |
| 푸시 | **표준 Web Push + VAPID** | 메시지당 $0, 추가 인프라 불필요 | ✅ |

> 이 스택은 설계 요청서 §3 후보와 일치하며, 6개 무료 티어를 모두 공식 문서로 검증했다. **모든 구성에서 결제 수단 등록이 불필요하고, 한도 초과 시 자동 과금 대신 차단/중단**된다.

---

## 2. 레이어별 비교·선정 근거

### 2.1 정적 호스팅: Cloudflare Pages vs GitHub Pages vs Netlify/Vercel
| 항목 | **Cloudflare Pages(추천)** | GitHub Pages | Netlify/Vercel |
|---|---|---|---|
| 정적 자산 | 요청·대역폭 무료·무제한 | ~100GB/월(소프트) | 100GB/월 |
| 빌드 | 500빌드/월, 동시 1 | 시간당 ~10회 | 300분/월(빌드) |
| 무료 HTTPS+서브도메인 | `*.pages.dev` | `*.github.io` | `*.netlify/vercel.app` |
| 카드 필요 | 불필요 | 불필요 | 불필요 |
| 자동 과금 | 없음(Free/Paid 분리) | 없음 | 초과 시 제한/업셀 |
- **선정**: Cloudflare Pages. 정적 자산 무제한 + 자동과금 구조 부재가 결정적. GitHub Pages는 백업 대안.

### 2.2 DB·인증: Supabase vs Neon vs SQLite-in-repo
| 항목 | **Supabase(추천)** | Neon | SQLite-in-repo |
|---|---|---|---|
| DB | Postgres 500MB | Postgres 0.5GB | 파일 |
| **내장 Auth** | ✅ 이메일/매직링크 | ❌ 별도 필요 | ❌ |
| RLS | ✅ | ✅(수동) | ❌ |
| 중지 리스크 | 7일 무활동 중지(배치가 방지), 복구 90일 | 스케일-투-제로(삭제 없음) | 없음 |
| 카드 필요 | 불필요 | 불필요 | - |
- **선정**: Supabase. **DB+Auth+RLS 일체 제공**이 단일 사용자 인증 요구(FR-21)에 최적. 중지 리스크는 일일 배치의 DB 쓰기로 방지(+실패일에도 상태 핑). Neon은 Auth 부재로 탈락하나 중지 걱정 없는 백업 후보.

### 2.3 AI: Gemini 무료 vs Groq vs 기타
| 항목 | **Gemini Flash-Lite(추천)** | Groq Free | OpenRouter :free |
|---|---|---|---|
| 무료 한도 | ~15 RPM / ~1,000 RPD / 250k TPM | ~30 RPM / ~1,000 RPD | 일일 호출 제한 |
| JSON Schema | ✅ responseSchema | JSON mode(모델별) | 모델별 |
| 하루 100건 | 충분(여유 10배) | 충분 | 가변 |
| 카드 필요 | 불필요 | 불필요 | 불필요 |
| 한도 초과 | 429 중단(과금 없음) | 429 | 제한 |
- **선정**: Gemini Flash-Lite. JSON Schema 강제 + 넉넉한 RPD. **교체 가능 어댑터**로 설계해 Groq 등으로 쉽게 전환(한도 축소·정책 변경 대비).
- ⚠ **무료 티어 데이터 정책**: 무료 입력/출력이 **Google 모델 개선에 사용**됨 → 민감 정보 입력 금지(공개 뉴스 메타만 전송하므로 수용 가능). `08-risks.md` 참조.
- ⚠ 무료 RPM/RPD 수치는 2026년 중 하향 변동 잦음 → 운영 전 AI Studio 대시보드 재확인(**확인 필요**).

### 2.4 예약 실행: GitHub Actions vs Cloudflare Workers Cron
- **선정**: GitHub Actions(Public). 표준 러너 무료·무제한, Secret 관리 내장, Python 파이프라인 실행에 적합.
- **한계**: 정확한 07:00 보장 불가(지연·드롭), 60일 무활동 시 스케줄 자동 비활성화 → 주기적 커밋/활동 필요. 정시성이 더 중요해지면 Workers Cron으로 트리거 분리 가능.

### 2.5 프론트엔드
- React + Vite + TS + Tailwind + `vite-plugin-pwa`(매니페스트·서비스워커 생성). 상태관리는 경량 유지(요청서 §7: 불필요한 상태관리 라이브러리 금지) — React Query 정도 또는 기본 훅.

---

## 3. 무료 조건 검증 근거 (공식 출처·확인일 2026-11-10)

### Cloudflare Pages
- 정적 자산 요청·대역폭 무료, 빌드 500/월, `*.pages.dev`+무료 TLS, 카드 불필요, Free/Paid 분리로 자동 과금 없음(초과 시 Functions만 Error 1027 차단).
- 출처: developers.cloudflare.com/pages/platform/limits/ , /pages/functions/pricing/ , /workers/platform/pricing/
- 확인 필요: 대역폭 "무제한" 정확 수치 단일 문장 인용.

### Supabase Free
- DB 500MB, 활성 프로젝트 2, 이메일/매직링크 Auth, 50k MAU, RLS 포함, egress 5GB/월, **카드 불필요, 무료 플랜 과금 경로 없음**. 7일 무활동 중지, 복구 90일.
- 출처: supabase.com/pricing , /docs/guides/platform/free-project-pausing , /docs/guides/platform/spend-cap , /docs/guides/database/postgres/row-level-security
- 확인 필요: 복구 기간 90일(changelog) vs 1년(docs) 상충 → 대시보드 재확인.

### Gemini API Free
- Flash/Flash-Lite 무료 티어, Flash-Lite ~1,000 RPD, 카드 불필요, 429 중단(자동 과금 없음), responseSchema JSON 지원. 무료 데이터는 학습 사용.
- 출처: aistudio.google.com/docs/pricing , /docs/rate-limits , /docs/logs-policy , /docs/structured-output
- 확인 필요: 정확한 RPM/RPD/TPM(동적 페이지, 변동 잦음).

### GitHub Actions (Public)
- 표준 러너 public 무료·무제한, 카드 미등록 시 차단(과금 아님), cron 지연·드롭 가능, Asia/Seoul 타임존 지정 가능(단 정시 보장 X), 60일 무활동 시 스케줄 비활성화, Secret 무료·마스킹.
- 출처: docs.github.com/en/billing/concepts/product-billing/github-actions , /actions/reference/workflows-and-actions/events-that-trigger-workflows , /actions/reference/limits , /actions/reference/security/secrets
- ⚠ larger runner는 public에서도 과금 → `runs-on: ubuntu-latest` 고정 필수.

### Web Push + VAPID
- 메시지당 과금 없음($0), P-256 ECDSA 키(개인키 서버 전용), iOS 16.4+ 홈화면 설치 필수, HTTPS 필수, 410/404로 만료 감지, 페이로드 4KB, CI 잡에서 발송 가능.
- 출처: web.dev/articles/push-notifications-web-push-protocol , /sending-messages-with-web-push-libraries , webkit.org/blog/13878/ , developer.mozilla.org Push API
- 확인 필요: FCM 엔드포인트 "무료" 명문 조항(업계 표준이나 1차 선언 문장 미확정).

> 전체 무료 운영 검증표(예상 사용량·초과 동작 포함)는 `07-infrastructure.md` §무료 운영 검증.

---

## 4. 저장소 구조 (제안 — M0에서 확정)

```
morning-brief/
├── apps/
│   └── web/                 # React+Vite+TS+Tailwind PWA
├── services/
│   └── news-pipeline/       # Python 수집·분석·선정·푸시
│       ├── sources/         # 소스 어댑터(RSS/API)
│       ├── pipeline/        # 정규화·중복제거·필터·선정
│       ├── ai/              # AI 어댑터(교체 가능)
│       ├── push/            # Web Push 발송
│       └── migrations/      # DB 스키마
├── .github/workflows/       # 예약 cron + 수동 재실행
├── docs/                    # 설계·구현 문서
└── .env.example
```

---

## 5. 의존성 최소주의 (요청서 §7)

- 과도한 추상화·마이크로서비스·불필요한 상태관리 라이브러리 금지.
- AI는 단일 모델 + 얇은 어댑터(교체 대비)만. 멀티 프로바이더 오케스트레이션 금지(MVP).
- 파이프라인은 단일 Python 프로세스(순차 단계). 큐·워커 인프라 불필요.

---

## 6. 사용자 준비(계정) 체크리스트 — 구현 전 사용자 작업

> 아래는 **사용자가 직접** 무료 계정을 만들고 키를 발급해야 하는 항목(코드로 대체 불가). 결제 수단 등록 없이 진행.

| 서비스 | 필요 작업 | 비밀 보관 위치 |
|---|---|---|
| Supabase | 무료 프로젝트 생성, URL/anon/service_role 키 | Actions Secret(서버), anon만 클라이언트 |
| Google AI Studio | 무료 API 키 발급(결제 비활성) | Actions Secret |
| VAPID | 키쌍 생성(`web-push generate-vapid-keys`) | 개인키 Secret, 공개키 클라이언트 |
| Cloudflare | Pages 프로젝트(GitHub 연동) | - |
| GitHub | 이미 생성됨(public), Secret 등록 | Actions Secret |

---

*다음 문서: `04-news-pipeline.md`*
