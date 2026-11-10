# 05 · 데이터베이스 설계 (Database)

> Morning Brief · 설계 문서 5/8 · 작성일 2026-11-10 · 상태: 초안(승인 대기)

엔진은 `03-tech-stack.md`의 추천에 따라 **Supabase(PostgreSQL)**를 전제로 설계한다(무료 검증 완료: 500MB, RLS 포함, 카드 불필요). 단일 사용자 MVP에 맞춰 불필요한 테이블은 합치고, 확장 가능성(멀티 유저)은 `user_id` 보존으로 열어둔다.

---

## 1. 설계 원칙

- **개인용 MVP 최소주의**: 과도한 정규화·추상화 지양. 조회 패턴(날짜별 브리핑 로드)에 최적화.
- **분석 후 선정**: `news_analyses`(모든 분석 결과 저장) ↔ `briefing_articles`(선정 결과) 분리. 비노출 분석도 보존.
- **멱등성**: 날짜(KST) 기준 unique 제약으로 동일 날짜 재실행 시 중복 방지.
- **저작권**: 원문 전문 미저장. 제목·메타데이터·canonical URL·독자적 짧은 요약만 저장.
- **보안**: RLS 전 테이블 적용. 쓰기는 서버(service_role)만, 읽기는 인증 사용자만. 푸시 구독 키 보호.
- **KST 날짜 키**: 배치는 UTC로 돌지만 "브리핑 날짜"는 `Asia/Seoul` 기준 `date`로 고정(멱등 키).

---

## 2. ERD (논리 모델)

```
                         ┌───────────────────┐
                         │  collection_jobs  │  배치 실행 1건 = 1 row
                         │  (run_id PK)      │
                         └─────────┬─────────┘
                                   │ 1
                                   │ produces
                      ┌────────────┴───────────┐
                      │ N                        │ 1
             ┌────────▼─────────┐      ┌─────────▼──────────┐
             │  news_articles   │      │  daily_briefings   │ 날짜(KST) UNIQUE
             │  (id PK)         │      │  (brief_date PK*)  │
             │  canonical_url U │      └─────────┬──────────┘
             └────────┬─────────┘                │ 1
                      │ 1                         │
                      │ analyzed_by               │ contains
             ┌────────▼─────────┐                 │ N
             │  news_analyses   │       ┌─────────▼──────────┐
             │  (id PK)         │◄──────│ briefing_articles  │ 선정 결과
             │  article_id FK   │ 1   N │ (id PK)            │
             │  impact enum     │       │ brief_date FK      │
             └──────────────────┘       │ article_id FK      │
                                        │ category, order    │
                                        └────────────────────┘

   ┌────────────────────┐   ┌───────────────────────┐   ┌─────────────────────┐
   │  push_subscriptions│   │ notification_deliveries│   │  user_preferences   │
   │  (id PK, endpoint U)│   │ (brief_date+sub UNIQUE)│   │  (user_id PK)       │
   └────────────────────┘   └───────────────────────┘   └─────────────────────┘
```

`*` `daily_briefings`는 `brief_date`를 자연키 겸 멱등키로 사용(단일 사용자).

---

## 3. 테이블 정의

### 3.1 `collection_jobs` — 배치 실행 로그/멱등 제어
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| run_id | uuid | PK, default gen_random_uuid() | 실행 ID |
| brief_date | date | NOT NULL | KST 기준 대상 날짜 |
| status | text | NOT NULL, CHECK in (`running`,`succeeded`,`failed`,`partial`) | 실행 상태 |
| stage_counts | jsonb | | 단계별 건수(수집/중복제거/필터/분석/선정) |
| error | text | | 실패 사유 요약 |
| retry_count | int | NOT NULL default 0 | 재시도 횟수 |
| started_at | timestamptz | NOT NULL default now() | 시작 |
| finished_at | timestamptz | | 종료 |

- 인덱스: `(brief_date, started_at desc)`. 부분 unique: 날짜당 `status='running'` 1건만 허용(동시 실행 방지) → `CREATE UNIQUE INDEX ON collection_jobs(brief_date) WHERE status='running'`.

### 3.2 `news_articles` — 수집 원본 메타데이터
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | uuid | PK | |
| canonical_url | text | NOT NULL, UNIQUE | 정규화 URL(중복 키) |
| source | text | NOT NULL | 출처명 |
| source_feed | text | | 피드/소스 식별자 |
| title | text | NOT NULL | 제목 |
| description | text | | 소스 제공 짧은 설명(원문 전문 아님) |
| category | text | NOT NULL, CHECK in 5개 | 분류 카테고리 |
| published_at | timestamptz | | 발행 시각 |
| collected_at | timestamptz | NOT NULL default now() | 수집 시각 |
| dedup_group | text | | 동일 사건 그룹 키(제목 유사도/클러스터) |
| lang | text | default 'ko' | 언어 |

