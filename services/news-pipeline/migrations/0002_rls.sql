-- Morning Brief · 0002 RLS 정책 (M5, 결정 D-3=로그인 없음)
-- 설계: docs/05-database.md §4 (anon 읽기로 수정).
-- 역할: anon(publishable key, 공개 읽기)·secret key(배치, RLS 우회).
-- 원칙: 공개 성격의 'ready' 브리핑만 anon 에 노출. 비노출 분석·실행 로그·발송 이력은 차단.
-- 쓰기는 전부 secret key(RLS 우회)로만. 예외: push_subscriptions 는 기기 자가 등록(anon INSERT/UPDATE).

alter table collection_jobs         enable row level security;
alter table news_articles           enable row level security;
alter table news_analyses           enable row level security;
alter table daily_briefings         enable row level security;
alter table briefing_articles       enable row level security;
alter table push_subscriptions      enable row level security;
alter table notification_deliveries enable row level security;
alter table user_preferences        enable row level security;

-- daily_briefings: 완료된 브리핑만 공개
drop policy if exists briefings_read on daily_briefings;
create policy briefings_read on daily_briefings
  for select to anon
  using (status in ('ready', 'empty_high'));

-- briefing_articles: 노출 상태 날짜의 선정 결과만
drop policy if exists brief_articles_read on briefing_articles;
create policy brief_articles_read on briefing_articles
  for select to anon
  using (exists (
    select 1 from daily_briefings b
    where b.brief_date = briefing_articles.brief_date
      and b.status in ('ready', 'empty_high')
  ));

-- news_articles: 노출된 선정 기사만
drop policy if exists articles_read on news_articles;
create policy articles_read on news_articles
  for select to anon
  using (exists (
    select 1 from briefing_articles ba
    join daily_briefings b on b.brief_date = ba.brief_date
    where ba.article_id = news_articles.id
      and b.status in ('ready', 'empty_high')
  ));

-- news_analyses: 노출된 선정 기사의 분석만(카드 근거 표시용). 비선정·MEDIUM/LOW 차단.
drop policy if exists analyses_read on news_analyses;
create policy analyses_read on news_analyses
  for select to anon
  using (exists (
    select 1 from briefing_articles ba
    join daily_briefings b on b.brief_date = ba.brief_date
    where ba.analysis_id = news_analyses.id
      and b.status in ('ready', 'empty_high')
  ));

-- push_subscriptions: 기기 자가 등록(INSERT) + 상태 변경(UPDATE, 예: active=false 해지).
-- 조회는 불허(타 기기 구독 보호). 배치는 secret key 로 전체 접근.
drop policy if exists subs_insert on push_subscriptions;
create policy subs_insert on push_subscriptions
  for insert to anon
  with check (true);

drop policy if exists subs_update on push_subscriptions;
create policy subs_update on push_subscriptions
  for update to anon
  using (true)
  with check (true);

-- collection_jobs / notification_deliveries / user_preferences:
-- anon 정책 없음 → 기본 차단(secret key 전용). user_preferences 는 MVP 에서 미사용(설정 로컬 저장).
