// 읽음 상태 (M3, 결정 D-2: 로컬 저장). localStorage 기반, 오프라인 동작.

import { useCallback, useState } from 'react';

const KEY = 'mb.read';

function load(): Set<string> {
  try {
    const raw = localStorage.getItem(KEY);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

function save(ids: Set<string>): void {
  try {
    localStorage.setItem(KEY, JSON.stringify([...ids]));
  } catch {
    // 저장 실패는 조용히 무시(사생활 모드 등)
  }
}

export function useReadState() {
  const [ids, setIds] = useState<Set<string>>(() => load());

  const isRead = useCallback((id: string) => ids.has(id), [ids]);

  const toggle = useCallback((id: string) => {
    setIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      save(next);
      return next;
    });
  }, []);

  const markRead = useCallback((id: string) => {
    setIds((prev) => {
      if (prev.has(id)) return prev;
      const next = new Set(prev);
      next.add(id);
      save(next);
      return next;
    });
  }, []);

  return { isRead, toggle, markRead };
}
