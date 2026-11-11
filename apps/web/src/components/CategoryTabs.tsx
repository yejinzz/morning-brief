// 카테고리 탭 (M3). 전체 + 5개. HIGH 건수 뱃지.

import { type Category } from '../types/contracts';
import { TABS, type Tab } from '../lib/tabs';

interface Props {
  active: Tab;
  counts: Record<Category, number>;
  onSelect: (tab: Tab) => void;
}

export function CategoryTabs({ active, counts, onSelect }: Props) {
  return (
    <nav className="-mx-5 overflow-x-auto px-5 py-1" aria-label="카테고리">
      <ul className="flex gap-2.5 whitespace-nowrap">
        {TABS.map(({ key, label }) => {
          const count = key === 'all' ? undefined : counts[key];
          const isActive = key === active;
          return (
            <li key={key}>
              <button
                type="button"
                onClick={() => onSelect(key)}
                aria-current={isActive ? 'page' : undefined}
                className={`rounded-full px-4 py-2 text-sm transition-shadow duration-150 ${
                  isActive
                    ? 'neu-inset font-semibold text-high'
                    : 'neu-raised-sm text-mute-light dark:text-mute-dark'
                }`}
              >
                {label}
                {count !== undefined && count > 0 && (
                  <span className="ml-1.5 text-xs font-semibold text-high">{count}</span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
