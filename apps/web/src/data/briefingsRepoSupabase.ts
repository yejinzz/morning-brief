// Supabase(PostgREST) 읽기 저장소 (M5, 결정 D-3=로그인 없음, anon 읽기).
// publishable key + anon RLS 로 'ready' 브리핑만 조회. 쓰기는 하지 않는다.

import type {
  ArticleCard,
  Briefing,
  BriefingStatus,
  Category,
  EvidenceBasis,
  Impact,
} from '@/types';
import { CATEGORIES } from '@/types';
import { SUPABASE_URL, supabaseHeaders } from '@/lib/env';
import type { BriefingsRepo } from './briefingsRepo';

// 임베디드 조회 select (brief + 조인된 기사/분석)
const SELECT =
  'brief_date,headline,collected_count,high_count,est_read_minutes,status,generated_at,' +
  'briefing_articles(display_order,is_high,category,' +
  'news_articles(id,title,source,canonical_url,published_at),' +
  'news_analyses(summary,rationale,dev_relevance,impact,evidence_basis))';

interface Row {
  brief_date: string;
  headline: string | null;
  collected_count: number;
  high_count: number;
  est_read_minutes: number | null;
  status: string;
  generated_at: string | null;
  briefing_articles: {
    display_order: number;
    is_high: boolean;
    category: string;
    news_articles: {
      id: string;
      title: string;
      source: string;
      canonical_url: string;
      published_at: string | null;
    } | null;
    news_analyses: {
      summary: string | null;
      rationale: string | null;
      dev_relevance: string | null;
      impact: string;
      evidence_basis: string;
    } | null;
  }[];
}

/** PostgREST row → Briefing (순수 함수, 테스트 대상). */
export function mapBriefingRow(row: Row): Briefing {
  const cards: ArticleCard[] = (row.briefing_articles ?? [])
    .filter((ba) => ba.news_articles)
    .map((ba) => ({
      id: ba.news_articles!.id,
      category: ba.category as Category,
      title: ba.news_articles!.title,
      summary: ba.news_analyses?.summary ?? null,
      rationale: ba.news_analyses?.rationale ?? null,
      dev_relevance: ba.news_analyses?.dev_relevance ?? null,
      source: ba.news_articles!.source,
      published_at: ba.news_articles!.published_at,
      url: ba.news_articles!.canonical_url,
      impact: (ba.news_analyses?.impact ?? 'HIGH') as Impact,
      evidence_basis: (ba.news_analyses?.evidence_basis ?? 'full') as EvidenceBasis,
      display_order: ba.display_order,
      is_high: ba.is_high,
    }))
    .sort(
      (a, b) =>
        CATEGORIES.indexOf(a.category) - CATEGORIES.indexOf(b.category) ||
        a.display_order - b.display_order,
    );
  return {
    brief_date: row.brief_date,
    headline: row.headline,
    collected_count: row.collected_count,
    high_count: row.high_count,
    est_read_minutes: row.est_read_minutes,
    status: row.status as BriefingStatus,
    generated_at: row.generated_at,
    articles: cards,
  };
}

async function pgGet(query: string): Promise<unknown[]> {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${query}`, { headers: supabaseHeaders() });
  if (!res.ok) throw new Error(`Supabase ${res.status}`);
  return (await res.json()) as unknown[];
}

export class SupabaseBriefingsRepo implements BriefingsRepo {
  async getByDate(date: string): Promise<Briefing | null> {
    const rows = (await pgGet(
      `daily_briefings?brief_date=eq.${date}&limit=1&select=${encodeURIComponent(SELECT)}`,
    )) as Row[];
    return rows[0] ? mapBriefingRow(rows[0]) : null;
  }

  async latestDate(): Promise<string | null> {
    const rows = (await pgGet(
      'daily_briefings?status=in.(ready,empty_high)&order=brief_date.desc&limit=1&select=brief_date',
    )) as { brief_date: string }[];
    return rows[0]?.brief_date ?? null;
  }

  async availableDates(): Promise<string[]> {
    const rows = (await pgGet(
      'daily_briefings?status=in.(ready,empty_high)&order=brief_date.desc&limit=90&select=brief_date',
    )) as { brief_date: string }[];
    return rows.map((r) => r.brief_date);
  }
}
