#!/usr/bin/env python3
"""Install the fixed admin quick menu and remove duplicate/auto-assign UI."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminFixedQuickMenuV20876'
if MARKER in html:
    print('ADMIN_FIXED_QUICK_MENU_ALREADY_OK')
    raise SystemExit(0)
if 'jmGameCountSelectionUnifiedV20867' not in html:
    raise SystemExit('v208.67 unified game-count selection prerequisite missing')

# The game-count controls now live only in the fixed quick menu.
setup_title = '멤버등록·비밀번호·게임횟수·콕제출체크'
if setup_title in html:
    html = html.replace(setup_title, '멤버등록·비밀번호·콕제출체크', 1)
elif '멤버등록·비밀번호·콕제출체크' not in html:
    raise SystemExit('admin setup title anchor missing')

# Auto-assign must not remain in the original fixed bottom menu.
bottom_auto = re.compile(
    r'<button\b(?=[^>]*(?:\bid=["\']adminBottomAutoAssign["\']|\bclass=["\'][^"\']*mobile-assign-button[^"\']*["\']))'
    r'(?=[^>]*\bonclick=["\']smartAssignSelected\(\)["\'])[^>]*>.*?</button>',
    re.S | re.I,
)
matches = list(bottom_auto.finditer(html))
if len(matches) > 1:
    raise SystemExit(f'bottom auto-assign button mismatch: {len(matches)}')
html = bottom_auto.sub('', html, count=1)

# Remove the original fixed bar from the APK document itself. It is not merely
# hidden: no old rounded button shells or reserved layout area may remain.
legacy_bar = re.compile(
    r'<div\b(?=[^>]*\bclass=["\'][^"\']*\bmobile-quick-bar\b[^"\']*\badmin-vnext-bottom-bar\b[^"\']*["\'])[^>]*>.*?</div>',
    re.S | re.I,
)
legacy_matches = list(legacy_bar.finditer(html))
if len(legacy_matches) > 1:
    raise SystemExit(f'legacy fixed bottom bar mismatch: {len(legacy_matches)}')
html = legacy_bar.sub('', html, count=1)

addon = r'''
<style id="jmAdminFixedQuickMenuStyle">
/* jmAdminFixedQuickMenuV20876 */
#jmAdminFixedQuickMenu{position:fixed!important;left:0!important;right:0!important;bottom:0!important;z-index:2147483000!important;background:#fff!important;border-top:2px solid #334155!important;padding:5px max(5px,env(safe-area-inset-right)) calc(5px + env(safe-area-inset-bottom)) max(5px,env(safe-area-inset-left))!important;box-shadow:0 -4px 18px rgba(15,23,42,.18)!important}
#jmAdminFixedQuickMenu .jm-q-first{display:grid!important;grid-template-columns:repeat(7,minmax(0,1fr)) 28px!important;gap:4px!important;padding:2px!important;border-radius:11px!important;background:#e2e8f0!important;box-shadow:0 2px 8px rgba(15,23,42,.16)!important}
#jmAdminFixedQuickMenu .jm-q-more{display:none!important;grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:4px!important;margin-top:5px!important;padding-top:5px!important;border-top:1px solid #cbd5e1!important}
#jmAdminFixedQuickMenu.jm-open .jm-q-more{display:grid!important}
#jmAdminFixedQuickMenu button{min-width:0!important;min-height:39px!important;padding:4px 2px!important;border:1px solid #94a3b8!important;border-radius:8px!important;background:#f8fafc!important;color:#172033!important;font-size:9.5px!important;font-weight:950!important;line-height:1.12!important;white-space:normal!important;word-break:keep-all!important}
#jmAdminFixedQuickMenu .jm-q-first button{min-height:45px!important;border-width:2px!important;border-color:rgba(255,255,255,.72)!important;font-size:10.5px!important;font-weight:1000!important;text-shadow:0 1px 1px rgba(0,0,0,.22)!important;box-shadow:0 2px 5px rgba(15,23,42,.25)!important}
#jmAdminFixedQuickMenu .jm-q-toggle{padding:0!important;font-size:17px!important;background:#1e293b!important;color:#fff!important}
#jmAdminFixedQuickMenu #jmQuickUndo{background:#dc2626!important;color:#fff!important}#jmAdminFixedQuickMenu #jmQuickActive{background:#2563eb!important;color:#fff!important}
#jmAdminFixedQuickMenu #jmQuickGameMinus{background:#c2410c!important;color:#fff!important}#jmAdminFixedQuickMenu #jmQuickTempTeam{background:#ca8a04!important;color:#fff!important}
#jmAdminFixedQuickMenu #jmQuickMessage{background:#0284c7!important;color:#fff!important}#jmAdminFixedQuickMenu #jmQuickMultiSwap{background:#059669!important;color:#fff!important}
#jmAdminFixedQuickMenu #jmQuickRefresh{background:#475569!important;color:#fff!important}
#jmAdminFixedQuickMenu #jmQuickAll{background:#334155!important;color:#fff!important}#jmAdminFixedQuickMenu #jmQuickBefore{background:#ea580c!important;color:#fff!important}
#jmAdminFixedQuickMenu #jmQuickAway{background:#64748b!important;color:#fff!important}#jmAdminFixedQuickMenu #jmQuickDelete{background:#b91c1c!important;color:#fff!important}
#jmAdminFixedQuickMenu #jmQuickTempClear{background:#fef3c7!important;border-color:#d4a017!important;color:#7a5200!important}
#jmAdminFixedQuickMenu #jmQuickPerm{background:#7c3aed!important;color:#fff!important}#jmAdminFixedQuickMenu #jmQuickPermClear{background:#ede9fe!important;border-color:#8b5cf6!important;color:#5b21b6!important}
#jmAdminFixedQuickMenu #jmQuickClear{background:#e2e8f0!important;border-color:#64748b!important;color:#1e293b!important}
#jmAdminFixedQuickMenu #jmQuickGamePlus{background:#0f766e!important;color:#fff!important}#jmAdminFixedQuickMenu #jmQuickGameZero{background:#991b1b!important;color:#fff!important}
#jmAdminFixedQuickMenu .jm-q-selection{position:absolute!important;left:7px!important;top:-23px!important;display:flex!important;align-items:center!important;justify-content:center!important;width:max-content!important;min-width:66px!important;padding:3px 8px!important;border:1px solid #15803d!important;border-radius:7px!important;background:rgba(236,253,245,.96)!important;color:#14532d!important;font-size:10.5px!important;font-weight:950!important;line-height:1.1!important;box-shadow:0 1px 4px rgba(15,118,55,.18)!important;pointer-events:none!important}
#jmAdminFixedQuickMenu .jm-q-kok{position:absolute!important;right:7px!important;top:-25px!important;min-height:23px!important;padding:3px 9px!important;border:1px solid #7c3aed!important;border-radius:7px!important;background:#f5f3ff!important;color:#5b21b6!important;font-size:10px!important;font-weight:950!important;box-shadow:0 1px 4px rgba(91,33,182,.18)!important}
#adminApp #jmUnlimitedToolbar{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;max-height:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important}
#adminApp .jm-unlimited-check{display:none!important;visibility:hidden!important;width:0!important;height:0!important;min-width:0!important;min-height:0!important;padding:0!important;margin:0!important;border:0!important;box-shadow:none!important;overflow:hidden!important}
#adminApp .quick-empty-slot.auto-assign-target{outline:0!important;border-color:inherit!important;background:inherit!important;box-shadow:none!important}
#adminApp .quick-empty-slot.auto-assign-target .empty-slot-label::after{content:none!important;display:none!important}
#adminApp .quick-empty-slot.jm-manual-first-target{outline:2px dashed #2563eb!important;outline-offset:-3px!important;background:#eff6ff!important;box-shadow:none!important}
#adminApp .admin-kok-submit-panel #kokSubmitRoster.jm-kok-roster-list{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:4px!important;margin-top:6px!important}
#adminApp .admin-kok-submit-panel .jm-kok-row{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;grid-template-areas:'name button' 'meta button'!important;column-gap:4px!important;row-gap:0!important;min-height:43px!important;padding:3px 4px!important;border:1px solid #dbe3ee!important;background:#fff!important}
#adminApp .admin-kok-submit-panel .jm-kok-row .name{grid-area:name!important;font-size:11px!important;font-weight:900!important;line-height:1.15!important;cursor:pointer!important}
#adminApp .admin-kok-submit-panel .jm-kok-row .meta{grid-area:meta!important;font-size:8.5px!important;line-height:1.1!important;white-space:nowrap!important}
#adminApp .admin-kok-submit-panel .jm-kok-complete-btn{grid-area:button!important;align-self:stretch!important;min-height:31px!important;min-width:38px!important;margin:0!important;padding:2px 4px!important;font-size:9px!important;border-radius:7px!important}
#adminApp .admin-kok-submit-panel .jm-kok-row.jm-kok-inactive{order:2!important;background:#f1f5f9!important;opacity:.58!important}
#adminApp .admin-kok-submit-panel .jm-kok-row.jm-kok-inactive .name{text-decoration:line-through!important}
#adminApp .admin-kok-submit-panel.jm-kok-overlay{display:block!important;position:fixed!important;z-index:2147482990!important;left:8px!important;right:8px!important;top:max(44px,env(safe-area-inset-top))!important;bottom:70px!important;margin:0!important;padding:10px!important;overflow:auto!important;background:#fff!important;border:2px solid #7c3aed!important;border-radius:14px!important;box-shadow:0 12px 40px rgba(15,23,42,.32)!important}
@media(min-width:700px){#adminApp .admin-kok-submit-panel #kokSubmitRoster.jm-kok-roster-list{grid-template-columns:repeat(3,minmax(0,1fr))!important}}
html body .jm-original-bottom-hidden,html body #adminApp .jm-original-bottom-hidden{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;max-height:0!important;padding:0!important;margin:0!important;border:0!important;overflow:hidden!important}
body.jm-quick-collapsed{padding-bottom:66px!important}body.jm-quick-expanded{padding-bottom:162px!important}
@media(max-width:390px){#jmAdminFixedQuickMenu button{font-size:8.3px!important;padding:3px 1px!important}#jmAdminFixedQuickMenu .jm-q-first{grid-template-columns:repeat(7,minmax(0,1fr)) 24px!important;gap:2px!important}}
</style>
<script id="jmAdminFixedQuickMenuScript">
(function(){
'use strict';
if(window.__jmAdminFixedQuickMenuV20876)return;
window.__jmAdminFixedQuickMenuV20876=true;
var running=false,queued=false;
var manualFirstTarget=null,kokWasClosed=false;
function compact(s){return String(s||'').replace(/\s+/g,'').trim();}
function adminReady(){
  var app=document.getElementById('adminApp');
  var hasCredential=false;try{hasCredential=typeof ADMIN_PIN_VALUE!=='undefined'&&!!ADMIN_PIN_VALUE;}catch(_){}
  if(!app||!hasCredential||app.classList.contains('hidden')||app.hidden)return false;
  try{var css=getComputedStyle(app);if(css.display==='none'||css.visibility==='hidden')return false;}catch(_){}
  return true;
}
function toolbarButton(action){return document.querySelector('#jmUnlimitedToolbar [data-a="'+action+'"]');}
function selectedIds(){
  var ids=new Set();
  try{Array.from(window.__jmUnlimitedSelected||[]).forEach(function(id){ids.add(String(id));});}catch(_){}
  try{Array.from(SELECTED||[]).forEach(function(id){ids.add(String(id));});}catch(_){}
  return Array.from(ids);
}
function selectedCount(){return selectedIds().length;}
function clearManualFirstTarget(){if(manualFirstTarget&&manualFirstTarget.classList)manualFirstTarget.classList.remove('jm-manual-first-target');manualFirstTarget=null;}
function toggleTempTeam(){
  var ids=selectedIds();if(!ids.length){alert('멤버를 먼저 선택하세요.');return;}
  var teamed=new Set();
  try{(STATE.tempPairs||[]).forEach(function(g){[g&&g.members,g&&g.pairA,g&&g.pairB].forEach(function(a){(Array.isArray(a)?a:[]).forEach(function(id){teamed.add(String(id));});});});}catch(_){}
  clickTarget(toolbarButton(ids.every(function(id){return teamed.has(String(id));})?'temp-clear':'temp'),'팀설정 기능을 찾을 수 없습니다.');
}
function sourceButton(text){
  return Array.prototype.find.call(document.querySelectorAll('button'),function(b){
    return !b.closest('#jmAdminFixedQuickMenu')&&compact(b.textContent)===compact(text);
  })||null;
}
function clickTarget(target,error){
  if(target){target.click();return;}
  if(typeof alert==='function')alert(error||'기능 버튼을 찾을 수 없습니다.');
}
function make(id,text,fn,cls){
  var b=document.createElement('button');b.id=id;b.type='button';b.textContent=text;
  if(cls)b.className=cls;
  b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();fn();});
  return b;
}
function installMenu(){
  var menu=document.getElementById('jmAdminFixedQuickMenu');
  if(menu){
    if(!document.getElementById('jmQuickSelectionCount')){var existingSelection=document.createElement('div');existingSelection.id='jmQuickSelectionCount';existingSelection.className='jm-q-selection';existingSelection.setAttribute('aria-live','polite');existingSelection.textContent='선택 0명';menu.insertBefore(existingSelection,menu.firstChild);}
    return menu;
  }
  menu=document.createElement('section');menu.id='jmAdminFixedQuickMenu';menu.setAttribute('aria-label','관리자 빠른 메뉴');
  var selection=document.createElement('div');selection.id='jmQuickSelectionCount';selection.className='jm-q-selection';selection.setAttribute('aria-live','polite');selection.textContent='선택 0명';menu.appendChild(selection);
  var kok=make('jmQuickKok','콕체크',function(){var panel=document.querySelector('.admin-kok-submit-panel'),details=panel&&panel.closest('details');if(!panel)return alert('콕 제출 명단을 찾을 수 없습니다.');var opening=!panel.classList.contains('jm-kok-overlay');if(opening){kokWasClosed=!!(details&&!details.open);if(details)details.open=true;panel.classList.add('jm-kok-overlay');kok.textContent='콕 닫기';}else{panel.classList.remove('jm-kok-overlay');kok.textContent='콕체크';if(details&&kokWasClosed)details.open=false;}},'jm-q-kok');menu.appendChild(kok);
  var first=document.createElement('div');first.className='jm-q-first';
  first.appendChild(make('jmQuickUndo','실행취소',function(){if(typeof window.undoLastAction==='function')window.undoLastAction();else if(typeof undoLastAction==='function')undoLastAction();else alert('실행취소 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickActive','배정대기',function(){clickTarget(toolbarButton('active'),'배정대기 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickGameMinus','게임 -1',function(){if(typeof window.decreaseSelectedGames==='function')window.decreaseSelectedGames();}));
  first.appendChild(make('jmQuickTempTeam','팀설정',toggleTempTeam));
  first.appendChild(make('jmQuickMessage','메시지',function(){clickTarget(toolbarButton('message'),'메시지 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickMultiSwap','다중교환',function(){clickTarget(toolbarButton('swap'),'다중교환 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickRefresh','새로고침',function(){if(typeof window.refreshAdminState==='function')window.refreshAdminState();else if(typeof refreshAdminState==='function')refreshAdminState();else if(typeof loadState==='function')loadState();else alert('새로고침 기능을 찾을 수 없습니다.');}));
  var toggle=make('jmQuickToggle','▼',function(){
    var open=menu.classList.toggle('jm-open');toggle.textContent=open?'▲':'▼';
    toggle.setAttribute('aria-expanded',open?'true':'false');
    document.body.classList.toggle('jm-quick-expanded',open);
    document.body.classList.toggle('jm-quick-collapsed',!open);
  },'jm-q-toggle');toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','추가 메뉴 펼치기');
  first.appendChild(toggle);menu.appendChild(first);
  var more=document.createElement('div');more.className='jm-q-more';
  [
    ['jmQuickAll','모두선택',function(){clickTarget(toolbarButton('all'));}],
    ['jmQuickBefore','도착전',function(){clickTarget(toolbarButton('before'));}],
    ['jmQuickAway','귀가',function(){clickTarget(toolbarButton('away'));}],
    ['jmQuickDelete','회원삭제',function(){clickTarget(toolbarButton('delete'));}],
    ['jmQuickTempClear','임시팀해제',function(){clickTarget(toolbarButton('temp-clear'));}],
    ['jmQuickPerm','영구팀설정',function(){clickTarget(toolbarButton('perm'));}],
    ['jmQuickPermClear','영구팀해제',function(){clickTarget(toolbarButton('perm-clear'));}],
    ['jmQuickClear','선택해제',function(){clickTarget(toolbarButton('clear'));}],
    ['jmQuickGamePlus','게임 +1',function(){if(typeof window.increaseSelectedGames==='function')window.increaseSelectedGames();}],
    ['jmQuickGameZero','게임 모두 0',function(){if(typeof window.resetSelectedGames==='function')window.resetSelectedGames();}]
  ].forEach(function(x){more.appendChild(make(x[0],x[1],x[2]));});
  menu.appendChild(more);document.body.appendChild(menu);document.body.classList.add('jm-quick-collapsed');
  return menu;
}
function removeAutoAssign(){
  Array.prototype.forEach.call(document.querySelectorAll('button'),function(b){
    var auto=compact(b.textContent)==='자동배정'||/smartAssignSelected\s*\(/.test(String(b.getAttribute('onclick')||''));
    if(auto)b.remove();
  });
}
function removeDuplicatePanels(){
  Array.prototype.forEach.call(document.querySelectorAll('.admin-game-count-panel'),function(node){node.remove();});
  Array.prototype.forEach.call(document.querySelectorAll('h1,h2,h3,strong'),function(h){
    if(compact(h.textContent)==='게임횟수카운트조정'){var card=h.closest('.card');if(card)card.remove();}
  });
}
function updateSelectionCount(){
  var badge=document.getElementById('jmQuickSelectionCount');if(badge)badge.textContent=manualFirstTarget?'빈자리 선택됨 · 멤버 누르기':'선택 '+selectedCount()+'명';
}
function removeLegacyBottom(){
  Array.prototype.forEach.call(document.querySelectorAll('#adminApp>.admin-vnext-bottom-bar,#jmBottomActionRowV2079'),function(node){node.remove();});
}
function ensure(){
  if(running)return;running=true;
  try{
    var existing=document.getElementById('jmAdminFixedQuickMenu');
    if(!adminReady()){
      if(existing&&existing.style.getPropertyValue('display')!=='none')existing.style.setProperty('display','none','important');
      document.body.classList.remove('jm-quick-collapsed','jm-quick-expanded');
      return;
    }
    var menu=installMenu();
    if(menu.style.getPropertyValue('display')==='none')menu.style.removeProperty('display');
    if(!document.body.classList.contains('jm-quick-collapsed')&&!document.body.classList.contains('jm-quick-expanded'))document.body.classList.add('jm-quick-collapsed');
    removeAutoAssign();removeDuplicatePanels();removeLegacyBottom();updateSelectionCount();
  }finally{running=false;}
}
function schedule(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;ensure();});}
function boot(){
  ensure();
  var app=document.getElementById('adminApp');
  var root=app||document.body;
  new MutationObserver(schedule).observe(root,{childList:true,subtree:true});
  if(app)new MutationObserver(schedule).observe(app,{attributes:true,attributeFilter:['class','style','hidden']});
  document.addEventListener('click',function(ev){
    var empty=ev.target&&ev.target.closest&&ev.target.closest('.empty,.quick-empty-slot,[onclick*="handleEmptySlotTap"],[onclick*="handleMemberWaitEmptyTap"]');
    if(empty&&selectedCount()===0){
      ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
      if(manualFirstTarget===empty)clearManualFirstTarget();else{clearManualFirstTarget();manualFirstTarget=empty;empty.classList.add('jm-manual-first-target');}
      updateSelectionCount();return;
    }
    if(!manualFirstTarget)return;
    var card=ev.target&&ev.target.closest&&ev.target.closest('.member,.person:not(.empty),.quick-member,.member-card,.member-item,.player-card,.court-player');
    if(!card||card.closest('.jm-kok-row')||ev.target.closest('button,select,input,textarea,a[href]'))return;
    var target=manualFirstTarget;clearManualFirstTarget();
    setTimeout(function(){if(selectedCount()>0&&target&&target.isConnected)target.click();updateSelectionCount();},0);
  },true);
  document.addEventListener('click',function(ev){var name=ev.target&&ev.target.closest&&ev.target.closest('#kokSubmitRoster .jm-kok-row .name');if(!name)return;var row=name.closest('.jm-kok-row'),button=row&&row.querySelector('.jm-kok-complete-btn');if(button){ev.preventDefault();ev.stopPropagation();button.click();}},true);
  document.addEventListener('click',schedule,true);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
</script>
'''
close = html.lower().rfind('</body>')
if close < 0:
    raise SystemExit('body close not found')
html = html[:close] + addon + '\n' + html[close:]
for required in (
    MARKER, "menu.id='jmAdminFixedQuickMenu'", "make('jmQuickUndo','실행취소'",
    "make('jmQuickGameMinus','게임 -1'", "make('jmQuickMultiSwap','다중교환'",
    "make('jmQuickRefresh','새로고침'", "make('jmQuickToggle','▼'",
    "['jmQuickAll','모두선택'", "['jmQuickGamePlus','게임 +1'",
    "['jmQuickGameZero','게임 모두 0'", "selection.id='jmQuickSelectionCount'",
    'function removeAutoAssign()', 'function removeDuplicatePanels()',
):
    if required not in html:
        raise SystemExit('quick menu requirement missing: ' + required)
path.write_text(html, encoding='utf-8')
print('ADMIN_FIXED_QUICK_MENU_OK')
