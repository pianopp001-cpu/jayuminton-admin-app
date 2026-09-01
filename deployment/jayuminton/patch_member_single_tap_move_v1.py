#!/usr/bin/env python3
"""Restore one-tap member moves, normalize status responses, and keep member replies reply-only."""

from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_single_tap_move_v1.py INDEX_HTML")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = re.sub(r'\s*<script id="jayuminton-member-single-tap-move-v1">[\s\S]*?</script>\s*', "\n", text, count=1, flags=re.I)
text = re.sub(r'\s*<script id="jayuminton-member-message-reply-v1">[\s\S]*?</script>\s*', "\n", text, count=1, flags=re.I)
text = re.sub(r'\s*<style id="jayuminton-self-status-badge-v1">[\s\S]*?</style>\s*', "\n", text, count=1, flags=re.I)
text = re.sub(r'\s*<script id="jayuminton-self-status-badge-v1-js">[\s\S]*?</script>\s*', "\n", text, count=1, flags=re.I)

# The received-message popup is the authority for the reply target. Persist the
# exact server message id on the popup while it is visible, and clear it on
# confirmation. Scope this to the direct-message alert patch so identical text
# can never bind a reply to a different message.
marker = text.find('JAYUMINTON_MEMBER_DIRECT_MESSAGE_ALERT_V1')
if marker < 0:
    raise SystemExit('direct message alert marker missing')
direct = text[marker:]
if 'box.dataset.messageId=activeId' not in direct:
    direct, changed = re.subn(
        r"(function\s+show\s*\(item\)\s*\{[\s\S]*?)(box\.classList\.remove\('hidden'\);)",
        r"\1box.dataset.messageId=activeId;\2",
        direct,
        count=1,
    )
    if changed != 1:
        raise SystemExit('direct message show hook missing')
if 'delete box.dataset.messageId' not in direct:
    direct, changed = re.subn(
        r"(window\.confirmJmDirectMessage\s*=\s*function\s*\(\)\s*\{[\s\S]*?var\s+box\s*=\s*getBox\(\);)if\(box\)box\.classList\.add\('hidden'\);",
        r"\1if(box){delete box.dataset.messageId;box.classList.add('hidden');}",
        direct,
        count=1,
    )
    if changed != 1:
        raise SystemExit('direct message confirm hook missing')
text = text[:marker] + direct

