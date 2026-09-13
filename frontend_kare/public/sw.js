/* Kare service worker — Web Push + install/update plumbing.
 *
 * Deliberately does NO asset caching (no cache-first fetch strategy): this
 * app has no offline mode, and a caching layer is exactly what causes a PWA
 * to keep serving old code after a deploy. skipWaiting()/clients.claim()
 * below make a new version take over as fast as the platform allows; the
 * client side (registerServiceWorker in services/notifications.ts) listens
 * for that handover and tells the running app to offer a refresh.
 */
const SHELL = "kare-shell-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

/* No-op network passthrough. Present (rather than omitted) because some
 * browsers' install-eligibility checks look for a fetch handler; it must
 * never call respondWith — that's how we guarantee this worker can't ever
 * serve a stale cached response. */
self.addEventListener("fetch", () => {});

/* Proactive check-in arrives */
self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { title: "Kare", body: event.data ? event.data.text() : "" };
  }
  const title = data.title || "Kare";
  const options = {
    body: data.body || "",
    tag: data.tag || "kare",
    renotify: true,
    icon: "/icons/icon-192.png",
    badge: "/icons/badge-72.png",
    data: { url: data.url || "/dashboard" },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

/* Tapping the notification reopens the exact conversation */
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/dashboard";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      return self.clients.openWindow(url);
    })
  );
});
