const CACHE_NAME = "tmh-ui-v20260328-r1";
const APP_SHELL = [
  "/ui/",
  "/ui/index.html",
  "/ui/app.css",
  "/ui/app.js",
  "/ui/manifest.webmanifest",
  "/ui/icon.svg",
  "/ui/icon-maskable.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const url = new URL(event.request.url);
  const isUiAsset = url.origin === self.location.origin && url.pathname.startsWith("/ui/");

  if (!isUiAsset) {
    return;
  }

  const isDocumentRequest =
    event.request.mode === "navigate" ||
    url.pathname === "/ui/" ||
    url.pathname.endsWith("/index.html");

  if (isDocumentRequest) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const cloned = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put("/ui/index.html", cloned));
          return response;
        })
        .catch(async () => {
          const cache = await caches.open(CACHE_NAME);
          return cache.match("/ui/index.html");
        }),
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).then((response) => {
        const cloned = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cloned));
        return response;
      });
    }),
  );
});
