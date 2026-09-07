#!/usr/bin/env python3
"""Enable consent-driven iPhone PWA Web Push on the production member page.

This patch intentionally keeps the runtime GAS-free:
- one root service worker: /sw.js
- Firebase Web Messaging for the browser push subscription
- Cloudflare user-push Worker for member <-> token registration
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# A root scope can only have one active service worker. Any older page code that
# still points at the legacy Firebase worker must converge on the unified worker.
text = text.replace("/firebase-messaging-sw.js", "/sw.js")

MARKER = "JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1"
if MARKER not in text:
    addon = r'''
<script>
/* JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1
   iPhone installed-PWA notification consent + FCM token registration.
   The permission request is only executed from the user's explicit button tap.
*/
(function installJayumintonIosPwaPushConsentV1(){
  if (window.__JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1__) return;
  window.__JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1__ = true;

  var VAPID_KEY = 'BNUQPnrOB2AKL7vkrpWQCqtCUyeQN9OInABU5eWBXpF1vGNTuW5ozOV5cdSBNj8d_y0Yc0UB8dolRz2xPLkZ0Rw';
  var REGISTER_URL = 'https://jayuminton-user-push.pianopp001.workers.dev/api/push/register';
  var UNREGISTER_URL = 'https://jayuminton-user-push.pianopp001.workers.dev/api/push/unregister';
  var TOKEN_KEY = 'jayuminton_ios_pwa_fcm_token_v1';
  var CONSENT_KEY = 'jayuminton_ios_pwa_push_consent_v1';
  var LATER_KEY = 'jayuminton_ios_pwa_push_later_until_v1';
  var MEMBER_KEY = 'jayuminton_web_push_selected_member_v1';
  var ALERT_KEY = 'jayuminton_member_alert_enabled_v1';
  var VIBRATION_KEY = 'jayuminton_member_vibration_enabled_v1';
  var promptOpen = false;
  var registrationInFlight = null;
  var sdkPromise = null;

  function isIos(){
    var ua = String(navigator.userAgent || '');
    return /iPhone|iPad|iPod/i.test(ua) ||
      (navigator.platform === 'MacIntel' && Number(navigator.maxTouchPoints || 0) > 1);
  }

  function isStandalone(){
    try {
      return window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true;
    } catch (error) { return false; }
  }

  if (!isIos() || !isStandalone()) return;

  function readMember(){
    try {
      if (typeof currentStoredWebPushMember === 'function') {
        var direct = currentStoredWebPushMember();
        if (direct && direct.id && direct.name) {
          return {id:String(direct.id), name:String(direct.name)};
        }
      }
    } catch (error) {}
    try {
      var saved = JSON.parse(localStorage.getItem(MEMBER_KEY) || 'null');
      return saved && saved.id && saved.name
        ? {id:String(saved.id), name:String(saved.name)} : null;
    } catch (error) { return null; }
  }

  function message(text, isError){
    try {
      if (typeof showMemberSettingMessage === 'function') {
        showMemberSettingMessage(String(text || ''), !!isError);
        return;
      }
    } catch (error) {}
    try { console[isError ? 'warn' : 'log']('[Jayuminton PWA Push]', text); } catch (error) {}
  }

  function loadScript(src){
    return new Promise(function(resolve, reject){
      var existing = Array.prototype.slice.call(document.scripts || []).find(function(item){
        return item.src === src;
      });
      if (existing && window.firebase) { resolve(); return; }
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = function(){ reject(new Error('알림 모듈을 불러오지 못했습니다.')); };
      document.head.appendChild(script);
    });
  }

  function ensureFirebase(){
    if (sdkPromise) return sdkPromise;
    sdkPromise = loadScript('https://www.gstatic.com/firebasejs/12.16.0/firebase-app-compat.js')
      .then(function(){ return loadScript('https://www.gstatic.com/firebasejs/12.16.0/firebase-messaging-compat.js'); })
      .then(function(){
        if (!window.firebase) throw new Error('Firebase 알림 모듈 초기화 실패');
        if (!firebase.apps.length) {
          firebase.initializeApp({
            apiKey: 'AIzaSyCS8MJsLHfjsiaQymEyEn-qqp_05WSW1cI',
            authDomain: 'jayuminton-push.firebaseapp.com',
            projectId: 'jayuminton-push',
            storageBucket: 'jayuminton-push.firebasestorage.app',
            messagingSenderId: '758697255400',
            appId: '1:758697255400:web:7214800018c65b7827045d'
          });
        }
        return firebase.messaging();
      });
    return sdkPromise;
  }

  async function unifiedRegistration(){
    if (!('serviceWorker' in navigator)) throw new Error('이 iPhone에서는 웹 알림을 지원하지 않습니다.');
    var reg = await navigator.serviceWorker.register('/sw.js', {scope:'/', updateViaCache:'none'});
    await navigator.serviceWorker.ready;
    try { await reg.update(); } catch (error) {}
    return reg;
  }

  async function registerToken(showConfirmation){
    if (registrationInFlight) return registrationInFlight;
    registrationInFlight = (async function(){
      var member = readMember();
      if (!member) throw new Error('먼저 내 이름을 선택해 주세요.');
      if (!('Notification' in window) || Notification.permission !== 'granted') {
        throw new Error('알림 허용이 필요합니다.');
      }
      if (!('PushManager' in window)) throw new Error('이 iPhone에서는 웹 푸시를 지원하지 않습니다.');

      var reg = await unifiedRegistration();
      var messaging = await ensureFirebase();
      var token = await messaging.getToken({vapidKey:VAPID_KEY, serviceWorkerRegistration:reg});
      if (!token) throw new Error('알림 연결 정보를 만들지 못했습니다.');

      var response = await fetch(REGISTER_URL, {
        method:'POST',
        mode:'cors',
        headers:{'content-type':'application/json'},
        body:JSON.stringify({
          action:'register_web_token',
          memberId:member.id,
          memberName:member.name,
          token:token,
          userAgent:String(navigator.userAgent || '') + ' JayumintonIOSPWA/1',
          platform:'ios-pwa'
        })
      });
      var result = null;
      try { result = await response.json(); } catch (error) {}
      if (!response.ok || !result || result.ok !== true) {
        throw new Error('Cloudflare 알림 등록에 실패했습니다.');
      }

      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(CONSENT_KEY, 'granted');
      localStorage.removeItem(LATER_KEY);
      localStorage.setItem(ALERT_KEY, 'true');
      localStorage.setItem(VIBRATION_KEY, 'true');
      try { if (typeof renderMemberSelfSettings === 'function') renderMemberSelfSettings(); } catch (error) {}

      if (showConfirmation && reg && typeof reg.showNotification === 'function') {
        try {
          await reg.showNotification('🏸 자유민턴 알림·진동 허용 완료', {
            body:'대기1 또는 코트배정 시 iPhone 알림으로 알려드립니다.',
            icon:'/icon-192.png',
            badge:'/icon-192.png',
            tag:'jayuminton-push-consent-confirmed',
            renotify:true,
            silent:false,
            vibrate:[900,260,900,260,900],
            data:{type:'push_enabled', assignmentId:''}
          });
        } catch (error) {}
      }
      message(member.name + '님 알림·진동 연결 완료');
      return token;
    })();
    try { return await registrationInFlight; }
    finally { registrationInFlight = null; }
  }

  async function unregisterToken(){
    var token = '';
    try { token = String(localStorage.getItem(TOKEN_KEY) || ''); } catch (error) {}
    if (!token) return;
    try {
      await fetch(UNREGISTER_URL, {
        method:'POST',
        mode:'cors',
        headers:{'content-type':'application/json'},
        body:JSON.stringify({action:'unregister_web_token', token:token})
      });
    } catch (error) {}
    try { localStorage.removeItem(TOKEN_KEY); } catch (error) {}
  }

  function closePrompt(){
    promptOpen = false;
    var overlay = document.getElementById('jmIosPwaPushConsent');
    if (overlay) overlay.remove();
  }

  function showPrompt(force){
    if (promptOpen || !readMember()) return;
    if (!('Notification' in window)) return;
    if (Notification.permission === 'granted') {
      registerToken(false).catch(function(error){ message(error.message || error, true); });
      return;
    }
    if (Notification.permission === 'denied') {
      if (force) message('iPhone 설정 > 알림에서 자유민턴 알림을 허용해 주세요.', true);
      return;
    }
    if (!force) {
      var laterUntil = 0;
      try { laterUntil = Number(localStorage.getItem(LATER_KEY) || 0); } catch (error) {}
      if (laterUntil > Date.now()) return;
    }

    promptOpen = true;
    var overlay = document.createElement('div');
    overlay.id = 'jmIosPwaPushConsent';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:2147483646;background:rgba(15,23,42,.62);display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box';
    overlay.innerHTML =
      '<div style="width:min(420px,100%);background:#fff;border-radius:20px;padding:22px;box-shadow:0 22px 60px rgba(0,0,0,.28);font-family:inherit">' +
        '<div style="font-size:20px;font-weight:900;color:#111827;margin-bottom:10px">🔔 알림·진동을 허용할까요?</div>' +
        '<div style="font-size:14px;line-height:1.65;color:#4b5563;margin-bottom:8px">대기1 또는 코트배정이 되면 자유민턴이 iPhone 알림 팝업으로 알려드립니다.</div>' +
        '<div style="font-size:13px;line-height:1.55;color:#6b7280;margin-bottom:18px">앱을 닫아둔 상태에서도 알림을 받을 수 있으며, 진동·햅틱은 iPhone의 알림/사운드 설정에 따라 동작합니다.</div>' +
        '<button type="button" id="jmIosPwaPushAllow" style="width:100%;min-height:50px;border:0;border-radius:12px;background:#315efb;color:#fff;font-size:16px;font-weight:900;margin-bottom:9px">알림·진동 허용</button>' +
        '<button type="button" id="jmIosPwaPushLater" style="width:100%;min-height:44px;border:0;border-radius:12px;background:#f3f4f6;color:#4b5563;font-size:14px;font-weight:800">나중에</button>' +
      '</div>';
    document.body.appendChild(overlay);

    overlay.querySelector('#jmIosPwaPushAllow').addEventListener('click', async function(){
      var button = this;
      button.disabled = true;
      button.textContent = '연결 중…';
      try {
        var permission = await Notification.requestPermission();
        if (permission !== 'granted') {
          localStorage.setItem(CONSENT_KEY, permission === 'denied' ? 'denied' : 'default');
          localStorage.setItem(ALERT_KEY, 'false');
          localStorage.setItem(VIBRATION_KEY, 'false');
          message('알림이 허용되지 않았습니다.', true);
          closePrompt();
          return;
        }
        await registerToken(true);
        closePrompt();
      } catch (error) {
        button.disabled = false;
        button.textContent = '알림·진동 허용';
        message(error && error.message ? error.message : String(error), true);
      }
    });

    overlay.querySelector('#jmIosPwaPushLater').addEventListener('click', function(){
      try {
        localStorage.setItem(LATER_KEY, String(Date.now() + 24 * 60 * 60 * 1000));
        localStorage.setItem(CONSENT_KEY, 'later');
        localStorage.setItem(ALERT_KEY, 'false');
        localStorage.setItem(VIBRATION_KEY, 'false');
      } catch (error) {}
      try { if (typeof renderMemberSelfSettings === 'function') renderMemberSelfSettings(); } catch (error) {}
      closePrompt();
    });
  }

  function prepareInitialConsentState(){
    try {
      var saved = localStorage.getItem(CONSENT_KEY);
      if (Notification.permission !== 'granted' && !saved) {
        localStorage.setItem(ALERT_KEY, 'false');
        localStorage.setItem(VIBRATION_KEY, 'false');
      }
      if (Notification.permission === 'granted') {
        localStorage.setItem(CONSENT_KEY, 'granted');
        localStorage.setItem(ALERT_KEY, 'true');
        localStorage.setItem(VIBRATION_KEY, 'true');
      }
    } catch (error) {}
  }

  function wrapExistingControls(){
    if (typeof window.toggleMemberAlertSetting === 'function' && !window.toggleMemberAlertSetting.__jmIosPushWrapped) {
      var originalAlertToggle = window.toggleMemberAlertSetting;
      var wrappedAlertToggle = function(){
        var before = true;
        try { before = typeof memberAlertEnabled === 'function' ? !!memberAlertEnabled() : true; } catch (error) {}
        var result = originalAlertToggle.apply(this, arguments);
        var after = !before;
        try { after = typeof memberAlertEnabled === 'function' ? !!memberAlertEnabled() : after; } catch (error) {}
        if (after) showPrompt(true);
        else unregisterToken();
        return result;
      };
      wrappedAlertToggle.__jmIosPushWrapped = true;
      window.toggleMemberAlertSetting = wrappedAlertToggle;
    }

    if (typeof window.clearMemberSelfSelection === 'function' && !window.clearMemberSelfSelection.__jmIosPushWrapped) {
      var originalClear = window.clearMemberSelfSelection;
      var wrappedClear = function(){
        unregisterToken();
        return originalClear.apply(this, arguments);
      };
      wrappedClear.__jmIosPushWrapped = true;
      window.clearMemberSelfSelection = wrappedClear;
    }

    if (typeof window.selectMemberSelf === 'function' && !window.selectMemberSelf.__jmIosPushWrapped) {
      var originalSelect = window.selectMemberSelf;
      var wrappedSelect = function(){
        var result = originalSelect.apply(this, arguments);
        Promise.resolve(result).finally(function(){ setTimeout(function(){
          if (Notification.permission === 'granted') registerToken(false).catch(function(){});
          else showPrompt(false);
        }, 120); });
        return result;
      };
      wrappedSelect.__jmIosPushWrapped = true;
      window.selectMemberSelf = wrappedSelect;
    }
  }

  function reconcile(){
    wrapExistingControls();
    if (!readMember()) return;
    if (Notification.permission === 'granted') {
      registerToken(false).catch(function(error){ message(error && error.message ? error.message : error, true); });
    } else if (Notification.permission === 'default') {
      showPrompt(false);
    }
  }

  prepareInitialConsentState();
  window.JayumintonPwaPush = {
    requestConsent:function(){ showPrompt(true); },
    refresh:function(){ reconcile(); },
    unregister:function(){ return unregisterToken(); }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function(){ setTimeout(reconcile, 500); }, {once:true});
  } else {
    setTimeout(reconcile, 500);
  }
  setInterval(reconcile, 2500);
})();
</script>
'''
    close = text.lower().rfind("</body>")
    if close < 0:
        raise SystemExit("body close marker missing for iOS PWA push consent injection")
    text = text[:close] + addon + "\n" + text[close:]

required = (
    MARKER,
    "navigator.serviceWorker.register('/sw.js'",
    "Notification.requestPermission()",
    "messaging.getToken({vapidKey:VAPID_KEY, serviceWorkerRegistration:reg})",
    "jayuminton-user-push.pianopp001.workers.dev/api/push/register",
    "register_web_token",
    "알림·진동 허용",
    "reg.showNotification('🏸 자유민턴 알림·진동 허용 완료'",
)
for value in required:
    if value not in text:
        raise SystemExit("iOS PWA push contract missing: " + value)

if "/firebase-messaging-sw.js" in text:
    raise SystemExit("legacy root-scope Firebase service worker reference still present")

path.write_text(text, encoding="utf-8")
print("JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1_OK")
