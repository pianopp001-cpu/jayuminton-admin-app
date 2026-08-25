#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_self_longpress_v6.py <html-file>")

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Remove older injected self-card addons so redeploys really replace the UI.
for pattern in (
    r'\n?<style id="jayuminton-md6-self-longpress-v1">[\s\S]*?</script>\s*',
    r'\n?<style id="jayuminton-md6-self-longpress-v2">[\s\S]*?</script>\s*',
    r'\n?<style id="jayuminton-md7-single-action-popup">[\s\S]*?</script>\s*',
):
    text = re.sub(pattern, '\n', text, count=1, flags=re.I)

addon = r'''
<style id="jayuminton-md7-single-action-popup">
/* JAYUMINTON_MD7_SINGLE_ACTION_POPUP_V1
   One popup only: court wait / rest / away / before / self info.
   The self-info editor lives inside the SAME popup. No second modal.
*/
#jmSelfProfileModal{display:none!important}
#jmSelfCardAction{position:fixed!important;z-index:2147483647!important;left:50%!important;bottom:calc(env(safe-area-inset-bottom,0px) + 18px)!important;transform:translateX(-50%)!important;width:min(92vw,390px)!important;padding:12px!important;border-radius:15px!important;background:#fff!important;box-shadow:0 18px 55px rgba(15,23,42,.38)!important;box-sizing:border-box!important}
#jmSelfCardAction.hidden{display:none!important}
#jmSelfCardAction .jm-md7-title{margin:0 34px 10px 0!important;font-size:15px!important;line-height:1.25!important;font-weight:950!important;color:#172033!important;text-align:left!important}
#jmSelfCardAction .jm-md7-close{position:absolute!important;right:8px!important;top:8px!important;width:30px!important;height:30px!important;min-height:30px!important;padding:0!important;border:0!important;border-radius:50%!important;background:#e2e8f0!important;color:#334155!important;font-size:18px!important;font-weight:900!important}
#jmSelfCardAction .jm-md7-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important}
#jmSelfCardAction .jm-md7-actions button{width:100%!important;min-height:43px!important;margin:0!important;padding:8px 5px!important;border:1px solid #dbe3ef!important;border-radius:10px!important;background:#f8fafc!important;color:#1e293b!important;font-size:13px!important;font-weight:900!important}
#jmSelfCardAction .jm-md7-actions .jm-md7-info{grid-column:1/-1!important;background:#315efb!important;border-color:#315efb!important;color:#fff!important}
#jmSelfCardAction .jm-md7-profile-view.hidden,#jmSelfCardAction .jm-md7-action-view.hidden{display:none!important}
#jmSelfCardAction .jm-md7-profile-view textarea{box-sizing:border-box!important;width:100%!important;min-height:86px!important;resize:vertical!important;border:1px solid #cbd5e1!important;border-radius:10px!important;padding:9px!important;font-size:11px!important;line-height:1.35!important;color:#334155!important}
#jmSelfCardAction .jm-md7-hint{margin:6px 0 9px!important;font-size:9px!important;line-height:1.35!important;color:#64748b!important}
#jmSelfCardAction .jm-md7-profile-buttons{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important}
#jmSelfCardAction .jm-md7-profile-buttons button{min-height:42px!important;border-radius:10px!important;font-weight:900!important;border:1px solid #cbd5e1!important;background:#f8fafc!important}
#jmSelfCardAction .jm-md7-profile-buttons .jm-md7-save{background:#315efb!important;border-color:#315efb!important;color:#fff!important}
#memberApp [data-member-id] .jm-public-memo,#memberApp [data-member-id] .member-public-memo{display:block!important;width:100%!important;margin-top:2px!important;font-size:9px!important;line-height:1.15!important;font-weight:700!important;color:#475569!important;text-align:center!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:keep-all!important}
</style>
<script id="jayuminton-md7-single-action-popup-script">
(function installMd7SingleActionPopup(){
  if(window.__JAYUMINTON_MD7_SINGLE_ACTION_POPUP_V1__) return;
  window.__JAYUMINTON_MD7_SINGLE_ACTION_POPUP_V1__=true;
  var HOLD_MS=650,holdTimer=0,holdTarget=null,suppressClickUntil=0;

  function state(){try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(_){return null;}}
  function selected(){
    try{
      var m=typeof selectedWebPushMember==='function'?selectedWebPushMember():null;
      if(m)return m;
      var id=String(localStorage.getItem('jayuminton_member_id')||localStorage.getItem('selectedMemberId')||'');
      var s=state();return s&&Array.isArray(s.members)?s.members.find(function(x){return String(x.id)===id;})||null:null;
    }catch(_){return null;}
  }
  function currentMember(){var m=selected(),s=state();if(!m)return null;return s&&Array.isArray(s.members)?s.members.find(function(x){return String(x.id)===String(m.id);})||m:m;}
  function ownCardFrom(node){var card=node&&node.closest?node.closest('[data-member-id]'):null,me=currentMember();if(!card||!me||!card.closest('#memberApp'))return null;return String(card.getAttribute('data-member-id')||'')===String(me.id)?card:null;}

  function removeLegacyProfileModal(){
    document.querySelectorAll('#jmSelfProfileModal').forEach(function(modal){
      modal.classList.add('hidden');
      modal.setAttribute('aria-hidden','true');
      modal.style.setProperty('display','none','important');
    });
  }

  function ensureAction(){
    var box=document.getElementById('jmSelfCardAction');
    if(!box){box=document.createElement('div');box.id='jmSelfCardAction';document.body.appendChild(box);}
    if(box.dataset.md7single!=='1'){
      box.dataset.md7single='1';box.className='hidden';
      box.innerHTML=''
        +'<button class="jm-md7-close" type="button" aria-label="닫기">×</button>'
        +'<div class="jm-md7-action-view">'
        +'<div class="jm-md7-title">어디로 이동할까요?</div>'
        +'<div class="jm-md7-actions">'
        +'<button data-status="active" type="button">코트배정대기</button>'
        +'<button data-status="rest" type="button">휴식</button>'
        +'<button data-status="away" type="button">귀가</button>'
        +'<button data-status="before" type="button">도착전</button>'
        +'<button class="jm-md7-info" type="button">내정보 입력</button>'
        +'</div></div>'
        +'<div class="jm-md7-profile-view hidden">'
        +'<div class="jm-md7-title">내정보 입력</div>'
        +'<textarea maxlength="120" placeholder="카드에 표시할 메모를 입력하세요."></textarea>'
        +'<div class="jm-md7-hint">입력한 메모는 내 카드와 관리자 멤버 메모에 같은 내용으로 표시됩니다.</div>'
        +'<div class="jm-md7-profile-buttons"><button class="jm-md7-back" type="button">뒤로</button><button class="jm-md7-save" type="button">저장</button></div>'
        +'</div>';
      box.querySelector('.jm-md7-close').onclick=closeAction;
      box.querySelectorAll('[data-status]').forEach(function(btn){btn.onclick=function(){moveSelf(btn.dataset.status);};});
      box.querySelector('.jm-md7-info').onclick=openInlineProfile;
      box.querySelector('.jm-md7-back').onclick=showActionView;
      box.querySelector('.jm-md7-save').onclick=saveProfile;
    }
    return box;
  }
  function showActionView(){var b=ensureAction();b.querySelector('.jm-md7-profile-view').classList.add('hidden');b.querySelector('.jm-md7-action-view').classList.remove('hidden');}
  function closeAction(){var b=document.getElementById('jmSelfCardAction');if(b){showActionView();b.classList.add('hidden');}}
  function openAction(){removeLegacyProfileModal();var b=ensureAction();showActionView();b.classList.remove('hidden');suppressClickUntil=Date.now()+700;}
  window.closeJmSelfCardAction=closeAction;

  function openInlineProfile(){
    var m=currentMember();if(!m)return;
    var b=ensureAction(),view=b.querySelector('.jm-md7-profile-view'),ta=view.querySelector('textarea');
    ta.value=String(m.publicMemo||'');
    b.querySelector('.jm-md7-action-view').classList.add('hidden');view.classList.remove('hidden');
    setTimeout(function(){ta.focus();},30);
  }
  window.openJmSelfProfile=function(e){if(e){e.preventDefault();e.stopPropagation();}openInlineProfile();};
  window.closeJmSelfProfile=showActionView;

  async function moveSelf(status){
    var m=currentMember();if(!m)return;closeAction();
    try{
      if(typeof showSavingOverlay==='function')showSavingOverlay('저장중');
      await server('memberMoveSelf',[String(m.id),{type:'status',status:String(status)}]);
      if(typeof refreshMemberState==='function')await refreshMemberState();
    }catch(error){alert(error&&error.message?error.message:String(error));}
    finally{if(typeof hideSavingOverlay==='function')hideSavingOverlay();}
  }
  window.jmMd6MoveSelf=moveSelf;

  async function saveProfile(){
    var m=currentMember(),b=ensureAction();if(!m)return;
    var memo=String(b.querySelector('.jm-md7-profile-view textarea').value||'').trim().slice(0,120);
    try{
      if(typeof showSavingOverlay==='function')showSavingOverlay('저장중');
      var result=await server('updateMyProfile',[String(m.id),memo]);
      if(result&&result.state){try{window.STATE=result.state;}catch(_){}}
      if(typeof refreshMemberState==='function')await refreshMemberState();
      syncMemos();closeAction();
    }catch(error){
      var msg=error&&error.message?error.message:String(error);
      alert('메모 저장 실패: '+msg);
    }finally{if(typeof hideSavingOverlay==='function')hideSavingOverlay();}
  }
  window.saveJmSelfProfile=saveProfile;

  function syncMemos(){
    var s=state();if(!s||!Array.isArray(s.members))return;
    var byId=new Map(s.members.map(function(m){return [String(m.id),String(m.publicMemo||'').trim()];}));
    document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
      var memo=byId.get(String(card.getAttribute('data-member-id')||''))||'';
      var node=card.querySelector('.jm-public-memo,.member-public-memo');
      if(memo&&!node){node=document.createElement('span');node.className='jm-public-memo';card.appendChild(node);}
      if(node){node.textContent=memo;node.hidden=!memo;}
    });
  }

  function beginHold(e){var card=ownCardFrom(e.target);if(!card)return;holdTarget=card;clearTimeout(holdTimer);holdTimer=setTimeout(function(){if(holdTarget===card)openAction();},HOLD_MS);}
  function cancelHold(){clearTimeout(holdTimer);holdTimer=0;holdTarget=null;}
  document.addEventListener('pointerdown',beginHold,true);
  document.addEventListener('pointerup',cancelHold,true);
  document.addEventListener('pointercancel',cancelHold,true);
  document.addEventListener('pointermove',function(e){if(holdTarget&&e.pressure===0)cancelHold();},true);
  document.addEventListener('contextmenu',function(e){if(ownCardFrom(e.target)){e.preventDefault();openAction();}},true);
  document.addEventListener('click',function(e){if(Date.now()<suppressClickUntil&&ownCardFrom(e.target)){e.preventDefault();e.stopImmediatePropagation();return false;}setTimeout(syncMemos,30);},true);

  var queued=false;function normalize(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;removeLegacyProfileModal();ensureAction();syncMemos();});}
  new MutationObserver(normalize).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',normalize,{once:true});
  setInterval(function(){removeLegacyProfileModal();syncMemos();},1000);normalize();
})();
</script>
'''

if "</body>" in text:
    text = text.replace("</body>", addon + "\n</body>", 1)
else:
    text += "\n" + addon

for required in (
    'JAYUMINTON_MD7_SINGLE_ACTION_POPUP_V1',
    '어디로 이동할까요?',
    '>코트배정대기</button>', '>휴식</button>', '>귀가</button>', '>도착전</button>', '>내정보 입력</button>',
    "server('memberMoveSelf'", "server('updateMyProfile'", '#jmSelfProfileModal{display:none!important}',
    'jm-md7-profile-view', 'publicMemo'
):
    if required not in text:
        raise SystemExit('missing single-popup member requirement: '+required)

path.write_text(text, encoding="utf-8")
print("MD7 single member popup patch applied")