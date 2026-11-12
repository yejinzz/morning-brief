// 로딩: 카드 스켈레톤 3개.

import { Skeleton } from '@/components/ui';

export function LoadingView() {
  return (
    <div className="space-y-5" aria-busy="true" aria-label="불러오는 중">
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="h-28" />
      ))}
    </div>
  );
}
