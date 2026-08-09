self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification && event.notification.data ? event.notification.data : {};
  const destination = new URL(data.link || '/', self.location.origin).toString();
  const assignmentId = String(data.assignmentId || '');

  event.waitUntil((async () => {
    const windows = await clients.matchAll({ type: 'window', includeUncontrolled: true });
    const sameApp = windows.find((client) => {
      try { return new URL(client.url).origin === self.location.origin; }
      catch (_) { return false; }
    });
    if (sameApp) {
      try {
        await sameApp.focus();
        sameApp.postMessage({ type: 'JAYUMINTON_NOTIFICATION_OPEN', assignmentId });
        return;
      } catch (_) {}
    }
    if (clients.openWindow) {
      const opened = await clients.openWindow(destination);
      if (opened) opened.postMessage({ type: 'JAYUMINTON_NOTIFICATION_OPEN', assignmentId });
    }
  })());
});

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
  const title = data.title || '자유민턴 배정 알림';
  return self.registration.showNotification(title, {
    body: data.body || '새 배정 안내가 있습니다.',
    icon: '/icon-dog.png',
    badge: '/badge.svg',
    tag: data.assignmentId || 'jayuminton-assignment',
    renotify: false,
    vibrate: [500, 180, 500],
    data: {
      link: '/?open=notification&event=' + encodeURIComponent(data.assignmentId || ''),
      assignmentId: data.assignmentId || ''
    }
  });
});
