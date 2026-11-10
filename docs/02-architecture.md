# 02 · 아키텍처 설계 (Architecture)

> Morning Brief · 설계 문서 2/8 · 작성일 2026-11-10 · 상태: 초안(승인 대기)

구성도·시퀀스·배치/PWA 역할·장애 흐름을 정의한다. 스택 확정 근거는 `03-tech-stack.md`, 무료 운영 검증은 `07-infrastructure.md`.

---

## 1. 시스템 구성도

```
                        ┌───────────────────────────────────────────┐
                        │              GitHub Actions                │
                        │        (예약 cron ~07:00 KST, Public)      │
                        │   ┌─────────────────────────────────────┐ │
   무료 RSS/API ───────────▶│  news-pipeline (Python)             │ │
   · Google News RSS     │  │  수집→정규화→중복제거→필터          │ │
   · 언론사/공공 RSS     │  │  →AI분석→선정→브리핑저장→푸시발송   │ │
   · HN/GitHub/AI 블로그 │  └──────┬───────────────┬──────────────┘ │
                        └─────────│───────────────│────────────────┘
                     service_role │(쓰기)         │ VAPID 서명 HTTPS POST
                                  ▼               ▼
                        ┌──────────────────┐   ┌──────────────────────┐
         AI 분석 ───────┤  Supabase        │   │  브라우저 푸시 서비스  │
     Gemini API(무료)   │  Postgres + Auth │   │  (FCM/Mozilla/Apple)  │
         (HTTPS)        │  + RLS           │   └──────────┬───────────┘
          ▲             └────────┬─────────┘              │ 푸시 전달
          │                      │ anon+세션(읽기 전용)    ▼
          │ 429 시 중단          │               ┌──────────────────────┐
          └──────────────────────│───────────────│   사용자 기기 (PWA)   │
                                 ▼               │  React+Vite+TS+Tailwind│
                        ┌──────────────────┐     │  서비스워커/오프라인캐시│
                        │ Cloudflare Pages │◀────│  홈화면 설치(iOS 필수) │
                        │ 정적 호스팅/HTTPS │ 앱로드└──────────────────────┘
                        └──────────────────┘
```

### 1.1 2계층 분리 (핵심 원칙)
- **서버 측 배치 (쓰기 경로)**: GitHub Actions에서 Python 파이프라인이 수집·분석·선정·저장·푸시. `service_role` 키·AI 키·VAPID 개인키는 **Actions Secret**에만 존재, 브라우저에 절대 노출 안 함.
- **클라이언트 조회 (읽기 경로)**: 정적 PWA는 Supabase `anon` 공개키 + 로그인 세션으로 **읽기만**. RLS가 노출 범위를 강제(HIGH만, 비노출 분석 차단).

---

## 2. 컴포넌트 역할

| 컴포넌트 | 역할 | 비밀키 접근 |
|---|---|---|
| GitHub Actions | 스케줄 트리거, 파이프라인 실행 환경, 수동 재실행 | Secret 보유(서버) |
| news-pipeline (Python) | 수집·정규화·중복제거·필터·AI호출·선정·저장·푸시 | service_role, AI, VAPID |
| Supabase (Postgres/Auth/RLS) | 영구 저장, 인증, 접근 제어 | - |
| Gemini API (무료) | 영향도 분류·요약·근거 JSON | 파이프라인만 호출 |
| 브라우저 푸시 서비스 | 표준 Web Push 전달 | - |
| Cloudflare Pages | 정적 PWA 호스팅, HTTPS | - |
| PWA (React) | 브리핑 조회, 설정, 푸시 구독, 오프라인 | anon(공개), 세션 |

---

## 3. 메인 시퀀스 (해피 패스)

```
GitHub Actions cron (~22:00 UTC = ~07:00 KST, 지연 가능)
  │
  ├─ 1. 동시실행 방지: collection_jobs(brief_date) running upsert
  │       └─ 충돌 → 이미 실행 중, 종료
  ├─ 2. 수집: 카테고리별 무료 RSS/API 호출 (24h→부족시 72h)
  │       └─ 소스 실패 → 해당 소스 skip, fallback(Google News) 사용
  ├─ 3. 정규화: URL canonical화, 발행시각 파싱, 카테고리 태깅
  ├─ 4. 중복 제거: canonical_url, 제목 유사도, dedup_group, 이전 브리핑 대조
  ├─ 5. 사전 필터: 관련성·출처 신뢰도·저품질 제거 (AI 호출 전 비용 절감)
  ├─ 6. AI 분석: 카테고리 단위 묶음 호출 → HIGH/MEDIUM/LOW+요약+근거 JSON
  │       ├─ 429(한도 소진) → 분석 중단, 상태 기록, 마지막 정상 브리핑 유지 (성공 알림 금지)
  │       ├─ JSON 검증 실패 → 제한 재시도 → 실패 격리(status=failed)
  │       └─ 일일 요청/토큰 상한 체크
  ├─ 7. 선정: 카테고리별 ≤3, 전체 ≤15, HIGH만 노출용. 분석 후 선정.
  ├─ 8. 브리핑 저장: daily_briefings(headline, counts, read_min, status=ready) + briefing_articles
  │       └─ HIGH 0건 → status=empty_high
  └─ 9. 푸시 발송: status=ready(또는 정책상 empty_high)일 때만
          ├─ notification_deliveries(brief_date, sub) 중복 체크
          ├─ VAPID 서명 → 각 구독 엔드포인트 POST
          ├─ 410/404 → 구독 비활성화/삭제
          └─ 실패 → 제한 재시도, 이력 기록

사용자: 푸시 탭 → PWA /d/:date → Supabase 읽기(RLS) → 카드 렌더 → 원문 링크
```

