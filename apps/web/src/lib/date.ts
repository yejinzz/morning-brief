// 날짜·시각 포맷 (M3). 한국어 표기, 외부 라이브러리 없이 Intl 사용.

const WEEKDAY = new Intl.DateTimeFormat('ko-KR', { weekday: 'short' });

/** "2026-11-10" → "2026-11-10 (월)" */
export function formatBriefDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  if (!y || !m || !d) return iso;
  const date = new Date(y, m - 1, d);
  return `${iso} (${WEEKDAY.format(date)})`;
}

/** ISO datetime → "07:04" (KST 표기 가정, 입력이 +09:00 이면 그대로) */
export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Asia/Seoul',
  }).format(date);
}
