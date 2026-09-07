/* JAYUMINTON_MEMBER_PWA_SW_V3
   One root-scope service worker for PWA installability + foreground bootstrap
   + Firebase Web Push background delivery.
*/
const JAYUMINTON_SW_VERSION = 'member-pwa-push-v3-20260908';

const IOS_PUSH_BOOTSTRAP = String.raw`
<script>
/* JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1 */
(function(){
  if (window.__JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1__) return;
  window.__JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1__ = true;

  var VAPID='BNUQPnrOB2AKL7vkrpWQCqtCUyeQN9OInABU5eWBXpF1vGNTuW5ozOV5cdSBNj8d_y0Yc0UB8dolRz2xPLkZ0Rw';
  var REGISTER='https://jayuminton-user-push.pianopp001.workers.dev/api/push/register';
  var UNREGISTER='https://jayuminton-user-push.pianopp001.workers.dev/api/push/unregister';
  var MEMBER_KEY='jayuminton_web_push_selected_member_v1';
  var TOKEN_KEY='jayuminton_ios_pwa_fcm_token_v1';
  var CONSENT_KEY='jayuminton_ios_pwa_push_consent_v1';
  var LATER_KEY='jayuminton_ios_pwa_push_later_until_v1';
  var ALERT_KEY='jayuminton_member_alert_enabled_v1';
  var VIB_KEY='jayuminton_member_vibration_enabled_v1';
  var sdkPromise=null, busy=null, promptOpen=false;

  function ios(){
    var ua=String(navigator.userAgent||'');
    return /iPhone|iPad|iPod/i.test(ua)||(navigator.platform==='MacIntel'&&Number(navigator.maxTouchPoints||0)>1);
  }
  function standalone(){
    try{return matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;}catch(e){return false;}
  }
  if(!ios()||!standalone()) return;

  function member(){
    try{
      if(typeof currentStoredWebPushMember==='function'){
        var m=currentStoredWebPushMember();
        if(m&&m.id&&m.name)return{id:String(m.id),name:String(m.name)};
      }
    }catch(e){}
    try{
      var s=JSON.parse(localStorage.getItem(MEMBER_KEY)||'null');
      return s&&s.id&&s.name?{id:String(s.id),name:String(s.name)}:null;
    }catch(e){return null;}
  }
  function status(t,err){
    try{if(typeof showMemberSettingMessage==='function'){showMemberSettingMessage(String(t||''),!!err);return;}}catch(e){}
    try{console[err?'warn':'log']('[Jayuminton PWA Push]',t);}catch(e){}
  }
  function load(src){
    return new Promise(function(ok,no){
      var found=Array.prototype.slice.call(document.scripts||[]).find(function(x){return x.src===src;});
      if(found&&window.firebase){ok();return;}
      var s=document.createElement('script');s.src=src;s.async=true;s.onload=ok;s.onerror=function(){no(new Error('알림 모듈을 불러오지 못했습니다.'));};document.head.appendChild(s);
    });
  }
  function messaging(){
    if(sdkPromise)return sdkPromise;
    sdkPromise=load('https://www.gstatic.com/firebasejs/12.16.0/firebase-app-compat.js')
      .then(function(){return load('https://www.gstatic.com/firebasejs/12.16.0/firebase-messaging-compat.js');})
      .then(function(){
        if(!firebase.apps.length)firebase.initializeApp({
          apiKey:'AIzaSyCS8MJsLHfjsiaQymEyEn-qqp_05WSW1cI',
          authDomain:'jayuminton-push.firebaseapp.com',
          projectId:'jayuminton-push',
          storageBucket:'jayuminton-push.firebasestorage.app',
          messagingSenderId:'758697255400',
          appId:'1:758697255400:web:7214800018c65b7827045d'
        });
        return firebase.messaging();
      });
    return sdkPromise;
  }
  async function swreg(){
    if(!('serviceWorker'in navigator))throw new Error('이 iPhone에서는 웹 알림을 지원하지 않습니다.');
    var r=await navigator.serviceWorker.register('/sw.js',{scope:'/',updateViaCache:'none'});
    await navigator.serviceWorker.ready;
    try{await r.update();}catch(e){}
    return r;
  }
  async function register(showTest){
    if(busy)return busy;
    busy=(async function(){
      var m=member();if(!m)throw new Error('먼저 내 이름을 선택해 주세요.');
      if(!('Notification'in window)||Notification.permission!=='granted')throw new Error('알림 허용이 필요합니다.');
      if(!('PushManager'in window))throw new Error('이 iPhone에서는 웹 푸시를 지원하지 않습니다.');
      var r=await swreg(), msg=await messaging();
      var token=await msg.getToken({vapidKey:VAPID,serviceWorkerRegistration:r});
      if(!token)throw new Error('알림 연결 정보를 만들지 못했습니다.');
      var res=await fetch(REGISTER,{method:'POST',mode:'cors',headers:{'content-type':'application/json'},body:JSON.stringify({action:'register_web_token',memberId:m.id,memberName:m.name,token:token,userAgent:String(navigator.userAgent||'')+' JayumintonIOSPWA/1',platform:'ios-pwa'})});
      var out=null;try{out=await res.json();}catch(e){}
      if(!res.ok||!out||out.ok!==true)throw new Error('Cloudflare 알림 등록에 실패했습니다.');
      localStorage.setItem(TOKEN_KEY,token);localStorage.setItem(CONSENT_KEY,'granted');localStorage.removeItem(LATER_KEY);localStorage.setItem(ALERT_KEY,'true');localStorage.setItem(VIB_KEY,'true');
      try{if(typeof renderMemberSelfSettings==='function')renderMemberSelfSettings();}catch(e){}
      if(showTest&&r&&r.showNotification){
        try{await r.showNotification('🏸 자유민턴 알림·진동 허용 완료',{body:'대기1 또는 코트배정 시 iPhone 알림으로 알려드립니다.',icon:'/icon-192.png',badge:'/icon-192.png',tag:'jayuminton-push-consent-confirmed',renotify:true,silent:false,vibrate:[900,260,900,260,900],data:{type:'push_enabled',assignmentId:''}});}catch(e){}
      }
      status(m.name+'님 알림·진동 연결 완료');
      return token;
    })();
    try{return await busy;}finally{busy=null;}
  }
  async function unregister(){
    var token='';try{token=String(localStorage.getItem(TOKEN_KEY)||'');}catch(e){}
    if(!token)return;
    try{await fetch(UNREGISTER,{method:'POST',mode:'cors',headers:{'content-type':'application/json'},body:JSON.stringify({action:'unregister_web_token',token:token})});}catch(e){}
    try{localStorage.removeItem(TOKEN_KEY);}catch(e){}
  }
  function close(){promptOpen=false;var x=document.getElementById('jmIosPwaPushConsent');if(x)x.remove();}
  function prompt(force){
    if(promptOpen||!member()||!('Notification'in window))return;
    if(Notification.permission==='granted'){register(false).catch(function(e){status(e.message||e,true);});return;}
    if(Notification.permission==='denied'){if(force)status('iPhone 설정 > 알림에서 자유민턴 알림을 허용해 주세요.',true);return;}
    if(!force){var until=0;try{until=Number(localStorage.getItem(LATER_KEY)||0);}catch(e){}if(until>Date.now())return;}
    promptOpen=true;
    var o=document.createElement('div');o.id='jmIosPwaPushConsent';o.style.cssText='position:fixed;inset:0;z-index:2147483646;background:rgba(15,23,42,.62);display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box';
    o.innerHTML='<div style="width:min(420px,100%);background:#fff;border-radius:20px;padding:22px;box-shadow:0 22px 60px rgba(0,0,0,.28);font-family:inherit"><div style="font-size:20px;font-weight:900;color:#111827;margin-bottom:10px">🔔 알림·진동을 허용할까요?</div><div style="font-size:14px;line-height:1.65;color:#4b5563;margin-bottom:8px">대기1 또는 코트배정이 되면 자유민턴이 iPhone 알림 팝업으로 알려드립니다.</div><div style="font-size:13px;line-height:1.55;color:#6b7280;margin-bottom:18px">앱을 닫아둔 상태에서도 알림을 받을 수 있으며, 진동·햅틱은 iPhone의 알림/사운드 설정에 따라 동작합니다.</div><button type="button" id="jmIosPwaPushAllow" style="width:100%;min-height:50px;border:0;border-radius:12px;background:#315efb;color:#fff;font-size:16px;font-weight:900;margin-bottom:9px">알림·진동 허용</button><button type="button" id="jmIosPwaPushLater" style="width:100%;min-height:44px;border:0;border-radius:12px;background:#f3f4f6;color:#4b5563;font-size:14px;font-weight:800">나중에</button></div>';
    document.body.appendChild(o);
    o.querySelector('#jmIosPwaPushAllow').addEventListener('click',async function(){var b=this;b.disabled=true;b.textContent='연결 중…';try{var p=await Notification.requestPermission();if(p!=='granted'){localStorage.setItem(CONSENT_KEY,p==='denied'?'denied':'default');localStorage.setItem(ALERT_KEY,'false');localStorage.setItem(VIB_KEY,'false');status('알림이 허용되지 않았습니다.',true);close();return;}await register(true);close();}catch(e){b.disabled=false;b.textContent='알림·진동 허용';status(e&&e.message?e.message:String(e),true);}});
    o.querySelector('#jmIosPwaPushLater').addEventListener('click',function(){try{localStorage.setItem(LATER_KEY,String(Date.now()+86400000));localStorage.setItem(CONSENT_KEY,'later');localStorage.setItem(ALERT_KEY,'false');localStorage.setItem(VIB_KEY,'false');}catch(e){}try{if(typeof renderMemberSelfSettings==='function')renderMemberSelfSettings();}catch(e){}close();});
  }
  function wrap(){
    if(typeof window.toggleMemberAlertSetting==='function'&&!window.toggleMemberAlertSetting.__jmIosPushWrapped){var a=window.toggleMemberAlertSetting,w=function(){var before=true;try{before=!!memberAlertEnabled();}catch(e){}var r=a.apply(this,arguments),after=!before;try{after=!!memberAlertEnabled();}catch(e){}if(after)prompt(true);else unregister();return r;};w.__jmIosPushWrapped=true;window.toggleMemberAlertSetting=w;}
    if(typeof window.clearMemberSelfSelection==='function'&&!window.clearMemberSelfSelection.__jmIosPushWrapped){var c=window.clearMemberSelfSelection,wc=function(){unregister();return c.apply(this,arguments);};wc.__jmIosPushWrapped=true;window.clearMemberSelfSelection=wc;}
    if(typeof window.selectMemberSelf==='function'&&!window.selectMemberSelf.__jmIosPushWrapped){var s=window.selectMemberSelf,ws=function(){var r=s.apply(this,arguments);Promise.resolve(r).finally(function(){setTimeout(function(){if(Notification.permission==='granted')register(false).catch(function(){});else prompt(false);},120);});return r;};ws.__jmIosPushWrapped=true;window.selectMemberSelf=ws;}
  }
  function reconcile(){wrap();if(!member())return;if(Notification.permission==='granted')register(false).catch(function(e){status(e&&e.message?e.message:e,true);});else if(Notification.permission==='default')prompt(false);}
  try{if(Notification.permission!=='granted'&&!localStorage.getItem(CONSENT_KEY)){localStorage.setItem(ALERT_KEY,'false');localStorage.setItem(VIB_KEY,'false');}if(Notification.permission==='granted'){localStorage.setItem(CONSENT_KEY,'granted');localStorage.setItem(ALERT_KEY,'true');localStorage.setItem(VIB_KEY,'true');}}catch(e){}
  window.JayumintonPwaPush={requestConsent:function(){prompt(true);},refresh:reconcile,unregister:unregister};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(reconcile,500);},{once:true});else setTimeout(reconcile,500);
  setInterval(reconcile,2500);
})();
</script>`;

