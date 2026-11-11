// 기사 카드. docs/06 §2.2: 제목·카테고리·요약·근거·출처·시각·원문·읽음. 뉴모피즘.

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
      className={`rounded-neu p-5 transition-opacity ${
        read ? 'neu-inset opacity-70' : 'neu-raised'
      }`}
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="neu-inset-sm rounded-full px-3 py-1 text-[11px] font-semibold text-mute-light dark:text-mute-dark">
          {CATEGORY_LABELS[card.category]}
        </span>
        <span className="flex items-center gap-2.5 text-[11px] text-mute-light dark:text-mute-dark">
          <span className="flex items-center gap-1 font-bold text-high">
            <span
              className="inline-block h-2 w-2 rounded-full bg-high"
              style={{ boxShadow: '0 0 6px rgba(239,90,71,0.7)' }}
              aria-hidden
            />
            HIGH
          </span>
          <time>{formatTime(card.published_at)}</time>
        </span>
      </div>

      <h2 className="text-[17px] font-bold leading-snug">{card.title}</h2>

      {card.summary && (
        <p className="mt-2 text-sm leading-relaxed text-ink-light/90 dark:text-ink-dark/90">
          {card.summary}
        </p>
      )}

      {card.rationale && (
        <p className="mt-3 rounded-2xl neu-inset-sm px-3.5 py-2.5 text-xs leading-relaxed text-mute-light dark:text-mute-dark">
          <span className="font-semibold text-high">근거</span> · {card.rationale}
        </p>
      )}

      {card.evidence_basis === 'title_desc_only' && (
        <p className="mt-1.5 text-[11px] text-mute-light dark:text-mute-dark">
          제목·설명 기반 분석
        </p>
      )}

      <div className="mt-4 flex items-center justify-between">
        <a
          href={card.url}
          target="_blank"
          rel="noreferrer noopener"
          className="text-xs font-semibold text-accent underline-offset-2 hover:underline"
        >
          {card.source} · 원문 보기 →
        </a>
        <button
          type="button"
          onClick={() => onToggleRead(card.id)}
          aria-pressed={read}
          className={`rounded-full px-3.5 py-1.5 text-xs transition-shadow duration-150 ${
            read
              ? 'neu-inset-sm font-semibold text-high'
              : 'neu-raised-sm text-mute-light dark:text-mute-dark'
          }`}
        >
          {read ? '✓ 읽음' : '읽음 표시'}
        </button>
      </div>
    </article>
  );
}
