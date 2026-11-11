# Morning Brief

> 매일 아침, AI가 선별한 국내외 시사·개발·AI 뉴스를 5분 안에. **월 운영비 0원 목표**의 개인용 모바일 PWA.

**라이브:** https://yejinzz.github.io/morning-brief/ · 매일 07:00 KST(목표) 자동 생성 + Web Push 알림

---

## 무엇을 하나

매일 새벽 클라우드 배치가 **무료 뉴스 소스**를 수집하고, **AI로 영향도를 분석**해 카테고리별로 중요한 소식만 골라 그날의 브리핑을 만듭니다. 생성이 끝나면 폰으로 **Web Push 알림**을 보냅니다. 앱을 열면 "오늘의 한 줄 브리핑"과 HIGH 등급 뉴스 카드(최대 15건)를 빠르게 읽을 수 있습니다.

- **카테고리**: 국내 시사 / 경제·국제 / AI·LLM / 개발·인프라 / 기타 테크
- **선정**: 분석 후 카테고리별 최대 3건, 전체 최대 15건, HIGH만 노출 (억지로 채우지 않음)
- **저작권**: 원문 전문 미저장 — 제목·메타데이터·짧은 자체 요약·원문 링크만

## 아키텍처 (2계층 분리)

```
GitHub Actions (cron ~07:00 KST)                 GitHub Pages (정적 PWA)
   └ Python 파이프라인                               └ React + Vite + TS + Tailwind
      수집→정규화→중복제거→사전필터                     - anon(publishable) 읽기, RLS
      →AI분석→선정→저장→Web Push                        - 오프라인 앱셸, 설치형 PWA
          │ secret key(쓰기)                              ▲ publishable key(읽기)
          ▼                                               │
                         Supabase (Postgres + RLS)  ──────┘
```

- **서버(쓰기)**: 배치가 `secret key`로 Supabase에 저장. 비밀키는 GitHub Actions Secret 전용(브라우저 미노출).
- **클라이언트(읽기)**: PWA가 `publishable key`로 **`ready` 브리핑만** RLS로 조회. 로그인 없음(공개 뉴스).
- **AI**: 교체 가능한 어댑터. 기본 Mock, `MB_AI=gemini`로 무료 Gemini Flash-Lite 전환.

자세한 설계: [`docs/01-requirements.md`](docs/01-requirements.md) ~ [`docs/08-risks.md`](docs/08-risks.md) · 구현 계획: [`docs/09`](docs/09-implementation-plan.md)~[`12`](docs/12-deployment-plan.md) · 진행 기록: [`docs/progress/`](docs/progress)

## 기술 스택 (모두 무료 티어, 결제수단 등록 없음)

| 레이어 | 사용 | 비고 |
|---|---|---|
| 프론트 | React · Vite · TypeScript · Tailwind · vite-plugin-pwa | GitHub Pages 배포 |
| 파이프라인 | Python (feedparser · pywebpush) | GitHub Actions 실행 |
| DB·인증 | Supabase Free (Postgres + RLS) | 신규 API 키(publishable/secret) |
| AI | Google Gemini Flash-Lite 무료 (교체 가능) | 기본은 Mock |
| 스케줄 | GitHub Actions cron | 정시 보장 X(아래 한계) |
| 푸시 | 표준 Web Push + VAPID | 메시지당 $0 |

## 저장소 구조

```
apps/web/                 # React PWA (읽기 전용 조회)
services/news-pipeline/   # Python 배치 (수집·분석·선정·저장·푸시)
  src/mb_pipeline/        # sources/ pipeline/ ai/ push/ supabase/
  migrations/             # 0001 스키마, 0002 RLS
.github/workflows/        # ci.yml, deploy-pages.yml, daily-brief.yml
docs/                     # 설계·구현·운영 문서
```

## 로컬 개발

```bash
# 파이프라인 (Python 3.12)
cd services/news-pipeline
python -m venv .venv && .venv/Scripts/activate   # win: .venv\Scripts\activate
pip install -e ".[dev]"
ruff check . && mypy && pytest -q                # 린트·타입·테스트
python -m mb_pipeline.run                         # Mock 드라이런(M1+M2 전체 흐름)
python -m mb_pipeline.smoke ai dev                # 실 RSS 수동 스모크

# 웹 (Node 24, pnpm)
cd apps/web
pnpm install
pnpm run typecheck && pnpm run lint && pnpm run test && pnpm run build
pnpm run dev                                      # 로컬 서버(환경변수 없으면 Mock 데이터)
```

## 배포 · 운영

- **배포**: `dev`에서 작업 → `main`으로 fast-forward 병합 → `deploy-pages.yml`가 자동 배포.
- **배치 수동 실행**: `gh workflow run daily-brief.yml --ref main` (예약 누락 시 복구용).
- **비밀키**: 레포 Settings → Secrets에 `SUPABASE_URL`·`SUPABASE_SECRET_KEY`·`SUPABASE_PUBLISHABLE_KEY`·`VAPID_PUBLIC_KEY`·`VAPID_PRIVATE_KEY`·`VAPID_SUBJECT`·(선택)`GEMINI_API_KEY`.
- 운영 상세: [`docs/13-runbook.md`](docs/13-runbook.md)

## 알려진 한계 (무료 플랫폼 제약 — 설계상 수용)

- ⚠️ **정확한 07:00 실행을 보장하지 않습니다.** GitHub 무료 cron은 지연·누락이 발생합니다. 누락 시 위 "배치 수동 실행"으로 복구하세요.
- ⚠️ **영구 0원을 보장하지 않습니다.** 무료 플랜 정책 변경 가능성이 있습니다(2026-11 기준 검증 통과).
- Supabase 무료 프로젝트는 7일 무활동 시 일시 중지되나, 일일 배치가 이를 방지합니다.
- iOS는 **홈 화면에 설치한 PWA**에서만 푸시를 받을 수 있습니다(iOS 16.4+).

## 라이선스 / 성격

개인용 프로젝트입니다. 뉴스 원문의 저작권은 각 출처에 있으며, 본 서비스는 제목·링크·짧은 자체 요약만 보관하고 원문으로 링크합니다.
