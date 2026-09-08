/* Kare service worker — Web Push + app-shell cache. */
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
