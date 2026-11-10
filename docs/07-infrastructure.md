# 07 · 인프라 · 무료 운영 (Infrastructure)

> Morning Brief · 설계 문서 7/8 · 작성일 2026-11-10 · 상태: 초안(승인 대기)
> 모든 무료 조건은 2026-11-10 공식 문서 기준. **무료 플랜 정책 변경으로 영구 0원은 보장 불가** — 위험은 §5 및 `08-risks.md`.

---

## 1. 배포 토폴로지

| 구성 | 서비스 | 배포 방식 |
|---|---|---|
| PWA(정적) | Cloudflare Pages | GitHub 연동 자동 빌드·배포, `*.pages.dev` HTTPS |
| 배치 | GitHub Actions(Public) | `.github/workflows/daily-brief.yml` cron + workflow_dispatch |
| DB·Auth | Supabase Free | 대시보드 프로젝트, 마이그레이션 적용 |
| AI | Gemini API | 파이프라인에서 HTTPS 호출 |
| 푸시 | Web Push/VAPID | 파이프라인에서 서명 POST |

---

## 2. 스케줄링 (KST 07:00 목표)

- cron: `7 22 * * *` (UTC 22:07 = KST 07:07). KST는 DST 없어 변환 단순.
- 정각(`0 22`) 회피 → GitHub 고부하 시간대 지연·드롭 완화.
- `workflow_dispatch`(입력: 대상 날짜)로 수동 재실행.
- **정확한 07:00 보장 불가**: GitHub 공식이 schedule 지연·누락 명시(NFR-3 수용). "대략 07시대" 목표.
- **60일 무활동 시 스케줄 자동 비활성화** → 월 1회 이상 커밋/활동 또는 봇 커밋으로 유지. 운영 체크리스트에 포함.
- `runs-on: ubuntu-latest`(표준 러너) **고정** — larger runner는 public에서도 과금.

---

## 3. 비밀키 관리

| 비밀 | 저장 | 노출 범위 |
|---|---|---|
| Supabase service_role | Actions Secret | 서버 전용(쓰기) |
| Supabase anon | 빌드 환경변수(공개 가능) | 클라이언트(읽기, RLS 전제) |
| Supabase URL | 공개 | 클라이언트 |
| Gemini API 키 | Actions Secret | 서버 전용 |
| VAPID 개인키 | Actions Secret | 서버 전용 |
| VAPID 공개키 | 빌드 환경변수 | 클라이언트(구독용) |

- **원칙**: service_role·AI·VAPID 개인키는 브라우저 번들·네트워크 응답에 절대 미포함. 빌드 산출물에 포함되는 건 anon·VAPID 공개키·URL뿐.
- Actions Secret은 무료·암호화·로그 자동 마스킹(48KB 한도).
- `.env.example`에 키 이름만(값 없음). 실제 `.env`는 gitignore.

---

## 4. 무료 운영 검증표 (필수 — 설계 요청서 §6)

| 구성 요소 | 후보 서비스 | 공식 무료 한도·조건 | 예상 일/월 사용량 | 초과 시 동작 | 결제수단 필수 | 과금 위험 | 무료 대안 |
|---|---|---|---|---|---|---|---|
| 정적 호스팅 | Cloudflare Pages | 정적자산 무제한, 빌드 500/월, 무료 HTTPS·서브도메인 | 배포 수십회/월, 트래픽 1인 미미 | Functions만 Error 1027 차단, 정적은 무제한 | ❌ 불필요 | **매우 낮음**(Free/Paid 분리) | GitHub Pages |
| DB·Auth | Supabase Free | DB 500MB, egress 5GB/월, 50k MAU, RLS, 활성 2프로젝트 | DB<수십MB, egress<1GB, MAU 1 | 차단/제한(과금 없음) | ❌ 불필요 | **매우 낮음** | Neon(Auth 없음) |
| AI | Gemini Flash-Lite 무료 | ~1,000 RPD/~15 RPM/250k TPM | ~100 req/일, ~15k TPM | 429 중단(폴백 없음) | ❌ 불필요 | **낮음**(결제 미연결 시) | Groq Free |
| 예약 실행 | GitHub Actions(Public) | 표준 러너 무료·무제한 | 1~수회/일, 수 분 | 차단(과금 아님) | ❌ 불필요 | **매우 낮음**(표준러너 한정) | Cloudflare Workers Cron |
| 푸시 | Web Push + VAPID | 메시지당 $0 | 1~수건/일 | - | ❌ 불필요 | **없음** | - |
| 도메인·HTTPS | *.pages.dev | 무료 서브도메인+TLS | - | - | ❌ 불필요 | **없음** | *.github.io |

**통과 판정**: 6개 구성 모두 ✅ — 유료 호출·자동 결제·유료 체험 크레딧 의존 없음. 결제 수단 미등록 시 한도 초과해도 **차단/중단**(자동 과금 없음).

### 예상 월 사용량 요약
- Gemini: ~100건/일 × 30 ≈ 3,000 req/월(무료 ~30,000 RPD 상당 여유).
- Supabase DB: 메타만 저장·주기 정리 → 수십 MB(한도 500MB).
- Actions: 일 1회 × 수 분 → public 무료·무제한.
- Pages 빌드: 코드 변경 시만 → 월 수십 회(한도 500).

---

## 5. 무료 운영 위험 (요약, 상세 `08-risks.md`)

| 위험 | 영향 | 대응 |
|---|---|---|
| 무료 플랜 정책 변경 | 한도 축소·유료화 | 어댑터로 교체 용이, 주기 재검토, 영구 0원 보장 불가 명시 |
| GitHub cron 지연·누락 | 그날 지연/누락 | 수동 재실행, Workers Cron 트리거 대안 |
| 60일 무활동 스케줄 비활성 | 배치 중단 | 월 1회+ 활동/봇 커밋 |
| Supabase 7일 중지 | 조회·배치 중단 | 일일 DB 쓰기로 방지, 실패일 상태 핑, 복구 90일 내 재개 |
| Gemini 무료 한도 하향 | 분석량 제한 | 사전 필터·묶음 분석·건수 축소, Groq 대체 |
| larger runner 오용 | public 과금 | `ubuntu-latest` 고정 |
| 무료 AI 학습 사용 | 프라이버시 | 공개 뉴스 메타만 전송, 민감정보 금지 |

---

## 6. 운영 (로그·복구·보관)

- **로그**: `collection_jobs.stage_counts`/`error` + Actions 실행 로그(90일 보관). 단계별 건수로 장애 지점 파악.
- **수동 재실행**: workflow_dispatch로 특정 날짜 재생성(멱등).
- **데이터 보관**: 브리핑 90~180일, 비선정 기사 14~30일, 이력 90일(`05-database.md` §6).
- **백업**: Supabase Free 자동 백업 없음 → 중요 데이터 적고 재생성 가능하므로 수용. 필요 시 주기적 export(선택).
- **무료 정책 재검토**: 분기별 각 서비스 무료 조건·확인일 갱신(이 문서의 출처 표 갱신).

---

## 7. 확인 필요 항목 (운영 전 재검증)

- Supabase 중지 후 복구 가능 기간(90일 vs 1년 상충) — 대시보드 확인.
- Gemini 무료 RPM/RPD/TPM 실제 수치 — AI Studio 대시보드(변동 잦음).
- Cloudflare 대역폭 "무제한" 정확 조건 — ToS.
- data.go.kr 정책뉴스 API 일일 한도, FSC RSS 가용성.
- Cloudflare Pages 비활성 프로젝트 중단 정책(문서 미확인).

---

*다음 문서: `08-risks.md`*
