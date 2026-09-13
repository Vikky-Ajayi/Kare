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

/** Dispatched on `window` once a new service worker has taken control of
 * this page — i.e. a deploy happened and the running app is one activation
 * behind it. `UpdateToast` listens for this to offer a refresh; nothing
 * reloads on its own, since forcing that mid-consultation would be worse
 * than running one version behind for a few minutes. */
export const SW_UPDATE_EVENT = 'kare:update-ready';

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) return null;
  try {
    const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });

    // The new worker calls skipWaiting()+clients.claim() (see sw.js) as soon
    // as it installs, so `controllerchange` is the reliable "a new version
    // just took over" signal — covers the PWA being left open for days,
    // which a plain per-navigation SW check would miss.
    let notified = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (notified) return;
      notified = true;
      window.dispatchEvent(new CustomEvent(SW_UPDATE_EVENT));
    });

    // Installed PWAs don't reliably get a fresh navigation for a long time;
    // ask the browser to re-check the worker script periodically and
    // whenever the tab regains focus, instead of only on cold start.
    const check = () => reg.update().catch(() => {});
    setInterval(check, 60_000);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') check();
    });

    return reg;
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