addon = r'''
<script id="jayuminton-member-single-tap-move-v1">
/* JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V2 compatibility marker for production verifier. */
/* JAYUMINTON_MEMBER_MOVESELF_FULL_STATE_V3 */
(function(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JM_MOVESELF_FULL_STATE_V3__)return;
  window.__JM_MOVESELF_FULL_STATE_V3__=true;
  function unwrap(v){for(var i=0;i<6;i++){if(v&&v.state&&typeof v.state==='object'){v=v.state;continue;}if(v&&v.result&&typeof v.result==='object'){v=v.result;continue;}break;}return v;}
  function full(v){return !!(v&&typeof v==='object'&&Array.isArray(v.members)&&Array.isArray(v.waitGroups)&&v.courts&&typeof v.courts==='object');}
  function statusSoon(){setTimeout(function(){try{if(typeof window.__jmApplySelfStatusBadgeV1==='function')window.__jmApplySelfStatusBadgeV1();}catch(_){}},60);}
  var rawServer=window.server;
  if(typeof rawServer==='function'){window.server=async function(name,args){var result=await rawServer.apply(this,arguments);if(String(name)!=='memberMoveSelf')return result;var candidate=unwrap(result);if(full(candidate)){statusSoon();return candidate;}var token=Array.isArray(args)&&args.length?args[0]:null;var fresh=await rawServer.call(this,'getPublicState',[token]);var state=unwrap(fresh);statusSoon();return full(state)?state:result;};}
  var moving=false;
  function session(){try{var a=memberWaitSeatSessionArgs();if(a&&a.member&&a.member.id&&a.token)return a;}catch(_){}return null;}
  async function move(type,index){if(moving)return false;var a=session();if(!a)return false;moving=true;try{var destination={type:type,key:type==='court'?String(index):String(Number(index)+1)};var state=await server('memberMoveSelf',[String(a.token),String(a.member.id),destination]);if(state&&typeof renderState==='function')renderState(state);statusSoon();return true;}catch(e){alert(String(e&&e.message||e||'빈자리 이동에 실패했습니다.'));return false;}finally{moving=false;}}
  window.handleMemberWaitEmptyTap=function(groupIndex,slotIndex,event){if(event){event.preventDefault();event.stopPropagation();}move('wait',Number(groupIndex));return false;};
  window.handleEmptySlotTap=function(type,index,slotIndex,event){if(event){event.preventDefault();event.stopPropagation();}move(String(type)==='court'?'court':'wait',Number(index));return false;};
  window.memberWaitEmptySlotCard=function(groupIndex,slotIndex){return '<div class="person empty" onclick="return handleMemberWaitEmptyTap('+Number(groupIndex)+','+Number(slotIndex)+',event)" title="한 번 터치하면 이 대기자리에 들어갑니다"><span class="empty-slot-label">비어 있음</span><small>한번 탭</small></div>';};
  function wire(){var root=document.getElementById('memberCourts');if(!root)return;for(var n=1;n<=4;n++)(function(no){var c=root.querySelector('.court-'+no);if(!c)return;c.querySelectorAll('.person.empty').forEach(function(slot,i){if(slot.dataset.jmSingleTapMoveV3==='1')return;slot.dataset.jmSingleTapMoveV3='1';slot.addEventListener('click',function(e){handleEmptySlotTap('court',no,i,e);});});})(n);}
  if(typeof MutationObserver!=='undefined')new MutationObserver(wire).observe(document.documentElement,{childList:true,subtree:true});document.addEventListener('DOMContentLoaded',wire,{once:true});setInterval(wire,1800);wire();
})();
</script>
<style id="jayuminton-self-status-badge-v1">body.jm-member-mode .jm-self-status-badge-v1{display:inline-flex!important;align-items:center!important;justify-content:center!important;margin-left:4px!important;padding:1px 5px!important;min-height:14px!important;border:1px solid currentColor!important;border-radius:999px!important;font-size:10px!important;line-height:1.2!important;font-weight:800!important;white-space:nowrap!important;vertical-align:middle!important;opacity:.92!important}</style>
<script id="jayuminton-self-status-badge-v1-js">
/* JAYUMINTON_MEMBER_SELF_STATUS_BADGE_V1 */
(function(){if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;if(window.__JM_MEMBER_SELF_STATUS_BADGE_V1__)return;window.__JM_MEMBER_SELF_STATUS_BADGE_V1__=true;var labels={before:'도착전',rest:'휴식',away:'귀가'};function session(){try{return typeof memberWaitSeatSessionArgs==='function'?memberWaitSeatSessionArgs():null;}catch(_){return null;}}function apply(){try{var a=session();if(!a||!a.member)return;var id=String(a.member.id||a.member.memberId||'');if(!id)return;var s=window.STATE||(typeof STATE!=='undefined'?STATE:null);var members=s&&Array.isArray(s.members)?s.members:[];var member=members.find(function(item){return String(item&&((item.id!=null?item.id:item.memberId))||'')===id;});var label=labels[String(member&&member.status||'')]||'';document.querySelectorAll('[data-member-id]').forEach(function(card){if(String(card.getAttribute('data-member-id')||'')!==id)return;var badge=card.querySelector('.jm-self-status-badge-v1');if(!label){if(badge)badge.remove();return;}if(!badge){badge=document.createElement('span');badge.className='jm-self-status-badge-v1';badge.setAttribute('aria-label','현재 상태');var name=card.querySelector('.name');if(name&&name.parentNode===card)name.insertAdjacentElement('afterend',badge);else card.appendChild(badge);}if(badge.textContent!==label)badge.textContent=label;});}catch(_){}}window.__jmApplySelfStatusBadgeV1=apply;document.addEventListener('DOMContentLoaded',function(){apply();setTimeout(apply,500);setTimeout(apply,1500);},{once:true});setInterval(apply,1800);apply();})();
</script>
<script id="jayuminton-member-message-reply-v1">
/* JAYUMINTON_MEMBER_MESSAGE_REPLY_ONLY_V1 */
(function(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;if(window.__JM_MEMBER_MESSAGE_REPLY_ONLY_V1__)return;window.__JM_MEMBER_MESSAGE_REPLY_ONLY_V1__=true;var sending=false;
  function session(){try{var a=memberWaitSeatSessionArgs();if(a&&a.member&&a.member.id&&a.token)return a;}catch(_){}return null;}
  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(_){return null;}}
  function popupVisible(box){return !!(box&&!box.classList.contains('hidden'));}
  function activeMessage(){var box=document.getElementById('jmDirectMessageAlert');if(!popupVisible(box))return null;var s=state(),a=session();if(!s||!a||!Array.isArray(s.memberMessages))return null;var list=s.memberMessages.filter(function(item){return item&&Array.isArray(item.memberIds)&&item.memberIds.map(String).indexOf(String(a.member.id))>=0;});var exactId=String(box.dataset&&box.dataset.messageId||'');if(!exactId)return null;for(var j=list.length-1;j>=0;j--){if(String(list[j].id||'')===exactId)return list[j];}return null;}
  function ensureUi(){var box=document.getElementById('jmDirectMessageAlert');if(!popupVisible(box))return;var card=box.querySelector('.jm-direct-message-card');if(!card)return;var item=activeMessage();if(!item||!item.id)return;var old=card.querySelector('.jm-member-reply-wrap');if(old&&String(old.dataset.messageId||'')!==String(item.id)){old.remove();old=null;}if(old)return;var wrap=document.createElement('div');wrap.className='jm-member-reply-wrap';wrap.dataset.messageId=String(item.id);wrap.style.cssText='margin-top:8px;display:flex;flex-direction:column;gap:6px';wrap.innerHTML='<button type="button" class="jm-member-reply-open" style="width:100%;min-height:36px;border:1px solid #cbd5e1;border-radius:9px;background:#f8fafc;font-weight:800">답장</button><div class="jm-member-reply-form" style="display:none;gap:6px;flex-direction:column"><textarea class="jm-member-reply-input" maxlength="80" rows="2" placeholder="관리자에게 답장 (80자 이내)" style="width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:9px;padding:8px;font-size:14px"></textarea><button type="button" class="jm-member-reply-send" style="width:100%;min-height:36px;border:0;border-radius:9px;background:#2563eb;color:#fff;font-weight:900">답장 보내기</button></div>';card.appendChild(wrap);wrap.querySelector('.jm-member-reply-open').addEventListener('click',function(){this.style.display='none';var form=wrap.querySelector('.jm-member-reply-form');form.style.display='flex';setTimeout(function(){wrap.querySelector('.jm-member-reply-input').focus();},30);});wrap.querySelector('.jm-member-reply-send').addEventListener('click',async function(){if(sending)return;var a=session(),current=activeMessage(),input=wrap.querySelector('.jm-member-reply-input');var replyText=String(input&&input.value||'').trim().slice(0,80);if(!a||!current||!current.id)return;if(!replyText){alert('답장 내용을 입력해 주세요.');return;}sending=true;this.disabled=true;this.textContent='전송 중...';try{await server('memberReplyToMessage',[String(a.token),String(a.member.id),String(current.id),replyText]);if(typeof confirmJmDirectMessage==='function')confirmJmDirectMessage();if(typeof showMemberSettingMessage==='function')showMemberSettingMessage('관리자에게 답장을 보냈습니다.');else alert('관리자에게 답장을 보냈습니다.');}catch(e){alert(String(e&&e.message||e||'답장 전송에 실패했습니다.'));this.disabled=false;this.textContent='답장 보내기';}finally{sending=false;}});}
  if(typeof MutationObserver!=='undefined')new MutationObserver(function(){setTimeout(ensureUi,0);}).observe(document.documentElement,{attributes:true,childList:true,subtree:true,attributeFilter:['class','data-message-id']});setInterval(ensureUi,900);document.addEventListener('DOMContentLoaded',ensureUi,{once:true});ensureUi();
})();
</script>
'''
pos=text.lower().rfind('</body>')
if pos<0: pos=text.lower().rfind('</html>')
if pos<0: raise SystemExit('member page closing marker missing')
text=text[:pos]+addon+'\n'+text[pos:]
for needle in ['JAYUMINTON_MEMBER_SINGLE_TAP_MOVE_V2','JAYUMINTON_MEMBER_MOVESELF_FULL_STATE_V3','window.server=async function',"getPublicState',[token]",'window.handleMemberWaitEmptyTap=function','window.handleEmptySlotTap=function','JAYUMINTON_MEMBER_MESSAGE_REPLY_ONLY_V1','memberReplyToMessage','maxlength="80"','JAYUMINTON_MEMBER_SELF_STATUS_BADGE_V1',"away:'귀가'",'box.dataset.messageId=activeId','delete box.dataset.messageId',"classList.contains('hidden')"]:
    if needle not in text: raise SystemExit('missing '+needle)
path.write_text(text,encoding='utf-8')
print('MEMBER_MOVESELF_V3_REPLY80_EXACT_ID_HIDDEN_POPUP_SELF_STATUS_BADGE_OK')
