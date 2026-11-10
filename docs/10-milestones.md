# 10 · 마일스톤 상세 (M0~M5)

> Morning Brief · 구현계획 2/4 · 작성일 2026-11-10 · 상태: 초안(승인 대기)
> 각 마일스톤은 impl-plan §5의 10개 항목을 포함. 경로는 `03-tech-stack.md §4` 구조 기준(M0에서 최종 확정).

---

## M0 — 프로젝트 기반 및 계약 확정

**1. 목표·사용자 가치**
신규 개발자가 무료 환경에서 로컬 실행을 재현할 수 있고, DB/API/AI 계약과 비밀키 정책이 문서·코드로 고정된다. 이후 마일스톤이 계약 위에서 독립 구현 가능.

**2. 선행 조건·의존성**
설계 01~08 승인(완료). 외부 계정은 아직 불필요(Mock 중심).

**3. 세부 작업 체크리스트**
- [ ] 모노레포 구조 생성: `apps/web`, `services/news-pipeline`, `.github/workflows`, `docs`.
- [ ] 루트 도구: `.gitignore`, `.editorconfig`, `.nvmrc`/`.python-version`, README 자리(추후).
- [ ] 프론트 품질 도구: ESLint + Prettier + TypeScript strict.
- [ ] 파이썬 품질 도구: ruff + black + mypy(가능 범위), `pyproject.toml`/`requirements.txt`.
- [ ] `.env.example` 작성(키 이름만, 값 없음) + 비밀 노출 방지 규칙 문서화.
- [ ] DB 마이그레이션 초안(`05-database.md` 스키마) + RLS 정책 SQL.
- [ ] API 응답 계약(TS 타입 + 파이썬 모델 공유 정의) 정의.
- [ ] AI JSON Schema(`04 §6.3`)를 코드 상수로 고정.
- [ ] Mock 데이터셋(샘플 기사/분석/브리핑 JSON) + 로컬 로더.
- [ ] 로컬 실행 스크립트(파이프라인 Mock 실행, 웹 dev 서버).

**4. 생성·수정 예상 파일**
```
.gitignore .editorconfig .nvmrc .python-version .env.example
apps/web/{package.json,tsconfig.json,.eslintrc,vite.config.ts,src/}
services/news-pipeline/{pyproject.toml,requirements.txt,ruff.toml,src/,tests/fixtures/}
services/news-pipeline/src/contracts/{schema.py,ai_schema.py}
services/news-pipeline/migrations/{0001_init.sql,0002_rls.sql}
apps/web/src/types/contracts.ts
docs/ (본 문서들)
```

**5. DB·API·데이터 계약 및 예외 처리**
- DB: `05-database.md` 전 테이블·인덱스·RLS를 마이그레이션으로. 멱등키(`brief_date`) 제약 포함.
- API 계약: PWA가 읽는 응답 형태(브리핑 헤더 + 카드 배열) 타입 고정.
- AI 계약: responseSchema 상수. 검증 실패·held/conflict 상태 정의.
- 예외: 계약 불일치 시 빌드/타입 에러로 조기 발견.

**6. 테스트 시나리오**
- 단위: 계약 타입 직렬화/역직렬화, AI Schema 검증(정상/비정상 JSON), 마이그레이션 적용(로컬 Postgres/Supabase local).
- 통합: Mock 데이터로 파이프라인 골격 "수집→저장" 드라이런(실제 외부 호출 없음).
- 자동화: CI에서 lint+type+unit(아직 외부 비밀 불필요).

**7. 무료 사용량·비밀키·과금 점검**
- 외부 호출 없음 → 사용량 0. 비밀키는 이름만 `.env.example`. 과금 위험 없음.
- `.gitignore`에 `.env`·키 파일 포함 확인.

