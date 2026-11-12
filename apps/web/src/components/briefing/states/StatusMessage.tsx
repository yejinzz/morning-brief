// 상태 메시지 공통 레이아웃(가운데 정렬 플랫 텍스트). 상태 뷰들이 공유.

import type { ReactNode } from 'react';

export function StatusMessage({ children }: { children: ReactNode }) {
  return (
    <div className="px-6 py-16 text-center text-sm text-mute-light dark:text-mute-dark">
      {children}
    </div>
  );
}