---

## 4. 장애 흐름 (실패 분기)

| 단계 | 실패 | 대응 | 사용자 영향 |
|---|---|---|---|
| 스케줄 | cron 지연/누락 | 무료 플랫폼 한계 수용. 다음날 정상. 수동 재실행 가능 | 그날 지연/누락, 마지막 브리핑 유지 |
| 수집 | 특정 소스 장애 | 소스 skip + Google News fallback | 영향 최소 |
| 수집 | 전 소스 24h 부족 | 72h로 확대 | 약간 오래된 기사 포함 |
| AI | JSON 오류 | 제한 재시도 → 개별 격리(failed) | 해당 기사만 누락 |
| AI | 무료 한도 소진(429) | **분석 중단, 자동 과금 없음, 마지막 정상 브리핑 유지** | 그날 신규 브리핑 없음 |
| 저장 | DB 중지/장애 | 재시도. Supabase 7일 무활동 중지는 일일 배치가 방지 | 일시 조회 불가 |
| 완료 판정 | 부분 성공 | 완료 기준 충족 시 ready(일부 미완료 표시), 미충족 시 failed | 투명 표시 |
| 푸시 | 발송 실패 | 브리핑 저장과 분리, 제한 재시도 | 알림만 누락, 브리핑은 조회 가능 |
| 전체 | 배치 실패 | **성공 알림 금지**, 마지막 정상 브리핑 노출 | 과거 브리핑 열람 |

**완료 기준(Definition of Done, 배치)**: `daily_briefings.status='ready'` 또는 `'empty_high'`로 전이 + `generated_at` 기록. 이 상태에서만 푸시·기본 노출.

---

## 5. 멱등성·재실행

- 멱등 키: `brief_date`(KST date). 동일 날짜 재실행은 분석 재사용 + 선정/헤더 upsert + 푸시 중복 방지(이력 기반).
- 수동 재실행: `workflow_dispatch`(입력: 대상 날짜). 동시 실행은 running 부분 unique로 차단.
- 로그: `collection_jobs.stage_counts`에 단계별 건수, `error`에 실패 요약.

---

## 6. 시간대 처리 (KST ↔ UTC)

- GitHub Actions cron은 UTC 기준(IANA 타임존 지정도 가능하나 지연·DST 영향 동일). KST=UTC+9, **DST 없음**.
- 07:00 KST = 22:00 UTC(전날). 고부하 정각 회피 위해 **22:0X(예: 22:07) 권장** → 약 07:07 KST 목표.
- "브리핑 날짜"는 항상 `Asia/Seoul` 기준 `date`로 계산(배치가 UTC로 돌아도 KST 날짜로 저장).
- **정확한 07:00 보장 불가**(GitHub 공식: 지연·드롭 가능). NFR-3로 수용, 사용자에게 명시.

---

## 7. 보안 경계

- **비밀 경계**: service_role / AI 키 / VAPID 개인키 = 서버(Actions Secret) 전용. 빌드 산출물·네트워크 응답에 미포함.
- **공개 경계**: anon 키, VAPID 공개키만 클라이언트.
- **접근 제어**: RLS로 인증 사용자 읽기, 비노출 분석·실행 로그 차단. 공개 회원가입 비활성화.
- 자세한 위협 모델은 `08-risks.md`.

---

## 8. 대안·축소안 (무료 운영 어려울 때)

| 어려움 | 축소/대체안 |
|---|---|
| GitHub Actions 정시성 부족 | Cloudflare Workers Cron으로 트리거만 분리(실작업은 서버리스/Actions) |
| Supabase 중지 리스크 | Neon(자동 휴면·복귀, 단 Auth 없음) 또는 핑 전략 유지 |
| AI 무료 한도 빡빡 | 분석 건수 축소, 사전 필터 강화, 카테고리 묶음 분석, Groq 대체 |
| 푸시 운영 부담 | 핵심 유지(표준 Web Push는 $0). HIGH 0건 미발송으로 발송량 절감 |

---

*다음 문서: `03-tech-stack.md`*
