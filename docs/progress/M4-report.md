# M4 완료 보고 — 예약 실행 및 Web Push

> 작성일 2026-11-10 · 브랜치 `dev`

## 1. 구현 범위·산출 파일

| 영역 | 산출물 |
|---|---|
| 예약 워크플로 | `.github/workflows/daily-brief.yml` — cron `7 22 * * *`(KST 07:07 목표) + `workflow_dispatch`(날짜 입력), `ubuntu-latest` 고정, Secret→env 매핑 |
| 배치 CLI | `run_daily_cli.py` — MB_MODE=mock(실 RSS + Mock AI + Mock 푸시, 키·비용 0) / live(M5 완성 예정) |
| 일일 오케스트레이션 | `pipeline/run_daily.py` — 동시실행 방지 → 수집 → 생성 → 저장 → (ready면)푸시. 한도 소진 중단, empty_high 미발송 |
| KST 유틸 | `pipeline/kst.py` — UTC→Asia/Seoul 날짜(멱등 키). `tzdata` 의존 추가(크로스 플랫폼) |
| 푸시 계층 | `push/base.py`(PushSender·만료 예외), `push/payload.py`(≤4KB), `push/mock.py`, `push/webpush.py`(pywebpush, 선택 의존성 `.[push]`, CI 미실행) |
| 발송 오케스트레이션 | `push/send.py` — 날짜·기기 중복 방지, 410/404 만료 정리, 실패 격리·재시도 |
| 저장소 | `push/stores.py`(구독·이력), `pipeline/stores.py`(브리핑·Job) — Protocol+인메모리, Supabase 구현은 M5 |
| 클라이언트 구독 | `apps/web/src/lib/push.ts` — VAPID 공개키 변환 + `pushManager.subscribe` (서버 저장은 M5) + 설정 연동 |

## 2. 테스트 결과 (실제 실행)

| 대상 | 결과 |
|---|---|
| Python ruff / mypy(strict) / pytest | ✅ / ✅ / ✅ **54 passed** |
| Web tsc / eslint / prettier / vitest / build | ✅ / ✅ / ✅ / ✅ **10 passed** / ✅ |
| **run_daily_cli(mock, 실 RSS)** | ✅ `job=succeeded briefing=ready push sent:1` — 실 수집→Mock분석→Mock푸시 end-to-end |

**커버 시나리오** (test-plan N·O·D 대응):
- 페이로드: 제목·본문(카테고리별 HIGH)·딥링크·4KB 이내.
- KST: 자정 넘는 UTC→KST 날짜.
- 발송: 다건 발송, **중복 방지(멱등)**, **만료(410) 구독 정리**, **실패 격리**.
- 배치: **ready→발송**, **empty_high→미발송(D-1)**, **한도 소진→중단·미저장·미발송**, **동시 실행 skip**, **동일 날짜 재실행 멱등(재발송 없음)**.

## 3. 무료 운영 게이트 체크

- ✅ 워크플로 `ubuntu-latest`만(larger runner 과금 방지), public 무료.
- ✅ CLI mock 모드는 **키·비용 0**(실 RSS 수집 + Mock AI/푸시). 스케줄 기본값 mock → 조용한 실패/과금 없음.
- ✅ Web Push 표준 발송은 메시지당 $0. `pywebpush` 는 선택 의존성(운영만).
- ✅ 비밀키는 Secret→env, 브라우저 미노출(클라이언트는 VAPID **공개키**만).
- ⚠ 무료 cron 은 **정확한 07:00 보장 불가**(지연·누락) — 워크플로 주석·문서에 명시.

## 4. 메모 / 다음 단계 확인

- **실 운영(live) 미완결**: `run_daily_cli` live 모드와 실제 Supabase 저장/조회, 실 Web Push 발송은 **Supabase 클라이언트 구현(M5)**과 사용자 키 준비 후 완성.
- **사용자 작업 필요(M5)**: Supabase 무료 프로젝트 + 마이그레이션 적용 + VAPID 키쌍 + Cloudflare Pages + GitHub Secret 등록(모두 결제 비활성).
- **60일 무활동 스케줄 비활성 / Supabase 7일 중지** 대응은 M5 운영 체크리스트로.
- 상세: `docs/progress/M4-report.md`

## 5. 다음 단계

- **M5 — 배포·통합 검증·운영 안정화**: Supabase 저장/조회 어댑터(live 모드 완성), Cloudflare Pages 배포, Secret 점검, 통합/E2E, 모바일·오프라인·푸시 실수신, 운영·복구·README.
- 사용자 승인 + 계정 준비 후 M5 착수.
