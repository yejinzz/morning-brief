# M0 완료 보고 — 프로젝트 기반 및 계약 확정

> 작성일 2026-11-10 · 브랜치 `dev` · 커밋 `03eb290` (+ `.gitattributes`)

## 1. 구현 범위·산출 파일

| 영역 | 산출물 |
|---|---|
| 저장소 구조 | 모노레포 `apps/web`, `services/news-pipeline`, `.github/workflows`, `docs` |
| 루트 도구 | `.gitignore`, `.gitattributes`, `.editorconfig`, `.nvmrc`(24), `.python-version`(3.12), `.env.example` |
| 비밀키 정책 | `docs/SECRETS.md` (서버/클라이언트 분류, 노출 방지 체크) |
| **공유 계약** | `services/.../contracts.py`(pydantic) ↔ `apps/web/src/types/contracts.ts` 미러 |
| **AI JSON Schema** | `services/.../ai_schema.py` + jsonschema 검증기(환각/근거 플래그) |
| DB 마이그레이션 | `migrations/0001_init.sql`(스키마·인덱스·멱등 제약), `0002_rls.sql`(RLS) |
| Mock/드라이런 | `mock/loader.py`, `tests/fixtures/*.json`, `run.py`(단계 순서 고정 골격) |
| 품질 도구 | ruff/mypy(strict)/pytest, eslint(flat)/prettier/tsc(strict), PWA 빌드 |
| CI | `.github/workflows/ci.yml` (python + web, `ubuntu-latest` 고정) |

## 2. 테스트 결과 (실제 실행 검증)

| 대상 | 결과 |
|---|---|
| Python `ruff check` | ✅ All checks passed |
| Python `mypy`(strict) | ✅ no issues (6 files) |
| Python `pytest` | ✅ **11 passed** (계약 round-trip, 선정 한도, AI 스키마 정상/누락/enum/미지정 필드/비객체/근거 플래그) |
| Python dry-run | ✅ `collected=3 high=2 status=ready read=4min articles=2` |
| Web `tsc --noEmit`(strict) | ✅ OK |
| Web `eslint` | ✅ OK |
| Web `prettier --check` | ✅ OK |
| Web `vite build` | ✅ dist + `manifest.webmanifest` + `sw.js` 생성 |
| 비밀 노출 스캔(dist) | ✅ clean (SERVICE_ROLE/GEMINI/VAPID_PRIVATE 없음) |

## 3. 무료 운영 게이트 체크

- ✅ 외부 유료 호출 없음(M0는 외부 호출 자체가 없음, Mock 중심).
- ✅ 결제 수단 등록 불필요.
- ✅ 비밀키는 `.env.example`에 이름만, 빌드 산출물 미노출.
- ✅ `ubuntu-latest` 표준 러너만 사용(larger runner 과금 차단).
- 사용량: 0 (로컬 개발만).

## 4. 계약 요약 (이후 마일스톤이 의존)

- **카테고리**: `domestic/economy/ai/dev/tech` (+표시명).
- **영향도**: `HIGH/MEDIUM/LOW`, 근거 범위 `full/title_desc_only`.
- **브리핑 상태**: `generating/ready/failed/empty_high`.
- **선정 규칙 상수**: 카테고리별 ≤3, 전체 ≤15.
- **AI 응답 스키마**: `results[]{article_ref,impact,summary,rationale,dev_relevance,evidence_basis,status}` (additionalProperties 금지 → 환각 필드 차단).
- **DB**: 멱등키 `brief_date`, 동시실행 방지(running 부분 unique), RLS로 노출 범위 강제.

## 5. 결정 사항·환경 메모

- 로컬 DB 실행은 **Docker/Supabase CLI 미설치**로 M0에서 실제 적용하지 않음 → 마이그레이션 SQL은 리뷰 완료, **Supabase 프로젝트 생성(M3 준비) 시 적용**. (M0 DoD의 "로컬 실행 재현"은 파이프라인 Mock 드라이런 + 웹 dev/build로 충족.)
- pnpm 11 빌드 스크립트 게이트: `pnpm-workspace.yaml`(onlyBuiltDependencies) + `.npmrc`(verify-deps-before-run=false)로 처리, esbuild 빌드 허용.

## 6. 미해결·다음 단계 확인 사항

- `apps/web`에 **Tailwind CSS**는 M3(UI 구현) 시 도입 예정(M0는 구조·계약 우선, 불필요한 선설치 지양).
- M1 진입 전 사용자 작업: **없음**(수집은 무료 RSS·키 불필요). `data.go.kr` 정책뉴스 API 사용 여부만 선택(미사용 시 Google News 폴백으로 대체).

## 7. 다음 단계 진입 조건

- **M1 — 뉴스 수집 엔진**: 무료 RSS/API 어댑터, 정규화·중복제거, 24→72h, 소스 장애 격리, 수집 저장·로그.
- 사용자 승인 후 M1 착수.
