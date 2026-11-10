import { describe, expect, it } from 'vitest';
import type { ArticleCard } from '../types/contracts';
import { categoryCounts, filterByTab } from './tabs';

function card(id: string, category: ArticleCard['category']): ArticleCard {
  return {
    id,
    category,
    title: `t-${id}`,
    source: 'S',
    url: 'https://ex.com',
    impact: 'HIGH',
    evidence_basis: 'full',
    display_order: 1,
    is_high: true,
  };
}

const cards = [card('1', 'ai'), card('2', 'ai'), card('3', 'dev')];

describe('tabs', () => {
  it('filterByTab: 전체는 그대로, 카테고리는 필터', () => {
    expect(filterByTab(cards, 'all')).toHaveLength(3);
    expect(filterByTab(cards, 'ai').map((c) => c.id)).toEqual(['1', '2']);
    expect(filterByTab(cards, 'economy')).toHaveLength(0);
  });

  it('categoryCounts: 카테고리별 건수', () => {
    const counts = categoryCounts(cards);
    expect(counts.ai).toBe(2);
    expect(counts.dev).toBe(1);
    expect(counts.economy).toBe(0);
  });
});
