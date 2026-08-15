#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v3_admin_fast_render_patch.py WORKDIR')
work=Path(sys.argv[1])
script=work/'Script.html'
s=script.read_text(encoding='utf-8')
addon=r'''

/* JAYUMINTON_ADMIN_FAST_RENDER_V1 */
(function(){
  if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
  function sig(state){
    if(!state)return '';
    var members=(state.members||[]).map(function(m){return [String(m.id||''),String(m.status||''),Number(m.games||0),!!m.isNew];});
    var courts={};[1,2,3,4].forEach(function(no){courts[no]=(state.courts&&state.courts[no]||[]).map(String);});
    var waits=(state.waitGroups||[]).map(function(g){return (g||[]).map(String);});
    return JSON.stringify([members,courts,waits,state.courtStartedAt||{}]);
  }
  window.batchAssignToTarget=async function(ids,targetType,targetIndex){
    var previousState=JSON.parse(JSON.stringify(STATE));
    try{
      applyBatchAssignLocally(ids,targetType,targetIndex);
      renderState();
      var optimistic=sig(STATE);
      var method=targetType==='court'?'assignMembersToCourt':'assignMembersToWaitGroup';
      var state=await server(method,[ADMIN_PIN_VALUE,Number(targetIndex),ids]);
      state=normalizeStateMemberProfiles(state);
      if(sig(state)!==optimistic)renderState(state);else STATE=state;
      setUndoState(previousState);
    }catch(error){
      STATE=previousState;renderState();alert(error.message||error);
    }
  };
  window.quickMoveOrSwap=async function(memberId,targetType,targetIndex,targetMemberId){
    var previousState=JSON.parse(JSON.stringify(STATE));
    try{
      applyMoveOrSwapLocally(memberId,targetType,targetIndex,targetMemberId||'');
      renderState();
      var optimistic=sig(STATE);
      var state=await server('moveOrSwapMember',[ADMIN_PIN_VALUE,memberId,targetType,String(targetIndex),targetMemberId||'']);
      state=normalizeStateMemberProfiles(state);
      if(sig(state)!==optimistic)renderState(state);else STATE=state;
      setUndoState(previousState);
    }catch(error){
      STATE=previousState;renderState();alert(error.message||error);
    }
  };
})();
'''
if 'JAYUMINTON_ADMIN_FAST_RENDER_V1' not in s:
    pos=s.rfind('</script>')
    if pos<0:raise SystemExit('Script closing tag missing')
    s=s[:pos]+addon+'\n'+s[pos:]
script.write_text(s,encoding='utf-8')
for n in ['JAYUMINTON_ADMIN_FAST_RENDER_V1','if(sig(state)!==optimistic)renderState(state);else STATE=state;']:
    if n not in script.read_text(encoding='utf-8'):raise SystemExit('missing '+n)
print('ADMIN_FAST_RENDER_OK')
