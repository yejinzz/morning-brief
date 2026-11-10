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
    <nav className="-mx-4 overflow-x-auto px-4" aria-label="카테고리">
      <ul className="flex gap-1 whitespace-nowrap">
        {TABS.map(({ key, label }) => {
          const count = key === 'all' ? undefined : counts[key];
          const isActive = key === active;
          return (
            <li key={key}>
              <button
                type="button"
                onClick={() => onSelect(key)}
                aria-current={isActive ? 'page' : undefined}
                className={`rounded-full px-3 py-1.5 text-sm ${
                  isActive
                    ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
                }`}
              >
                {label}
                {count !== undefined && count > 0 && (
                  <span className="ml-1 text-xs opacity-80">{count}</span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
