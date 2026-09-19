#!/usr/bin/env python3
"""Show member-owned appended memo on admin cards without merging it into admin fields."""

from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
text = path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_ADMIN_MEMBER_MEMO_OWNERSHIP_V20916"

if MARKER in text:
    print("ADMIN_V20916_MEMBER_MEMO_OWNERSHIP_ALREADY_OK")
    raise SystemExit(0)

addon = r'''
<style id="jayuminton-admin-member-memo-ownership-v20916">
/* JAYUMINTON_ADMIN_MEMBER_MEMO_OWNERSHIP_V20916 */
#adminApp [data-member-id]>.jm-member-owned-memo,
#adminApp [data-member-id] .jm-member-owned-memo{
  display:block!important;
  width:100%!important;
  margin:2px 0 0!important;
  font-size:9px!important;
  line-height:1.18!important;
  font-weight:800!important;
  color:#d946ef!important;
  text-align:center!important;
  white-space:normal!important;
  overflow-wrap:anywhere!important;
  word-break:keep-all!important;
}
</style>
<script>
(function installAdminMemberMemoOwnershipV20916(){
  if(window.__JAYUMINTON_ADMIN_MEMBER_MEMO_OWNERSHIP_V20916__)return;
  window.__JAYUMINTON_ADMIN_MEMBER_MEMO_OWNERSHIP_V20916__=true;
  var queued=false;
  function getState(){
    try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(error){return null;}
  }
  function sync(){
    queued=false;
    var state=getState();
    if(!state||!Array.isArray(state.members))return;
    var byId={};
    state.members.forEach(function(member){
      if(member&&member.id!=null)byId[String(member.id)]=member;
    });
    document.querySelectorAll('#adminApp [data-member-id]').forEach(function(card){
      var member=byId[String(card.getAttribute('data-member-id')||'')];
      if(!member)return;
      var memo=String(member.userMemo||'').trim();
      var node=card.querySelector(':scope > .jm-member-owned-memo');
      if(!memo){
        if(node)node.remove();
        return;
      }
      if(!node){
        node=document.createElement('span');
        node.className='jm-member-owned-memo';
        card.appendChild(node);
      }
      if(node.textContent!==memo)node.textContent=memo;
    });
  }
  function schedule(){
    if(queued)return;
    queued=true;
    requestAnimationFrame(sync);
  }
  new MutationObserver(schedule).observe(document.getElementById('adminApp')||document.documentElement,{childList:true,subtree:true});
  document.addEventListener('DOMContentLoaded',schedule,{once:true});
  document.addEventListener('click',function(){setTimeout(schedule,80);},true);
  setInterval(schedule,1200);
  schedule();
})();
</script>
'''

close = text.lower().rfind("</body>")
if close < 0:
    raise SystemExit("admin body close not found")
text = text[:close] + addon + "\n" + text[close:]

for required in (MARKER, "member.userMemo", "jm-member-owned-memo"):
    if required not in text:
        raise SystemExit("v209.16 output missing: " + required)

path.write_text(text, encoding="utf-8")
print("ADMIN_V20916_MEMBER_MEMO_OWNERSHIP_OK")
