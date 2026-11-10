# 04 · 뉴스 파이프라인 (News Pipeline)

> Morning Brief · 설계 문서 4/8 · 작성일 2026-11-10 · 상태: 초안(승인 대기)
> 뉴스 소스는 2026-11-10 실제 접근 검증. 소스 가용성은 변할 수 있어 **Google News 검색 RSS를 전 카테고리 공통 안전망**으로 둔다.

---

## 1. 파이프라인 단계 (고정 순서)

```
① 후보 수집 → ② 정규화 → ③ 중복 제거 → ④ 사전 필터(출처·관련성·저품질)
   → ⑤ AI 영향도 분석 → ⑥ 카테고리별 최대 3건 선정 → ⑦ HIGH만 노출 브리핑 생성
```
- **불변 규칙**: ⑤ 분석 **후** ⑥ 선정. 최신순 상위 N건을 분석 없이 고정하지 않는다(AC-2).
- 사전 필터(④)는 AI 호출 전 저품질·중복·무관 기사를 제거해 **AI 비용 절감**.

---

## 2. 뉴스 소스 평가표 (검증: 2026-11-10)

### 공통 안전망 — Google News RSS (전 카테고리)
- 토픽: `https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko`
- 검색: `https://news.google.com/rss/search?q=<쿼리>&hl=ko&gl=KR&ceid=KR:ko`
- 형식 RSS2.0, `pubDate` 제공, **제목+링크만**(저작권 최안전), 키 불필요. 과도 폴링 자제(카테고리당 수십 분~1h 간격).

### 2.1 국내 시사
| 출처 | URL | 형식 | 본문범위 | 비고 |
|---|---|---|---|---|
| Google News 한국 Top | `/rss?hl=ko&gl=KR&ceid=KR:ko` | RSS | 제목+링크 | 1차 안전망 |
| Google News 검색(정책/법안) | `q=정부정책 OR 법안 OR 공공기관` | RSS | 제목+링크 | |
| 연합뉴스 종합 | `https://www.yna.co.kr/rss/news.xml` | RSS | 제목+요약 | UA 설정 필요(봇차단) |
| data.go.kr 정책뉴스 API | `apis.data.go.kr/1371000/policyNewsService2` | JSON/XML | 보도자료(공공저작물) | serviceKey 발급 필요 |

⚠ **정책브리핑 korea.kr RSS는 2026-07-01 종료** → data.go.kr API 또는 Google News로 대체.

### 2.2 경제·국제
| 출처 | URL | 본문 | 비고 |
|---|---|---|---|
| Google News 검색 | `q=금리 OR 환율 OR 인플레이션 OR 거시경제` | 제목+링크 | 안전망 |
| 연합뉴스 경제/국제 | `/rss/economy.xml`, `/rss/international.xml` | 제목+요약 | UA 필요 |
| 한국경제 | `https://www.hankyung.com/feed/economy` | 제목+요약 | |
| 금융위 보도자료 | `fsc.go.kr/.../rss?fid=0111` | 보도자료 | **확인 필요**(503 관측) |

### 2.3 AI·LLM
| 출처 | URL | 본문 | 비고 |
|---|---|---|---|
| OpenAI 블로그 | `https://openai.com/blog/rss.xml` | 제목+요약 | |
| Google AI 블로그 | `https://blog.google/technology/ai/rss/` | 제목+요약 | |
| Hugging Face | `https://huggingface.co/blog/feed.xml` | 제목만 | |
| Google News(AI 한국어) | `q=인공지능 OR LLM OR AI에이전트` | 제목+링크 | |
| Google News(AI 기업) | `q=Anthropic OR Claude OR OpenAI OR Gemini` | 제목+링크 | Anthropic 공식 RSS 없음 → 이걸로 커버 |

