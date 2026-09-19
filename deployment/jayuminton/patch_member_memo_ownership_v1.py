#!/usr/bin/env python3
"""Keep administrator card fields immutable to members and append member-owned memo."""

from pathlib import Path
import sys

MARKER = "JAYUMINTON_MEMBER_MEMO_OWNERSHIP_V1"

ADDON = r'''
<style id="jayuminton-member-memo-ownership-v1">
/* JAYUMINTON_MEMBER_MEMO_OWNERSHIP_V1 */
#memberApp [data-member-id]>.member-public-memo{
  color:#536178!important;
  text-shadow:none!important;
}
#memberApp [data-member-id]>.jm-user-owned-memo{
  display:block!important;
  width:100%!important;
  margin:2px 0 0!important;
  font-size:10px!important;
  line-height:1.25!important;
  font-weight:900!important;
  color:#d946ef!important;
  text-align:center!important;
  white-space:normal!important;
  overflow-wrap:anywhere!important;
  word-break:keep-all!important;
}
</style>
<script>
(function installMemberMemoOwnershipV1(){
  if(typeof IS_ADMIN!=='undefined'&&IS_ADMIN)return;
  if(window.__JAYUMINTON_MEMBER_MEMO_OWNERSHIP_V1__)return;
  window.__JAYUMINTON_MEMBER_MEMO_OWNERSHIP_V1__=true;

  var queued=false;
  var originalSettings=window.openMemberSelfSettings;

  function state(){
    try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(error){return null;}
  }
  function selected(){
    try{
      if(typeof selectedWebPushMember==='function')return selectedWebPushMember();
      if(typeof currentStoredWebPushMember==='function')return currentStoredWebPushMember();
    }catch(error){}
    return null;
  }
  function current(){
    var me=selected(),s=state();
    if(!me||!s||!Array.isArray(s.members))return null;
    return s.members.find(function(member){return member&&String(member.id)===String(me.id);})||me;
  }
  function fillSelfInputs(){
    var member=current(),value=String(member&&member.userMemo||'');
    var profileInput=document.getElementById('jmSelfProfileMemo');
    if(profileInput)profileInput.value=value;
    var settingsInput=document.getElementById('jmMemberSelfMemoInput');
    if(settingsInput)settingsInput.value=value;
    var help=document.querySelector('#jmSelfProfileModal .jm-self-profile-help');
    if(help)help.textContent='관리자가 등록한 급수·구력·메모는 수정할 수 없습니다. 아래 내용은 관리자 정보 뒤에 추가됩니다.';
  }

  window.openJmSelfProfile=function(event){
    if(event){event.preventDefault();event.stopPropagation();}
    var modal=document.getElementById('jmSelfProfileModal');
    if(!current()||!modal)return;
    fillSelfInputs();
    modal.classList.remove('hidden');
    setTimeout(function(){
      fillSelfInputs();
      var input=document.getElementById('jmSelfProfileMemo');
      if(input)input.focus();
    },30);
  };

  if(typeof originalSettings==='function'){
    window.openMemberSelfSettings=function(){
      var result=originalSettings.apply(this,arguments);
      setTimeout(fillSelfInputs,0);
      setTimeout(fillSelfInputs,80);
      return result;
    };
  }

  function sync(){
    queued=false;
    var s=state();
    if(!s||!Array.isArray(s.members))return;
    var byId={};
    s.members.forEach(function(member){
      if(member&&member.id!=null)byId[String(member.id)]=member;
    });
    document.querySelectorAll('#memberApp [data-member-id]').forEach(function(card){
      var member=byId[String(card.getAttribute('data-member-id')||'')];
      if(!member)return;
      var memo=String(member.userMemo||'').trim();
      var node=card.querySelector(':scope > .jm-user-owned-memo');
      if(!memo){
        if(node)node.remove();
      }else{
        if(!node){
          node=document.createElement('span');
          node.className='jm-user-owned-memo';
          card.appendChild(node);
        }
        if(node.textContent!==memo)node.textContent=memo;
      }
    });
    var member=current(),hasMemo=!!String(member&&member.userMemo||'').trim();
    document.querySelectorAll('#jmMemberSelfStatusMenu [data-action="내 정보 입력"]').forEach(function(button){
      button.textContent=hasMemo?'내 정보 수정':'내 정보 입력';
    });
    var save=document.getElementById('jmMemberSelfMemoSaveBtn');
    if(save&&!save.disabled)save.textContent=hasMemo?'내 정보 수정':'내 정보 저장';
  }

  function schedule(){
    if(queued)return;
    queued=true;
    requestAnimationFrame(sync);
  }
  new MutationObserver(schedule).observe(document.getElementById('memberApp')||document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});
  setInterval(schedule,1200);
  schedule();
})();
</script>
'''

def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print("MEMBER_MEMO_OWNERSHIP_ALREADY_OK")
        return
    close = text.lower().rfind("</body>")
    if close < 0:
        raise SystemExit("body close not found")
    text = text[:close] + ADDON + "\n" + text[close:]
    for required in (
        MARKER,
        "member.userMemo",
        "관리자가 등록한 급수·구력·메모는 수정할 수 없습니다.",
        "jm-user-owned-memo",
    ):
        if required not in text:
            raise SystemExit("memo ownership output missing: " + required)
    path.write_text(text, encoding="utf-8")
    print("MEMBER_MEMO_OWNERSHIP_OK")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_memo_ownership_v1.py INDEX_HTML")
    patch(Path(sys.argv[1]))
