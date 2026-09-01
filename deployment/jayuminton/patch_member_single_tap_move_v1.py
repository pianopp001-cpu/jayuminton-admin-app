#!/usr/bin/env python3
"""Restore one-tap member moves, normalize memberMoveSelf responses, and allow reply-only admin messaging."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_single_tap_move_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = re.sub(r'\s*<script id="jayuminton-member-single-tap-move-v1">[\s\S]*?</script>\s*', "\n", text, count=1, flags=re.I)
text = re.sub(r'\s*<script id="jayuminton-member-message-reply-v1">[\s\S]*?</script>\s*', "\n", text, count=1, flags=re.I)

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

<script id="jayuminton-member-message-reply-v1">
/* JAYUMINTON_MEMBER_MESSAGE_REPLY_ONLY_V1
   Members cannot initiate admin messages. A reply control appears only while a
   received administrator message is visible, and every reply is tied to the
   original message id. */
(function(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JM_MEMBER_MESSAGE_REPLY_ONLY_V1__)return;
  window.__JM_MEMBER_MESSAGE_REPLY_ONLY_V1__=true;
  var sending=false;

  function session(){
    try{var a=memberWaitSeatSessionArgs();if(a&&a.member&&a.member.id&&a.token)return a;}catch(_){}
    return null;
  }
  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(_){return null;}}
  function activeMessage(){
    var box=document.getElementById('jmDirectMessageAlert');
    var body=document.getElementById('jmDirectMessageBody');
    if(!box||box.classList.contains('hidden')||!body)return null;
    var s=state(),a=session();if(!s||!a||!Array.isArray(s.memberMessages))return null;
    var text=String(body.textContent||'');
    var list=s.memberMessages.filter(function(item){
      return item&&Array.isArray(item.memberIds)&&item.memberIds.map(String).indexOf(String(a.member.id))>=0;
    });
    for(var i=list.length-1;i>=0;i--){if(String(list[i].text||'')===text)return list[i];}
    return list.length?list[list.length-1]:null;
  }
  function ensureUi(){
    var box=document.getElementById('jmDirectMessageAlert');if(!box||box.classList.contains('hidden'))return;
    var card=box.querySelector('.jm-direct-message-card');if(!card||card.querySelector('.jm-member-reply-wrap'))return;
    var item=activeMessage();if(!item||!item.id)return;
    var wrap=document.createElement('div');wrap.className='jm-member-reply-wrap';
    wrap.style.cssText='margin-top:10px;display:flex;flex-direction:column;gap:8px';
    wrap.innerHTML='<button type="button" class="jm-member-reply-open" style="width:100%;min-height:42px;border:1px solid #cbd5e1;border-radius:10px;background:#f8fafc;font-weight:800">답장</button>'+
      '<div class="jm-member-reply-form" style="display:none;gap:8px;flex-direction:column">'+
      '<textarea class="jm-member-reply-input" maxlength="300" rows="3" placeholder="관리자에게 답장" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:10px;padding:10px;font-size:14px"></textarea>'+
      '<button type="button" class="jm-member-reply-send" style="width:100%;min-height:42px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:900">답장 보내기</button></div>';
    card.appendChild(wrap);
    wrap.querySelector('.jm-member-reply-open').addEventListener('click',function(){
      this.style.display='none';var form=wrap.querySelector('.jm-member-reply-form');form.style.display='flex';setTimeout(function(){wrap.querySelector('.jm-member-reply-input').focus();},30);
    });
    wrap.querySelector('.jm-member-reply-send').addEventListener('click',async function(){
      if(sending)return;var a=session(),current=activeMessage(),input=wrap.querySelector('.jm-member-reply-input');
      var text=String(input&&input.value||'').trim();if(!a||!current||!current.id)return;if(!text){alert('답장 내용을 입력해 주세요.');return;}
      sending=true;this.disabled=true;this.textContent='전송 중...';
      try{
        await server('memberReplyToMessage',[String(a.token),String(a.member.id),String(current.id),text]);
        if(typeof confirmJmDirectMessage==='function')confirmJmDirectMessage();
        if(typeof showMemberSettingMessage==='function')showMemberSettingMessage('관리자에게 답장을 보냈습니다.');
        else alert('관리자에게 답장을 보냈습니다.');
      }catch(e){alert(String(e&&e.message||e||'답장 전송에 실패했습니다.'));this.disabled=false;this.textContent='답장 보내기';}
      finally{sending=false;}
    });
  }
  if(typeof MutationObserver!=='undefined')new MutationObserver(function(){setTimeout(ensureUi,0);}).observe(document.documentElement,{attributes:true,childList:true,subtree:true,attributeFilter:['class']});
  setInterval(ensureUi,900);document.addEventListener('DOMContentLoaded',ensureUi,{once:true});ensureUi();
})();
</script>
'''

pos=text.lower().rfind('</body>')
if pos<0: pos=text.lower().rfind('</html>')
if pos<0: raise SystemExit('member page closing marker missing')
text=text[:pos]+addon+'\n'+text[pos:]
for needle in ['JAYUMINTON_MEMBER_MOVESELF_FULL_STATE_V3','window.server=async function','getPublicState\',[token]','window.handleMemberWaitEmptyTap=function','window.handleEmptySlotTap=function','JAYUMINTON_MEMBER_MESSAGE_REPLY_ONLY_V1','memberReplyToMessage','답장 보내기']:
    if needle not in text: raise SystemExit('missing '+needle)
path.write_text(text,encoding='utf-8')
print('MEMBER_MOVESELF_FULL_STATE_V3_REPLY_ONLY_V1_OK')
