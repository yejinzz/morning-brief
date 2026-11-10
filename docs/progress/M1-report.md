# M1 완료 보고 — 뉴스 수집 엔진

> 작성일 2026-11-10 · 브랜치 `dev`

## 1. 구현 범위·산출 파일

| 영역 | 산출물 |
|---|---|
| 소스 어댑터 | `sources/base.py`(Source·Fetcher·http_fetcher·SourceError), `sources/rss.py`(feedparser 파싱) |
| 소스 카탈로그 | `sources/registry.py` — 카테고리별 1차 소스 + **Google News 폴백(공통 안전망)** |
| 정규화 | `pipeline/normalize.py` — URL canonical(추적 파라미터 제거·호스트 소문자·슬래시/fragment 정리), 결정적 id(uuid5), RawArticle→Article |
| 중복 제거 | `pipeline/dedup.py` — canonical 일치 / 제목 유사도(토큰 자카드) 그룹화 / 이전 브리핑 대조 |
| 수집 오케스트레이션 | `pipeline/collect.py` — 소스 격리·재시도, 24→48→72h 윈도우 확장, 카테고리별 상한, 단계별 건수 |
| 저장소 | `store/articles.py` — ArticleStore 프로토콜 + 인메모리(canonical upsert 멱등). Supabase 구현은 이후 |
| 수동 스모크 | `smoke.py` — 실 RSS 수집(CI 미실행) |

## 2. 테스트 결과 (실제 실행 검증)

| 대상 | 결과 |
|---|---|
| ruff / mypy(strict) | ✅ / ✅ (17 files) |
| pytest | ✅ **31 passed** |

**커버 시나리오** (test-plan C-1~C-8 대응):
- 정규화: 추적 파라미터 제거, 호스트/스킴 소문자, 슬래시·fragment, 결정적 id.
- RSS/Atom 파싱: pubDate/updated 타임존 변환(UTC), 제목·링크 없는 항목 스킵, 파싱 실패 시 SourceError.
- 중복: canonical 일치 제거, 제목 유사도 그룹(대표=최초 발행), 카테고리 다르면 미그룹, 이전 브리핑 URL 제외.
- 수집: **소스 장애 격리**(한 소스 실패해도 나머지 진행+실패 기록), **24→72h 윈도우 확장**, **24h 우선**(충분하면 오래된 것 제외), **카테고리 상한**, 이전 브리핑 대조.
- 저장: canonical_url 기준 upsert 멱등.

## 3. 실 RSS 스모크 (수동, 네트워크)

`python -m mb_pipeline.smoke ai dev` 실제 실행 결과:
```
[ai]  fetched=2392 deduped=2265 dropped_dup=127 candidates=20 window=24h failures=0
[dev] fetched=55   deduped=54   dropped_dup=1   candidates=20 window=24h failures=0
```
→ 실제 한국어 AI 뉴스 + HN/Lobsters 개발 뉴스 수집·중복제거·윈도우·상한 정상 동작, 발행 시각 포함, 소스 실패 0.

## 4. 무료 운영 게이트 체크

- ✅ 무료 RSS·키 불필요(Google News/HN/Lobsters/언론사). `data.go.kr`는 선택(미사용 시 폴백).
- ✅ 결제 수단 불필요, 유료 호출 없음.
- ✅ 폴링 매너: 식별 UA + 소스별 타임아웃(10s). 과도 폴링 방지.
- ✅ CI는 네트워크 없는 fixture 테스트만(실 RSS 스모크는 수동).

## 5. 설계 반영·메모

- **Supabase 영구 저장은 미연동**(클라이언트 부재) — 인메모리 store로 계약·멱등 검증. 실제 DB 저장은 Supabase 프로젝트 생기는 시점(M3/M4)에 ArticleStore 구현 추가.
- 구현계획 M1의 `source_feed/타임아웃/재시도/부분 실패` 모두 반영. collect() 는 fetcher 주입식이라 테스트가 네트워크 독립.
- CI 수정: 웹 `prettier --check .` 가 생성물(pnpm-lock.yaml)까지 검사해 실패 → `.prettierignore` 추가로 해결(이번 커밋 포함).

## 6. 다음 단계

- **M2 — AI 분석 및 브리핑 생성**: Gemini Flash-Lite 연동(교체 어댑터), 카테고리 묶음 분석, JSON Schema 검증, 사전 필터, 일일 상한/429 중단, 분석 후 선정(≤3/≤15), HIGH만 브리핑, 멱등.
- M2 실연동 시 사용자 작업: **Gemini 무료 API 키 발급**(결제 비활성). 그전까지 Mock로 개발.
- 사용자 승인 후 M2 착수.