**8. Definition of Done**
- 로컬에서 `설치→lint→type→unit→Mock 파이프라인 실행→웹 dev 기동`이 문서 절차대로 재현됨.
- DB 스키마·RLS·AI Schema·API 계약이 코드로 존재하고 테스트 통과.
- 비밀키 관리 규칙 문서화.

**9. 예상 위험·사용자 확인**
- 저장소 구조 변경(모노레포) 확정 필요 — 제안대로 진행(확인 가능).
- 로컬 Postgres vs Supabase local CLI 선택 — 권장 Supabase CLI local(실환경 근접). ✅ 확인 필요.

**10. 완료 보고·진입 조건**
보고(구조·계약·테스트·게이트) → 승인 → M1 진입.

---

## M1 — 뉴스 수집 엔진

**1. 목표·사용자 가치**
검증된 무료 소스에서 카테고리별 후보를 안정적으로 수집·정규화·중복제거하여 분석 입력을 확보.

**2. 선행 조건·의존성**
M0(계약·DB·Mock). 외부: 무료 RSS(키 불필요), data.go.kr은 선택(serviceKey, 없으면 skip).

**3. 세부 작업 체크리스트**
- [ ] 소스 어댑터 인터페이스(`fetch() -> list[RawArticle]`) + 소스별 구현(`04 §2` 표).
- [ ] 전 카테고리 **Google News 검색 RSS 폴백** 구현.
- [ ] 정규화: URL canonical(utm 제거, Google News 리다이렉트 해석), 발행시각 파싱(UTC), 카테고리 태깅.
- [ ] 중복제거: canonical 일치 → 제목 유사도 → dedup_group → 이전 N일 대조.
- [ ] 24h 우선·부족 시 72h 확대 로직.
- [ ] 소스별 타임아웃·재시도·부분 실패 격리(한 소스 실패가 전체 중단 안 함).
- [ ] 무료 호출량 상한(소스별 간격/상한) + 폴링 매너(UA, 간격).
- [ ] 수집 결과 `news_articles` 저장 + `collection_jobs` 단계 로그.

**4. 생성·수정 예상 파일**
```
services/news-pipeline/src/sources/{base.py,google_news.py,yna.py,hn.py,etnews.py,...}
services/news-pipeline/src/pipeline/{normalize.py,dedup.py,collect.py}
services/news-pipeline/src/store/articles.py
services/news-pipeline/tests/{test_normalize.py,test_dedup.py,test_sources.py,fixtures/}
```

**5. DB·계약·예외**
- 쓰기: `news_articles`(canonical_url unique → upsert), `collection_jobs.stage_counts`.
- 예외: 소스 HTTP 오류/타임아웃 → skip+폴백, 로그. 발행시각 누락 → 보정+플래그.

**6. 테스트 시나리오**
- 단위: URL 정규화 케이스, 제목 유사도 중복, 발행시각 파싱, 카테고리 태깅.
- 통합(픽스처): 24/72h 경계, 기사 부족→확대, 소스 장애 격리, URL·사건 중복 제거, 폴백 동작.
- 실서비스(제한적, 수동): 실제 RSS 1회 수집 smoke(네트워크, CI 외).

**7. 무료 사용량·비밀키·과금 점검**
- RSS 무료·키 불필요. data.go.kr serviceKey는 Secret(선택). 과금 위험 없음.
- 폴링 간격 준수(차단 방지).

**8. Definition of Done**
- 픽스처로 중복제거·시각필터·카테고리분류·소스장애 격리 재현, 무료 호출 상한 초과 없음.
- 카테고리당 후보 10~20건(소스 가용 시) 확보.

**9. 위험·확인**
- 일부 언론사 봇 차단(UA 필요) → 폴백으로 커버. ✅ 확인: data.go.kr 사용 여부(serviceKey 발급).

**10. 보고·진입**
보고 → 승인 → M2.

---

## M2 — AI 분석 및 브리핑 생성

**1. 목표·사용자 가치**
수집 후보를 무료 AI로 영향도 분석(JSON)하고, 분석 후 선정·브리핑을 생성하여 "오늘 읽을 것"을 만든다.

