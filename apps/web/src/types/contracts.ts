// 공유 데이터 계약 (M0) — Python 쪽 services/news-pipeline/src/mb_pipeline/contracts.py 와 미러.
// 한쪽을 바꾸면 반드시 다른 쪽도 함께 갱신한다.
// 설계 근거: docs/05-database.md, docs/04-news-pipeline.md §6.3

export const CATEGORIES = ['domestic', 'economy', 'ai', 'dev', 'tech'] as const;
export type Category = (typeof CATEGORIES)[number];

export const CATEGORY_LABELS: Record<Category, string> = {
  domestic: '국내 시사',
  economy: '경제·국제',
  ai: 'AI·LLM',
  dev: '개발·인프라',
  tech: '기타 테크',
};

export type Impact = 'HIGH' | 'MEDIUM' | 'LOW';
export type EvidenceBasis = 'full' | 'title_desc_only';
export type BriefingStatus = 'generating' | 'ready' | 'failed' | 'empty_high';

// PWA 카드 1건 (기본 노출은 HIGH 만)
export interface ArticleCard {
  id: string;
  category: Category;
  title: string;
  summary?: string | null;
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
