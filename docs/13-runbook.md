# 13 · 운영 런북 (Runbook)

> Morning Brief · 운영 절차 · 작성일 2026-11-11 · 라이브: https://yejinzz.github.io/morning-brief/

실제 배포·운영 중 자주 하는 작업과 장애 대응을 정리한다. 설계 배경은 `07-infrastructure.md`, `08-risks.md`, `12-deployment-plan.md`.

---

## 1. 매일 정상 흐름

1. GitHub Actions `daily-brief.yml`가 cron(`7 22 * * *` UTC = KST 07:07)으로 배치 실행.
2. 실 RSS 수집 → (Mock 또는 Gemini) 분석 → 선정 → Supabase 저장 → ready면 Web Push 발송.
3. 폰/웹에서 당일 브리핑 조회. 알림 누르면 해당 날짜로 딥링크.

## 2. "오늘 브리핑이 안 보여요" (가장 흔한 상황)

**원인 1순위: 무료 cron 누락/지연** (GitHub 공식 한계, 설계상 수용).

**복구 — 수동 재실행:**
```bash
gh workflow run daily-brief.yml --ref main
# 또는 GitHub → Actions → Daily Brief → Run workflow
```
- 성공 로그: `[run_daily] db=supabase ... job=succeeded briefing=ready push={sent:N}`
- 멱등하므로 같은 날짜 재실행해도 안전(중복 브리핑/중복 푸시 없음).

**오늘 브리핑 존재 확인** (publishable 공개키로 조회, 읽기 전용):
```bash
curl -s "https://<project>.supabase.co/rest/v1/daily_briefings?select=brief_date,status,high_count&order=brief_date.desc&limit=3" \
  -H "apikey: <publishable>" -H "Authorization: Bearer <publishable>"
```

## 3. AI를 실제 Gemini로 전환

기본은 Mock 분석(요약이 "…(모의)"). 실제 요약을 원하면:
1. 레포 Settings → Secrets and variables → **Variables** → `MB_AI` = `gemini` 추가.
2. `GEMINI_API_KEY` Secret이 등록돼 있어야 함(무료 키, 결제 비활성).
3. 배치 재실행. 무료 한도 소진 시 자동 중단(유료 전환 없음) — 그날은 분석 실패 격리/empty로 처리.

## 4. 푸시 운영

- **구독**: 사용자가 설정 → "알림 받기" → publishable 키로 `push_subscriptions`에 저장(plain INSERT, 중복이면 PATCH). iOS는 홈 화면 설치 필수.
- **발송**: 배치가 secret 키로 활성 구독을 읽어 발송. 날짜·기기별 중복 방지(`notification_deliveries`).
- **만료/무효 정리**: 410/404 또는 잘못된 키 구독은 자동으로 `active=false` 처리(gone). 별도 작업 불필요.
- **구독 확인/정리**: Supabase → Table Editor → `push_subscriptions`. 실제 구독은 `endpoint`가 `https://web.push.apple.com/...`(iOS)/FCM/mozilla, 키가 긺.

## 5. 장애 대응

| 증상 | 원인 | 대응 |
|---|---|---|
| 예약 실행 누락 | 무료 cron 지연 | 수동 재실행(§2) |
| `job=skipped` | 크래시로 남은 running job | 5분 지나면 `try_start` 자가 복구(stale). 그 전이면 잠시 후 재실행 |
| `job=failed` + ai_quota | Gemini 무료 한도 소진 | 당일 중단, 마지막 정상 브리핑 유지. 다음날 자동 재개 |
| 특정 소스 수집 0 | 소스 장애/봇 차단 | Google News 폴백이 커버. 지속 시 `registry.py` 소스 점검 |
| 푸시 `failed:N` | 일시적 전송 실패 | 다음 실행 재시도. 영구 무효면 자동 gone 처리 |
| 조회 404/`PGRST` | SUPABASE_URL에 경로 포함 | 코드가 scheme+host로 정규화함(이미 처리). 시크릿을 `https://x.supabase.co`로 정리 가능 |
| Supabase 일시 중지 | 7일 무활동 | 일일 배치가 방지. 중지 시 대시보드 Resume(복구 90일 내) |

## 6. 모니터링 (주기적)

- **배치 결과**: GitHub Actions → Daily Brief 실행 로그, `collection_jobs` 테이블.
- **무료 한도**: Supabase 사용량(DB<500MB, egress<5GB), Gemini 대시보드(사용 시), Actions 사용량(public 무료).
- **스케줄 활성**: 60일 무활동 시 예약 워크플로 자동 비활성 → 월 1회+ 커밋/활동 유지.
- **무료 정책 재검토**: 분기별 각 서비스 공식 조건 확인(`07-infrastructure.md` 출처 표).

## 7. 데이터 보관 (자동)

배치 말미에 `cleanup_retention`이 best-effort로 정리(실패해도 배치는 성공):
- 브리핑 180일 / 실행 로그 90일 / 발송 이력 90일 / 기사 180일.
- 비선정 기사의 조기(30일) 정리는 DB 용량 증가 시 DB 함수로 강화 가능(현재 180일 바운드로 충분).

## 8. 비밀키 (GitHub Actions Secrets)

| 이름 | 용도 |
|---|---|
| `SUPABASE_URL` | 공용 |
| `SUPABASE_SECRET_KEY` (`sb_secret_…`) | 배치 쓰기(RLS 우회) |
| `SUPABASE_PUBLISHABLE_KEY` (`sb_publishable_…`) | 클라이언트 빌드(읽기) |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_SUBJECT` | Web Push |
| `GEMINI_API_KEY` (선택) | 실 AI 분석 |

> 상세 보안 정책: `docs/SECRETS.md`. 배포 산출물(dist)에 secret/VAPID 개인키가 없어야 함(배포 워크플로 전제).

## 9. 정시성 개선 (선택, 향후)

무료 cron의 정시 누락이 잦으면: ① cron 분(分)을 바꿔 고부하 시간대 회피, ② 외부 무료 핑어(cron-job.org 등)로 `workflow_dispatch` 트리거, ③ Cloudflare Workers Cron으로 트리거 분리. 모두 0원 유지 범위에서 가능.