self.addEventListener('install', function () {
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (event.request.mode === 'navigate' && (url.pathname === '/' || url.pathname === '/index.html')) {
    event.respondWith((async function () {
      const response = await fetch(event.request, { cache: 'no-store' });
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('text/html')) return response;
      let html = await response.text();
      html = html.split('/firebase-messaging-sw.js').join('/sw.js');
      if (!html.includes('JAYUMINTON_IOS_PWA_PUSH_CONSENT_V1')) {
        const bodyClose = html.toLowerCase().lastIndexOf('</body>');
        html = bodyClose >= 0
          ? html.slice(0, bodyClose) + IOS_PUSH_BOOTSTRAP + html.slice(bodyClose)
          : html + IOS_PUSH_BOOTSTRAP;
      }
      const headers = new Headers(response.headers);
      headers.set('cache-control', 'no-store');
      headers.delete('content-length');
      return new Response(html, { status: response.status, statusText: response.statusText, headers: headers });
    })());
    return;
  }

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
  return [900, 260, 900, 260, 900];
}

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  const data = event.notification && event.notification.data ? event.notification.data : {};
  const assignmentId = String(data.assignmentId || '');
  const destination = new URL('/?source=pwa&open=member&app=user&mode=user&event=' + encodeURIComponent(assignmentId), self.location.origin).toString();
  event.waitUntil((async function () {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const sameOrigin = windows.find(function (client) {
      try { return new URL(client.url).origin === self.location.origin; } catch (error) { return false; }
    });
    if (sameOrigin) {
      try { await sameOrigin.focus(); sameOrigin.postMessage({ type: 'JAYUMINTON_NOTIFICATION_OPEN', assignmentId: assignmentId }); return; } catch (error) {}
    }
    if (self.clients.openWindow) await self.clients.openWindow(destination);
  })());
});

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
          data: { assignmentId: assignmentId, type: type, memberId: String(data.memberId || ''), courtNo: String(data.courtNo || '') }
        });
        if (index + 1 < repeats) await new Promise(function (resolve) { setTimeout(resolve, 1800); });
      }
    })();
  });
} catch (error) {
  console.error('[Jayuminton] unified PWA push worker initialization failed:', error);
}

self.addEventListener('message', function (event) {
  if (event.data && event.data.type === 'JAYUMINTON_SKIP_WAITING') self.skipWaiting();
});
