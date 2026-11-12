import type { ReactNode } from 'react';

// 플랫 틴트 칩(라벨·뱃지). 뉴모피즘 아님.
export function Chip({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={`rounded-full bg-black/5 px-2.5 py-0.5 text-[11px] font-medium text-mute-light dark:bg-white/10 dark:text-mute-dark ${className}`}
    >
      {children}
    </span>
  );
}
