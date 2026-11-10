// Supabase 공개 설정(읽기·구독 공용). publishable key + 정규화된 origin.

function toOrigin(u: string): string {
  const s = u.trim();
  try {
    const p = new globalThis.URL(s);
    return `${p.protocol}//${p.host}`;
  } catch {
    return s.replace(/\/+$/, '');
  }
}

export const SUPABASE_URL = toOrigin(import.meta.env.VITE_SUPABASE_URL ?? '');
export const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? '';

export function supabaseConfigured(): boolean {
  return SUPABASE_URL.length > 0 && SUPABASE_KEY.length > 0;
}

export function supabaseHeaders(extra?: Record<string, string>): Record<string, string> {
  return { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, ...extra };
}
