const JAYUMINTON_SW_VERSION = '1.6.37-fix1';
const JAYUMINTON_CACHE = 'jayuminton-shell-v211';
const JAYUMINTON_SHELL = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/setup-v205.css',
  '/setup-v205.js',
  '/config-v204.js',
  '/icon-198.png',
  '/icon-512.png',
  '/apple-touch-icon-180.png',
  '/badge-96.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(JAYUMINTON_CACHE);
    await Promise.all(JAYUMINTON_SHELL.map(async (url) => {
      try { await cache.add(new Request(url, {cache:'reload'})); } catch (_) {}
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key !== JAYUMINTON_CACHE).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (event.request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const response = await fetch(event.request);
        const cache = await caches.open(JAYUMINTON_CACHE);
        cache.put('/index.html', response.clone()).catch(() => {});
        return response;
      } catch (_) {
        return (await caches.match('/index.html')) || Response.error();
      }
    })());
    return;
  }
  event.respondWith((async () => {
    try {
      const response = await fetch(event.request, {cache:'no-store'});
      const cache = await caches.open(JAYUMINTON_CACHE);
      cache.put(event.request, response.clone()).catch(() => {});
      return response;
    } catch (_) {
      return (await caches.match(event.request)) || Response.error();
    }
  })());
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification && event.notification.data ? event.notification.data : {};
  const assignmentId = String(data.assignmentId || '');
  const destination = new URL('/?open=member&app=user&mode=user&event=' + encodeURIComponent(assignmentId), self.location.origin).toString();

  event.waitUntil((async () => {
    const windows = await clients.matchAll({ type: 'window', includeUncontrolled: true });
    const sameOrigin = windows.find((client) => {
      try { return new URL(client.url).origin === self.location.origin; }
      catch (_) { return false; }
    });
    if (sameOrigin) {
      try {
        await sameOrigin.focus();
        sameOrigin.postMessage({ type: 'JAYUMINTON_NOTIFICATION_OPEN', assignmentId });
        return;
      } catch (_) {}
    }
    if (clients.openWindow) await clients.openWindow(destination);
  })());
});

let messaging = null;
try {
  importScripts('https://www.gstatic.com/firebasejs/12.16.0/firebase-app-compat.js');
  importScripts('https://www.gstatic.com/firebasejs/12.16.0/firebase-messaging-compat.js');
  
  firebase.initializeApp({
    apiKey: 'AIzaSyCS8MJsLHfjsiaQymEyEn-qqp_05WSW1cI',
    authDomain: 'jayuminton-push.firebaseapp.com',
    projectId: 'jayuminton-push',
    storageBucket: 'jayuminton-push.firebasestorage.app',
    messagingSenderId: '758697255400',
    appId: '1:758697255400:web:7214800018c65b7827045d'
  });
  
  const messaging = firebase.messaging();
  
  messaging.onBackgroundMessage((payload) => {
    const data = payload && payload.data ? payload.data : {};
    const vibration = data.type === 'court_assignment'
      ? [1400,500,1400,500,1400]
      : [900,450,900,450,900];
    const repeatCount = Math.max(1, Math.min(3, Number(
      data.repeatCount || (data.type === 'court_assignment' ? 3 : 1)
    )));
  
    return (async () => {
      for (let repeatIndex = 0; repeatIndex < repeatCount; repeatIndex += 1) {
        const titleBase = data.title || '자유민턴 배정 알림';
        const shownTitle = data.type === 'court_assignment' && repeatCount > 1
          ? '🚨 ' + titleBase + ' (' + (repeatIndex + 1) + '/3)'
          : '🏸 ' + titleBase;
        await self.registration.showNotification(shownTitle, {
          body: data.body || '새 배정 안내가 있습니다.',
          requireInteraction: data.type === 'court_assignment',
          silent: false,
          icon: '/icon-198.png',
          badge: '/badge-96.png',
          tag: (data.notificationTag || data.assignmentId || 'jayuminton-assignment') + '_' + (repeatIndex + 1),
          renotify: true,
          vibrate: vibration,
          data: {
            assignmentId: data.assignmentId || ''
          }
        });
        if (repeatIndex + 1 < repeatCount) {
          await new Promise((resolve) => setTimeout(resolve, 6500));
        }
      }
    })();
  });
} catch (error) {
  // PWA installation and basic service-worker control must still work even if the Firebase CDN is temporarily unavailable.
  console.error('[Jayuminton] Firebase messaging worker initialization failed:', error);
}


self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'JAYUMINTON_SKIP_WAITING') self.skipWaiting();
});
