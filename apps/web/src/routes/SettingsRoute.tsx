// 설정 화면: 테마 · 알림 · 정보. 뉴모피즘.

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

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-3 px-1 text-xs font-semibold uppercase tracking-widest text-mute-light dark:text-mute-dark">
        {title}
      </h2>
      {children}
    </section>
  );
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
      try {
        await subscribeToPush();
      } catch {
        /* 구독 실패는 조용히 무시(권한만 유지) */
      }
    }
  }

  return (
    <div className="space-y-7">
      <header className="flex items-center gap-3">
        <Link
          to="/"
          aria-label="뒤로"
          className="neu-btn flex h-11 w-11 items-center justify-center text-lg text-mute-light dark:text-mute-dark"
        >
          ←
        </Link>
        <h1 className="text-xl font-bold tracking-tight">설정</h1>
      </header>

      <Section title="테마">
        <div className="flex gap-2.5">
          {THEMES.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setTheme(key)}
              aria-pressed={theme === key}
              className={`rounded-full px-4 py-2 text-sm transition-shadow duration-150 ${
                theme === key
                  ? 'neu-inset font-semibold text-high'
                  : 'neu-raised-sm text-mute-light dark:text-mute-dark'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </Section>

      <Section title="알림">
        {permission === 'unsupported' ? (
          <p className="neu-inset rounded-neu px-4 py-3 text-sm text-mute-light dark:text-mute-dark">
            이 브라우저는 알림을 지원하지 않아요.
          </p>
        ) : permission === 'granted' ? (
          <p className="neu-inset rounded-neu px-4 py-3 text-sm text-mute-light dark:text-mute-dark">
            알림이 켜져 있어요. 매일 아침 브리핑을 보내드릴게요.
          </p>
        ) : (
          <button
            type="button"
            onClick={requestPush}
            className="neu-btn w-full px-4 py-3.5 text-sm font-semibold text-high"
          >
            알림 받기
          </button>
        )}
        {!isStandalone() && (
          <p className="mt-3 px-1 text-xs leading-relaxed text-mute-light dark:text-mute-dark">
            iOS는 공유 → “홈 화면에 추가”로 설치한 뒤에만 알림을 받을 수 있어요 (iOS 16.4+).
          </p>
        )}
      </Section>

      <Section title="정보">
        <p className="neu-inset rounded-neu px-4 py-3 text-xs leading-relaxed text-mute-light dark:text-mute-dark">
          Morning Brief — 매일 아침 AI가 선별하는 뉴스 브리핑. 월 운영비 0원을 목표로 하며, 정확한
          07:00 실행은 무료 플랫폼 특성상 보장되지 않아요.
        </p>
      </Section>
    </div>
  );
}
