-- Morning Brief · 0002 RLS 정책 (M0)
-- 설계: docs/05-database.md §4. 역할: anon(차단), authenticated(소유자 읽기), service_role(배치 전체).
-- service_role 은 RLS 를 우회하므로 배치 쓰기는 정책과 무관하게 동작한다.
-- authenticated 에는 "노출 가능한 것"만 명시적으로 SELECT 허용. 그 외 기본 차단.

-- 전 테이블 RLS 활성화
alter table collection_jobs        enable row level security;
alter table news_articles          enable row level security;
alter table news_analyses          enable row level security;
alter table daily_briefings        enable row level security;
alter table briefing_articles      enable row level security;
alter table push_subscriptions     enable row level security;
alter table notification_deliveries enable row level security;
alter table user_preferences       enable row level security;

-- daily_briefings: 완료된 브리핑만 조회
drop policy if exists briefings_read on daily_briefings;
create policy briefings_read on daily_briefings
  for select to authenticated
  using (status in ('ready','empty_high'));

-- briefing_articles: 조인된 날짜가 노출 상태일 때만
drop policy if exists brief_articles_read on briefing_articles;
create policy brief_articles_read on briefing_articles
  for select to authenticated
  using (exists (
    select 1 from daily_briefings b
    where b.brief_date = briefing_articles.brief_date
      and b.status in ('ready','empty_high')
  ));

-- news_articles: 선정되어 노출된 기사만(briefing_articles 경유)
drop policy if exists articles_read on news_articles;
create policy articles_read on news_articles
  for select to authenticated
  using (exists (
    select 1 from briefing_articles ba
    join daily_briefings b on b.brief_date = ba.brief_date
    where ba.article_id = news_articles.id
      and b.status in ('ready','empty_high')
  ));

-- news_analyses: 노출된 선정 기사의 분석만(근거 표시용). MEDIUM/LOW·비선정 분석은 차단.
drop policy if exists analyses_read on news_analyses;
create policy analyses_read on news_analyses
  for select to authenticated
  using (exists (
    select 1 from briefing_articles ba
    join daily_briefings b on b.brief_date = ba.brief_date
    where ba.analysis_id = news_analyses.id
      and b.status in ('ready','empty_high')
  ));

-- push_subscriptions: 본인(user_id = auth.uid()) 것만 CRUD
drop policy if exists subs_rw on push_subscriptions;
create policy subs_rw on push_subscriptions
  for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- user_preferences: 본인 것만
drop policy if exists prefs_rw on user_preferences;
create policy prefs_rw on user_preferences
  for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- collection_jobs / notification_deliveries: authenticated 정책 없음 → 기본 차단(service_role 전용)