**2. 선행 조건·의존성**
M1(수집). 외부: Gemini 무료 키(사용자). Mock 모드로 키 없이도 개발 가능.

**3. 세부 작업 체크리스트**
- [ ] AI 어댑터 인터페이스(`analyze(batch) -> Results`) + Gemini 구현(responseSchema).
- [ ] **카테고리 묶음 분석**(D-4) + 개별 결과 파싱·격리.
- [ ] 사전 필터(저품질·무관 제거, AI 호출 전).
- [ ] 일일 요청/토큰/실패 상한 + 429 감지 → **중단**(유료 폴백 없음).
- [ ] JSON Schema 검증 + 실패 재시도 제한 + `status` 매핑(analyzed/held/conflict/failed).
- [ ] 환각 방지: evidence_basis 표시, 범위 밖 생성 억제 프롬프트.
- [ ] 선정: 카테고리별 ≤3, 전체 ≤15, HIGH 우선, 억지 승격 없음.
- [ ] 브리핑 생성: headline(한 줄), high_count, est_read_minutes, status(ready/empty_high).
- [ ] 멱등: 동일 날짜 재실행 시 분석 재사용 + upsert.

**4. 생성·수정 예상 파일**
```
services/news-pipeline/src/ai/{base.py,gemini.py,prompt.py,limits.py}
services/news-pipeline/src/pipeline/{prefilter.py,select.py,briefing.py}
services/news-pipeline/src/store/{analyses.py,briefings.py}
services/news-pipeline/tests/{test_ai_schema.py,test_select.py,test_briefing.py,fixtures/ai_*.json}
```

**5. DB·계약·예외**
- 쓰기: `news_analyses`, `daily_briefings`, `briefing_articles`.
- 예외: 잘못된 JSON→재시도→격리. 429/한도→중단+상태기록+마지막 브리핑 유지. HIGH 0건→empty_high.

**6. 테스트 시나리오**
- 단위: Schema 검증(정상/깨진 JSON), 선정 규칙(≤3/≤15), 읽기시간 계산, headline 생성, 멱등.
- 통합: 분석 후 선정 순서 보장, HIGH만 노출, HIGH 0건, 한도 소진 중단, 환각 플래그.
- Mock vs 실서비스: 기본 Mock(픽스처). 실 Gemini는 수동 smoke 1회(키 보유 시).

**7. 무료 사용량·비밀키·과금 점검**
- Gemini 키 = Actions Secret(서버). 하루 ~100 req ≪ 무료 RPD. 429 시 중단. **유료 폴백 코드 금지**.
- 민감정보 미전송(공개 메타만).

**8. Definition of Done**
- AI 오류·한도소진·후보부족·HIGH 0건·동일날짜 재실행 테스트 통과, 유료 호출 없이 브리핑 데이터 생성.

**9. 위험·확인**
- Gemini 무료 RPD 변동 → 상한·축소로 대응. ✅ 확인: 실 키로 PoC 1회 수행 여부.

**10. 보고·진입**
보고 → 승인 → M3.

---

## M3 — 모바일 PWA

**1. 목표·사용자 가치**
모바일에서 핵심 뉴스를 5분 이내로 읽는 조회 경험. 탭·카드·상태 UI·오프라인.

**2. 선행 조건·의존성**
M0 계약(병렬 가능). 데이터는 Mock→실 Supabase. 외부: Supabase(사용자).

