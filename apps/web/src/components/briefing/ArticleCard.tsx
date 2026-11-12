// 기사 카드 — 글래스 카드(콘텐츠) + 카테고리 칩 + 읽음 토글.

import type { ArticleCard as Card } from '@/types';
import { CATEGORY_LABELS } from '@/types';
import { formatTime } from '@/lib/date';
import { Card as Surface, Chip } from '@/components/ui';

interface Props {
  card: Card;
  read: boolean;
  onToggleRead: (id: string) => void;
}

export function ArticleCard({ card, read, onToggleRead }: Props) {
  return (
    <Surface as="article" className={`p-5 transition-opacity ${read ? 'opacity-55' : ''}`}>
      <div className="mb-2 flex items-center justify-between">
        <Chip>{CATEGORY_LABELS[card.category]}</Chip>
        <span className="flex items-center gap-2.5 text-[11px] text-mute-light dark:text-mute-dark">
          <span className="flex items-center gap-1 font-bold text-accent">
            <span
              className="accent-glow inline-block h-1.5 w-1.5 rounded-full bg-accent"
              aria-hidden
            />
            HIGH
          </span>
          <time>{formatTime(card.published_at)}</time>
        </span>
      </div>

      <h2 className="text-[17px] font-bold leading-snug">{card.title}</h2>

      {card.summary && (
        <p className="mt-2 text-sm leading-relaxed text-ink-light/85 dark:text-ink-dark/85">
          {card.summary}
        </p>
      )}

      {card.rationale && (
        <p className="mt-2.5 text-xs leading-relaxed text-mute-light dark:text-mute-dark">
          <span className="font-semibold text-accent">근거</span> {card.rationale}
        </p>
      )}

      {card.evidence_basis === 'title_desc_only' && (
        <p className="mt-1.5 text-[11px] text-mute-light dark:text-mute-dark">
          제목·설명 기반 분석
        </p>
      )}

      <div className="mt-4 flex items-center justify-between border-t border-[var(--hairline)] pt-3">
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
          className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
            read
              ? 'bg-black/5 font-semibold text-accent dark:bg-white/10'
              : 'bg-black/5 text-mute-light hover:bg-black/10 dark:bg-white/10 dark:text-mute-dark'
          }`}
        >
          {read ? '✓ 읽음' : '읽음'}
        </button>
      </div>
    </Surface>
  );
}
