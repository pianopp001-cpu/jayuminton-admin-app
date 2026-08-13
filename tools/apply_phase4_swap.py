from pathlib import Path

sp=Path('source-snapshot/current-main/Script.html')
cp=Path('source-snapshot/current-main/Code.js')
s=sp.read_text(encoding='utf-8')
c=cp.read_text(encoding='utf-8')

if 'function memberRequestWaitSwap(' in s or 'function memberRequestWaitSwap(' in c:
    raise SystemExit('phase4 swap already present; refusing duplicate patch')

client_anchor="""async function memberLeaveWaitGroup(){
  const a=memberWaitSeatSessionArgs(); if(!a||ACTION_IN_FLIGHT)return;
  try{const state=await server('memberLeaveWaitGroup',[a.token,String(a.member.id)]);clearMemberWaitSeatPick();renderState(state);}
  catch(e){clearMemberWaitSeatPick();alert(e.message||e);}
}
"""
if s.count(client_anchor)!=1: raise SystemExit('unsafe: client leave anchor mismatch')
client_add=r'''async function memberRequestWaitSwap(targetMemberId){
  const a=memberWaitSeatSessionArgs(); if(!a||ACTION_IN_FLIGHT)return;
  try{const result=await server('memberRequestWaitSwap',[a.token,String(a.member.id),String(targetMemberId)]);clearMemberWaitSeatPick();showMemberSettingMessage(result&&result.message?result.message:'자리 교환을 요청했어요.');}
  catch(e){clearMemberWaitSeatPick();alert(e.message||e);}
}
function handleMemberWaitOtherTap(groupIndex,targetMemberId,event){
  if(IS_ADMIN)return;
  if(event){event.preventDefault();event.stopPropagation();}
  const a=memberWaitSeatSessionArgs(); if(!a)return;
  if(String(targetMemberId)===String(a.member.id))return;
  if(MEMBER_WAIT_SEAT_PICK&&MEMBER_WAIT_SEAT_PICK.type==='self'){clearMemberWaitSeatPick();memberRequestWaitSwap(targetMemberId);return;}
  MEMBER_WAIT_SEAT_PICK={type:'other',groupIndex:Number(groupIndex),memberId:String(targetMemberId)};
  showMemberSettingMessage('내 자리를 터치하면 교환 요청을 보냅니다.');
}
let MEMBER_WAIT_SWAP_CHECKING=false;
let MEMBER_WAIT_SWAP_SHOWN='';
async function checkMemberWaitSwapRequest(){
  if(IS_ADMIN||MEMBER_WAIT_SWAP_CHECKING||ACTION_IN_FLIGHT)return;
  const a=memberWaitSeatSessionArgs(); if(!a)return;
  MEMBER_WAIT_SWAP_CHECKING=true;
  try{
    const req=await server('memberGetWaitSwapRequest',[a.token,String(a.member.id)]);
    if(!req||!req.id||String(req.id)===MEMBER_WAIT_SWAP_SHOWN)return;
    MEMBER_WAIT_SWAP_SHOWN=String(req.id);
    const accepted=confirm(String(req.requesterName||'다른 회원')+'님이 자리 교환을 요청했어요.\n\n서로 상의하셨다면 확인을 눌러 교환하세요.');
    const state=await server('memberRespondWaitSwap',[a.token,String(a.member.id),String(req.id),accepted]);
    if(state&&state.members)renderState(state); else if(!accepted)showMemberSettingMessage('자리 교환 요청을 거절했습니다.');
  }catch(e){console.warn(e);}finally{MEMBER_WAIT_SWAP_CHECKING=false;}
}
setInterval(checkMemberWaitSwapRequest,5000);
'''
s=s.replace(client_anchor,client_anchor+client_add,1)

self_old="""    if(MEMBER_WAIT_SEAT_PICK&&MEMBER_WAIT_SEAT_PICK.type==='empty'){const g=MEMBER_WAIT_SEAT_PICK.groupIndex;clearMemberWaitSeatPick();memberMoveToWaitGroup(g);return;}
    MEMBER_WAIT_SEAT_PICK={type:'self',groupIndex:Number(groupIndex)};"""
self_new="""    if(MEMBER_WAIT_SEAT_PICK&&MEMBER_WAIT_SEAT_PICK.type==='empty'){const g=MEMBER_WAIT_SEAT_PICK.groupIndex;clearMemberWaitSeatPick();memberMoveToWaitGroup(g);return;}
    if(MEMBER_WAIT_SEAT_PICK&&MEMBER_WAIT_SEAT_PICK.type==='other'){const target=MEMBER_WAIT_SEAT_PICK.memberId;clearMemberWaitSeatPick();memberRequestWaitSwap(target);return;}
    MEMBER_WAIT_SEAT_PICK={type:'self',groupIndex:Number(groupIndex)};"""
if s.count(self_old)!=1: raise SystemExit('unsafe: self tap anchor mismatch')
s=s.replace(self_old,self_new,1)

card_old="""                return memberCard(member, false, false);
              }

              return (
                '<div class=\"person ' +"""