**3. 세부 작업 체크리스트**
- [ ] 라우팅: `/`(오늘), `/d/:date`(지난), `/settings`.
- [ ] 홈: 헤더(날짜·생성시각), 한 줄 브리핑, 통계 바, 탭(전체+5), 카드 리스트.
- [ ] 카드 컴포넌트(`06 §2.2`): 제목·카테고리·요약·근거·출처·시각·원문링크·읽음.
- [ ] 상태 UI(`06 §3`): 로딩/생성중/empty_high/카테고리0/오류/오프라인/실패.
- [ ] 읽음 상태 **로컬 저장**(D-2, IndexedDB/localStorage).
- [ ] 설정: 테마(라이트/다크/시스템), 관심 카테고리, 알림(권한·구독 UI 자리).
- [ ] PWA: 매니페스트, 서비스워커(앱셸+데이터 캐시), 설치 UX(iOS 안내).
- [ ] Supabase 클라이언트(anon+세션, 읽기), 인증(D-3 최소 로그인).
- [ ] 접근성·반응형.

**4. 생성·수정 예상 파일**
```
apps/web/src/{App.tsx,main.tsx,routes/}
apps/web/src/components/{BriefingHeader,OneLiner,StatsBar,Tabs,ArticleCard,StateViews}.tsx
apps/web/src/lib/{supabase.ts,readState.ts,theme.ts}
apps/web/src/pwa/{manifest.webmanifest,sw.ts}
apps/web/tests/ (컴포넌트/상태 테스트)
```

**5. DB·계약·예외**
- 읽기: RLS 통해 `daily_briefings`(ready/empty_high) + `briefing_articles` 조인. 비노출 분석 접근 불가.
- 예외: 네트워크 오류→캐시 폴백, 데이터 없음→상태 뷰.

**6. 테스트 시나리오**
- 단위/컴포넌트: 탭 전환, 카드 렌더, 읽음 토글, 상태 뷰 분기.
- 통합: Mock 데이터로 날짜별 조회, 원문 링크, 빈/오류/오프라인.
- E2E(일부): 모바일 뷰포트, PWA 설치 가능 여부, 오프라인 캐시(실브라우저, M5와 연계).

**7. 무료 사용량·비밀키·과금 점검**
- 클라이언트엔 anon·VAPID 공개키·URL만. service_role 절대 미포함(빌드 산출물 검사).
- Supabase 읽기 egress 미미.

**8. Definition of Done**
- Android/iOS 브라우저 및 홈화면 설치 시나리오 검증, 5분 이내 읽기 표시, 상태 UI 완비.

**9. 위험·확인**
- iOS 설치 전 푸시 불가 안내 필요. ✅ 확인: D-3 로그인 UX(매직링크 등) 상세.

**10. 보고·진입**
보고 → 승인 → M4.

---

## M4 — 예약 실행 및 Web Push

**1. 목표·사용자 가치**
매일 KST 07시대 자동 생성 + 정상 완료 후 푸시로 알림. 기기 전원 무관.

**2. 선행 조건·의존성**
M2(브리핑 생성), M3(딥링크·구독 UI). 외부: VAPID 키(사용자), Supabase.

**3. 세부 작업 체크리스트**
- [ ] `.github/workflows/daily-brief.yml`: cron `7 22 * * *` + workflow_dispatch(날짜 입력), `ubuntu-latest` 고정.
- [ ] 실행 중복 방지(running 부분 unique), 실패 상태 기록, 단계 재시도, 완료 상태 정의.
- [ ] KST 날짜 계산(UTC→Asia/Seoul).
- [ ] Web Push 발송: VAPID 서명, 구독별 POST, 페이로드(≤4KB).
- [ ] 구독 관리: 저장/해지, 만료(410/404) 정리, `notification_deliveries` 중복 방지.
- [ ] **브리핑 성공 후에만 발송**. HIGH 0건 **미발송**(D-1).
- [ ] 딥링크(`/d/:date`), iOS 설치 조건 안내 연계.
- [ ] 무료 스케줄러 지연·누락·DB 중지 대처(수동 재실행, 핑).