### 2.4 개발·인프라
| 출처 | URL | 본문 | 비고 |
|---|---|---|---|
| Hacker News(hnrss) | `https://hnrss.org/newest?points=100` | 제목+메타 | 점수 필터 |
| HN 공식 API | `hacker-news.firebaseio.com/v0/topstories.json` | 제목+링크 | hnrss 장애 시 |
| Lobsters | `https://lobste.rs/rss` | 제목+요약 | TTL 2h 준수 |
| GitHub Releases | `github.com/{org}/{repo}/releases.atom` | ⚠ 전문 포함 | **본문 버리고 제목+링크만 저장** |
| Google News(개발) | `q=Spring Boot OR Docker OR Kubernetes OR React` | 제목+링크 | |

### 2.5 기타 테크
| 출처 | URL | 본문 | 비고 |
|---|---|---|---|
| 전자신문 ETNews | `http://rss.etnews.com/Section901.xml`(+AI/반도체 섹션) | 제목+요약 | 한국어 주력 |
| ZDNet Korea | `zdnet.co.kr/.../ZDNetKorea_News.asp` | 제목+요약 | **확인 필요**(EUC 인코딩) |
| The Verge | `https://www.theverge.com/rss/index.xml` | 발췌 | UA 필요 |
| Ars Technica | `https://arstechnica.com/ai/feed/` | 발췌 | |
| Google News(HW/반도체) | `q=반도체 OR 모바일 OR 하드웨어` | 제목+링크 | |

### 장애 대체 원칙
각 카테고리 1차 소스가 봇차단/장애 시 → **해당 카테고리 Google News 검색 RSS로 자동 폴백**. 카테고리당 10~20건 확보 안정화.

---

## 3. 정규화 (②)

- **URL canonical화**: 추적 파라미터(utm_*, fbclid 등) 제거, Google News 리다이렉트 URL → 실제 원문 URL 해석(가능 시), 소문자 호스트, 말미 슬래시 정리.
- **발행 시각**: `pubDate`/`updated`/`time`(unix) 파싱 → UTC 저장. 없으면 수집 시각으로 보정하되 플래그.
- **카테고리 태깅**: 소스별 기본 카테고리 + 키워드 보정.
- **언어**: 기본 ko. 영문 소스는 그대로 저장(요약은 한국어 생성).

---

## 4. 중복 제거 (③)

- **1차**: `canonical_url` 완전 일치 → 제거.
- **2차**: 제목 정규화 후 유사도(예: 토큰 자카드/정규화 편집거리 임계값) → 동일 사건 `dedup_group` 부여.
- **3차**: 이전 N일 브리핑에 선정된 기사와 대조 → 재노출 방지.
- 같은 사건 다수 보도 시 **출처 신뢰도·발행 시각**으로 대표 1건 선택.

---

## 5. 사전 필터 (④, AI 호출 전)

- 출처 신뢰도 낮음·광고/홍보성·목록형·중복 그룹 잔여 제거.
- 카테고리 관련성 키워드 매칭(약한 필터, 과도 제거 금지).
- 24시간 내 우선, 후보 부족 시 72시간 확대.
- 카테고리별 후보 상한(예: 20건)으로 AI 호출량 제어.

---

## 6. AI 영향도 분석 (⑤)

### 6.1 호출 전략 — 결정 항목 D-4
- **권장: 카테고리 단위 묶음(batch) 분석**. 카테고리별 후보 N건을 한 번의 호출로 분석 → 호출 수↓(RPM 여유), 카테고리 내 상대 비교 용이.
- 단건 분석은 오류 격리는 쉬우나 호출 수↑(무료 RPM 압박). 묶음 + 개별 실패 격리(파싱 단위 분리)로 절충.
- 일일 상한: 요청 수·토큰 수·실패 횟수 상한 설정. 초과·429 시 **중단**(유료 폴백 금지).

### 6.2 분류 기준
| 영향도 | 기준 |
|---|---|
| **HIGH** | 광범위한 사회·경제 영향, 중대한 정책 변화, 중요한 AI 플랫폼 변화, 심각한 보안 취약점, 개발 실무에 직접 영향 |
| MEDIUM | 주목할 만하나 즉각적·광범위 영향은 아님 |
| LOW | 일반/부수적 소식 |

