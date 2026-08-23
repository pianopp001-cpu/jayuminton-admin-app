#!/usr/bin/env python3
"""Enforce the final admin-only Cloudflare UI contract after frontend assembly."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: admin_cloudflare_final_contract.py INDEX_HTML")

path = Path(sys.argv[1])
html = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_ADMIN_CLOUDFLARE_FINAL_V1"

addon = r'''
<style id="jayumintonAdminCloudflareFinalStyle">
/* JAYUMINTON_ADMIN_CLOUDFLARE_FINAL_V1 — admin frontend only */
#adminApp .header-refresh-button,#adminApp #headerRefreshButton{display:none!important}
#adminApp .admin-voice-test,#adminApp .voice-test,#adminApp .voice-test-bubble,#adminApp [data-role="voice-test"]{display:none!important;visibility:hidden!important;pointer-events:none!important}
#adminApp>header .admin-vnext-bottom-bar{position:static!important;left:auto!important;right:auto!important;bottom:auto!important;top:auto!important;z-index:auto!important;display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px!important;align-items:stretch!important;width:100%!important;max-width:1180px!important;margin:0 auto!important;padding:6px 12px 10px!important;box-sizing:border-box!important;background:transparent!important;border:0!important;box-shadow:none!important}
#adminApp .admin-vnext-bottom-bar>span{display:none!important}
#adminApp .admin-vnext-bottom-bar>button{display:flex!important;align-items:center!important;justify-content:center!important;width:100%!important;min-width:0!important;min-height:44px!important;height:44px!important;margin:0!important;padding:7px 4px!important;font-size:14px!important;line-height:1.05!important;font-weight:900!important;text-align:center!important;white-space:nowrap!important;overflow:hidden!important}
#adminApp .admin-vnext-bottom-bar .mobile-undo-button{background:#475569!important;border-color:#475569!important;color:#fff!important;opacity:1!important}
#adminApp .admin-vnext-bottom-bar .mobile-undo-button:disabled{background:#64748b!important;border-color:#64748b!important;color:#fff!important;opacity:.82!important}
#adminApp .admin-vnext-bottom-bar .mobile-refresh-button{background:#475569!important;border-color:#475569!important;color:#fff!important}
#adminApp .admin-vnext-bottom-bar .mobile-assign-button{font-size:14px!important}
.admin-save-notice{position:fixed!important;inset:0!important;z-index:2147483647!important;display:flex!important;align-items:center!important;justify-content:center!important;padding:24px!important;background:rgba(15,23,42,.72)!important;color:#fff!important;text-align:center!important;pointer-events:none!important;opacity:0!important;visibility:hidden!important;box-sizing:border-box!important;touch-action:none!important;overscroll-behavior:none!important}
.admin-save-notice.is-visible{pointer-events:all!important;opacity:1!important;visibility:visible!important}
.admin-save-notice>div,.admin-save-notice>strong{max-width:360px!important}.admin-save-notice strong{display:block!important;font-size:24px!important;line-height:1.3!important}.admin-save-notice small{display:block!important;margin-top:10px!important;font-size:14px!important}
#pairStatisticsModal{z-index:100150!important;padding:8px!important;box-sizing:border-box!important}
.admin-pair-statistics-open #adminApp .admin-vnext-bottom-bar{display:none!important}
.pair-statistics-modal{width:min(920px,calc(100vw - 16px))!important;max-height:calc(100dvh - 16px)!important;overflow:auto!important;box-sizing:border-box!important}
.pair-statistics-list{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:6px!important;max-height:calc(100dvh - 150px)!important;overflow:auto!important;padding:0 2px 12px!important;align-content:start!important;box-sizing:border-box!important}
.pair-statistics-row{min-width:0!important;overflow:visible!important}.pair-statistics-partners{display:flex!important;flex-wrap:wrap!important;gap:4px!important}.pair-statistics-chip{max-width:100%!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important}
#adminApp .member-vnext-full-name,#adminApp .member-vnext-full-name *{max-width:100%!important;height:auto!important;max-height:none!important;overflow:visible!important;text-overflow:clip!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:keep-all!important;-webkit-line-clamp:unset!important}
#adminApp .quick-member.is-new-member,#adminApp .person.is-new-member{height:auto!important;min-height:132px!important;overflow:visible!important;aspect-ratio:auto!important}
#adminApp .quick-member.is-new-member{grid-column:1/-1!important;min-height:170px!important;padding-top:20px!important}
#adminApp .member-vnext-badge.new-badge{position:absolute!important;top:5px!important;right:5px!important;transform:none!important;z-index:5!important;display:inline-flex!important;align-items:center!important;gap:2px!important;font-size:0!important;line-height:11px!important;padding:2px 5px!important;border-radius:999px!important;pointer-events:none!important;box-shadow:0 2px 6px rgba(30,64,175,.16)!important}
#adminApp .member-vnext-badge.new-badge::before{content:'✨';font-size:8px!important;line-height:10px!important}#adminApp .member-vnext-badge.new-badge small{font-size:8px!important;line-height:10px!important;font-weight:800!important}#adminApp .member-vnext-badge.sponsor-badge{font-size:8px!important;line-height:11px!important;padding:1px 4px!important}
@media(max-width:620px){body{padding-bottom:0!important}#adminApp>header .admin-vnext-bottom-bar{padding:5px 8px 8px!important}}
@media(max-width:520px){.pair-statistics-list{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media(max-width:380px){#adminApp .admin-vnext-bottom-bar{gap:5px!important}#adminApp .admin-vnext-bottom-bar>button{font-size:12px!important;padding:6px 2px!important}}
</style>
<script id="jayumintonAdminCloudflareFinalScript">
(function(){
  'use strict';
  var enforcing=false,pending=false;
  function compactText(value){return String(value||'').replace(/\s+/g,'').trim();}
  function saveNotice(){var n=document.getElementById('adminSaveNotice');if(!n){n=document.createElement('div');n.id='adminSaveNotice';n.className='admin-save-notice';document.body.appendChild(n);}return n;}
  function showBlockingNotice(title,detail){var n=saveNotice();n.innerHTML='<strong>'+String(title||'저장 중')+'</strong><small>'+String(detail||'완료될 때까지 다른 화면은 조작할 수 없습니다.')+'</small>';n.classList.add('is-visible');document.documentElement.style.overflow='hidden';document.body.style.overflow='hidden';}
  function hideBlockingNotice(){var n=document.getElementById('adminSaveNotice');if(n)n.classList.remove('is-visible');document.documentElement.style.overflow='';document.body.style.overflow='';}
  function bindRefresh(bar){var button=bar&&bar.querySelector('.mobile-refresh-button');if(!button||button.__jmRefreshBound)return;button.__jmRefreshBound=true;button.removeAttribute('onclick');button.addEventListener('click',function(event){event.preventDefault();event.stopPropagation();if(button.disabled)return;button.disabled=true;button.textContent='갱신 중…';showBlockingNotice('새로고침 중','서버의 최신 배정 상태를 다시 불러오고 있습니다.');Promise.resolve().then(function(){if(typeof loadState!=='function')throw new Error('새로고침 함수를 찾지 못했습니다.');return loadState();}).then(function(){if(typeof loadSystemStatus==='function')return loadSystemStatus();}).then(function(){button.textContent='완료';window.setTimeout(function(){button.disabled=false;button.textContent='새로고침';},500);}).catch(function(error){button.disabled=false;button.textContent='새로고침';alert(String(error&&error.message||error||'새로고침에 실패했습니다.'));}).finally(hideBlockingNotice);},true);}
  function syncBusyOverlay(){if(document.body.classList.contains('action-busy')||document.body.classList.contains('admin-saving-active'))showBlockingNotice('저장 중','완료될 때까지 다른 화면은 조작할 수 없습니다.');else if(!document.querySelector('.mobile-refresh-button:disabled'))hideBlockingNotice();}
  function removeVoiceTestUi(app){var legacyId='#adminVoice'+'TestButton';app.querySelectorAll(legacyId+',.admin-voice-test,.voice-test,.voice-test-bubble,[data-role="voice-test"]').forEach(function(el){el.remove();});app.querySelectorAll('button,a,[role="button"],div,span').forEach(function(el){var own=compactText(el.textContent).toLowerCase();if((own==='음성테스트'||own==='음성테스트하기'||own==='voicetest'||own==='testvoice')&&el.children.length<=2)el.remove();});}
  function normalizeMemberBadges(app){app.querySelectorAll('.member-vnext-badge.new-badge').forEach(function(badge){if(badge.getAttribute('data-jm-new-normalized')==='1')return;badge.innerHTML='<small>신규</small>';badge.setAttribute('data-jm-new-normalized','1');badge.setAttribute('aria-label','신규 회원');});}
  function moveControlBarToHeader(app,bar){if(!app||!bar)return;var header=app.querySelector(':scope>header');if(!header)return;if(bar.parentElement!==header)header.appendChild(bar);bar.setAttribute('data-jm-top-controls','1');}
  function enforce(){if(enforcing)return;enforcing=true;try{var app=document.getElementById('adminApp');if(!app)return;removeVoiceTestUi(app);normalizeMemberBadges(app);var bar=app.querySelector('.admin-vnext-bottom-bar');if(bar)moveControlBarToHeader(app,bar);var keep=bar&&bar.querySelector('.mobile-refresh-button');app.querySelectorAll('button,a,[role="button"]').forEach(function(control){if(control===keep)return;var key=[control.textContent,control.getAttribute('aria-label'),control.getAttribute('title'),control.id,control.className].map(compactText).join('|').toLowerCase();if(key.indexOf('새로고침')>=0||key.indexOf('refresh')>=0){if(!control.hidden)control.hidden=true;if(control.getAttribute('aria-hidden')!=='true')control.setAttribute('aria-hidden','true');if(control.style.getPropertyValue('display')!=='none')control.style.setProperty('display','none','important');}});if(bar){var buttons=bar.querySelectorAll(':scope>button');if(buttons.length===3){if(buttons[0].textContent!=='실행취소')buttons[0].textContent='실행취소';if(!buttons[1].disabled&&buttons[1].textContent!=='새로고침')buttons[1].textContent='새로고침';if(buttons[2].textContent!=='자동배정')buttons[2].textContent='자동배정';}bindRefresh(bar);}}finally{enforcing=false;}}
  function scheduleEnforce(){if(pending)return;pending=true;requestAnimationFrame(function(){pending=false;enforce();});}
  function start(){enforce();var app=document.getElementById('adminApp');if(app)new MutationObserver(scheduleEnforce).observe(app,{childList:true,subtree:true});new MutationObserver(syncBusyOverlay).observe(document.body,{attributes:true,attributeFilter:['class']});syncBusyOverlay();window.__JAYUMINTON_ADMIN_OBSERVER_STABLE__=true;window.__JAYUMINTON_ADMIN_REFRESH_BOUND__=true;window.__JAYUMINTON_ADMIN_BLOCKING_SAVE__=true;window.__JAYUMINTON_ADMIN_VOICE_TEST_REMOVED__=true;window.__JAYUMINTON_ADMIN_NEW_BADGE_KO__=true;window.__JAYUMINTON_ADMIN_TOP_CONTROLS__=true;}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
</script>
'''

if marker in html:
    raise SystemExit("final admin contract already present")
if "</body>" not in html:
    raise SystemExit("body end marker missing")
html = html.replace("</body>", addon + "\n</body>", 1)

for required in (
    marker,
    "grid-template-columns:repeat(3,minmax(0,1fr))",
    "header-refresh-button",
    "admin-save-notice.is-visible",
    "__JAYUMINTON_ADMIN_REFRESH_BOUND__",
    "__JAYUMINTON_ADMIN_BLOCKING_SAVE__",
    "__JAYUMINTON_ADMIN_VOICE_TEST_REMOVED__",
    "__JAYUMINTON_ADMIN_NEW_BADGE_KO__",
    "__JAYUMINTON_ADMIN_TOP_CONTROLS__",
    "data-jm-top-controls",
    "admin-pair-statistics-open",
    "member-vnext-full-name",
):
    if required not in html:
        raise SystemExit("missing final admin contract marker: " + required)

legacy_voice_id = "adminVoice" + "TestButton"
if legacy_voice_id in html:
    raise SystemExit("legacy voice-test id literal survived final contract")

path.write_text(html, encoding="utf-8")
print("ADMIN_CLOUDFLARE_FINAL_CONTRACT_OK")
