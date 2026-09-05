#!/usr/bin/env python3
"""Install the two-row fixed admin quick menu and keep auto-assign in member toolbar."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminFixedQuickMenuV20870'
if MARKER in html:
    print('ADMIN_FIXED_QUICK_MENU_ALREADY_OK')
    raise SystemExit(0)
if 'jmGameCountSelectionUnifiedV20867' not in html:
    raise SystemExit('v208.67 unified game-count selection prerequisite missing')

# Auto-assign must not remain in the original fixed bottom menu.
bottom_auto = re.compile(
    r'<button\b(?=[^>]*(?:\bid=["\']adminBottomAutoAssign["\']|\bclass=["\'][^"\']*mobile-assign-button[^"\']*["\']))'
    r'(?=[^>]*\bonclick=["\']smartAssignSelected\(\)["\'])[^>]*>.*?</button>',
    re.S | re.I,
)
matches = list(bottom_auto.finditer(html))
if len(matches) != 1:
    raise SystemExit(f'bottom auto-assign button mismatch: {len(matches)}')
html = bottom_auto.sub('', html, count=1)

addon = r'''
<style id="jmAdminFixedQuickMenuStyle">
/* jmAdminFixedQuickMenuV20870 */
#jmAdminFixedQuickMenu{position:fixed!important;left:0!important;right:0!important;bottom:0!important;z-index:2147483000!important;background:#fff!important;border-top:2px solid #334155!important;padding:5px max(5px,env(safe-area-inset-right)) calc(5px + env(safe-area-inset-bottom)) max(5px,env(safe-area-inset-left))!important;box-shadow:0 -4px 18px rgba(15,23,42,.18)!important}
#jmAdminFixedQuickMenu .jm-q-first{display:grid!important;grid-template-columns:repeat(7,minmax(0,1fr)) 28px!important;gap:3px!important}
#jmAdminFixedQuickMenu .jm-q-more{display:none!important;grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:4px!important;margin-top:5px!important;padding-top:5px!important;border-top:1px solid #cbd5e1!important}
#jmAdminFixedQuickMenu.jm-open .jm-q-more{display:grid!important}
#jmAdminFixedQuickMenu button{min-width:0!important;min-height:39px!important;padding:4px 2px!important;border:1px solid #94a3b8!important;border-radius:8px!important;background:#f8fafc!important;color:#172033!important;font-size:9.5px!important;font-weight:950!important;line-height:1.12!important;white-space:normal!important;word-break:keep-all!important}
#jmAdminFixedQuickMenu .jm-q-toggle{padding:0!important;font-size:15px!important;background:#334155!important;color:#fff!important}
#jmQuickUndo{background:#dc2626!important;color:#fff!important}#jmQuickActive{background:#2563eb!important;color:#fff!important}
#jmQuickGameMinus{background:#b45309!important;color:#fff!important}#jmQuickTempTeam{background:#d4a017!important;color:#fff!important}
#jmQuickMessage{background:#0891b2!important;color:#fff!important}#jmQuickMultiSwap{background:#059669!important;color:#fff!important}
#jmQuickRefresh{background:#475569!important;color:#fff!important}
#jmToolbarAutoAssign{background:#166534!important;border-color:#166534!important;color:#fff!important;font-weight:950!important}
.jm-original-bottom-hidden{display:none!important}
body.jm-quick-collapsed{padding-bottom:58px!important}body.jm-quick-expanded{padding-bottom:154px!important}
@media(max-width:390px){#jmAdminFixedQuickMenu button{font-size:8.3px!important;padding:3px 1px!important}#jmAdminFixedQuickMenu .jm-q-first{grid-template-columns:repeat(7,minmax(0,1fr)) 24px!important;gap:2px!important}}
</style>
<script id="jmAdminFixedQuickMenuScript">
(function(){
'use strict';
if(window.__jmAdminFixedQuickMenuV20870)return;
window.__jmAdminFixedQuickMenuV20870=true;
var running=false,queued=false;
function compact(s){return String(s||'').replace(/\s+/g,'').trim();}
function toolbarButton(action){return document.querySelector('#jmUnlimitedToolbar [data-a="'+action+'"]');}
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
  if(menu)return menu;
  menu=document.createElement('section');menu.id='jmAdminFixedQuickMenu';menu.setAttribute('aria-label','관리자 빠른 메뉴');
  var first=document.createElement('div');first.className='jm-q-first';
  first.appendChild(make('jmQuickUndo','실행취소',function(){clickTarget(sourceButton('실행취소'),'실행취소 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickActive','배정대기',function(){clickTarget(toolbarButton('active'),'배정대기 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickGameMinus','게임 -1',function(){if(typeof window.decreaseSelectedGames==='function')window.decreaseSelectedGames();}));
  first.appendChild(make('jmQuickTempTeam','팀설정',function(){clickTarget(document.getElementById('jmBottomTeamButton')||toolbarButton('temp'),'팀설정 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickMessage','메시지',function(){clickTarget(toolbarButton('message'),'메시지 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickMultiSwap','다중교환',function(){clickTarget(document.getElementById('jmBottomMoveButton')||toolbarButton('swap'),'다중교환 기능을 찾을 수 없습니다.');}));
  first.appendChild(make('jmQuickRefresh','새로고침',function(){clickTarget(sourceButton('새로고침'),'새로고침 기능을 찾을 수 없습니다.');}));
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
function keepAutoInMemberToolbar(){
  var toolbar=document.getElementById('jmUnlimitedToolbar'),grid=toolbar&&toolbar.querySelector('.jm-u-grid');
  var desired=document.getElementById('jmToolbarAutoAssign');
  Array.prototype.forEach.call(document.querySelectorAll('button'),function(b){
    var auto=compact(b.textContent)==='자동배정'||/smartAssignSelected\s*\(/.test(String(b.getAttribute('onclick')||''));
    if(auto&&b!==desired)b.remove();
  });
  if(!grid)return;
  if(!desired||!document.contains(desired)){
    desired=make('jmToolbarAutoAssign','자동배정',function(){if(typeof window.smartAssignSelected==='function')window.smartAssignSelected();});
  }
  if(desired.parentElement!==grid)grid.appendChild(desired);
  var message=toolbarButton('message');if(message&&desired.nextSibling!==message)grid.insertBefore(desired,message);
}
function hideOriginalBottom(){
  var refresh=sourceButton('새로고침');
  if(refresh&&refresh.parentElement&&!refresh.parentElement.classList.contains('jm-original-bottom-hidden'))refresh.parentElement.classList.add('jm-original-bottom-hidden');
}
function ensure(){
  if(running)return;running=true;
  try{installMenu();keepAutoInMemberToolbar();hideOriginalBottom();}finally{running=false;}
}
function schedule(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;ensure();});}
function boot(){ensure();var root=document.getElementById('adminApp')||document.body;new MutationObserver(schedule).observe(root,{childList:true,subtree:true});}
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
    "['jmQuickGameZero','게임 모두 0'", "make('jmToolbarAutoAssign','자동배정'",
):
    if required not in html:
        raise SystemExit('quick menu requirement missing: ' + required)
path.write_text(html, encoding='utf-8')
print('ADMIN_FIXED_QUICK_MENU_OK')
