// 탭/필터 로직 (M3). 순수 함수 → 테스트 용이.

import { CATEGORIES, type ArticleCard, type Category } from '@/types';

export type Tab = 'all' | Category;

export const TABS: { key: Tab; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'domestic', label: '국내 시사' },
  { key: 'economy', label: '경제·국제' },
  { key: 'ai', label: 'AI·LLM' },
  { key: 'dev', label: '개발·인프라' },
  { key: 'tech', label: '기타 테크' },
];

/** 선택 탭 기준 카드 필터(전체 탭은 그대로). display_order 는 카테고리 내 순서. */
export function filterByTab(cards: ArticleCard[], tab: Tab): ArticleCard[] {
  if (tab === 'all') return cards;
  return cards.filter((c) => c.category === tab);
}

/** 카테고리별 HIGH 건수(탭 뱃지용). */
export function categoryCounts(cards: ArticleCard[]): Record<Category, number> {
  const counts = Object.fromEntries(CATEGORIES.map((c) => [c, 0])) as Record<Category, number>;
  for (const card of cards) counts[card.category] += 1;
  return counts;
}
