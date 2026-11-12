// 카테고리 탭. 전체 + 5개. HIGH 건수 뱃지. 가로 오버레이 스크롤(호버 시 표시).

import { OverlayScrollbarsComponent } from 'overlayscrollbars-react';
import type { Category } from '@/types';
import { TABS, type Tab } from '@/lib/tabs';
import { PillButton } from '@/components/ui';

interface Props {
  active: Tab;
  counts: Record<Category, number>;
  onSelect: (tab: Tab) => void;
}

export function CategoryTabs({ active, counts, onSelect }: Props) {
  return (
    <OverlayScrollbarsComponent
      element="nav"
      aria-label="카테고리"
      className="-mx-5 px-5"
      defer
      options={{
        scrollbars: { theme: 'os-theme-dark', autoHide: 'leave', autoHideDelay: 250 },
        overflow: { y: 'hidden' }, // 가로만 스크롤
      }}
    >
      {/* pt: 솟은 버튼 그림자 여백 · pb: 스크롤바가 버튼과 안 겹치게 */}
      <ul className="flex gap-2.5 whitespace-nowrap pb-3 pt-1">
        {TABS.map(({ key, label }) => {
          const count = key === 'all' ? undefined : counts[key];
          const isActive = key === active;
          return (
            <li key={key}>
              <PillButton
                active={isActive}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => onSelect(key)}
              >
                {label}
                {count !== undefined && count > 0 && (
                  <span className="ml-1.5 text-xs font-semibold text-accent">{count}</span>
                )}
              </PillButton>
            </li>
          );
        })}
      </ul>
    </OverlayScrollbarsComponent>
  );
}
