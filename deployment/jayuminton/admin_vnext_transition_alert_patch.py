#!/usr/bin/env python3
"""Admin-only Script patch: route court/wait transition events through the native alert bridge.

The live admin source no longer guarantees a showPendingAlertsIfReady() helper, so
this patch hooks renderState() and consumes the persistent adminVnextEvents contract
already published by the backend. It intentionally ignores COURT_FINISHED because
finishCourt() already raises its immediate alert before the server response.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Script.html'
source = path.read_text(encoding='utf-8')

if '__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__' in source:
    print('ADMIN_TRANSITION_ALERT_BRIDGE_ALREADY_PRESENT')
    raise SystemExit(0)

close = source.rfind('</script>')
if close < 0:
    raise SystemExit('Script.html closing wrapper missing')
if 'function renderState(' not in source:
    raise SystemExit('renderState function missing')

addon = r'''
(function(){
  var jmSeenTransitionEvents = {};
  var jmOriginalRenderState = renderState;
  function jmMemberNameFromState(state,id){
    var members=(state&&state.members)||[];
    for(var i=0;i<members.length;i++){
      if(String(members[i]&&members[i].id)===String(id)){
        return String(members[i].name||members[i].fullName||'').trim();
      }
    }
    return '';
  }
  function jmTransitionMessage(state,event){
    if(!event)return '';
    var names=(event.memberIds||[]).map(function(id){return jmMemberNameFromState(state,id);}).filter(Boolean).map(function(name){return name+'님';});
    if(event.type==='COURT_PROMOTED'){
      return (names.length?names.join(', ')+'\n':'')+String(event.courtNo||'')+'번 코트로 들어가 주세요.';
    }
    if(event.type==='WAIT_ONE_PROMOTED'){
      return '대기 1번 '+(names.length?names.join(', ')+' ':'')+'준비해 주세요.';
    }
    return '';
  }
  function jmDeliverTransitionEvents(state){
    var events=(state&&state.adminVnextEvents)||[];
    events.forEach(function(event){
      if(!event||!event.eventId||jmSeenTransitionEvents[event.eventId])return;
      jmSeenTransitionEvents[event.eventId]=true;
      if(event.type==='COURT_FINISHED')return;
      var message=jmTransitionMessage(state,event);
      if(!message)return;
      if(typeof window.__JAYUMINTON_TRANSITION_ALERT__==='function') window.__JAYUMINTON_TRANSITION_ALERT__(message);
      else window.alert(message);
    });
    var ids=Object.keys(jmSeenTransitionEvents);
    if(ids.length>40){
      var keep={};ids.slice(-20).forEach(function(id){keep[id]=true;});jmSeenTransitionEvents=keep;
    }
  }
  renderState=function(state){
    var result=jmOriginalRenderState.apply(this,arguments);
    try{jmDeliverTransitionEvents(state||STATE);}catch(e){}
    return result;
  };
  window.__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__=function(){return {renderHook:true,courtPromoted:true,waitOnePromoted:true,finishHandledSeparately:true};};
})();
'''

source = source[:close] + addon + '\n' + source[close:]

for required in [
    '__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__',
    "event.type==='COURT_PROMOTED'",
    "event.type==='WAIT_ONE_PROMOTED'",
    "event.type==='COURT_FINISHED'",
    '__JAYUMINTON_TRANSITION_ALERT__',
    'renderState=function(state)'
]:
    if required not in source:
        raise SystemExit('transition event hook missing: '+required)

path.write_text(source, encoding='utf-8')
print('ADMIN_TRANSITION_ALERT_BRIDGE_OK')