/* JAYUMINTON_MEMBER_PWA_SW_V2
   One root-scope service worker for BOTH PWA installability and Firebase Web Push.
   - no application-state caching: court state must always come from the network
   - background FCM data messages become iOS/Android system notifications
   - notification click reopens/focuses the installed court-status PWA
*/
const JAYUMINTON_SW_VERSION = 'member-pwa-push-v2-20260908';

self.addEventListener('install', function () {
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function (event) {
  event.respondWith(fetch(event.request));
});

function notificationTitle(type) {
  return String(type || '') === 'court_assignment'
    ? '🚨 코트 입장 — 지금 이동하세요'
    : '🏸 대기 1 — 라켓 들고 준비해 주세요';
}

function notificationBody(type, data) {
  if (data && data.body) return String(data.body);
  return String(type || '') === 'court_assignment'
    ? '코트에 배정되었습니다. 지금 코트로 이동해 주세요.'
    : '대기 1입니다. 라켓 들고 준비해 주세요.';
}

function repeatCount(type) {
  return String(type || '') === 'court_assignment' ? 5 : 3;
}

function requestedVibrationPattern() {
  // iOS decides the final notification haptic itself. Browsers that support the
  // vibration option can additionally use this pattern.
  return [900, 260, 900, 260, 900];
}

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  const data = event.notification && event.notification.data ? event.notification.data : {};
  const assignmentId = String(data.assignmentId || '');
  const destination = new URL(
    '/?source=pwa&open=member&app=user&mode=user&event=' + encodeURIComponent(assignmentId),
    self.location.origin
  ).toString();

  event.waitUntil((async function () {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const sameOrigin = windows.find(function (client) {
      try { return new URL(client.url).origin === self.location.origin; }
      catch (error) { return false; }
    });
    if (sameOrigin) {
      try {
        await sameOrigin.focus();
        sameOrigin.postMessage({ type: 'JAYUMINTON_NOTIFICATION_OPEN', assignmentId: assignmentId });
        return;
      } catch (error) {}
    }
    if (self.clients.openWindow) await self.clients.openWindow(destination);
  })());
});

/* Firebase Web Messaging background receiver. The Cloudflare user-push Worker
   sends data-only FCM messages, so this worker is responsible for presenting
   the visible notification while the PWA is backgrounded or closed. */
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

  messaging.onBackgroundMessage(function (payload) {
    const data = payload && payload.data ? payload.data : {};
    const type = String(data.type || '');
    const assignmentId = String(data.assignmentId || '');
    const baseTag = String(data.notificationTag || assignmentId || ('jayuminton-' + type + '-' + Date.now()));
    const repeats = repeatCount(type);

    return (async function () {
      for (let index = 0; index < repeats; index += 1) {
        const title = notificationTitle(type) + (repeats > 1 ? ' (' + (index + 1) + '/' + repeats + ')' : '');
        await self.registration.showNotification(title, {
          body: notificationBody(type, data),
          icon: '/icon-192.png',
          badge: '/icon-192.png',
          tag: baseTag + '-alert-' + (index + 1),
          renotify: true,
          requireInteraction: true,
          silent: false,
          vibrate: requestedVibrationPattern(),
          timestamp: Date.now(),
          data: {
            assignmentId: assignmentId,
            type: type,
            memberId: String(data.memberId || ''),
            courtNo: String(data.courtNo || '')
          }
        });
        if (index + 1 < repeats) {
          await new Promise(function (resolve) { setTimeout(resolve, 1800); });
        }
      }
    })();
  });
} catch (error) {
  console.error('[Jayuminton] unified PWA push worker initialization failed:', error);
}

self.addEventListener('message', function (event) {
  if (event.data && event.data.type === 'JAYUMINTON_SKIP_WAITING') self.skipWaiting();
});
