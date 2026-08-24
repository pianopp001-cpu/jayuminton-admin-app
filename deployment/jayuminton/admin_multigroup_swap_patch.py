#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
marker = "</body>"
if marker not in source:
    raise SystemExit("body marker missing")

patch = r'''
<style id="jayuminton-admin-multigroup-swap-v1">
.member.group-swap-selected,.member.selected{outline:3px solid #1565c0!important;outline-offset:-3px!important;box-shadow:0 0 0 2px rgba(21,101,192,.22)!important}
.member.group-swap-target{outline-color:#ef6c00!important;box-shadow:0 0 0 2px rgba(239,108,0,.22)!important}
</style>
<script id="jayuminton-admin-multigroup-swap-v1">
(function(){
  var sourcePick=null;
  var targetPick=null;
  function key(location){return location.type+':'+String(location.index||'');}
  function same(a,b){return !!a&&!!b&&key(a)===key(b);}
  function ids(pick){return pick?pick.ids.slice():[];}
  function clear(){
    sourcePick=null;targetPick=null;QUICK_PICK=null;SELECTED.clear();
    document.querySelectorAll('.group-swap-selected,.group-swap-target,.selected,.quick-picked').forEach(function(el){
      el.classList.remove('group-swap-selected','group-swap-target','selected','quick-picked');
    });
    if(typeof renderSelectionCount==='function')renderSelectionCount();
  }
  function sync(){
    SELECTED.clear();
    ids(sourcePick).concat(ids(targetPick)).forEach(function(id){SELECTED.add(id);});
    document.querySelectorAll('[data-member-id]').forEach(function(el){
      var id=String(el.getAttribute('data-member-id')||'');
      var inSource=sourcePick&&sourcePick.ids.indexOf(id)>=0;
      var inTarget=targetPick&&targetPick.ids.indexOf(id)>=0;
      el.classList.toggle('selected',!!(inSource||inTarget));
      el.classList.toggle('group-swap-selected',!!inSource);
      el.classList.toggle('group-swap-target',!!inTarget);
    });
    if(typeof renderSelectionCount==='function')renderSelectionCount();
  }
  function toggleIn(pick,id){
    var at=pick.ids.indexOf(id);
    if(at>=0){pick.ids.splice(at,1);return false;}
    if(pick.ids.length>=4){alert('같은 위치에서는 최대 4명까지 선택할 수 있습니다.');return false;}
    pick.ids.push(id);return true;
  }
  async function execute(){
    var left=ids(sourcePick),right=ids(targetPick);
    if(!left.length||left.length!==right.length)return;
    var previous=JSON.parse(JSON.stringify(STATE));
    clear();
    try{
      var state=await server('swapMembers',[ADMIN_PIN_VALUE,left,right]);
      renderState(state);setUndoState(previous);
    }catch(error){
      STATE=previous;renderState();alert(error.message||error);
    }
  }
  function tap(location,id,event){
    if(event&&event.target&&event.target.closest('button.small'))return;
    if(event){event.preventDefault();event.stopPropagation();}
    id=String(id); location={type:String(location.type),index:String(location.index||'')};
    if(sourcePick&&sourcePick.ids.indexOf(id)>=0){
      toggleIn(sourcePick,id);
      if(!sourcePick.ids.length){sourcePick=targetPick;targetPick=null;}
      sync();return;
    }
    if(targetPick&&targetPick.ids.indexOf(id)>=0){
      toggleIn(targetPick,id);
      if(!targetPick.ids.length)targetPick=null;
      sync();return;
    }
    if(!sourcePick){sourcePick={location:location,ids:[id]};sync();return;}
    if(same(sourcePick.location,location)){
      if(targetPick){alert('교환 상대를 선택 중입니다. 상대 선택을 다시 눌러 취소한 뒤 선택하세요.');return;}
      toggleIn(sourcePick,id);sync();return;
    }
    if(!targetPick)targetPick={location:location,ids:[]};
    if(!same(targetPick.location,location)){
      alert('교환 상대도 한 곳에서만 선택하세요. 선택한 상대를 다시 눌러 취소할 수 있습니다.');return;
    }
    if(targetPick.ids.length>=sourcePick.ids.length){
      alert('양쪽에서 같은 인원수만 선택할 수 있습니다.');return;
    }
    toggleIn(targetPick,id);sync();execute();
  }
  window.handleCourtMemberTap=function(courtNo,memberId,event){tap({type:'court',index:String(courtNo)},memberId,event);};
  window.handleWaitMemberTap=function(groupIndex,memberId,event){tap({type:'wait',index:String(groupIndex)},memberId,event);};
  window.handleExcludedMemberTap=function(memberId,event){tap({type:'active',index:''},memberId,event);};
  window.cancelQuickPick=clear;
  window.__JAYUMINTON_ADMIN_MULTIGROUP_SWAP_V1__=function(){return {maxPerLocation:4,equalCount:true,reclickCancels:true,oneByOneAutoSwap:true,titleWholeSwap:true};};
})();
</script>'''

if "jayuminton-admin-multigroup-swap-v1" not in source:
    source = source.replace(marker, patch + "\n" + marker, 1)
for needle in (
    "jayuminton-admin-multigroup-swap-v1",
    "__JAYUMINTON_ADMIN_MULTIGROUP_SWAP_V1__",
    "server('swapMembers'",
    "maxPerLocation:4",
    "reclickCancels:true",
):
    if needle not in source:
        raise SystemExit("missing " + needle)
path.write_text(source, encoding="utf-8")
