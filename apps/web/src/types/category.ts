// 카테고리 타입·상수. Python 쪽 mb_pipeline/contracts.py 와 미러.

export const CATEGORIES = ['domestic', 'economy', 'ai', 'dev', 'tech'] as const;
export type Category = (typeof CATEGORIES)[number];

export const CATEGORY_LABELS: Record<Category, string> = {
  domestic: '국내 시사',
  economy: '경제·국제',
  ai: 'AI·LLM',
  dev: '개발·인프라',
  tech: '기타 테크',
};
