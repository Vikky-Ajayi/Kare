/**
 * Web Push subscription flow for Kare's proactive check-ins.
 *
 *   await enableCheckIns()   // asks permission, subscribes, tells the backend
 *   await disableCheckIns()  // unsubscribes this device
 */
import { api } from './api';

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

export function pushSupported(): boolean {
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) return null;
  try {
    return await navigator.serviceWorker.register('/sw.js', { scope: '/' });
  } catch (e) {
    console.warn('SW registration failed', e);
    return null;
  }
}

export async function enableCheckIns(): Promise<'ok' | 'denied' | 'unsupported'> {
  if (!pushSupported()) return 'unsupported';

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return 'denied';

  const reg = (await navigator.serviceWorker.ready) as ServiceWorkerRegistration;
  const { data } = await api.get('/notifications/vapid-key');
  const sub =
    (await reg.pushManager.getSubscription()) ||
    (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(data.public_key),
    }));

  const json = sub.toJSON();
  await api.post('/notifications/subscribe', {
    endpoint: json.endpoint,
    keys: json.keys,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  return 'ok';
}

export async function disableCheckIns(): Promise<void> {
  const reg = await navigator.serviceWorker.getRegistration();
  const sub = await reg?.pushManager.getSubscription();
  if (sub) {
    await api.post('/notifications/unsubscribe', { endpoint: sub.endpoint }).catch(() => {});
    await sub.unsubscribe().catch(() => {});
  }
  await api.patch('/notifications/preferences', { followups_enabled: false }).catch(() => {});
}

/** Call on app load when arriving from a notification: /dashboard/voice?c=<id>&f=<id> */
export async function ackFollowupClick(): Promise<{ conversationId?: string }> {
  const params = new URLSearchParams(window.location.search);
  const f = params.get('f');
  const c = params.get('c') || undefined;
  if (f) await api.post(`/notifications/followups/${f}/clicked`).catch(() => {});
  return { conversationId: c };
}
