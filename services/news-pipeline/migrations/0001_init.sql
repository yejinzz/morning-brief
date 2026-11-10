-- Morning Brief · 0001 초기 스키마 (M0)
-- 설계: docs/05-database.md. 대상: Supabase(PostgreSQL).
-- 적용은 Supabase 프로젝트 생성 후(M3 준비). 전진(forward-only) 설계.

create extension if not exists pgcrypto;  -- gen_random_uuid()

-- ── 카테고리/상태 enum ────────────────────────────────────────
do $$ begin
  create type category as enum ('domestic','economy','ai','dev','tech');
exception when duplicate_object then null; end $$;

do $$ begin
  create type impact as enum ('HIGH','MEDIUM','LOW');
exception when duplicate_object then null; end $$;

do $$ begin
  create type evidence_basis as enum ('full','title_desc_only');
exception when duplicate_object then null; end $$;

do $$ begin
  create type analysis_status as enum ('analyzed','held','conflict','failed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type briefing_status as enum ('generating','ready','failed','empty_high');
exception when duplicate_object then null; end $$;

do $$ begin
  create type job_status as enum ('running','succeeded','failed','partial');
exception when duplicate_object then null; end $$;

-- ── collection_jobs ──────────────────────────────────────────
create table if not exists collection_jobs (
  run_id       uuid primary key default gen_random_uuid(),
  brief_date   date not null,
  status       job_status not null,
  stage_counts jsonb,
  error        text,
  retry_count  int not null default 0,
  started_at   timestamptz not null default now(),
  finished_at  timestamptz
);
create index if not exists idx_jobs_date on collection_jobs (brief_date, started_at desc);
-- 동일 날짜 동시 실행 방지(running 1건)
create unique index if not exists uq_jobs_running
  on collection_jobs (brief_date) where status = 'running';

-- ── news_articles ────────────────────────────────────────────
create table if not exists news_articles (
  id            uuid primary key default gen_random_uuid(),
  canonical_url text not null unique,
  source        text not null,
  source_feed   text,
  title         text not null,
  description   text,
  category      category not null,
  published_at  timestamptz,
  collected_at  timestamptz not null default now(),
  dedup_group   text,
  lang          text not null default 'ko'
);
create index if not exists idx_articles_cat_pub on news_articles (category, published_at desc);
create index if not exists idx_articles_dedup on news_articles (dedup_group);
create index if not exists idx_articles_collected on news_articles (collected_at);

-- ── news_analyses (모든 분석 결과 저장) ───────────────────────
create table if not exists news_analyses (
  id             uuid primary key default gen_random_uuid(),
  article_id     uuid not null references news_articles (id) on delete cascade,
  brief_date     date not null,
  model          text not null,
  impact         impact not null,
  rationale      text,
  summary        text,
  dev_relevance  text,
  evidence_basis evidence_basis not null,
  status         analysis_status not null,
  analyzed_at    timestamptz not null default now(),
  -- 동일 기사·동일 날짜·동일 모델 재분석 멱등
  unique (article_id, brief_date, model)
);
create index if not exists idx_analyses_date_impact on news_analyses (brief_date, impact);
create index if not exists idx_analyses_article on news_analyses (article_id);

-- ── daily_briefings (날짜=멱등키) ─────────────────────────────
create table if not exists daily_briefings (
  brief_date        date primary key,
  headline          text,
  collected_count   int not null default 0,
  high_count        int not null default 0,
  est_read_minutes  int,
  status            briefing_status not null,
  generated_at      timestamptz,
  run_id            uuid references collection_jobs (run_id)
);

-- ── briefing_articles (노출용 선정 결과) ──────────────────────
create table if not exists briefing_articles (
  id            uuid primary key default gen_random_uuid(),
  brief_date    date not null references daily_briefings (brief_date) on delete cascade,
  article_id    uuid not null references news_articles (id),
  analysis_id   uuid references news_analyses (id),
  category      category not null,
  display_order int not null,
  is_high       boolean not null default true,
  unique (brief_date, article_id)
);
create index if not exists idx_brief_articles on briefing_articles (brief_date, category, display_order);

-- ── push_subscriptions ───────────────────────────────────────
create table if not exists push_subscriptions (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null,
  endpoint        text not null unique,
  p256dh          text not null,
  auth            text not null,
  expiration_time timestamptz,
  active          boolean not null default true,
  last_status     text,
  created_at      timestamptz not null default now()
);
create index if not exists idx_subs_user on push_subscriptions (user_id, active);

-- ── notification_deliveries (날짜·기기 중복 발송 방지) ────────
create table if not exists notification_deliveries (
  id              uuid primary key default gen_random_uuid(),
  brief_date      date not null,
  subscription_id uuid not null references push_subscriptions (id) on delete cascade,
  status          text not null check (status in ('sent','failed','skipped')),
  attempts        int not null default 1,
  sent_at         timestamptz default now(),
  unique (brief_date, subscription_id)
);

-- ── user_preferences ─────────────────────────────────────────
create table if not exists user_preferences (
  user_id               uuid primary key,
  theme                 text not null default 'system' check (theme in ('light','dark','system')),
  favorite_categories   category[],
  notifications_enabled boolean not null default true,
  updated_at            timestamptz not null default now()
);
