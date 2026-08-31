/* JAYUMINTON_MEMBER_PWA_SW_V1
   Pass-through only. The rest of this site is served with
   Cache-Control: no-store on every response by design (state changes
   constantly), so this worker must never cache -- it exists solely to
   satisfy the browser's PWA installability requirement.
*/
self.addEventListener('install', function () {
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function (event) {
  event.respondWith(fetch(event.request));
});
