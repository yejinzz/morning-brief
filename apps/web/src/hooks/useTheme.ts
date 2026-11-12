// 테마 (M3): light/dark/system. html.dark 클래스 토글 + localStorage.

import { useCallback, useEffect, useState } from 'react';

export type Theme = 'light' | 'dark' | 'system';
const KEY = 'mb.theme';

function systemPrefersDark(): boolean {
  return typeof matchMedia !== 'undefined' && matchMedia('(prefers-color-scheme: dark)').matches;
}

export function applyTheme(theme: Theme): void {
  const dark = theme === 'dark' || (theme === 'system' && systemPrefersDark());
  document.documentElement.classList.toggle('dark', dark);
}

function loadTheme(): Theme {
  const raw = (typeof localStorage !== 'undefined' && localStorage.getItem(KEY)) || 'system';
  return raw === 'light' || raw === 'dark' ? raw : 'system';
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => loadTheme());

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* ignore */
    }
    setThemeState(next);
  }, []);

  return { theme, setTheme };
}
