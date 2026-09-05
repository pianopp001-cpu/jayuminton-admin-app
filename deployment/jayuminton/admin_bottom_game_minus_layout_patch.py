#!/usr/bin/env python3
"""Keep auto-assign only in the member/team toolbar and game -1 in bottom bar."""
from pathlib import Path
import re
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminAutoAssignToolbarGameMinusV20869'
if MARKER in html:
    print('ADMIN_AUTO_ASSIGN_TOOLBAR_GAME_MINUS_ALREADY_OK')
    raise SystemExit(0)
if 'jmGameCountSelectionUnifiedV20867' not in html:
    raise SystemExit('v208.67 unified game-count selection prerequisite missing')

bottom_auto = re.compile(
    r'<button\b(?=[^>]*(?:\bid=["\']adminBottomAutoAssign["\']|\bclass=["\'][^"\']*mobile-assign-button[^"\']*["\']))'
    r'(?=[^>]*\bonclick=["\']smartAssignSelected\(\)["\'])[^>]*>.*?</button>',
    re.S | re.I,
)
matches = list(bottom_auto.finditer(html))
if len(matches) != 1:
    raise SystemExit(f'bottom auto-assign button mismatch: {len(matches)}')
html = bottom_auto.sub(
    '<button id="adminBottomGameMinus" class="game-minus-button" type="button" '
    'onclick="decreaseSelectedGames()">게임 -1</button>', html, count=1)

runtime = r'''
<style id="jmAdminAutoAssignToolbarGameMinusStyle">
/* jmAdminAutoAssignToolbarGameMinusV20869 */
#jmToolbarAutoAssign{background:#166534!important;border-color:#166534!important;color:#fff!important;font-weight:950!important}
#adminBottomGameMinus{background:#b45309!important;border-color:#b45309!important;color:#fff!important;font-weight:950!important}
</style>
<script id="jmAdminAutoAssignToolbarGameMinusScript">
(function(){
'use strict';
if(window.__jmAdminAutoAssignToolbarGameMinusV20869)return;
window.__jmAdminAutoAssignToolbarGameMinusV20869=true;
var running=false,queued=false;
function label(b){return String(b&&b.textContent||'').replace(/\s+/g,'').trim();}
function isAuto(b){return !!b&&(label(b)==='자동배정'||/smartAssignSelected\s*\(/.test(String(b.getAttribute('onclick')||'')));}
function ensure(){
  if(running)return;running=true;
  try{
    var toolbar=document.getElementById('jmUnlimitedToolbar');
    var grid=toolbar&&toolbar.querySelector('.jm-u-grid');
    var desired=document.getElementById('jmToolbarAutoAssign');
    Array.prototype.forEach.call(document.querySelectorAll('button'),function(b){
      if(isAuto(b)&&b!==desired)b.remove();
    });
    if(grid){
      if(!desired||!document.contains(desired)){
        desired=document.createElement('button');
        desired.id='jmToolbarAutoAssign';desired.type='button';desired.textContent='자동배정';
        desired.addEventListener('click',function(e){
          e.preventDefault();e.stopImmediatePropagation();
          if(typeof window.smartAssignSelected==='function')window.smartAssignSelected();
        },true);
      }
      if(desired.parentElement!==grid)grid.appendChild(desired);
      var message=grid.querySelector('[data-a="message"]');
      if(message&&desired.nextSibling!==message)grid.insertBefore(desired,message);
    }
    var minus=document.getElementById('adminBottomGameMinus');
    Array.prototype.forEach.call(document.querySelectorAll('button'),function(b){
      if(label(b)==='게임-1'&&b!==minus)b.remove();
    });
    if(!minus){
      var refresh=Array.prototype.find.call(document.querySelectorAll('button'),function(b){return label(b)==='새로고침';});
      if(refresh&&refresh.parentElement){
        minus=document.createElement('button');minus.id='adminBottomGameMinus';minus.type='button';
        minus.className=refresh.className||'';minus.textContent='게임 -1';
        minus.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();if(typeof window.decreaseSelectedGames==='function')window.decreaseSelectedGames();});
        refresh.parentElement.insertBefore(minus,refresh);
      }
    }
  }finally{running=false;}
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
html = html[:close] + runtime + '\n' + html[close:]
for required in (
    MARKER, 'id="jmToolbarAutoAssign"', 'window.smartAssignSelected()',
    'id="adminBottomGameMinus"',
    'onclick="decreaseSelectedGames()">게임 -1</button>',
    "label(b)==='자동배정'",
):
    if required not in html:
        raise SystemExit('layout requirement missing: ' + required)
path.write_text(html, encoding='utf-8')
print('ADMIN_AUTO_ASSIGN_TOOLBAR_GAME_MINUS_OK')
