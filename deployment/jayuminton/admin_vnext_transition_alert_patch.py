#!/usr/bin/env python3
"""Admin-only Script patch: track transition event ids without showing member alerts.

Member-device wait1/court notifications are delivered by the push relay. The admin
screen must never mirror those notifications as a popup or vibration. This hook only
seeds/records persistent adminVnextEvents so stale events are not replayed on load.
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
  var jmTransitionBaselineReady = false;
  var jmOriginalRenderState = renderState;
  function jmRecordTransitionEvents(state){
    var events=(state&&state.adminVnextEvents)||[];
    events.forEach(function(event){
      if(event&&event.eventId)jmSeenTransitionEvents[event.eventId]=true;
    });
    jmTransitionBaselineReady=true;
    var ids=Object.keys(jmSeenTransitionEvents);
    if(ids.length>40){
      var keep={};ids.slice(-20).forEach(function(id){keep[id]=true;});jmSeenTransitionEvents=keep;
    }
  }
  renderState=function(state){
    var result=jmOriginalRenderState.apply(this,arguments);
    try{jmRecordTransitionEvents(state||STATE);}catch(e){}
    return result;
  };
  window.__JAYUMINTON_TRANSITION_ALERT__=function(){return;};
  window.__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__=function(){return {
    renderHook:true,
    memberDeviceOnly:true,
    adminPopup:false,
    adminVibration:false,
    initialReplaySuppressed:true,
    baselineReady:jmTransitionBaselineReady
  };};
})();
'''

source = source[:close] + addon + '\n' + source[close:]

for required in [
    '__JAYUMINTON_ADMIN_TRANSITION_ALERT_BRIDGE_V1__',
    '__JAYUMINTON_TRANSITION_ALERT__=function(){return;}',
    'renderState=function(state)',
    'jmRecordTransitionEvents(state||STATE)',
    'memberDeviceOnly:true',
    'adminPopup:false',
    'adminVibration:false',
    'initialReplaySuppressed:true'
]:
    if required not in source:
        raise SystemExit('transition event suppression missing: '+required)

if 'window.alert(message)' in addon or 'NativeVoice.vibrate' in addon or 'navigator.vibrate' in addon:
    raise SystemExit('admin member alert side effect reintroduced')

path.write_text(source, encoding='utf-8')
print('ADMIN_TRANSITION_EVENTS_TRACK_ONLY_OK')
