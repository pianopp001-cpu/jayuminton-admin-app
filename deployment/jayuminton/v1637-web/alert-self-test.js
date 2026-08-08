(() => {
  'use strict';

  const TEST_KEY = 'jayuminton_web_alert_self_test_v1';
  let lastRequestAt = 0;

  function browserLabel() {
    const ua = String(navigator.userAgent || '');
    if (/SamsungBrowser/i.test(ua)) return '삼성 인터넷';
    if (/EdgA|EdgiOS|Edg/i.test(ua)) return 'Edge';
    if (/Chrome|CriOS/i.test(ua)) return 'Chrome';
    return '현재 브라우저';
  }

  function testPattern() {
    // One full 3-pulse set repeated three times. Same channel/path as real web notifications.
    return [650,220,650,220,650,1100,650,220,650,220,650,1100,650,220,650,220,650];
  }

  async function runSelfTest() {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    if (!navigator.serviceWorker) return;

    let registration;
    try {
      registration = await navigator.serviceWorker.ready;
    } catch (_) {
      return;
    }
    if (!registration || !registration.showNotification) return;

    try {
      await registration.showNotification('🔔 자유민턴 알림 테스트', {
        body: '이 알림이 화면 위에 팝업되고 진동해야 정상입니다.',
        icon: '/icon-198.png',
        badge: '/badge-96.png',
        silent: false,
        renotify: true,
        tag: 'jayuminton-self-test-' + Date.now(),
        vibrate: testPattern(),
        timestamp: Date.now(),
        data: { type: 'self_test' }
      });
      try { localStorage.setItem(TEST_KEY, String(Date.now())); } catch (_) {}

      window.setTimeout(() => {
        const browser = browserLabel();
        window.alert(
          '알림 테스트를 방금 보냈습니다.\n\n' +
          '위쪽 팝업과 진동이 모두 느껴졌으면 정상입니다.\n\n' +
          '팝업이나 진동이 없었다면 휴대폰 설정 → 알림 → ' + browser +
          '에서 알림 허용, 팝업 표시, 진동을 켜 주세요.\n' +
          '이 설정이 꺼져 있으면 웹사이트가 강제로 켤 수 없습니다.'
        );
      }, 5000);
    } catch (_) {}
  }

  window.addEventListener('message', (event) => {
    const data = event && event.data ? event.data : {};
    if (data.type !== 'JAYUMINTON_PUSH_SETUP_REQUEST') return;
    const now = Date.now();
    if (now - lastRequestAt < 4000) return;
    lastRequestAt = now;
    window.setTimeout(runSelfTest, 2200);
  });
})();
