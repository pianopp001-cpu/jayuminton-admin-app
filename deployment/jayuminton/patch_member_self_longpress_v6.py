#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_member_self_longpress_v6.py <html-file>")

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_MD6_SELF_LONGPRESS_V1"
if marker in text:
    print("MD6 self long-press patch already present")
    raise SystemExit(0)

addon = r'''
<style id="jayuminton-md6-self-longpress-v1">
/* JAYUMINTON_MD6_SELF_LONGPRESS_V1 */
#jmSelfCardAction{position:fixed!important;z-index:2147483647!important;left:50%!important;bottom:calc(env(safe-area-inset-bottom,0px) + 18px)!important;transform:translateX(-50%)!important;width:min(92vw,380px)!important;padding:10px!important;border-radius:14px!important;background:#fff!important;box-shadow:0 18px 55px rgba(15,23,42,.35)!important}
#jmSelfCardAction.hidden{display:none!important}
#jmSelfCardAction .jm-md6-self-actions{display:grid!important;grid-template-columns:1fr 1fr!important;gap:7px!important}
#jmSelfCardAction .jm-md6-self-actions button{width:100%!important;min-height:42px!important;margin:0!important;padding:8px 5px!important;border:1px solid #dbe3ef!important;border-radius:10px!important;background:#f8fafc!important;color:#1e293b!important;font-size:13px!important;font-weight:900!important}
#jmSelfCardAction .jm-md6-self-actions .jm-md6-info{grid-column:1/-1!important;background:#315efb!important;border-color:#315efb!important;color:#fff!important}
#jmSelfCardAction .jm-md6-close{position:absolute!important;right:7px!important;top:-38px!important;width:34px!important;height:34px!important;min-height:34px!important;padding:0!important;border:0!important;border-radius:50%!important;background:#334155!important;color:#fff!important;font-size:18px!important;font-weight:900!important}
#memberApp [data-member-id] .jm-public-memo,
#memberApp [data-member-id] .member-public-memo{font-size:9px!important;line-height:1.15!important;font-weight:700!important;color:#475569!important;margin-top:2px!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:keep-all!important}
#jmSelfProfileModal .jm-self-profile-card textarea{font-size:11px!important;line-height:1.35!important}
</style>
<script>
(function installMd6SelfLongPressV1(){
  if(window.__JAYUMINTON_MD6_SELF_LONGPRESS_V1__) return;
  window.__JAYUMINTON_MD6_SELF_LONGPRESS_V1__ = true;

  function currentMember(){
    try{
      var selected = typeof selectedWebPushMember === 'function' ? selectedWebPushMember() : null;
      var state = window.STATE || (typeof STATE !== 'undefined' ? STATE : null);
      if(!selected) return null;
      if(state && Array.isArray(state.members)){
        return state.members.find(function(m){return String(m.id)===String(selected.id);}) || selected;
      }
      return selected;
    }catch(e){ return null; }
  }

  function closeAction(){
    var box=document.getElementById('jmSelfCardAction');
    if(box) box.classList.add('hidden');
  }
  window.closeJmSelfCardAction=closeAction;

  window.jmMd6MoveSelf=async function(status){
    var member=currentMember();
    if(!member) return;
    closeAction();
    try{
      if(typeof showSavingOverlay === 'function') showSavingOverlay('저장중');
      await server('memberMoveSelf',[String(member.id),{type:'status',status:String(status)}]);
      if(typeof refreshMemberState === 'function') await refreshMemberState();
    }catch(error){
      alert(error&&error.message?error.message:String(error));
    }finally{
      if(typeof hideSavingOverlay === 'function') hideSavingOverlay();
    }
  };

  function rebuildAction(){
    var box=document.getElementById('jmSelfCardAction');
    if(!box || box.dataset.md6SelfLongpress==='1') return;
    box.dataset.md6SelfLongpress='1';
    box.innerHTML = ''+
      '<button class="jm-md6-close" type="button" aria-label="닫기" onclick="closeJmSelfCardAction()">×</button>'+
      '<div class="jm-md6-self-actions">'+
        '<button type="button" onclick="jmMd6MoveSelf(\'before\')">도착전</button>'+
        '<button type="button" onclick="jmMd6MoveSelf(\'active\')">코트배정대기</button>'+
        '<button type="button" onclick="jmMd6MoveSelf(\'rest\')">휴식</button>'+
        '<button type="button" onclick="jmMd6MoveSelf(\'away\')">귀가</button>'+
        '<button class="jm-md6-info" type="button" onclick="closeJmSelfCardAction();openJmSelfProfile(event)">내정보입력</button>'+
      '</div>';
  }

  function syncOwnMemo(){
    var member=currentMember();
    if(!member) return;
    var memo=String(member.publicMemo||'').trim();
    document.querySelectorAll('[data-member-id="'+String(member.id).replace(/"/g,'')+'"]').forEach(function(card){
      if(!card.closest('#memberApp')) return;
      var node=card.querySelector('.jm-public-memo,.member-public-memo');
      if(memo && !node){
        node=document.createElement('span');
        node.className='jm-public-memo';
        card.appendChild(node);
      }
      if(node){
        node.textContent=memo;
        node.hidden=!memo;
      }
    });
  }

  var queued=false;
  function normalize(){
    if(queued) return;
    queued=true;
    requestAnimationFrame(function(){queued=false;rebuildAction();syncOwnMemo();});
  }
  new MutationObserver(normalize).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',normalize,{once:true});
  document.addEventListener('click',function(){setTimeout(normalize,40);},true);
  setInterval(normalize,1200);
  normalize();
})();
</script>
'''

if "</body>" in text:
    text = text.replace("</body>", addon + "\n</body>", 1)
else:
    text += "\n" + addon

path.write_text(text, encoding="utf-8")
print("MD6 self long-press patch applied")