card_new="""                return '<div class=\"person member-info-card ' + genderClass(member) + '\" data-member-id=\"' + member.id + '\" onclick=\"handleMemberWaitOtherTap(' + groupIndex + ',\\\'' + member.id + '\\\',event)\">' + '<span class=\"name\">' + escapeMemberInfo(member.name) + '</span>' + memberInfoDetailHtml(member) + '</div>';
              }

              return (
                '<div class=\"person ' +"""
if s.count(card_old)<1: raise SystemExit('unsafe: member card anchor missing')
# use the last occurrence, which is the wait-group member branch
p=s.rfind(card_old); s=s[:p]+card_new+s[p+len(card_old):]

mut_old="""    'memberMoveToWaitGroup','memberLeaveWaitGroup',
    'createManualBackup'"""
mut_new="""    'memberMoveToWaitGroup','memberLeaveWaitGroup',
    'memberRequestWaitSwap','memberRespondWaitSwap',
    'createManualBackup'"""
if s.count(mut_old)!=1: raise SystemExit('unsafe: mutation anchor mismatch')
s=s.replace(mut_old,mut_new,1)

server_anchor='function changeMemberPassword(pin, newPassword) {'
if c.count(server_anchor)!=1: raise SystemExit('unsafe: server anchor mismatch')
server_add=r'''function memberWaitLocation_(waitGroups,memberId){
  for(var g=0;g<waitGroups.length;g+=1){var p=(waitGroups[g]||[]).indexOf(String(memberId));if(p>=0)return {group:g,position:p};}
  return null;
}
function memberWaitSwapCacheKey_(memberId){return 'JAYUMINTON_WAIT_SWAP_'+String(memberId);}
function memberRequestWaitSwap(sessionToken,requesterId,targetId){
  return withDocumentLock_('회원 자리 교환 요청',function(){
    requesterId=memberSessionAuth_(sessionToken,requesterId);targetId=String(targetId||'');
    if(!targetId||targetId===requesterId)throw new Error('교환할 다른 회원을 선택하세요.');
    if(!readMembers_().some(function(m){return String(m.id)===targetId;}))throw new Error('상대 회원을 찾을 수 없습니다.');
    var waitGroups=readWaitGroups_(),a=memberWaitLocation_(waitGroups,requesterId),b=memberWaitLocation_(waitGroups,targetId);
    if(!a||!b)throw new Error('두 사람 모두 대기자리에 있을 때만 교환할 수 있습니다.');
    var req={id:Utilities.getUuid(),requesterId:requesterId,targetId:targetId,createdAt:Date.now()};
    CacheService.getDocumentCache().put(memberWaitSwapCacheKey_(targetId),JSON.stringify(req),300);
    return {ok:true,message:'자리 교환을 요청했어요.'};
  });
}
function memberGetWaitSwapRequest(sessionToken,memberId){
  memberId=memberSessionAuth_(sessionToken,memberId);
  var cache=CacheService.getDocumentCache(),key=memberWaitSwapCacheKey_(memberId),raw=cache.get(key);if(!raw)return null;
  var req;try{req=JSON.parse(raw);}catch(e){cache.remove(key);return null;}
  if(!req||String(req.targetId)!==memberId)return null;
  var waitGroups=readWaitGroups_();if(!memberWaitLocation_(waitGroups,req.requesterId)||!memberWaitLocation_(waitGroups,memberId)){cache.remove(key);return null;}
  var member=readMembers_().find(function(m){return String(m.id)===String(req.requesterId);});
  return {id:String(req.id),requesterId:String(req.requesterId),requesterName:member?String(member.name):'다른 회원'};
}
function memberRespondWaitSwap(sessionToken,targetId,requestId,accept){
  return withDocumentLock_('회원 자리 교환 응답',function(){
    targetId=memberSessionAuth_(sessionToken,targetId);requestId=String(requestId||'');
    var cache=CacheService.getDocumentCache(),key=memberWaitSwapCacheKey_(targetId),raw=cache.get(key);if(!raw)throw new Error('교환 요청이 만료되었어요.');
    var req=JSON.parse(raw);if(String(req.id)!==requestId||String(req.targetId)!==targetId)throw new Error('교환 요청이 변경되었어요.');
    cache.remove(key);if(!accept)return {ok:true,rejected:true};
    var waitGroups=readWaitGroups_(),a=memberWaitLocation_(waitGroups,req.requesterId),b=memberWaitLocation_(waitGroups,targetId);
    if(!a||!b)throw new Error('대기자리가 변경되어 교환할 수 없습니다. 다시 요청해 주세요.');
    waitGroups[a.group][a.position]=targetId;waitGroups[b.group][b.position]=String(req.requesterId);
    writeWaitGroups_(waitGroups);touch_();return getPublicState();
  });
}
'''
c=c.replace(server_anchor,server_add+server_anchor,1)

sp.write_text(s,encoding='utf-8')
cp.write_text(c,encoding='utf-8')
print('phase4 swap patch applied safely')
