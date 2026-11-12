// 클라이언트 푸시 구독 (M5). VAPID 공개키로 구독 → Supabase push_subscriptions 에 저장(anon INSERT).

import { SUPABASE_URL, supabaseConfigured, supabaseHeaders } from './env';

/** VAPID 공개키(base64url) → Uint8Array(applicationServerKey). */
export function urlBase64ToUint8Array(base64: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const normalized = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(normalized);
  const out = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i += 1) out[i] = raw.charCodeAt(i);
  return out;
}

export const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY ?? '';

export function pushConfigured(): boolean {
  return VAPID_PUBLIC_KEY.length > 0 && supabaseConfigured();
}

/** 기기 식별자(로그인 없음 → 기기별 로컬 uuid). */
function deviceId(): string {
  const KEY = 'mb.device';
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

// 구독 저장: 플레인 INSERT. 중복(409)이면 PATCH 로 갱신.
// (anon 에는 SELECT 정책이 없어 ON CONFLICT upsert 가 RLS 로 막히므로 INSERT/UPDATE 분리)
async function saveSubscription(sub: PushSubscription): Promise<void> {
  const json = sub.toJSON();
  const keys = { p256dh: json.keys?.p256dh, auth: json.keys?.auth };
  const res = await fetch(`${SUPABASE_URL}/rest/v1/push_subscriptions`, {
    method: 'POST',
    headers: supabaseHeaders({ 'Content-Type': 'application/json', Prefer: 'return=minimal' }),
    body: JSON.stringify([{ user_id: deviceId(), endpoint: json.endpoint, ...keys, active: true }]),
  });
  if (res.ok) return;
  if (res.status === 409) {
    // 이미 등록된 endpoint → 활성화/키 갱신
    const q = `endpoint=eq.${encodeURIComponent(json.endpoint ?? '')}`;
    const patch = await fetch(`${SUPABASE_URL}/rest/v1/push_subscriptions?${q}`, {
      method: 'PATCH',
      headers: supabaseHeaders({ 'Content-Type': 'application/json', Prefer: 'return=minimal' }),
      body: JSON.stringify({ ...keys, active: true }),
    });
    if (!patch.ok) throw new Error(`구독 갱신 실패 ${patch.status}`);
    return;
  }
  throw new Error(`구독 저장 실패 ${res.status}`);
}

/** 서비스워커 등록 후 푸시 구독 + 서버 저장. 미구성/미지원이면 null. */
export async function subscribeToPush(): Promise<PushSubscription | null> {
  if (!pushConfigured() || !('serviceWorker' in navigator)) return null;
  const reg = await navigator.serviceWorker.ready;
  const existing = await reg.pushManager.getSubscription();
  const sub =
    existing ??
    (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
    }));
  await saveSubscription(sub);
  return sub;
}
