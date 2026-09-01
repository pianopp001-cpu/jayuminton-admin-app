#!/usr/bin/env python3
"""Add PWA installability and a native-user route guard to the member page."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

HEAD_MARKER = "JAYUMINTON_MEMBER_PWA_HEAD_V1"
if HEAD_MARKER not in text:
    head_tags = (
        '<link rel="manifest" href="/manifest.webmanifest"><!-- ' + HEAD_MARKER + ' -->\n'
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
        '<meta name="theme-color" content="#315efb">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
        '<meta name="apple-mobile-web-app-title" content="자유민턴">\n'
    )
    lower = text.lower()
    head_close = lower.find("</head>")
    if head_close < 0:
        raise SystemExit("head close marker missing for PWA tag injection")
    text = text[:head_close] + head_tags + text[head_close:]

if HEAD_MARKER not in text:
    raise SystemExit("PWA head tag injection did not apply")

# Emergency compatibility guard for the already-published Android user app.
# If a stale link/script tries to navigate the native user WebView to an
# explicit admin route, normalize it back to the member route without
# requiring a new AAB first.
ROUTE_MARKER = "JAYUMINTON_NATIVE_USER_ROUTE_GUARD_V1"
if ROUTE_MARKER not in text:
    route_script = '''<script>
/* ''' + ROUTE_MARKER + ''' */
(function guardNativeUserRouteV1(){
  var ua = String(navigator.userAgent || '');
  var nativeUser = /JayumintonUserNative|JayumintonNativeAndroid/i.test(ua) || !!window.NativeUserApp;
  if (!nativeUser) return;
  var url = new URL(window.location.href);
  var mode = String(url.searchParams.get('mode') || '').toLowerCase();
  var adminPath = /(^|\\/)admin(?:\\/|$)/i.test(url.pathname || '');
  if (mode === 'admin' || adminPath) {
    url.pathname = '/';
    url.searchParams.set('mode', 'user');
    url.searchParams.set('apkUser', '1');
    url.searchParams.set('routeGuard', 'web-v1');
    url.searchParams.set('ts', String(Date.now()));
    window.location.replace(url.toString());
  }
})();
</script>'''
    lower = text.lower()
    head_close = lower.find("</head>")
    if head_close < 0:
        raise SystemExit("head close marker missing for route guard injection")
    text = text[:head_close] + route_script + "\n" + text[head_close:]

BODY_MARKER = "JAYUMINTON_MEMBER_PWA_INSTALL_V1"
if BODY_MARKER not in text:
    script = '''<script>
/* ''' + BODY_MARKER + ''' */
(function installMemberPwaV1(){
  if (typeof IS_ADMIN !== 'undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_MEMBER_PWA_INSTALL_V1__) return;
  window.__JAYUMINTON_MEMBER_PWA_INSTALL_V1__ = true;

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(function(){});
  }

  function isStandalone(){
    try {
      return window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true;
    } catch (e) { return false; }
  }
  function isIos(){
    return /iPhone|iPad|iPod/i.test(String(navigator.userAgent || ''));
  }

  window.addEventListener('beforeinstallprompt', function(event){
    event.preventDefault();
  });

  if (!isIos() || isStandalone()) return;

  var DISMISS_KEY = 'jayuminton_pwa_ios_banner_dismissed_until_v1';
  try {
    var until = Number(localStorage.getItem(DISMISS_KEY) || 0);
    if (until && Date.now() < until) return;
  } catch (e) {}

  function dismiss(days){
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now() + days * 86400000));
    } catch (e) {}
    var bar = document.getElementById('jmPwaIosBanner');
    if (bar) bar.remove();
  }

  function openGuide(){
    if (document.getElementById('jmPwaIosGuide')) return;
    var overlay = document.createElement('div');
    overlay.id = 'jmPwaIosGuide';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:2147483600;background:rgba(15,23,42,.55);display:flex;align-items:flex-end;justify-content:center;padding:0';
    overlay.innerHTML =
      '<div style="width:100%;max-width:480px;background:#fff;border-radius:16px 16px 0 0;padding:20px 20px calc(20px + env(safe-area-inset-bottom));box-sizing:border-box;font-family:inherit">' +
        '<div style="font-size:17px;font-weight:800;color:#111827;margin-bottom:14px">홈 화면에 추가하는 방법</div>' +
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px"><div style="flex:0 0 auto;width:32px;height:32px;border-radius:50%;background:#315efb;color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center">1</div><div style="font-size:14px;color:#374151">Safari 하단(또는 상단)의 공유 버튼 <b>⬆️</b> 을 탭하세요.</div></div>' +
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px"><div style="flex:0 0 auto;width:32px;height:32px;border-radius:50%;background:#315efb;color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center">2</div><div style="font-size:14px;color:#374151">메뉴에서 <b>홈 화면에 추가</b>를 선택하세요.</div></div>' +
        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:18px"><div style="flex:0 0 auto;width:32px;height:32px;border-radius:50%;background:#315efb;color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center">3</div><div style="font-size:14px;color:#374151">오른쪽 위 <b>추가</b>를 탭하면 완료됩니다.</div></div>' +
        '<button type="button" id="jmPwaIosGuideClose" style="width:100%;min-height:46px;border:0;border-radius:10px;background:#f3f5fa;color:#111827;font-weight:800;font-size:14px">확인</button>' +
      '</div>';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', function(e){
      if (e.target === overlay || e.target.id === 'jmPwaIosGuideClose') overlay.remove();
    });
  }

  function showBanner(){
    if (document.getElementById('jmPwaIosBanner') || !document.body) return;
    var bar = document.createElement('div');
    bar.id = 'jmPwaIosBanner';
    bar.style.cssText = 'position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:2147483500;background:#111827;color:#fff;border-radius:14px;padding:12px 12px 12px 16px;display:flex;align-items:center;gap:10px;box-shadow:0 8px 24px rgba(0,0,0,.25);font-family:inherit';
    bar.innerHTML =
      '<div style="flex:1;font-size:13px;line-height:1.4">📲 아이폰 홈 화면에 추가하면 앱처럼 바로 열 수 있어요.</div>' +
      '<button type="button" id="jmPwaIosBannerOpen" style="flex:0 0 auto;min-height:34px;padding:0 14px;border:0;border-radius:8px;background:#315efb;color:#fff;font-weight:800;font-size:13px">방법 보기</button>' +
      '<button type="button" id="jmPwaIosBannerClose" aria-label="닫기" style="flex:0 0 auto;width:28px;height:28px;border:0;border-radius:50%;background:transparent;color:#9ca3af;font-size:18px;line-height:1">×</button>';
    document.body.appendChild(bar);
    bar.querySelector('#jmPwaIosBannerOpen').addEventListener('click', openGuide);
    bar.querySelector('#jmPwaIosBannerClose').addEventListener('click', function(){ dismiss(14); });
  }

  if (document.body) showBanner();
  else document.addEventListener('DOMContentLoaded', showBanner, { once: true });
})();
</script>'''
    lower = text.lower()
    body_close = lower.rfind("</body>")
    if body_close < 0:
        raise SystemExit("body close marker missing for PWA install script injection")
    text = text[:body_close] + script + "\n" + text[body_close:]

required = (
    HEAD_MARKER,
    ROUTE_MARKER,
    BODY_MARKER,
    'rel="manifest" href="/manifest.webmanifest"',
    "navigator.serviceWorker.register('/sw.js')",
    "beforeinstallprompt",
    "event.preventDefault()",
    "JayumintonUserNative",
    "url.searchParams.set('mode', 'user')",
    "routeGuard",
    "isIos()",
    "isStandalone()",
    "jmPwaIosBanner",
    "jmPwaIosGuide",
)
for marker in required:
    if marker not in text:
        raise SystemExit("PWA/route-guard contract missing: " + marker)

path.write_text(text, encoding="utf-8")
print("MEMBER_PWA_INSTALL_AND_NATIVE_ROUTE_GUARD_V1_OK")
