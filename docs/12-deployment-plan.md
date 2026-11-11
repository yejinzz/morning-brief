# 12 · 배포 · 운영 · 복구 플랜 (Deployment)

> Morning Brief · 구현계획 4/4 · 작성일 2026-11-10 · 상태: 초안(승인 대기)
>
> ⚠️ **M5 구현 반영**: 호스팅 Cloudflare Pages→**GitHub Pages**, Supabase 키 anon/service_role→**publishable/secret**(`SUPABASE_SECRET_KEY`/`SUPABASE_PUBLISHABLE_KEY`), 인증 '로그인 없음'. 실제 배포·운영 절차는 [`README`](../README.md)·[`13-runbook`](13-runbook.md) 가 최신 기준.
> 무료 배포·환경 변수·스케줄러·푸시·운영·복구 절차. 전제: 모든 계정 **결제 수단 미등록**.

---

## 1. 배포 대상 요약

| 구성 | 플랫폼 | 트리거 | 산출 |
|---|---|---|---|
| PWA(정적) | Cloudflare Pages | `apps/web` 변경 push → 자동 빌드 | `*.pages.dev` HTTPS |
| 배치 | GitHub Actions | cron `7 22 * * *` + 수동 | 브리핑 생성·푸시 |
| DB·Auth | Supabase Free | 마이그레이션 적용(수동/CI) | Postgres+RLS |

---

## 2. 환경 변수 / 비밀 (Secret) 매핑

### 2.1 서버(배치) — GitHub Actions Secret (브라우저 미노출)
| 이름 | 용도 |
|---|---|
| `SUPABASE_URL` | 접속 URL |
| `SUPABASE_SERVICE_ROLE_KEY` | 쓰기(RLS 우회) |
| `GEMINI_API_KEY` | AI 분석 |
| `VAPID_PRIVATE_KEY` | 푸시 서명 |
| `VAPID_SUBJECT` | mailto: 연락처 |
| `DATA_GO_KR_KEY` | (선택) 정책뉴스 API |

### 2.2 클라이언트(PWA) — 빌드 환경변수 (공개 가능)
| 이름 | 용도 |
|---|---|
| `VITE_SUPABASE_URL` | 조회 |
| `VITE_SUPABASE_ANON_KEY` | 조회(RLS 전제) |
| `VITE_VAPID_PUBLIC_KEY` | 구독 |

- `.env.example`에 이름만. 실제 값은 Secret/Pages 환경변수에만.
- **검증(배포 전)**: 빌드 산출물에 `SERVICE_ROLE`·`GEMINI`·`VAPID_PRIVATE` 문자열 부재 확인(O-4).

---

## 3. 초기 배포 절차 (최초 1회)

1. **Supabase**(사용자): 무료 프로젝트 생성 → URL/anon/service_role 확보 → 마이그레이션 적용(`migrations/*.sql`) → RLS 정책 확인 → 공개 회원가입 비활성화, 단일 계정 생성(D-3).
2. **Gemini**(사용자): AI Studio 무료 키 발급(결제 비활성 확인).
3. **VAPID**(사용자): `npx web-push generate-vapid-keys` → 공개/개인 키.
4. **GitHub**: 위 Secret 등록(2.1). 워크플로 활성.
5. **Cloudflare Pages**(사용자): GitHub 연동, 빌드 명령/출력 디렉터리 설정, 클라이언트 환경변수(2.2) 입력 → `*.pages.dev` 발급.
6. **검증**: 수동 `workflow_dispatch` 1회 실행 → 브리핑 생성 → PWA 조회 → (설치형) 푸시 수신.

---

## 4. 스케줄러 운영

- cron `7 22 * * *`(UTC) = KST 07:07 목표. 정각 회피로 지연 완화.
- **정확 07:00 보장 불가**(GitHub 공식 지연·누락). 수용(NFR-3).
- 수동 재실행: Actions → Run workflow(날짜 입력) → 멱등 재생성.
- **60일 무활동 방지**: 월 1회 이상 커밋 또는 활동 유지 잡. 비활성 시 UI/커밋으로 재활성화.
- `runs-on: ubuntu-latest` 고정(larger runner 과금 차단).

---

## 5. 푸시 운영

- 발송: 브리핑 `ready`에서만(HIGH 0건=empty_high는 **미발송**, D-1).
- 구독 수명주기: 410/404 → 비활성화/삭제. `pushsubscriptionchange` → 재구독.
- 중복 방지: `notification_deliveries(brief_date, sub)` unique.
- iOS: 홈화면 설치형에서만 수신(16.4+) — 설치 안내 UX.
- 비용 $0(표준 Web Push).

---

## 6. 운영 모니터링

| 항목 | 방법 | 주기 |
|---|---|---|
| 배치 성공/실패 | Actions 로그 + `collection_jobs` | 매일 |
| 무료 한도 | Supabase 사용량, Gemini 대시보드, Actions 사용량 | 주/월 |
| 스케줄 지연·누락 | 실행 시각 관측, 누락 시 수동 재실행 | 수시 |
| DB 중지 여부 | Supabase 대시보드(7일 무활동) | 주 |
| 구독 상태 | `push_subscriptions.active`, 실패율 | 주 |
| 무료 정책 변경 | 각 서비스 공식 문서 재검토(08 §10) | 분기 |

---

## 7. 데이터 보관·정리

| 데이터 | 보관 | 정리 |
|---|---|---|
| 비선정 기사 | 14~30일 | cleanup 잡 |
| 브리핑/선정 | 90~180일 | 오래된 날짜 삭제 |
| 분석 | 기사와 함께(CASCADE) | |
| 실행/발송 이력 | 90일 | |

- 500MB 한도 여유 유지(원문 미저장+정리).

---

## 8. 백업·복구

- Supabase Free 자동 백업 없음 → 데이터는 **재생성 가능**(뉴스 메타·분석). 수용.
- 선택: 주기적 `pg_dump`/export로 브리핑만 백업.
- **중지 복구**: 7일 무활동 중지 시 대시보드 Resume(복구 가능 기간 90일 내). 일일 배치가 중지 방지.
- **장애 복구**: 배치 실패일은 수동 재실행. 부분 실패는 멱등 재실행으로 보완.

---

## 9. 롤백

- PWA: Cloudflare Pages 이전 배포로 롤백(배포 히스토리).
- 배치: 워크플로/코드 revert 후 재실행. DB 마이그레이션은 전진 전용 설계(파괴적 변경 지양, 필요 시 보상 마이그레이션).

---

## 10. 무료 정책 변경 대응 (Contingency)

| 변경 | 대응 |
|---|---|
| Gemini 무료 축소/종료 | AI 어댑터로 Groq 등 교체, 건수 축소 |
| Supabase 무료 축소 | Neon(+별도 Auth) 또는 데이터 정리 강화 |
| Cloudflare Pages 조건 변경 | GitHub Pages로 이전 |
| GitHub Actions public 정책 변경 | Workers Cron 트리거 전환 |
| 전반 유료화 압박 | 기능 축소(알림·분석 빈도↓), 0원 유지 우선 |

- 원칙: **어떤 경우에도 자동 과금 경로를 만들지 않는다.** 교체 비용 < 과금 수용.

---

## 11. 운영 문서(M5 산출)

- `README.md`: 개요·실행·배포.
- 운영 매뉴얼: 재실행·장애 대응·한도 모니터링·정책 재검토 절차.
- 배포 가이드: 계정 준비·Secret·Pages 설정 단계별.

---

*구현계획 문서 완결(09~12). 다음: 구현계획 승인 → M0 착수.*
