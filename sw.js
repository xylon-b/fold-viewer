// 펼침 뷰어: works offline after the first visit
const CACHE = "fold-viewer-231658a7";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png",
  "lib/pdf.min.js", "lib/pdf.worker.min.js", "lib/jszip.min.js"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.protocol === "blob:" || url.protocol === "data:") return;
  // the page itself: network first so updates arrive, cache when offline
  if (e.request.mode === "navigate") {
    e.respondWith(fetch(e.request).then((r) => { const c = r.clone(); caches.open(CACHE).then((k) => k.put("index.html", c)); return r; })
      .catch(() => caches.match("index.html")));
    return;
  }
  // everything else (libraries, fonts): cache first
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then((r) => {
    if (r.ok || r.type === "opaque") { const c = r.clone(); caches.open(CACHE).then((k) => k.put(e.request, c)); }
    return r;
  })));
});
