// 클라이언트 푸시 구독 (M4). VAPID 공개키로 구독 → 서버 저장(저장은 M5 Supabase 연동).

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
  return VAPID_PUBLIC_KEY.length > 0;
}

/** 서비스워커 등록 후 푸시 구독. VAPID 키/SW 가 없으면 null. */
export async function subscribeToPush(): Promise<PushSubscription | null> {
  if (!pushConfigured() || !('serviceWorker' in navigator)) return null;
  const reg = await navigator.serviceWorker.ready;
  const existing = await reg.pushManager.getSubscription();
  if (existing) return existing;
  return reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
  });
  // TODO(M5): 구독 결과를 Supabase push_subscriptions 에 저장(anon+세션).
}