**4. 생성·수정 예상 파일**
```
.github/workflows/daily-brief.yml
services/news-pipeline/src/push/{vapid.py,send.py,subscriptions.py}
services/news-pipeline/src/run.py (엔트리: 수집→분석→선정→저장→푸시)
apps/web/src/pwa/sw.ts (push/notificationclick 핸들러)
apps/web/src/features/push/subscribe.ts
tests/ (푸시 멱등·만료·실패 격리)
```

**5. DB·계약·예외**
- `push_subscriptions`, `notification_deliveries(brief_date,sub) unique`.
- 예외: 저장 성공↔발송 실패 분리, 제한 재시도, 410→정리, 생성 실패 시 발송 금지.

**6. 테스트 시나리오**
- 단위: VAPID 서명, 페이로드 구성, KST 변환, 중복 방지 키.
- 통합: 성공/실패 분기, 중복 푸시 방지, 만료 구독 정리, 권한 거부, empty_high 미발송.
- 실서비스(수동): 실제 구독→발송→수신 1회, iOS 설치형 수신.

**7. 무료 사용량·비밀키·과금 점검**
- VAPID 개인키·service_role·Gemini 키 = Secret. Web Push $0. Actions public 무료.
- larger runner 미사용 확인.

**8. Definition of Done**
- 예약·수동 재실행, 성공·실패 알림 분기, 중복 방지, 구독·해지 재현, 과금 없음.

**9. 위험·확인**
- cron 지연·누락(수용), 60일 무활동 비활성(활동 유지). ✅ 확인: 사용자 기기로 실제 푸시 수신 테스트.

**10. 보고·진입**
보고 → 승인 → M5.

---

## M5 — 배포·통합 검증·운영 안정화

**1. 목표·사용자 가치**
기기가 꺼져 있어도 클라우드 배치가 돌고, 조회·푸시·복구가 확인되는 운영 가능 상태.

**2. 선행 조건·의존성**
M1~M4. 외부: Cloudflare Pages(사용자), 전 Secret 등록.

**3. 세부 작업 체크리스트**
- [ ] Cloudflare Pages 배포(빌드 설정, `*.pages.dev`, 환경변수 anon/VAPID공개/URL).
- [ ] GitHub Actions Secret 전부 등록·점검.
- [ ] 통합/E2E: 수집→분석→브리핑→푸시→조회 전체 흐름.
- [ ] 모바일 성능·접근성·오프라인·알림 테스트.
- [ ] 운영: 로그 확인, 장애 재실행, 데이터 보관·정리 잡, 무료 한도 모니터링.
- [ ] 문서: README, 배포 가이드, 운영 매뉴얼, 무료 정책 변경 대응(`12-deployment-plan.md` 참조).

**4. 생성·수정 예상 파일**
```
README.md
docs/ (운영 매뉴얼 보강)
.github/workflows/ (cleanup 잡, 활동 유지)
apps/web/ (프로덕션 빌드 설정)
```

**5. DB·계약·예외**
- 보관·정리 잡(오래된 기사/브리핑/이력 삭제). 백업 부재 수용(재생성 가능).

**6. 테스트 시나리오**
- E2E 전체 흐름, KST 시간대, 수동 재실행, 비밀키 노출 검사(빌드 산출물 grep), 무료 한도 초과 시 중단, 서비스 일시중지 시 동작.
- 모바일: 설치·오프라인·푸시 수신.

**7. 무료 사용량·비밀키·과금 점검**
- 전 구성 무료 검증표(`07 §4`) 재확인. 빌드 산출물에 서버 키 부재 검증(AC-8).

**8. Definition of Done**
- 기기 오프 상태에서 배치 실행·브리핑·푸시·복구 확인, 유료·자동과금 경로 없음. **정확 07:00은 무료 제약 명시**.

**9. 위험·확인**
- 무료 정책 변경 모니터링 체계. ✅ 확인: 운영 시작 전 각 "확인 필요" 항목(08 §10) 최종 재검증.

**10. 보고·진입**
최종 보고 → 운영 전환. 이후 유지보수.

---

*다음: `11-test-plan.md`*
