#!/usr/bin/env python3
"""Unify the two admin member-selection stores used by game-count controls.

The v208.66 UI has the legacy ``SELECTED`` set and the newer unlimited-toolbar
``window.__jmUnlimitedSelected`` set. Card taps are captured by the newer
toolbar, while the game-count buttons still read only ``SELECTED``. Therefore
visibly selected cards are reported as no selection. This patch makes all
game-count actions read the union, synchronizes Select All, and adds an explicit
Clear All button.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')

MARKER = 'jmGameCountSelectionUnifiedV20867'
if MARKER in html:
    print('ADMIN_GAME_COUNT_SELECTION_FIX_ALREADY_OK')
    raise SystemExit(0)

select_button = '<button type="button" onclick="selectAllMembers()">멤버 모두선택</button>'
clear_button = select_button + '\n        <button type="button" id="jmGameCountClearSelection" onclick="clearGameCountSelectionV20867()">전체 해제</button>'
if html.count(select_button) != 1:
    raise SystemExit(f'game-count select-all anchor mismatch: {html.count(select_button)}')
html = html.replace(select_button, clear_button, 1)

addon = r'''
<script id="jmGameCountSelectionFixV20867">
(function(){
  'use strict';
  if(window.__jmGameCountSelectionUnifiedV20867)return;
  window.__jmGameCountSelectionUnifiedV20867=true;

  function allStoredSelectionIds(){
    var ids=new Set();
    try{Array.from(SELECTED||[]).forEach(function(id){ids.add(String(id));});}catch(_){}
    try{Array.from(window.__jmUnlimitedSelected||[]).forEach(function(id){ids.add(String(id));});}catch(_){}
    var valid=new Set();
    try{(STATE.members||[]).forEach(function(member){if(member&&member.id!=null)valid.add(String(member.id));});}catch(_){}
    return Array.from(ids).filter(function(id){return valid.has(id);});
  }

  function clearBothSelections(){
    try{SELECTED.clear();}catch(_){}
    try{if(typeof window.__jmClearUnlimitedSelectedV1==='function')window.__jmClearUnlimitedSelectedV1();
        else if(window.__jmUnlimitedSelected&&window.__jmUnlimitedSelected.clear)window.__jmUnlimitedSelected.clear();}catch(_){}
    try{if(typeof cancelQuickPick==='function')cancelQuickPick();}catch(_){}
  }

  window.clearGameCountSelectionV20867=function(){
    clearBothSelections();
    try{renderState();}catch(_){}
  };

  var legacySelectAll=window.selectAllMembers;
  window.selectAllMembers=function(){
    if(!IS_ADMIN)return;
    if(typeof legacySelectAll==='function')legacySelectAll();
    var ids=[];
    try{ids=(STATE.members||[]).map(function(member){return String(member.id);});}catch(_){}
    try{SELECTED=new Set(ids);}catch(_){}
    try{
      if(window.__jmUnlimitedSelected){
        window.__jmUnlimitedSelected.clear();
        ids.forEach(function(id){window.__jmUnlimitedSelected.add(id);});
      }
    }catch(_){}
    try{renderState();}catch(_){}
  };

  window.increaseSelectedGames=function(){
    var ids=allStoredSelectionIds();
    if(!ids.length){alert('게임횟수를 올릴 멤버를 선택하세요.');return;}
    var index=0,lastState=null;
    function next(){
      if(index>=ids.length){clearBothSelections();if(lastState)renderState(lastState);else loadState();return;}
      var id=ids[index++];
      server('adjustMemberGames',[ADMIN_PIN_VALUE,id,1]).then(function(state){lastState=state;next();})
        .catch(function(error){alert(error.message||error);});
    }
    next();
  };

  window.decreaseSelectedGames=function(){
    var ids=allStoredSelectionIds();
    if(!ids.length){alert('게임횟수를 내릴 멤버를 선택하세요.');return;}
    return runAction('decreaseSelectedGameCounts',[ADMIN_PIN_VALUE,ids]);
  };

  window.resetSelectedGames=function(){
    var ids=allStoredSelectionIds();
    if(!ids.length){alert('멤버를 선택하세요.');return;}
    if(!confirm('선택한 멤버의 게임 횟수를 0으로 초기화할까요?'))return;
    return runAction('resetSelectedGameCounts',[ADMIN_PIN_VALUE,ids]);
  };
})();
</script>
<!-- jmGameCountSelectionUnifiedV20867 -->
'''
if '</body>' not in html:
    raise SystemExit('body marker missing')
html = html.replace('</body>', addon + '\n</body>', 1)

for required in (
    MARKER,
    'id="jmGameCountClearSelection"',
    '>전체 해제</button>',
    'function allStoredSelectionIds()',
    'window.__jmUnlimitedSelected||[]',
    "server('adjustMemberGames',[ADMIN_PIN_VALUE,id,1])",
    "runAction('decreaseSelectedGameCounts',[ADMIN_PIN_VALUE,ids])",
    "runAction('resetSelectedGameCounts',[ADMIN_PIN_VALUE,ids])",
):
    if required not in html:
        raise SystemExit('game-count selection requirement missing: ' + required)

path.write_text(html, encoding='utf-8')
print('ADMIN_GAME_COUNT_SELECTION_FIX_OK')
