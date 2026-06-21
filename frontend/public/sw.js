// Domestique service worker — offline shell cache + web push (PRD §10).
const CACHE = "domestique-v1";
const SHELL = ["/", "/index.html", "/manifest.webmanifest", "/icon.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Network-first for API, cache-first for the shell.
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith("/api")) return; // always live
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});

// Deadline push notifications.
self.addEventListener("push", (e) => {
  const data = e.data ? e.data.json() : {};
  e.waitUntil(
    self.registration.showNotification(data.title || "Domestique", {
      body: data.body || "Stage deadline approaching.",
      icon: "/icon.svg",
      badge: "/icon.svg",
    })
  );
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  e.waitUntil(self.clients.openWindow("/"));
});
