// 브리핑 상단 헤더: 날짜·생성시각 + 설정 진입.

import type { Briefing } from '@/types';
import { formatBriefDate, formatTime } from '@/lib/date';
import { IconButton } from '@/components/ui';

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
      <IconButton label="설정" to="/settings">
        ⚙️
      </IconButton>
    </header>
  );
}
