#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2: raise SystemExit('usage: admin_md_autoassign_slots_patch.py INDEX_HTML')
path=Path(sys.argv[1]); html=path.read_text(encoding='utf-8')
marker='__JAYUMINTON_ADMIN_MD_AUTOASSIGN_SLOTS_V1__'
if marker in html: raise SystemExit(0)
if '</body>' not in html: raise SystemExit('body missing')
addon=r'''
<script id="jayuminton-admin-md-autoassign-slots-v1">
(function(){
  'use strict';
  window.__JAYUMINTON_ADMIN_MD_AUTOASSIGN_SLOTS_V1__=true;

  function targetGroups(){
    var map=new Map();
    try{
      (EMPTY_SLOT_TARGETS||[]).forEach(function(t){
        var type=String(t.type||'');
        var index=Number(t.index);
        var key=type+':'+index;
        if(!map.has(key))map.set(key,{type:type,index:index,slots:0});
        map.get(key).slots+=1;
      });
    }catch(e){}
    return Array.from(map.values());
  }
  function currentGroup(t){
    return t.type==='court'?(STATE.courts[t.index]||[]):(STATE.waitGroups[t.index]||[]);
  }
  function activePool(){
    // Preserve user-made court/wait assignments. Only members still in the
    // unassigned active pool may be used by the administrator auto-assign.
    var occupied=new Set();
    try{Object.keys(STATE.courts||{}).forEach(function(key){(STATE.courts[key]||[]).forEach(function(id){occupied.add(String(id));});});}catch(e){}
    try{(STATE.waitGroups||[]).forEach(function(group){(group||[]).forEach(function(id){occupied.add(String(id));});});}catch(e){}
    var list=(STATE.members||[]).filter(function(m){
      return m&&String(m.status)==='active'&&!occupied.has(String(m.id));
    });
    if(typeof sortMembersByKoreanName==='function')list=sortMembersByKoreanName(list);
    return list.map(function(m){return String(m.id);});
  }
  function male(id){
    var m=typeof memberById==='function'?memberById(id):null;
    var g=String(m&&m.gender||'').toLowerCase();
    return g==='남'||g==='male'||g.indexOf('m')===0;
  }
  function partialPick(pool,count,existing){
    var picked=[];
    var menExisting=(existing||[]).filter(male).length;
    var womenExisting=(existing||[]).length-menExisting;
    var preferMale=menExisting<=womenExisting;
    while(pool.length&&picked.length<count){
      var at=pool.findIndex(function(id){return preferMale?male(id):!male(id);});
      if(at<0)at=0;
      picked.push(pool.splice(at,1)[0]);
      preferMale=!preferMale;
    }
    return picked;
  }

  window.smartAssignSelected=async function(){
    try{if(typeof pruneEmptySlotTargets==='function')pruneEmptySlotTargets();}catch(e){}
    var targets=targetGroups();
    if(!targets.length){alert('먼저 코트 또는 대기조의 비어 있는 자리를 1개~4개 선택해 주세요. 여러 위치를 연속 선택할 수 있습니다.');return;}
    var previous=JSON.parse(JSON.stringify(STATE));
    var manual=[];
    try{manual=Array.from(SELECTED||[]).map(String).filter(Boolean);}catch(e){}
    var pool=manual.length?manual:activePool();
    var assigned=0;
    try{
      for(var i=0;i<targets.length;i+=1){
        var t=targets[i], group=currentGroup(t).slice();
        var actualFree=Math.max(0,4-group.length);
        var wanted=Math.min(actualFree,Number(t.slots||0),pool.length);
        if(wanted<=0)continue;
        var ids=[];
        if(manual.length){
          ids=pool.splice(0,wanted);
        }else if(group.length+wanted===4&&wanted===actualFree&&typeof autoPickCourtFillIds==='function'){
          var existing=group.map(function(id){return memberById(id);}).filter(Boolean);
          var auto=autoPickCourtFillIds(existing).map(String).filter(function(id){return pool.indexOf(id)>=0;});
          if(auto.length===wanted){
            ids=auto;
            var chosen=new Set(ids);pool=pool.filter(function(id){return !chosen.has(id);});
          }else if(pool.length<=wanted){
            ids=pool.splice(0,wanted);
          }else{
            ids=partialPick(pool,wanted,group);
          }
        }else{
          ids=partialPick(pool,wanted,group);
        }
        if(!ids.length)continue;
        var method=t.type==='court'?'autoFillCourt':'autoFillWaitGroup';
        var next=await server(method,[ADMIN_PIN_VALUE,t.index,ids]);
        if(next&&next.members)renderState(next);
        assigned+=ids.length;
      }
      try{SELECTED.clear();}catch(e){}
      try{if(typeof clearEmptySlotTargets==='function')clearEmptySlotTargets();}catch(e){}
      renderState();
      if(assigned&&typeof setUndoState==='function')setUndoState(previous);
      if(!assigned)alert('선택한 빈자리에 배정할 코트배정 대기 인원이 없습니다.');
    }catch(error){
      STATE=previous;
      renderState();
      alert(error.message||error);
    }
  };
})();
</script>
<!-- __JAYUMINTON_ADMIN_MD_AUTOASSIGN_SLOTS_V1__ -->
'''
html=html.replace('</body>',addon+'\n</body>',1)
for req in (marker,'targetGroups()','EMPTY_SLOT_TARGETS','1개~4개','autoFillCourt','autoFillWaitGroup','pool.length<=wanted','occupied=new Set()','!occupied.has(String(m.id))'):
    if req not in html: raise SystemExit('autoassign slots marker missing '+req)
path.write_text(html,encoding='utf-8')
print('ADMIN_MD_AUTOASSIGN_SLOTS_V1_OK')
