#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
marker = '</body>'
if marker not in s:
    raise SystemExit('body marker missing')
patch = r'''
<style id="jayuminton-user-native-dialog-style">
.jm-user-modal{position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.42);display:flex;align-items:center;justify-content:center;padding:20px}.jm-user-modal.hidden{display:none}.jm-user-modal-card{width:min(92vw,380px);background:#fff;border-radius:18px;padding:18px;box-shadow:0 16px 50px rgba(0,0,0,.28)}.jm-user-modal-title{font-size:19px;font-weight:800;margin:0 0 8px}.jm-user-modal-body{font-size:15px;line-height:1.45;margin-bottom:14px;white-space:pre-line}.jm-user-modal-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px}.jm-user-modal-actions.status{grid-template-columns:1fr 1fr}.jm-user-modal-actions button{min-height:46px;border-radius:12px;font-weight:700}.jm-user-modal-actions .wide{grid-column:1/-1}.jm-user-modal-actions .primary{font-weight:800}
</style>
<div id="jmUserModal" class="jm-user-modal hidden" aria-hidden="true">
  <div class="jm-user-modal-card" role="dialog" aria-modal="true" aria-labelledby="jmUserModalTitle">
    <div id="jmUserModalTitle" class="jm-user-modal-title"></div>
    <div id="jmUserModalBody" class="jm-user-modal-body"></div>
    <div id="jmUserModalActions" class="jm-user-modal-actions"></div>
  </div>
</div>
<script id="jayuminton-user-native-dialog-v3">
(function(){
  if(window.__JM_USER_NATIVE_DIALOG_V3__)return;
  window.__JM_USER_NATIVE_DIALOG_V3__=true;
  var modal=document.getElementById('jmUserModal'),title=document.getElementById('jmUserModalTitle'),body=document.getElementById('jmUserModalBody'),actions=document.getElementById('jmUserModalActions');
  function close(){modal.classList.add('hidden');modal.setAttribute('aria-hidden','true');actions.innerHTML='';}
  function show(t,b,buttons,status){title.textContent=t||'';body.textContent=b||'';actions.className='jm-user-modal-actions'+(status?' status':'');actions.innerHTML='';(buttons||[]).forEach(function(x){var bt=document.createElement('button');bt.type='button';bt.textContent=x.label;bt.className=x.primary?'primary':'';if(x.wide)bt.classList.add('wide');bt.onclick=function(){close();x.run&&x.run();};actions.appendChild(bt);});modal.classList.remove('hidden');modal.setAttribute('aria-hidden','false');}
  modal.addEventListener('click',function(e){if(e.target===modal)close();});
  window.__jmUserModalShow=show;window.__jmUserModalClose=close;

  function stored(){try{return JSON.parse(localStorage.getItem('jayuminton_web_push_selected_member_v1')||'null');}catch(e){return null;}}
  function selfId(){var m=stored();return m&&m.id?String(m.id):'';}

  // No self selected: one tap on any visible member card sets that member as "me".
  document.addEventListener('click',function(e){
    if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
    if(selfId())return;
    var card=e.target&&e.target.closest?e.target.closest('[data-member-id]'):null;
    if(!card)return;
    var id=String(card.getAttribute('data-member-id')||'');
    var m=(STATE.members||[]).find(function(x){return x&&String(x.id)===id;});
    if(!m)return;
    e.preventDefault();e.stopImmediatePropagation();
    selectMemberSelf(id);
    if(typeof syncNativeUserPushBridge==='function')syncNativeUserPushBridge();
    if(typeof showMemberSettingMessage==='function')showMemberSettingMessage(String(m.name||'')+'님으로 내 이름을 설정했어요.');
  },true);

  window.handleMemberWaitOtherTap=function(groupIndex,targetMemberId,event){
    if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
    if(event){event.preventDefault();event.stopPropagation();}
    var target=(STATE.members||[]).find(function(x){return x&&String(x.id)===String(targetMemberId);});
    if(!target)return;
    var me=stored();
    if(!me||!me.id){selectMemberSelf(targetMemberId);if(typeof syncNativeUserPushBridge==='function')syncNativeUserPushBridge();return;}
    if(String(me.id)===String(targetMemberId))return;
    show('자리 바꾸기',String(target.name||'선택한 회원')+'님과 자리를 바꿀까요?',[{label:'취소',run:function(){}},{label:'바꾸기 요청',primary:true,run:function(){if(typeof clearMemberWaitSeatPick==='function')clearMemberWaitSeatPick();memberRequestWaitSwap(targetMemberId);}}]);
  };

  async function setStatus(status){
    var a=typeof memberWaitSeatSessionArgs==='function'?memberWaitSeatSessionArgs():null;if(!a||!a.member||!a.member.id)return;
    var labels={active:'코트배정대기',away:'귀가',rest:'휴식',before:'도착전'};
    try{var state=await server('memberSetOwnStatus',[a.token,String(a.member.id),status]);if(typeof clearMemberWaitSeatPick==='function')clearMemberWaitSeatPick();renderState(state);if(typeof syncNativeUserPushBridge==='function')syncNativeUserPushBridge();if(typeof showMemberSettingMessage==='function')showMemberSettingMessage(labels[status]+' 상태로 이동했어요.');}catch(e){show('상태 변경 실패',String(e&&e.message||e||'요청에 실패했습니다.'),[{label:'확인',primary:true,wide:true,run:function(){}}]);}
  }
  window.memberSetOwnStatus=setStatus;
  window.openMemberSelfStatusMenu=function(){
    show('내 상태 이동','이동할 상태를 선택하세요.',[
      {label:'코트배정대기',primary:true,run:function(){setStatus('active');}},
      {label:'휴식',run:function(){setStatus('rest');}},
      {label:'귀가',run:function(){setStatus('away');}},
      {label:'도착전',run:function(){setStatus('before');}},
      {label:'취소',wide:true,run:function(){}}
    ],true);
  };

  // Long press works from the stored self id, even if an older renderer missed is-self-member.
  var lp=null,startX=0,startY=0,blockUntil=0;
  document.addEventListener('pointerdown',function(e){
    if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
    var card=e.target&&e.target.closest?e.target.closest('[data-member-id]'):null;if(!card)return;
    if(String(card.getAttribute('data-member-id')||'')!==selfId())return;
    startX=e.clientX||0;startY=e.clientY||0;if(lp)clearTimeout(lp);
    lp=setTimeout(function(){lp=null;blockUntil=Date.now()+900;try{if(navigator.vibrate)navigator.vibrate(35);}catch(_e){}openMemberSelfStatusMenu();},600);
  },true);
  document.addEventListener('pointermove',function(e){if(!lp)return;if(Math.abs((e.clientX||0)-startX)>14||Math.abs((e.clientY||0)-startY)>14){clearTimeout(lp);lp=null;}},true);
  ['pointerup','pointercancel'].forEach(function(t){document.addEventListener(t,function(){if(lp){clearTimeout(lp);lp=null;}},true);});
  document.addEventListener('click',function(e){if(Date.now()>blockUntil)return;var card=e.target&&e.target.closest?e.target.closest('[data-member-id]'):null;if(card&&String(card.getAttribute('data-member-id')||'')===selfId()){e.preventDefault();e.stopImmediatePropagation();}},true);

  window.checkMemberWaitSwapRequest=async function(){
    if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN||window.MEMBER_WAIT_SWAP_CHECKING||window.ACTION_IN_FLIGHT)return;
    var a=typeof memberWaitSeatSessionArgs==='function'?memberWaitSeatSessionArgs():null;if(!a)return;
    window.MEMBER_WAIT_SWAP_CHECKING=true;
    try{var req=await server('memberGetWaitSwapRequest',[a.token,String(a.member.id)]);if(!req||!req.id||String(req.id)===String(window.MEMBER_WAIT_SWAP_SHOWN||''))return;window.MEMBER_WAIT_SWAP_SHOWN=String(req.id);show('자리 바꾸기 요청',String(req.requesterName||'다른 회원')+'님이 자리 바꾸기를 요청했어요.',[{label:'거절',run:async function(){try{var st=await server('memberRespondWaitSwap',[a.token,String(a.member.id),String(req.id),false]);if(st&&st.members)renderState(st);}catch(e){}}},{label:'수락',primary:true,run:async function(){try{var st=await server('memberRespondWaitSwap',[a.token,String(a.member.id),String(req.id),true]);if(st&&st.members)renderState(st);}catch(e){}}}]);}catch(e){}finally{window.MEMBER_WAIT_SWAP_CHECKING=false;}
  };
})();
</script>
'''
if 'jayuminton-user-native-dialog-v3' not in s:
    s = s.replace(marker, patch + '\n' + marker, 1)
p.write_text(s, encoding='utf-8')
