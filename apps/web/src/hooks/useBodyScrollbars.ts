// 페이지(body) 스크롤을 호버 시에만 보이는 오버레이 스크롤바로 초기화하는 훅.

import { useEffect } from 'react';
import { useOverlayScrollbars } from 'overlayscrollbars-react';

export function useBodyScrollbars() {
  const [initialize, getInstance] = useOverlayScrollbars({
    defer: true,
    options: {
      scrollbars: {
        theme: 'os-theme-dark',
        autoHide: 'leave', // 호버 시 표시, 벗어나면 숨김
        autoHideDelay: 250,
      },
    },
  });

  useEffect(() => {
    initialize({
      target: document.body,
      // OS가 오버레이/자동숨김 네이티브 스크롤바여도 강제 초기화
      cancel: { nativeScrollbarsOverlaid: false },
    });
    // StrictMode 이중 마운트/언마운트 대비: 정리 시 인스턴스 파괴
    return () => getInstance()?.destroy();
  }, [initialize, getInstance]);
}
