#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_self_longpress_v6.py <html-file>")

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Replace the old MD6 addon instead of skipping it. This makes a production
# redeploy actually upgrade pages that already contain V1.
text = re.sub(
    r'\n?<style id="jayuminton-md6-self-longpress-v1">[\s\S]*?</script>\s*',
    '\n', text, count=1, flags=re.I
)

addon = r'''
<style id="jayuminton-md6-self-longpress-v2">
/* JAYUMINTON_MD6_SELF_LONGPRESS_V2 - CLOUDFLARE ONLY */
#jmSelfCardAction{position:fixed!important;z-index:2147483646!important;left:50%!important;bottom:calc(env(safe-area-inset-bottom,0px) + 18px)!important;transform:translateX(-50%)!important;width:min(92vw,390px)!important;padding:12px!important;border-radius:15px!important;background:#fff!important;box-shadow:0 18px 55px rgba(15,23,42,.38)!important}
#jmSelfCardAction.hidden{display:none!important}
#jmSelfCardAction .jm-md6-self-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important}
#jmSelfCardAction .jm-md6-self-actions button{width:100%!important;min-height:43px!important;margin:0!important;padding:8px 5px!important;border:1px solid #dbe3ef!important;border-radius:10px!important;background:#f8fafc!important;color:#1e293b!important;font-size:13px!important;font-weight:900!important}
#jmSelfCardAction .jm-md6-self-actions .jm-md6-info{grid-column:1/-1!important;background:#315efb!important;border-color:#315efb!important;color:#fff!important}
#jmSelfCardAction .jm-md6-close{position:absolute!important;right:7px!important;top:-38px!important;width:34px!important;height:34px!important;min-height:34px!important;padding:0!important;border:0!important;border-radius:50%!important;background:#334155!important;color:#fff!important;font-size:18px!important;font-weight:900!important}
#jmSelfProfileModal{position:fixed!important;z-index:2147483647!important;inset:0!important;display:flex!important;align-items:center!important;justify-content:center!important;padding:18px!important;background:rgba(15,23,42,.48)!important}
#jmSelfProfileModal.hidden{display:none!important}
#jmSelfProfileModal .jm-self-profile-card{width:min(92vw,390px)!important;background:#fff!important;border-radius:16px!important;padding:16px!important;box-shadow:0 22px 70px rgba(0,0,0,.35)!important}
#jmSelfProfileModal .jm-self-profile-title{font-size:16px!important;font-weight:900!important;margin-bottom:8px!important;color:#172033!important}
#jmSelfProfileModal textarea{box-sizing:border-box!important;width:100%!important;min-height:90px!important;resize:vertical!important;border:1px solid #cbd5e1!important;border-radius:10px!important;padding:10px!important;font-size:9px!important;line-height:1.3!important;color:#334155!important}
#jmSelfProfileModal .jm-self-profile-hint{margin:6px 0 10px!important;font-size:9px!important;color:#64748b!important}
#jmSelfProfileModal .jm-self-profile-buttons{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important}
#jmSelfProfileModal .jm-self-profile-buttons button{min-height:42px!important;border-radius:10px!important;font-weight:900!important;border:1px solid #cbd5e1!important;background:#f8fafc!important}
#jmSelfProfileModal .jm-self-save{background:#315efb!important;border-color:#315efb!important;color:white!important}
#memberApp [data-member-id] .jm-public-memo,#memberApp [data-member-id] .member-public-memo{display:block!important;width:100%!important;margin-top:2px!important;font-size:9px!important;line-height:1.15!important;font-weight:700!important;color:#475569!important;text-align:center!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:keep-all!important}
</style>
<script id="jayuminton-md6-self-longpress-v2-script">
(function installMd6SelfLongPressV2(){
  if(window.__JAYUMINTON_MD6_SELF_LONGPRESS_V2__) return;
  window.__JAYUMINTON_MD6_SELF_LONGPRESS_V2__=true;
  var HOLD_MS=650, holdTimer=0, holdTarget=null, suppressClickUntil=0;

  function state(){ try{return window.STATE || (typeof STATE!=='undefined'?STATE:null);}catch(_){return null;} }
  function selected(){
    try{
      var m=typeof selectedWebPushMember==='function'?selectedWebPushMember():null;
      if(m) return m;
      var id=String(localStorage.getItem('jayuminton_member_id')||localStorage.getItem('selectedMemberId')||'');
      var s=state(); return s&&Array.isArray(s.members)?s.members.find(function(x){return String(x.id)===id;})||null:null;
    }catch(_){return null;}
  }
  function currentMember(){
    var m=selected(),s=state();
    if(!m) return null;
    return s&&Array.isArray(s.members)?s.members.find(function(x){return String(x.id)===String(m.id);})||m:m;
  }
  function ownCardFrom(node){
    var card=node&&node.closest?node.closest('[data-member-id]'):null, me=currentMember();
    if(!card||!me||!card.closest('#memberApp')) return null;
    return String(card.getAttribute('data-member-id')||'')===String(me.id)?card:null;
  }
  function ensureAction(){
    var box=document.getElementById('jmSelfCardAction');
    if(!box){box=document.createElement('div');box.id='jmSelfCardAction';document.body.appendChild(box);}
    if(!box.dataset.md6v2){
      box.dataset.md6v2='1';box.className='hidden';
      box.innerHTML='<button class="jm-md6-close" type="button" aria-label="닫기">×</button><div class="jm-md6-self-actions"><button data-status="before" type="button">도착전</button><button data-status="active" type="button">코트배정대기</button><button data-status="rest" type="button">휴식</button><button data-status="away" type="button">귀가</button><button class="jm-md6-info" type="button">내정보입력</button></div>';
      box.querySelector('.jm-md6-close').onclick=closeAction;
      box.querySelectorAll('[data-status]').forEach(function(btn){btn.onclick=function(){moveSelf(btn.dataset.status);};});
      box.querySelector('.jm-md6-info').onclick=function(){closeAction();openProfile();};
    }
    return box;
  }
  function closeAction(){var b=document.getElementById('jmSelfCardAction');if(b)b.classList.add('hidden');}
  function openAction(){var b=ensureAction();b.classList.remove('hidden');suppressClickUntil=Date.now()+700;}
  window.closeJmSelfCardAction=closeAction;

  function ensureProfile(){
    var modal=document.getElementById('jmSelfProfileModal');
    if(!modal){
      modal=document.createElement('div');modal.id='jmSelfProfileModal';modal.className='hidden';
      modal.innerHTML='<div class="jm-self-profile-card"><div class="jm-self-profile-title">내 정보 입력</div><textarea maxlength="120" placeholder="관리자와 다른 사용자에게 보일 간단한 메모를 입력하세요."></textarea><div class="jm-self-profile-hint">구력과 비슷한 작은 글씨로 카드에 표시됩니다. (최대 120자)</div><div class="jm-self-profile-buttons"><button class="jm-self-cancel" type="button">취소</button><button class="jm-self-save" type="button">저장</button></div></div>';
      document.body.appendChild(modal);
      modal.querySelector('.jm-self-cancel').onclick=function(){modal.classList.add('hidden');};
      modal.addEventListener('click',function(e){if(e.target===modal)modal.classList.add('hidden');});
      modal.querySelector('.jm-self-save').onclick=saveProfile;
    }
    return modal;
  }
  function openProfile(){
    var m=currentMember();if(!m)return;
    var modal=ensureProfile();modal.querySelector('textarea').value=String(m.publicMemo||'');modal.classList.remove('hidden');setTimeout(function(){modal.querySelector('textarea').focus();},40);
  }
  window.openJmSelfProfile=function(e){if(e&&e.preventDefault)e.preventDefault();openProfile();};

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
    var m=currentMember(),modal=ensureProfile();if(!m)return;
    var memo=String(modal.querySelector('textarea').value||'').trim().slice(0,120);
    modal.classList.add('hidden');
    try{
      if(typeof showSavingOverlay==='function')showSavingOverlay('저장중');
      var result=await server('updateMyProfile',[String(m.id),memo]);
      if(result&&result.state){try{window.STATE=result.state;}catch(_){}}
      if(typeof refreshMemberState==='function')await refreshMemberState();
      syncMemos();
    }catch(error){alert(error&&error.message?error.message:String(error));}
    finally{if(typeof hideSavingOverlay==='function')hideSavingOverlay();}
  }

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

  function beginHold(e){
    var card=ownCardFrom(e.target);if(!card)return;
    holdTarget=card;clearTimeout(holdTimer);holdTimer=setTimeout(function(){if(holdTarget===card)openAction();},HOLD_MS);
  }
  function cancelHold(){clearTimeout(holdTimer);holdTimer=0;holdTarget=null;}
  document.addEventListener('pointerdown',beginHold,true);
  document.addEventListener('pointerup',cancelHold,true);
  document.addEventListener('pointercancel',cancelHold,true);
  document.addEventListener('pointermove',function(e){if(holdTarget&&e.pressure===0)cancelHold();},true);
  document.addEventListener('contextmenu',function(e){if(ownCardFrom(e.target)){e.preventDefault();openAction();}},true);
  document.addEventListener('click',function(e){
    if(Date.now()<suppressClickUntil&&ownCardFrom(e.target)){e.preventDefault();e.stopImmediatePropagation();return false;}
    setTimeout(syncMemos,30);
  },true);

  var queued=false;function normalize(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;ensureAction();ensureProfile();syncMemos();});}
  new MutationObserver(normalize).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',normalize,{once:true});
  setInterval(syncMemos,1000);normalize();
})();
</script>
'''

if "</body>" in text:
    text = text.replace("</body>", addon + "\n</body>", 1)
else:
    text += "\n" + addon

for required in (
    'JAYUMINTON_MD6_SELF_LONGPRESS_V2',
    '>도착전</button>', '>코트배정대기</button>', '>휴식</button>', '>귀가</button>', '내정보입력',
    "server('memberMoveSelf'", "server('updateMyProfile'", 'font-size:9px!important', 'pointerdown', 'publicMemo'
):
    if required not in text:
        raise SystemExit('missing self-card requirement: '+required)

path.write_text(text, encoding="utf-8")
print("MD6 self long-press V2 Cloudflare patch applied")
