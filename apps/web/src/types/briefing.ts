// 브리핑 데이터 계약. Python 쪽 mb_pipeline/contracts.py 와 미러(한쪽 변경 시 함께 갱신).

import type { Category } from './category';

export type Impact = 'HIGH' | 'MEDIUM' | 'LOW';
export type EvidenceBasis = 'full' | 'title_desc_only';
export type BriefingStatus = 'generating' | 'ready' | 'failed' | 'empty_high';

// PWA 카드 1건 (기본 노출은 HIGH 만)
export interface ArticleCard {
  id: string;
  category: Category;
  title: string;
  summary?: string | null;
  keywords?: string[];
  rationale?: string | null;
  dev_relevance?: string | null;
  source: string;
  published_at?: string | null; // ISO datetime
  url: string;
  impact: Impact;
  evidence_basis: EvidenceBasis;
  display_order: number;
  is_high: boolean;
}

// 날짜별 브리핑 응답 — PWA 가 소비하는 최상위 계약
export interface Briefing {
  brief_date: string; // KST ISO date (YYYY-MM-DD)
  headline?: string | null;
  collected_count: number;
  high_count: number;
  est_read_minutes?: number | null;
  status: BriefingStatus;
  generated_at?: string | null;
  articles: ArticleCard[];
}

// 선정 규칙 상수 (docs/04 §7)
export const MAX_PER_CATEGORY = 3;
export const MAX_TOTAL = 15;