- 인덱스: `canonical_url`(unique), `(category, published_at desc)`, `dedup_group`, `collected_at`.
- 보관: 발행/수집 후 N일 경과분 정리(§6).

### 3.3 `news_analyses` — 기사별 AI 분석 (모든 결과 저장)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | uuid | PK | |
| article_id | uuid | FK→news_articles.id ON DELETE CASCADE | |
| brief_date | date | NOT NULL | 분석 대상 날짜 |
| model | text | NOT NULL | 모델명·버전 |
| impact | text | NOT NULL, CHECK in (`HIGH`,`MEDIUM`,`LOW`) | 영향도 |
| rationale | text | | 판단 근거 |
| summary | text | | 3문장 이내 독자적 요약 |
| dev_relevance | text | | 개발자 관련성 |
| evidence_basis | text | CHECK in (`full`,`title_desc_only`) | 분석 근거 범위(환각 방지 표시) |
| status | text | NOT NULL, CHECK in (`analyzed`,`held`,`conflict`,`failed`) | 분석 상태 |
| analyzed_at | timestamptz | NOT NULL default now() | |

- 인덱스: `(brief_date, impact)`, `(article_id)`, unique `(article_id, brief_date, model)`(동일 기사·동일 날짜 재분석 멱등).

### 3.4 `daily_briefings` — 날짜별 브리핑 헤더
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| brief_date | date | PK | KST 날짜(멱등키) |
| headline | text | | 오늘의 한 줄 브리핑(1~2문장) |
| collected_count | int | NOT NULL default 0 | 수집 수 |
| high_count | int | NOT NULL default 0 | HIGH 수 |
| est_read_minutes | int | | 예상 읽기 시간(분) |
| status | text | NOT NULL, CHECK in (`generating`,`ready`,`failed`,`empty_high`) | 생성 상태 |
| generated_at | timestamptz | | 생성 완료 시각 |
| run_id | uuid | FK→collection_jobs.run_id | 생성한 실행 |

- `status='ready'`일 때만 PWA 기본 노출·푸시 발송 대상.
- `empty_high`: HIGH 0건(정상 완료, 노출할 HIGH 없음).

### 3.5 `briefing_articles` — 날짜별 선정 결과(노출용)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | uuid | PK | |
| brief_date | date | FK→daily_briefings.brief_date ON DELETE CASCADE | |
| article_id | uuid | FK→news_articles.id | |
| analysis_id | uuid | FK→news_analyses.id | 선정 근거 분석 |
| category | text | NOT NULL, CHECK in 5개 | |
| display_order | int | NOT NULL | 탭 내 표시 순서 |
| is_high | boolean | NOT NULL default true | 기본 노출(HIGH)만 true |

- 제약: unique `(brief_date, article_id)`. 선정 규칙(카테고리별 ≤3, 전체 ≤15)은 애플리케이션에서 보장하고 DB는 중복만 방지.
- 인덱스: `(brief_date, category, display_order)`.

### 3.6 `push_subscriptions` — 기기별 푸시 구독
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | uuid | PK | |
| user_id | uuid | NOT NULL | 소유자(단일) |
| endpoint | text | NOT NULL, UNIQUE | 푸시 엔드포인트 |
| p256dh | text | NOT NULL | 공개키 |
| auth | text | NOT NULL | 인증 시크릿 |
| expiration_time | timestamptz | | 구독 만료(있으면) |
| active | boolean | NOT NULL default true | 활성 여부 |
| last_status | text | | 최종 전송 상태(200/410 등) |
| created_at | timestamptz | NOT NULL default now() | |

- 410/404 수신 시 `active=false` 또는 삭제(§08 푸시 정리).

### 3.7 `notification_deliveries` — 발송 이력(중복 방지)
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | uuid | PK | |
| brief_date | date | NOT NULL | |
| subscription_id | uuid | FK→push_subscriptions.id ON DELETE CASCADE | |
| status | text | NOT NULL, CHECK in (`sent`,`failed`,`skipped`) | |
| attempts | int | NOT NULL default 1 | |
| sent_at | timestamptz | default now() | |

- 제약: unique `(brief_date, subscription_id)` → 날짜·기기별 **중복 발송 방지**(멱등).

### 3.8 `user_preferences` — 설정
| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| user_id | uuid | PK | |
| theme | text | CHECK in (`light`,`dark`,`system`) default 'system' | |
| favorite_categories | text[] | | 관심 카테고리 |
| notifications_enabled | boolean | default true | |
| updated_at | timestamptz | default now() | |

