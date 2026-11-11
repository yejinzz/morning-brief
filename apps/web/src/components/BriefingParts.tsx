// 브리핑 상단 요소: 헤더, 한 줄 브리핑(히어로), 통계. 뉴모피즘.

import { Link } from 'react-router-dom';
import type { Briefing } from '../types/contracts';
import { formatBriefDate, formatTime } from '../lib/date';

export function BriefingHeader({ briefing }: { briefing: Briefing }) {
  return (
    <header className="flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold tracking-tight">{formatBriefDate(briefing.brief_date)}</h1>
        {briefing.generated_at && (
          <p className="mt-0.5 text-xs text-mute-light dark:text-mute-dark">
            {formatTime(briefing.generated_at)} 생성 완료
          </p>
        )}
      </div>
      <Link
        to="/settings"
        className="neu-btn flex h-11 w-11 items-center justify-center text-mute-light dark:text-mute-dark"
        aria-label="설정"
      >
        ⚙️
      </Link>
    </header>
  );
}

// 히어로(시그니처): 오늘의 한 줄 브리핑 — 솟은 명판 + 일출 코랄 악센트
export function OneLiner({ text }: { text: string }) {
  return (
    <section className="neu-raised relative overflow-hidden rounded-neu p-5">
      <span
        aria-hidden
        className="absolute left-0 top-0 h-full w-1.5 bg-high"
        style={{ boxShadow: '0 0 12px rgba(239,90,71,0.5)' }}
      />
      <p className="pl-3 text-[13px] font-semibold uppercase tracking-widest text-high">Today</p>
      <p className="mt-1.5 pl-3 text-[17px] font-semibold leading-relaxed">{text}</p>
    </section>
  );
}

export function StatsBar({ briefing }: { briefing: Briefing }) {
  const items = [
    { label: '수집', value: String(briefing.collected_count) },
    { label: 'HIGH', value: String(briefing.high_count) },
    ...(briefing.est_read_minutes
      ? [{ label: '읽기', value: `${briefing.est_read_minutes}분` }]
      : []),
  ];
  return (
    <div className="neu-inset flex items-center justify-around rounded-neu px-4 py-3">
      {items.map((it) => (
        <div key={it.label} className="flex flex-col items-center">
          <span className="text-base font-bold tabular-nums">{it.value}</span>
          <span className="text-[11px] text-mute-light dark:text-mute-dark">{it.label}</span>
        </div>
      ))}
    </div>
  );
}
