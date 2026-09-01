#!/usr/bin/env python3
"""Restore one-tap member moves and normalize memberMoveSelf responses."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_single_tap_move_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = re.sub(r'\s*<script id="jayuminton-member-single-tap-move-v1">[\s\S]*?</script>\s*', "\n", text, count=1, flags=re.I)

addon = r'''
<script id="jayuminton-member-single-tap-move-v1">
/* JAYUMINTON_MEMBER_MOVESELF_FULL_STATE_V3 */
(function(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JM_MOVESELF_FULL_STATE_V3__)return;
  window.__JM_MOVESELF_FULL_STATE_V3__=true;

  function unwrap(v){
    for(var i=0;i<6;i++){
      if(v&&v.state&&typeof v.state==='object'){v=v.state;continue;}
      if(v&&v.result&&typeof v.result==='object'){v=v.result;continue;}
      break;
    }
    return v;
  }
  function full(v){
    return !!(v&&typeof v==='object'&&Array.isArray(v.members)&&Array.isArray(v.waitGroups)&&v.courts&&typeof v.courts==='object');
  }

  /* The long-press status menu is injected later and calls server('memberMoveSelf')
     then renderState(response) directly. Normalize at the RPC boundary itself so
     every caller receives a complete state. Use the SAME member token from the
     mutation for getPublicState; the previous null-token refresh could not fix it. */
  var rawServer=window.server;
  if(typeof rawServer==='function'){
    window.server=async function(name,args){
      var result=await rawServer.apply(this,arguments);
      if(String(name)!=='memberMoveSelf')return result;
      var candidate=unwrap(result);
      if(full(candidate))return candidate;
      var token=Array.isArray(args)&&args.length?args[0]:null;
      var fresh=await rawServer.call(this,'getPublicState',[token]);
      var state=unwrap(fresh);
      return full(state)?state:result;
    };
  }

  var moving=false;
  function session(){
    try{var a=memberWaitSeatSessionArgs();if(a&&a.member&&a.member.id&&a.token)return a;}catch(_){}
    return null;
  }
  async function move(type,index){
    if(moving)return false;
    var a=session();if(!a)return false;
    moving=true;
    try{
      var destination={type:type,key:type==='court'?String(index):String(Number(index)+1)};
      var state=await server('memberMoveSelf',[String(a.token),String(a.member.id),destination]);
      if(state&&typeof renderState==='function')renderState(state);
      return true;
    }catch(e){alert(String(e&&e.message||e||'빈자리 이동에 실패했습니다.'));return false;}
    finally{moving=false;}
  }
  window.handleMemberWaitEmptyTap=function(groupIndex,slotIndex,event){if(event){event.preventDefault();event.stopPropagation();}move('wait',Number(groupIndex));return false;};
  window.handleEmptySlotTap=function(type,index,slotIndex,event){if(event){event.preventDefault();event.stopPropagation();}move(String(type)==='court'?'court':'wait',Number(index));return false;};
  window.memberWaitEmptySlotCard=function(groupIndex,slotIndex){return '<div class="person empty" onclick="return handleMemberWaitEmptyTap('+Number(groupIndex)+','+Number(slotIndex)+',event)" title="한 번 터치하면 이 대기자리에 들어갑니다"><span class="empty-slot-label">비어 있음</span><small>한번 탭</small></div>';};
  function wire(){
    var root=document.getElementById('memberCourts');if(!root)return;
    for(var n=1;n<=4;n++)(function(no){var c=root.querySelector('.court-'+no);if(!c)return;c.querySelectorAll('.person.empty').forEach(function(slot,i){if(slot.dataset.jmSingleTapMoveV3==='1')return;slot.dataset.jmSingleTapMoveV3='1';slot.addEventListener('click',function(e){handleEmptySlotTap('court',no,i,e);});});})(n);
  }
  if(typeof MutationObserver!=='undefined')new MutationObserver(wire).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',wire,{once:true});setInterval(wire,1800);wire();
})();
</script>
'''

pos=text.lower().rfind('</body>')
if pos<0: pos=text.lower().rfind('</html>')
if pos<0: raise SystemExit('member page closing marker missing')
text=text[:pos]+addon+'\n'+text[pos:]
for needle in ['JAYUMINTON_MEMBER_MOVESELF_FULL_STATE_V3','window.server=async function','getPublicState\',[token]','window.handleMemberWaitEmptyTap=function','window.handleEmptySlotTap=function']:
    if needle not in text: raise SystemExit('missing '+needle)
path.write_text(text,encoding='utf-8')
print('MEMBER_MOVESELF_FULL_STATE_V3_OK')
