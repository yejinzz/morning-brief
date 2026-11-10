// 브리핑 상단 요소 (M3): 헤더, 한 줄 브리핑, 통계 바.

import { Link } from 'react-router-dom';
import type { Briefing } from '../types/contracts';
import { formatBriefDate, formatTime } from '../lib/date';

export function BriefingHeader({ briefing }: { briefing: Briefing }) {
  return (
    <header className="flex items-center justify-between">
      <div>
        <h1 className="text-lg font-bold">{formatBriefDate(briefing.brief_date)}</h1>
        {briefing.generated_at && (
          <p className="text-xs text-slate-500">{formatTime(briefing.generated_at)} 생성 완료</p>
        )}
      </div>
      <Link
        to="/settings"
        className="rounded p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
        aria-label="설정"
      >
        ⚙️
      </Link>
    </header>
  );
}

export function OneLiner({ text }: { text: string }) {
  return <p className="rounded-lg bg-slate-50 p-3 text-sm font-medium dark:bg-slate-900">{text}</p>;
}

export function StatsBar({ briefing }: { briefing: Briefing }) {
  return (
    <p className="text-xs text-slate-500">
      수집 {briefing.collected_count} · HIGH {briefing.high_count}
      {briefing.est_read_minutes ? ` · 약 ${briefing.est_read_minutes}분` : ''}
    </p>
  );
}
