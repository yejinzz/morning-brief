// 설정 화면 (M3). 테마 · 알림(권한/설치 안내, 구독은 M4) · 정보.

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTheme, type Theme } from '../lib/theme';
import { pushConfigured, subscribeToPush } from '../lib/push';

const THEMES: { key: Theme; label: string }[] = [
  { key: 'system', label: '시스템' },
  { key: 'light', label: '라이트' },
  { key: 'dark', label: '다크' },
];

function isStandalone(): boolean {
  return typeof matchMedia !== 'undefined' && matchMedia('(display-mode: standalone)').matches;
}

export function SettingsRoute() {
  const { theme, setTheme } = useTheme();
  const [permission, setPermission] = useState<NotificationPermission | 'unsupported'>(
    typeof Notification !== 'undefined' ? Notification.permission : 'unsupported',
  );

  async function requestPush() {
    if (typeof Notification === 'undefined') return;
    const result = await Notification.requestPermission();
    setPermission(result);
    if (result === 'granted' && pushConfigured()) {
      // VAPID 공개키가 구성된 경우 구독 시도(서버 저장은 M5 Supabase 연동).
      try {
        await subscribeToPush();
      } catch {
        /* 구독 실패는 조용히 무시(권한만 유지) */
      }
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center gap-2">
        <Link
          to="/"
          aria-label="뒤로"
          className="rounded p-1 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          ←
        </Link>
        <h1 className="text-lg font-bold">설정</h1>
      </header>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-500">테마</h2>
        <div className="flex gap-2">
          {THEMES.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTheme(key)}
              aria-pressed={theme === key}
              className={`rounded-full px-3 py-1.5 text-sm ${
                theme === key
                  ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-500">알림</h2>
        {permission === 'unsupported' ? (
          <p className="text-sm text-slate-500">이 브라우저는 알림을 지원하지 않습니다.</p>
        ) : permission === 'granted' ? (
          <p className="text-sm text-slate-500">알림이 허용되었습니다. (구독 연결은 다음 단계)</p>
        ) : (
          <button
            type="button"
            onClick={requestPush}
            className="rounded bg-blue-600 px-3 py-2 text-sm text-white"
          >
            알림 받기
          </button>
        )}
        {!isStandalone() && (
          <p className="mt-2 text-xs text-slate-400">
            iOS에서는 공유 → “홈 화면에 추가”로 설치한 뒤에만 푸시를 받을 수 있습니다 (iOS 16.4+).
          </p>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-500">정보</h2>
        <p className="text-xs text-slate-400">
          Morning Brief · 월 운영비 0원 목표. 정확한 07:00 실행은 무료 플랫폼 제약으로 보장되지
          않습니다.
        </p>
      </section>
    </div>
  );
}
