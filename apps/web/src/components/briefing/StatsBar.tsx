// 통계 — 플랫 텍스트 한 줄(박스 없음).

import type { Briefing } from '@/types';

export function StatsBar({ briefing }: { briefing: Briefing }) {
  const items = [
    { label: '수집', value: String(briefing.collected_count) },
    { label: 'HIGH', value: String(briefing.high_count) },
    ...(briefing.est_read_minutes
      ? [{ label: '읽기', value: `${briefing.est_read_minutes}분` }]
      : []),
  ];
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 px-1 text-xs text-mute-light dark:text-mute-dark">
      {items.map((it) => (
        <span key={it.label}>
          <span className="font-bold tabular-nums text-ink-light dark:text-ink-dark">
            {it.value}
          </span>{' '}
          {it.label}
        </span>
      ))}
    </div>
  );
}
