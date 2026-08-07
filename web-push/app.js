(() => {
  'use strict';

  const cfg = window.JAYUMINTON_WEB_PUSH_CONFIG || {};
  const frame = document.getElementById('memberFrame');
  const loader = document.getElementById('loader');
  const toast = document.getElementById('toast');
  const setupBackdrop = document.getElementById('setupBackdrop');
  const setupMember = document.getElementById('setupMember');
  const setupContent = document.getElementById('setupContent');
  const setupPrimary = document.getElementById('setupPrimary');
  const setupSecondary = document.getElementById('setupSecondary');
  const disableButton = document.getElementById('disableButton');
  const browserEscape = document.getElementById('browserEscape');
  const browserEscapeButton = document.getElementById('browserEscapeButton');
  const relayForm = document.getElementById('relayForm');
  const relayPayload = document.getElementById('relayPayload');
  const submitFrame = document.getElementById('submitFrame');

  const STORAGE = Object.freeze({
    member: 'jayuminton_unified_member_v2',
    auth: 'jayuminton_unified_auth_v2',
    push: 'jayuminton_unified_push_v2',
    lastEvent: 'jayuminton_unified_last_event_v2'
  });

  const ua = navigator.userAgent || '';
  const isIos = /iPad|iPhone|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const isAndroid = /Android/i.test(ua);
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const isChromeAndroid = isAndroid && /Chrome\//i.test(ua) && !/(wv|KAKAOTALK|DaumApps|NAVER|Instagram|FBAN|FBAV|EverytimeApp)/i.test(ua);
  const isInApp = /(KAKAOTALK|DaumApps|NAVER|Instagram|FBAN|FBAV|Line\/|EverytimeApp|wv\))/i.test(ua) || (isAndroid && /; wv\)/i.test(ua));

  let selectedMember = loadJson(STORAGE.member);
  let authVersion = localStorage.getItem(STORAGE.auth) || '';
  let messaging = null;
  let registration = null;
  let pendingAction = null;
  let toastTimer = null;

  restoreHandoff();
  frame.src = addQuery(cfg.memberPageUrl, { unified: '1', embedded: '1' });

  function loadJson(key) {
    try { return JSON.parse(localStorage.getItem(key) || 'null'); }
    catch (_) { return null; }
  }

  function saveJson(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) {}
  }

  function base64UrlEncode(value) {
    const bytes = new TextEncoder().encode(JSON.stringify(value));
    let binary = '';
    bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  }

  function base64UrlDecode(value) {
    try {
      const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
      const binary = atob(normalized + '='.repeat((4 - normalized.length % 4) % 4));
      const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
      return JSON.parse(new TextDecoder().decode(bytes));
    } catch (_) { return null; }
  }

  function addQuery(url, values) {
    const parsed = new URL(url, location.href);
    Object.keys(values || {}).forEach((key) => parsed.searchParams.set(key, values[key]));
    return parsed.toString();
  }

  function restoreHandoff() {
    const params = new URLSearchParams(location.search);
    const handoff = base64UrlDecode(params.get('h') || '');
    if (!handoff) return;
    if (handoff.member && handoff.member.id && handoff.member.name) {
      selectedMember = { id: String(handoff.member.id), name: String(handoff.member.name) };
      saveJson(STORAGE.member, selectedMember);
    }
    if (handoff.auth) {
      authVersion = String(handoff.auth);
      localStorage.setItem(STORAGE.auth, authVersion);
    }
  }

  function updateHandoffUrl() {
    const payload = {};
    if (selectedMember && selectedMember.id && selectedMember.name) payload.member = selectedMember;
    if (authVersion) payload.auth = authVersion;
    const url = new URL(location.href);
    if (Object.keys(payload).length) url.searchParams.set('h', base64UrlEncode(payload));
    else url.searchParams.delete('h');
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }

  function isTrustedMemberOrigin(origin) {
    try {
      const host = new URL(origin).hostname;
      return origin === 'https://script.google.com' || host.endsWith('.googleusercontent.com');
    } catch (_) { return false; }
  }

  function postToMember(type, extra) {
    if (!frame.contentWindow) return;
    frame.contentWindow.postMessage(Object.assign({ type }, extra || {}), '*');
  }

  function sendBootstrap() {
    postToMember('JAYUMINTON_UNIFIED_BOOTSTRAP', {
      authVersion,
      member: selectedMember,
      notificationPermission: 'Notification' in window ? Notification.permission : 'unsupported',
      standalone: isStandalone,
      platform: isIos ? 'ios' : (isAndroid ? 'android' : 'other')
    });
  }

  function showToast(message, type, duration) {
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.className = 'toast' + (type ? ' ' + type : '');
    toastTimer = setTimeout(() => toast.classList.add('hidden'), duration || 3200);
  }

  function showSetup(mode) {
    setupMember.textContent = selectedMember ? selectedMember.name + '님' : '이름을 먼저 선택해 주세요.';
    disableButton.classList.toggle('hidden', !loadJson(STORAGE.push));
    setupPrimary.classList.remove('hidden');
    pendingAction = mode;

    if (mode === 'ios-install') {
      updateHandoffUrl();
      setupContent.innerHTML = [
        '<p>한 번만 홈 화면에 추가하면 이후에는 자유민턴 아이콘과 배정 알림이 같은 화면으로 연결됩니다.</p>',
        '<ol class="steps">',
        '<li>브라우저의 <b>공유</b> 메뉴를 누릅니다.</li>',
        '<li><b>홈 화면에 추가</b>를 누르고, 추가된 <b>자유민턴</b> 아이콘을 한 번 엽니다.</li>',
        '<li>같은 화면에서 알림 허용 버튼이 바로 나타나면 한 번 눌러 주세요.</li>',
        '</ol>',
        '<p class="small">선택한 이름과 로그인 상태는 홈 화면 웹앱으로 이어지므로 비밀번호 화면부터 다시 시작하지 않습니다.</p>'
      ].join('');
      setupPrimary.textContent = '설치 안내 확인';
    } else if (mode === 'external-browser') {
      setupContent.innerHTML = '<p>카카오톡·당근 안의 내장 브라우저에서는 백그라운드 알림 등록이 제한됩니다. 아래 버튼 한 번으로 같은 화면을 Chrome에서 이어서 엽니다.</p>';
      setupPrimary.textContent = 'Chrome에서 계속';
    } else {
      setupContent.innerHTML = '<p>대기2에서 대기1로 올라갈 때와 코트에 들어갈 때, 선택한 이름의 휴대폰에만 알림을 보냅니다.</p><p class="small">휴대폰의 무음·집중 모드 또는 햅틱 설정에 따라 진동은 달라질 수 있습니다.</p>';
      setupPrimary.textContent = '알림 허용';
    }
    setupBackdrop.classList.remove('hidden');
  }

  function hideSetup() {
    setupBackdrop.classList.add('hidden');
    pendingAction = null;
  }

  function chromeIntentUrl() {
    const target = new URL(location.href);
    target.searchParams.set('continuePush', '1');
    const schemeLess = target.toString().replace(/^https?:\/\//, '');
    return 'intent://' + schemeLess + '#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url=' +
      encodeURIComponent(target.toString()) + ';end';
  }

  function openChrome() {
    location.href = chromeIntentUrl();
  }

  async function initializeMessaging() {
    if (!cfg.relayUrl || !/^https:\/\/script\.google\.com\/macros\/s\/.+\/exec$/.test(cfg.relayUrl)) {
      throw new Error('알림 발송 주소가 아직 연결되지 않았습니다.');
    }
    if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) {
      throw new Error('현재 브라우저에서는 알림 등록을 할 수 없습니다.');
    }
    if (!window.firebase || !firebase.messaging) throw new Error('알림 모듈을 불러오지 못했습니다.');
    if (!firebase.apps.length) firebase.initializeApp(cfg.firebase);
    registration = registration || await navigator.serviceWorker.register('/firebase-messaging-sw.js', { scope: '/' });
    await navigator.serviceWorker.ready;
    messaging = messaging || firebase.messaging();
    messaging.onMessage((payload) => {
      const data = payload && payload.data ? payload.data : {};
      const eventId = data.assignmentId || String(Date.now());
      if (localStorage.getItem(STORAGE.lastEvent) === eventId) return;
      localStorage.setItem(STORAGE.lastEvent, eventId);
      showToast(data.body || '새 배정 안내가 있습니다.', 'success', 7000);
      try { if (navigator.vibrate) navigator.vibrate([500, 180, 500]); } catch (_) {}
      requestMemberRefresh(eventId);
      registration.showNotification(data.title || '자유민턴 배정 알림', {
        body: data.body || '새 배정 안내가 있습니다.',
        icon: '/icon.svg',
        badge: '/badge.svg',
        tag: eventId,
        renotify: false,
        vibrate: [500, 180, 500],
        data: { link: '/', assignmentId: eventId }
      }).catch(() => {});
    });
    return messaging;
  }

  function submitRelay(action, token) {
    return new Promise((resolve, reject) => {
      try {
        relayForm.action = cfg.relayUrl;
        relayPayload.value = JSON.stringify({
          action,
          memberId: selectedMember && selectedMember.id,
          memberName: selectedMember && selectedMember.name,
          token,
          userAgent: navigator.userAgent
        });
        let done = false;
        const finish = () => { if (!done) { done = true; resolve(); } };
        const timer = setTimeout(finish, 1800);
        submitFrame.onload = () => { clearTimeout(timer); finish(); };
        relayForm.submit();
      } catch (error) { reject(error); }
    });
  }

  async function enableNotifications() {
    if (!selectedMember) throw new Error('알림 받을 본인 이름을 먼저 선택하세요.');
    const instance = await initializeMessaging();
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') throw new Error('알림 권한이 허용되지 않았습니다. 휴대폰 설정에서 자유민턴 알림을 허용해 주세요.');
    registration = registration || await navigator.serviceWorker.ready;
    const token = await instance.getToken({ vapidKey: cfg.vapidKey, serviceWorkerRegistration: registration });
    if (!token) throw new Error('알림 주소를 만들지 못했습니다.');
    await submitRelay('register_web_token', token);
    saveJson(STORAGE.push, { member: selectedMember, tokenUpdatedAt: Date.now() });
    updateHandoffUrl();
    postToMember('JAYUMINTON_UNIFIED_PUSH_STATUS', {
      ok: true,
      member: selectedMember,
      message: selectedMember.name + '님의 개인 배정 알림이 연결되었습니다.'
    });
    showToast(selectedMember.name + '님의 알림 설정이 완료되었습니다.', 'success', 4500);
  }

  async function disableNotifications() {
    const instance = await initializeMessaging();
    const token = await instance.getToken({ vapidKey: cfg.vapidKey, serviceWorkerRegistration: registration });
    if (token) {
      await submitRelay('unregister_web_token', token);
      await instance.deleteToken();
    }
    localStorage.removeItem(STORAGE.push);
    postToMember('JAYUMINTON_UNIFIED_PUSH_STATUS', { ok: true, message: '이 휴대폰의 개인 알림을 해제했습니다.' });
    showToast('이 휴대폰의 개인 알림을 해제했습니다.', 'success');
  }

  function requestMemberRefresh(eventId) {
    postToMember('JAYUMINTON_UNIFIED_REFRESH', { eventId: eventId || '' });
  }

  function handleSetupRequest() {
    if (!selectedMember) {
      showToast('알림 받을 본인 이름을 먼저 선택하세요.', 'error');
      return;
    }
    updateHandoffUrl();
    if (isIos && !isStandalone) {
      showSetup('ios-install');
      return;
    }
    if (isAndroid && isInApp && !isChromeAndroid) {
      showSetup('external-browser');
      return;
    }
    showSetup('permission');
  }

  setupPrimary.addEventListener('click', async () => {
    if (pendingAction === 'ios-install') {
      showToast('공유 메뉴에서 홈 화면에 추가한 뒤 자유민턴 아이콘을 열어 주세요.', '', 5000);
      return;
    }
    if (pendingAction === 'external-browser') {
      openChrome();
      return;
    }
    setupPrimary.disabled = true;
    setupPrimary.textContent = '연결 중…';
    try {
      await enableNotifications();
      hideSetup();
    } catch (error) {
      showToast(error && error.message ? error.message : String(error), 'error', 6500);
      setupContent.innerHTML = '<p>' + escapeHtml(error && error.message ? error.message : String(error)) + '</p>';
    } finally {
      setupPrimary.disabled = false;
      setupPrimary.textContent = '알림 허용';
    }
  });

  setupSecondary.addEventListener('click', hideSetup);
  disableButton.addEventListener('click', async () => {
    disableButton.disabled = true;
    try { await disableNotifications(); hideSetup(); }
    catch (error) { showToast(error && error.message ? error.message : String(error), 'error'); }
    finally { disableButton.disabled = false; }
  });
  browserEscapeButton.addEventListener('click', openChrome);

  window.addEventListener('message', (event) => {
    if (!isTrustedMemberOrigin(event.origin)) return;
    const data = event.data || {};
    if (data.type === 'JAYUMINTON_MEMBER_BRIDGE_READY') {
      loader.classList.add('hidden');
      sendBootstrap();
      return;
    }
    if (data.type === 'JAYUMINTON_MEMBER_AUTH_READY') {
      authVersion = String(data.version || '');
      if (authVersion) localStorage.setItem(STORAGE.auth, authVersion);
      updateHandoffUrl();
      return;
    }
    if (data.type === 'JAYUMINTON_MEMBER_SELECTED') {
      if (data.member && data.member.id && data.member.name) {
        selectedMember = { id: String(data.member.id), name: String(data.member.name) };
        saveJson(STORAGE.member, selectedMember);
      } else {
        selectedMember = null;
        localStorage.removeItem(STORAGE.member);
      }
      updateHandoffUrl();
      return;
    }
    if (data.type === 'JAYUMINTON_PUSH_SETUP_REQUEST') {
      if (data.member && data.member.id && data.member.name) {
        selectedMember = { id: String(data.member.id), name: String(data.member.name) };
        saveJson(STORAGE.member, selectedMember);
      }
      handleSetupRequest();
    }
  });

  navigator.serviceWorker && navigator.serviceWorker.addEventListener('message', (event) => {
    const data = event.data || {};
    if (data.type === 'JAYUMINTON_NOTIFICATION_OPEN') {
      requestMemberRefresh(data.assignmentId || '');
    }
  });

  frame.addEventListener('load', () => {
    setTimeout(sendBootstrap, 150);
    setTimeout(() => loader.classList.add('hidden'), 5000);
  });

  function escapeHtml(value) {
    return String(value || '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  }

  const params = new URLSearchParams(location.search);
  if (params.get('continuePush') === '1') {
    history.replaceState(null, '', location.pathname + (params.get('h') ? '?h=' + encodeURIComponent(params.get('h')) : ''));
    setTimeout(() => {
      if (selectedMember) showSetup(isIos && !isStandalone ? 'ios-install' : 'permission');
    }, 900);
  } else if (isIos && isStandalone && selectedMember && !loadJson(STORAGE.push)) {
    setTimeout(async () => {
      if ('Notification' in window && Notification.permission === 'granted') {
        try { await enableNotifications(); }
        catch (error) { showSetup('permission'); }
      } else {
        showSetup('permission');
      }
    }, 1100);
  }

  if (isAndroid && isInApp && !isChromeAndroid && !sessionStorage.getItem('jayuminton_chrome_attempted')) {
    sessionStorage.setItem('jayuminton_chrome_attempted', '1');
    setTimeout(() => {
      if (!document.hidden) {
        try { openChrome(); } catch (_) {}
        setTimeout(() => { if (!document.hidden) browserEscape.classList.remove('hidden'); }, 1100);
      }
    }, 350);
  }

  updateHandoffUrl();
})();
