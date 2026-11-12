// 브리핑 로딩 훅 (M3). 로딩/오류/로드 상태 관리.

import { useEffect, useState } from 'react';
import type { Briefing } from '@/types';
import { repo } from '@/data/briefingsRepo';

export type LoadState =
  | { status: 'loading' }
  | { status: 'error'; error: string }
  | { status: 'loaded'; briefing: Briefing | null };

export function useBriefing(date: string | null): LoadState {
  const [state, setState] = useState<LoadState>({ status: 'loading' });

  useEffect(() => {
    let active = true;
    setState({ status: 'loading' });
    const target = date ? Promise.resolve(date) : repo.latestDate().then((d) => d ?? '');
    target
      .then((d) => (d ? repo.getByDate(d) : Promise.resolve(null)))
      .then((briefing) => {
        if (active) setState({ status: 'loaded', briefing });
      })
      .catch((e: unknown) => {
        if (active) setState({ status: 'error', error: String(e) });
      });
    return () => {
      active = false;
    };
  }, [date]);

  return state;
}