### 3.9 읽음 상태 — **결정 항목 D-2**
- 권장: **클라이언트 로컬 저장(IndexedDB/localStorage)**. 단일 사용자·단일 주요 기기 가정 시 서버 테이블 불필요, 오프라인에서도 동작.
- 서버 동기화를 원하면 `read_states(user_id, article_id, read_at)` 테이블 추가(선택). MVP는 로컬 권장.

---

## 4. RLS (Row Level Security) 정책

전 테이블 RLS 활성화. 역할 구분: `anon`(비로그인, 접근 없음), `authenticated`(소유자, 읽기), `service_role`(서버 배치, 전체).

| 테이블 | authenticated(소유자) | service_role(배치) |
|---|---|---|
| daily_briefings | SELECT where status in ('ready','empty_high') | ALL |
| briefing_articles | SELECT (조인된 날짜가 ready) | ALL |
| news_articles | SELECT (선정된 것만, 뷰 경유 권장) | ALL |
| news_analyses | 기본 비노출(선정 근거만 뷰로) | ALL |
| push_subscriptions | 본인 user_id INSERT/UPDATE/DELETE | ALL |
| user_preferences | 본인 row SELECT/UPDATE | ALL |
| notification_deliveries | 없음 | ALL |
| collection_jobs | 없음(또는 상태만) | ALL |

- 서버 배치는 `service_role` 키(브라우저 미노출, Actions Secret) 사용 → RLS 우회하여 쓰기.
- PWA는 `anon` 공개키 + 로그인 세션으로 `authenticated` 권한 읽기만.
- 비노출 원칙: 기본 UI는 HIGH만. `news_analyses` 전체·MEDIUM/LOW는 일반 조회에 노출하지 않음(필요 시 소유자 전용 뷰).

---

## 5. 멱등성·동시성

- **날짜 멱등키**: `daily_briefings.brief_date` PK, `notification_deliveries(brief_date, subscription_id)` unique.
- **동시 실행 방지**: `collection_jobs` 날짜당 `running` 1건 부분 unique 인덱스. 배치 시작 시 upsert 시도 → 충돌이면 이미 실행 중으로 간주하고 종료.
- **재실행(수동)**: 동일 날짜 재실행 시 기존 분석 재사용(unique `(article_id, brief_date, model)`), 선정·헤더 upsert로 덮어쓰기. 푸시는 이미 `sent` 이력이 있으면 재발송 안 함.
- **부분 성공**: 일부 기사 분석 실패는 `news_analyses.status='failed'`로 격리, 브리핑은 완료 기준 충족 시 `ready`.

---

## 6. 데이터 보관·정리 (무료 용량 관리, 500MB 한도)

| 데이터 | 보관 | 정리 방법 |
|---|---|---|
| news_articles (비선정) | 14~30일 | 주기적 삭제(배치 말미 또는 별도 cleanup) |
| news_articles (선정됨) | 브리핑 보관 기간과 동일 | 브리핑 삭제 시 함께 |
| news_analyses | 기사와 동일(CASCADE) | |
| daily_briefings / briefing_articles | **90~180일**(개인 열람 범위) | 오래된 날짜 삭제 |
| collection_jobs | 90일 | |
| notification_deliveries | 90일 | |

- 500MB 한도상 원문 전문 미저장·주기 정리로 충분(기사 메타만 저장).
- **비활성 중지 방지**: 매 배치가 DB에 쓰므로 7일 무활동 중지에 도달하지 않음. 배치 실패일에도 `collection_jobs`에 row를 남겨 "핑" 효과.

---

## 7. 마이그레이션 전략

- SQL 마이그레이션 파일을 `services/.../migrations/` 또는 Supabase migration으로 버전 관리(M0에서 경로 확정).
- 순서: ① extension(`pgcrypto` for gen_random_uuid) → ② 테이블 → ③ 인덱스/제약 → ④ RLS 정책 → ⑤ 뷰(소유자 노출용).
- 시드/목 데이터: 로컬 개발·테스트용 픽스처(M0).

---

## 8. 결정 필요 / 확인 필요

- **D-2 읽음 상태**: 로컬 저장 권장(서버 테이블 생략). 승인 요청.
- **Supabase 복구 기간**: 중지 후 복구 가능 기간이 문서상 90일(최신 changelog) vs 1년(구 문구) 상충 → 운영 전 대시보드 재확인(`07-infrastructure.md` 위험표).
- 멀티 유저 확장은 범위 외지만 `user_id` 컬럼 유지로 추후 열어둠.

---

*다음 문서: `06-ui-ux.md`*
