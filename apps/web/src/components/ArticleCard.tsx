// 기사 카드 (M3). docs/06 §2.2: 제목·카테고리·요약·근거·출처·시각·원문·읽음.

import { CATEGORY_LABELS, type ArticleCard as Card } from '../types/contracts';
import { formatTime } from '../lib/date';

interface Props {
  card: Card;
  read: boolean;
  onToggleRead: (id: string) => void;
}

export function ArticleCard({ card, read, onToggleRead }: Props) {
  return (
    <article
      className={`rounded-lg border border-slate-200 p-4 dark:border-slate-800 ${
        read ? 'opacity-60' : ''
      }`}
    >
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          {CATEGORY_LABELS[card.category]}
        </span>
        <span className="flex items-center gap-2">
          <span className="font-semibold text-high">● HIGH</span>
          <time>{formatTime(card.published_at)}</time>
        </span>
      </div>

      <h2 className="text-base font-semibold leading-snug">{card.title}</h2>

      {card.summary && (
        <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{card.summary}</p>
      )}

      {card.rationale && (
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          <span aria-hidden>💡 </span>
          HIGH 근거: {card.rationale}
        </p>
      )}

      {card.evidence_basis === 'title_desc_only' && (
        <p className="mt-1 text-[11px] text-slate-400">제목·설명 기반 분석</p>
      )}

      <div className="mt-3 flex items-center justify-between text-xs">
        <a
          href={card.url}
          target="_blank"
          rel="noreferrer noopener"
          className="font-medium text-blue-600 underline-offset-2 hover:underline dark:text-blue-400"
        >
          {card.source} · 원문 보기 →
        </a>
        <button
          type="button"
          onClick={() => onToggleRead(card.id)}
          className="rounded px-2 py-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-pressed={read}
        >
          {read ? '✓ 읽음' : '읽음 표시'}
        </button>
      </div>
    </article>
  );
}
