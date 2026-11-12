-- 0003_keywords.sql — 분석 결과에 핵심 키워드 추가 (요약 강화)
-- 비파괴적: nullable + 기본값 '{}'. 기존 행은 빈 배열로 채워지고, 웹은 칩 미표시(하위호환).
-- Supabase SQL Editor 에서 1회 실행.

alter table news_analyses
  add column if not exists keywords text[] not null default '{}';
