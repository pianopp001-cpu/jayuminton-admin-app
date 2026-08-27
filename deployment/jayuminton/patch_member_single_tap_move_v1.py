#!/usr/bin/env python3
"""Restore the member page's one-tap move contract for every empty slot."""

from pathlib import Path
import re
import sys


if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_single_tap_move_v1.py INDEX_HTML")


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Idempotency: replace an older copy instead of stacking click handlers.
text = re.sub(
    r'\s*<script id="jayuminton-member-single-tap-move-v1">[\s\S]*?</script>\s*',
    "\n",
    text,
    count=1,
    flags=re.I,
)

addon = r'''
<script id="jayuminton-member-single-tap-move-v1">
/* JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V1
   One empty-slot tap immediately moves the signed-in member.
   The current Cloudflare compatibility response may wrap the state in
   {ok:true,state:{...}}, so always unwrap it before renderState().
*/
(function installMemberSingleTapMoveV1(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V1__)return;
  window.__JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V1__=true;

  var moving=false;

  function clone(value){
    try{return JSON.parse(JSON.stringify(value));}catch(_){return null;}
  }

  function unwrappedState(result){
    var value=result;
    for(var depth=0;depth<3;depth+=1){
      if(value&&value.state&&Array.isArray(value.state.members)){value=value.state;continue;}
      break;
    }
    return value&&Array.isArray(value.members)&&value.courts?value:null;
  }

  function session(){
    try{
      if(typeof memberWaitSeatSessionArgs==='function')return memberWaitSeatSessionArgs();
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

  function ensureShape(state){
    if(!state||typeof state!=='object')return null;
    if(!state.courts||typeof state.courts!=='object')state.courts={};
    for(var courtNo=1;courtNo<=4;courtNo+=1){
      if(!Array.isArray(state.courts[String(courtNo)]))state.courts[String(courtNo)]=[];
    }
    if(!Array.isArray(state.waitGroups))state.waitGroups=[];
    while(state.waitGroups.length<5)state.waitGroups.push([]);
    state.waitGroups=state.waitGroups.map(function(group){return Array.isArray(group)?group:[];});
    if(!Array.isArray(state.members))state.members=[];
    return state;
  }

  function targetGroup(state,type,index){
    state=ensureShape(state);
    if(!state)return null;
    return type==='court'
      ? state.courts[String(Number(index))]
      : state.waitGroups[Number(index)];
  }

  function applyOptimistic(memberId,type,index){
    var state=ensureShape(typeof STATE!=='undefined'?STATE:null);
    if(!state)return false;
    var id=String(memberId),destination=targetGroup(state,type,index);
    if(!destination||destination.length>=4)return false;

    Object.keys(state.courts).forEach(function(key){
      state.courts[key]=state.courts[key].filter(function(value){return String(value)!==id;});
    });
    state.waitGroups=state.waitGroups.map(function(group){
      return group.filter(function(value){return String(value)!==id;});
    });
    destination=targetGroup(state,type,index);
    if(destination.indexOf(id)<0)destination.push(id);
    state.members.forEach(function(member){
      if(member&&String(member.id)===id)member.status=type==='court'?'playing':'waiting';
    });
    if(typeof renderState==='function')renderState(state);
    return true;
  }

  function clearOldDoubleTap(){
    try{
      if(MEMBER_WAIT_EMPTY_TAP&&MEMBER_WAIT_EMPTY_TAP.timer)clearTimeout(MEMBER_WAIT_EMPTY_TAP.timer);
      MEMBER_WAIT_EMPTY_TAP={key:'',tappedAt:0,timer:null};
    }catch(_){}
    try{if(typeof clearMemberWaitSeatPick==='function')clearMemberWaitSeatPick();}catch(_){}
  }

  async function moveSelfTo(type,index){
    if(moving)return false;
    var auth=session();
    if(!auth)return false;
    type=String(type)==='court'?'court':'wait';
    index=Number(index);
    var current=ensureShape(typeof STATE!=='undefined'?STATE:null);
    var group=targetGroup(current,type,index);
    if(!group||group.length>=4){
      alert('선택한 위치에는 빈자리가 없습니다.');
      return false;
    }

    moving=true;
    clearOldDoubleTap();
    var previous=clone(current);
    applyOptimistic(String(auth.member.id),type,index);
    var destination={type:type,key:type==='court'?String(index):String(index+1)};

    try{
      var result=await server('memberMoveSelf',[
        String(auth.token),String(auth.member.id),destination
      ]);
      var next=unwrappedState(result);
      if(!next)throw new Error('서버 상태 응답을 읽을 수 없습니다.');
      ensureShape(next);
      if(typeof renderState==='function')renderState(next);
      return true;
    }catch(error){
      if(previous&&typeof renderState==='function')renderState(previous);
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
    "JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V1",
    "window.handleMemberWaitEmptyTap=function",
    "window.handleEmptySlotTap=function",
    "server('memberMoveSelf'",
    "function unwrappedState(result)",
    "value&&value.state&&Array.isArray(value.state.members)",
    "한 번 터치하면 이 대기자리에 들어갑니다",
]
for needle in required:
    if needle not in text:
        raise SystemExit(f"single-tap member contract missing: {needle}")

path.write_text(text, encoding="utf-8")
print("MEMBER_SINGLE_TAP_MOVE_V1_OK")
