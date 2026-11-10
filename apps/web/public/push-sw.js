// Web Push 핸들러 (M5). 생성된 서비스워커가 importScripts 로 포함.
// 배치 페이로드: { title, body, url, date }. url 은 앱 경로(예: /d/2026-11-10).

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = {};
  }
  const title = data.title || 'Morning Brief';
  const options = {
    body: data.body || '오늘의 브리핑이 준비되었습니다.',
    tag: data.date || 'morning-brief',
    data: { url: data.url || '/' },
    badge: undefined,
    icon: undefined,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const rel = (event.notification.data && event.notification.data.url) || '/';
  // 스코프(예: https://host/morning-brief/) 기준으로 딥링크 해석
  const target = new URL(rel.replace(/^\//, ''), self.registration.scope).href;
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if (w.url.startsWith(self.registration.scope) && 'focus' in w) {
          w.navigate(target);
          return w.focus();
        }
      }
      return self.clients.openWindow(target);
    }),
  );
});