- HIGH는 **엄격 적용**. 억지 승격 금지(HIGH 0건 허용).
- **환각 방지**: 제공된 제목·요약·링크 범위 밖 사실 생성 금지. 제목·설명만으로 분석 시 `evidence_basis='title_desc_only'` 표시. 검증 불가·출처 충돌 → `status='held'`/`'conflict'`.

### 6.3 AI 응답 JSON Schema (responseSchema로 강제)
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "article_ref": { "type": "string", "description": "입력 기사 식별자" },
          "impact": { "type": "string", "enum": ["HIGH", "MEDIUM", "LOW"] },
          "summary": { "type": "string", "description": "3문장 이내 독자적 요약(원문 복붙 금지)" },
          "rationale": { "type": "string", "description": "영향도 판단 근거 1~2문장" },
          "dev_relevance": { "type": "string", "description": "개발 실무 관련성(없으면 '해당 없음')" },
          "evidence_basis": { "type": "string", "enum": ["full", "title_desc_only"] },
          "status": { "type": "string", "enum": ["analyzed", "held", "conflict"] }
        },
        "required": ["article_ref", "impact", "summary", "rationale", "evidence_basis", "status"]
      }
    }
  },
  "required": ["results"]
}
```
- 모델명·버전·분석 시각은 서버가 `news_analyses`에 기록(모델 응답 아님).
- JSON 검증 실패 → 제한 재시도 → 실패 시 해당 기사 `status='failed'` 격리.

---

## 7. 선정 (⑥) 및 브리핑 생성 (⑦)

- **선정 규칙**: 카테고리별 **HIGH 우선, 최대 3건**. 동점 시 영향도>최신성>출처 신뢰도>개발 관련성.
- 전체 **최대 15건**. 수량 위해 부적절 기사 채우지 않음(HIGH 부족 시 적게).
- 기본 노출은 **HIGH만**. MEDIUM/LOW 분석 결과는 저장하되 비노출(선택적 "더 보기").
- **HIGH 0건** → `daily_briefings.status='empty_high'`, 임의 승격 없음.
- **한 줄 브리핑**: 당일 HIGH들로 1~2문장 생성(AI 또는 규칙 기반). 당일 HIGH 없으면 생략/"조용한 날".
- **예상 읽기 시간**: 선정 기사 요약 길이 합산 기준(목표 5분 이내).

---

## 8. 완료 기준 (배치 DoD)

- `ready`: 수집·분석·선정 완료, 1건 이상 노출(HIGH) + 헤더·통계 저장.
- `empty_high`: 정상 완료했으나 HIGH 0건.
- `partial`: 일부 소스/기사 실패했으나 완료 기준 충족(일부 미완료 표시).
- `failed`: 완료 기준 미충족 → 성공 알림 금지, 마지막 정상 브리핑 유지.

---

## 9. 저작권·약관 준수

- **원문 전문 저장·표시 금지.** dev.to/GitHub Atom 등 피드에 전문이 와도 저장 단계에서 버리고 제목·링크·발행시각만 보존.
- 요약은 **짧은 독자적 사실 요약**(원문 문장 복붙 금지).
- 출처명 + 원문 링크 항상 병기(deep-link).
- Google News RSS는 관행적 서비스 → 과도 폴링 금지.
- **확인 필요** 소스(data.go.kr 한도, FSC RSS, ZDNet EUC, Anthropic 비공식 미러)는 실제 사용 전 재검증.

---

## 10. 테스트 포인트 (상세는 `11-test-plan.md`, 구현계획 단계)

- 24/72시간 경계, 기사 부족, 소스 장애·타임아웃, URL·사건 중복.
- AI: 정상/잘못된 JSON, 환각 방지, HIGH/MEDIUM/LOW 경계, 한도 소진(429), 요청·토큰 상한.
- 선정: 카테고리별 ≤3, 전체 ≤15, 분석 후 선정, HIGH만 노출, HIGH 0건, 읽기 시간.

---

*다음 문서: `07-infrastructure.md`*
