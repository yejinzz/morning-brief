import { describe, expect, it } from 'vitest';
import { mapBriefingRow } from './briefingsRepoSupabase';

const row = {
  brief_date: '2026-11-10',
  headline: '오늘의 요약',
  collected_count: 10,
  high_count: 2,
  est_read_minutes: 3,
  status: 'ready',
  generated_at: '2026-11-10T07:04:00+09:00',
  briefing_articles: [
    {
      display_order: 1,
      is_high: true,
      category: 'dev',
      news_articles: {
        id: 'a2',
        title: '개발 뉴스',
        source: 'HN',
        canonical_url: 'https://ex.com/a2',
        published_at: null,
      },
      news_analyses: {
        summary: '요약2',
        rationale: '근거2',
        dev_relevance: '관련',
        impact: 'HIGH',
        evidence_basis: 'title_desc_only',
      },
    },
    {
      display_order: 1,
      is_high: true,
      category: 'ai',
      news_articles: {
        id: 'a1',
        title: 'AI 뉴스',
        source: 'GN',
        canonical_url: 'https://ex.com/a1',
        published_at: '2026-11-10T00:00:00+09:00',
      },
      news_analyses: {
        summary: '요약1',
        keywords: ['키워드A', '키워드B'],
        rationale: '근거1',
        dev_relevance: '해당 없음',
        impact: 'HIGH',
        evidence_basis: 'full',
      },
    },
  ],
};

describe('mapBriefingRow', () => {
  it('헤더와 카드를 매핑하고 카테고리 순서로 정렬한다', () => {
    const b = mapBriefingRow(row);
    expect(b.status).toBe('ready');
    expect(b.high_count).toBe(2);
    // ai 가 dev 보다 앞(CATEGORIES 순서: domestic,economy,ai,dev,tech)
    expect(b.articles.map((c) => c.id)).toEqual(['a1', 'a2']);
    expect(b.articles[0].summary).toBe('요약1');
    expect(b.articles[0].keywords).toEqual(['키워드A', '키워드B']);
    expect(b.articles[0].evidence_basis).toBe('full');
  });

  it('조인 누락(news_articles=null)은 카드에서 제외한다', () => {
    const broken = {
      ...row,
      briefing_articles: [{ ...row.briefing_articles[0], news_articles: null }],
    };
    expect(mapBriefingRow(broken).articles).toHaveLength(0);
  });
});
