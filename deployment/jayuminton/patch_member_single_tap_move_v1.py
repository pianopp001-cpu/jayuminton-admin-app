#!/usr/bin/env python3
"""Restore one-tap member moves without mutating STATE before the server replies."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_single_tap_move_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

text = re.sub(
    r'\s*<script id="jayuminton-member-single-tap-move-v1">[\s\S]*?</script>\s*',
    "\n",
    text,
    count=1,
    flags=re.I,
)

addon = r'''
<script id="jayuminton-member-single-tap-move-v1">
/* JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V2
   A single tap on an empty court/wait slot immediately submits the member move.
   Do not optimistically rewrite STATE: older restored renderers can throw on
   partially-normalized court/wait arrays (for example reading undefined['1']).
*/
(function installMemberSingleTapMoveV2(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V2__)return;
  window.__JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V2__=true;
  window.__JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V1__=true;

  var moving=false;

  function unwrap(result){
    var value=result;
    for(var depth=0;depth<4;depth+=1){
      if(value&&value.state&&typeof value.state==='object'){value=value.state;continue;}
      if(value&&value.result&&typeof value.result==='object'){value=value.result;continue;}
      break;
    }
    return value&&typeof value==='object'?value:null;
  }

  function session(){
    try{
      if(typeof memberWaitSeatSessionArgs==='function'){
        var args=memberWaitSeatSessionArgs();
        if(args&&args.member&&args.member.id&&args.token)return args;
      }
    }catch(_){}
    var member=null,token='';
    try{member=typeof currentStoredWebPushMember==='function'?currentStoredWebPushMember():null;}catch(_){}
    try{token=typeof currentMemberSessionToken==='function'?String(currentMemberSessionToken()||''):'';}catch(_){}
    if(!member||!member.id){
      if(typeof showMemberSettingMessage==='function')showMemberSettingMessage('먼저 내 이름을 선택하세요.',true);
      return null;
    }
    if(!token){
      if(typeof showMemberSettingMessage==='function')showMemberSettingMessage('회원 인증을 다시 해주세요.',true);
      return null;
    }
    return {member:member,token:token};
  }

  function clearLegacyTapState(){
    try{
      if(typeof MEMBER_WAIT_EMPTY_TAP!=='undefined'&&MEMBER_WAIT_EMPTY_TAP&&MEMBER_WAIT_EMPTY_TAP.timer)clearTimeout(MEMBER_WAIT_EMPTY_TAP.timer);
      if(typeof MEMBER_WAIT_EMPTY_TAP!=='undefined')MEMBER_WAIT_EMPTY_TAP={key:'',tappedAt:0,timer:null};
    }catch(_){}
    try{if(typeof clearMemberWaitSeatPick==='function')clearMemberWaitSeatPick();}catch(_){}
  }

  async function refreshState(fallback){
    var next=unwrap(fallback);
    try{
      if(typeof server==='function'){
        var fresh=unwrap(await server('getPublicState',[null]));
        if(fresh)next=fresh;
      }
    }catch(_){}
    if(next&&typeof renderState==='function')renderState(next);
  }

  async function moveSelfTo(type,index){
    if(moving)return false;
    var auth=session();
    if(!auth)return false;
    type=String(type)==='court'?'court':'wait';
    index=Number(index);
    if(!Number.isFinite(index)||index<0)return false;

    moving=true;
    clearLegacyTapState();
    try{
      var destination={type:type,key:type==='court'?String(index):String(index+1)};
      var result=await server('memberMoveSelf',[String(auth.token),String(auth.member.id),destination]);
      await refreshState(result);
      return true;
    }catch(error){
      alert(String(error&&error.message||error||'빈자리 이동에 실패했습니다.'));
      return false;
    }finally{
      moving=false;
    }
  }

  window.handleMemberWaitEmptyTap=function(groupIndex,slotIndex,event){
    if(event){event.preventDefault();event.stopPropagation();}
    moveSelfTo('wait',Number(groupIndex));
    return false;
  };

  window.handleEmptySlotTap=function(type,index,slotIndex,event){
    if(event){event.preventDefault();event.stopPropagation();}
    moveSelfTo(String(type),Number(index));
    return false;
  };

  window.memberWaitEmptySlotCard=function(groupIndex,slotIndex){
    return '<div class="person empty" onclick="return handleMemberWaitEmptyTap('+Number(groupIndex)+','+Number(slotIndex)+',event)" title="한 번 터치하면 이 대기자리에 들어갑니다"><span class="empty-slot-label">비어 있음</span><small>한번 탭</small></div>';
  };

  function wireCourtEmptySlots(){
    if(typeof document==='undefined')return;
    var root=document.getElementById('memberCourts');if(!root)return;
    for(var courtNo=1;courtNo<=4;courtNo+=1){
      (function(no){
        var court=root.querySelector('.court-'+no);if(!court)return;
        court.querySelectorAll('.person.empty').forEach(function(slot,slotIndex){
          if(slot.dataset.jmSingleTapMoveV2==='1')return;
          slot.dataset.jmSingleTapMoveV2='1';
          slot.title='한 번 터치하면 이 코트 자리에 들어갑니다';
          slot.style.cursor='pointer';
          slot.addEventListener('click',function(event){handleEmptySlotTap('court',no,slotIndex,event);});
        });
      })(courtNo);
    }
  }
  if(typeof document!=='undefined'){
    if(typeof MutationObserver!=='undefined')new MutationObserver(wireCourtEmptySlots).observe(document.documentElement,{childList:true,subtree:true});
    document.addEventListener('DOMContentLoaded',wireCourtEmptySlots,{once:true});
    setInterval(wireCourtEmptySlots,1800);wireCourtEmptySlots();
  }
})();
</script>
'''

insert_at = text.lower().rfind("</body>")
if insert_at < 0:
    insert_at = text.lower().rfind("</html>")
if insert_at < 0:
    raise SystemExit("member page closing body/html marker missing")

text = text[:insert_at] + addon + "\n" + text[insert_at:]

required = [
    "JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V2",
    "window.handleMemberWaitEmptyTap=function",
    "window.handleEmptySlotTap=function",
    "server('memberMoveSelf'",
    "server('getPublicState'",
    "한 번 터치하면 이 대기자리에 들어갑니다",
    "wireCourtEmptySlots",
]
for needle in required:
    if needle not in text:
        raise SystemExit(f"single-tap member contract missing: {needle}")

if "applyOptimistic" in addon:
    raise SystemExit("optimistic STATE mutation must not return")

path.write_text(text, encoding="utf-8")
print("MEMBER_SINGLE_TAP_MOVE_V2_OK")
