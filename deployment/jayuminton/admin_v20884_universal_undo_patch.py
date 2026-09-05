#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
html = path.read_text(encoding='utf-8')
MARKER = 'jmAdminUniversalUndoV20884'

if MARKER in html:
    print('ADMIN_UNIVERSAL_UNDO_V20884_ALREADY_OK')
    raise SystemExit(0)

for required in (
    'jmAdminReplyRepositionV20883',
    'jmAdminKokCompactV20882',
    'jmAdminFixedQuickMenuV20880',
    'function installThreeStepUndo()',
    "window.undoLastAction=async function()",
):
    if required not in html:
        raise SystemExit('v208.84 prerequisite missing: ' + required)

SCRIPT = r'''
<script id="jmAdminUniversalUndoV20884Script">
(function(){
  'use strict';
  if(window.__jmAdminUniversalUndoV20884)return;
  window.__jmAdminUniversalUndoV20884=true;

  var authoritative=null;
  var lastPushedSig='';
  var installTries=0;

  function clone(value){
    if(!value)return null;
    try{return JSON.parse(JSON.stringify(value));}catch(_){return null;}
  }
  function currentState(){
    try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(_){return null;}
  }
  function stateFromResult(result){
    if(result&&Array.isArray(result.members)&&result.courts&&Array.isArray(result.waitGroups))return result;
    if(result&&result.state&&Array.isArray(result.state.members)&&result.state.courts&&Array.isArray(result.state.waitGroups))return result.state;
    return null;
  }
  function scrub(value,key){
    if(key&&/^(serverTime|syncedAt|lastPolledAt|lastFetchedAt)$/i.test(key))return undefined;
    if(Array.isArray(value))return value.map(function(v){return scrub(v,'');});
    if(value&&typeof value==='object'){
      var out={};Object.keys(value).sort().forEach(function(k){var v=scrub(value[k],k);if(v!==undefined)out[k]=v;});return out;
    }
    return value;
  }
  function sig(state){
    try{return JSON.stringify(scrub(state,''));}catch(_){return '';}
  }
  function isUndoableName(name){
    name=String(name||'');
    if(!name||name==='undoLastAction'||name==='sendMemberMessage'||name==='createManualBackup'||name==='changeMemberPassword')return false;
    return /^(add|update|set|clear|delete|assign|smartAssign|finish|swap|move|adjust|decrease|reset|restore|dismiss)/.test(name);
  }
  function chainHas(fn,prop){
    var depth=0,seen=[];
    while(typeof fn==='function'&&depth++<16){
      if(fn[prop])return true;
      if(seen.indexOf(fn)>=0)break;seen.push(fn);
      fn=fn.__original||fn.__jmInner||null;
    }
    return false;
  }
  function pushUndo(snapshot){
    if(!snapshot||typeof window.setUndoState!=='function')return;
    var s=sig(snapshot);
    if(s&&s===lastPushedSig)return;
    window.setUndoState(snapshot);
  }

  function wrapUndoFunctions(){
    if(typeof window.setUndoState!=='function'||typeof window.undoLastAction!=='function')return false;

    if(!window.setUndoState.__jmUniversalUndoDedupV20884){
      var oldSetUndo=window.setUndoState;
      var wrappedSetUndo=function(state){
        var copy=clone(state);if(!copy)return;
        var s=sig(copy);if(s&&s===lastPushedSig)return;
        lastPushedSig=s;
        return oldSetUndo.call(this,copy);
      };
      wrappedSetUndo.__jmUniversalUndoDedupV20884=true;
      wrappedSetUndo.__original=oldSetUndo;
      window.setUndoState=wrappedSetUndo;
      try{setUndoState=wrappedSetUndo;}catch(_){}
    }

    if(!window.undoLastAction.__jmUniversalUndoRefreshV20884){
      var oldUndo=window.undoLastAction;
      var wrappedUndo=async function(){
        try{return await oldUndo.apply(this,arguments);}
        finally{
          authoritative=clone(currentState())||authoritative;
          lastPushedSig='';
        }
      };
      wrappedUndo.__jmUniversalUndoRefreshV20884=true;
      wrappedUndo.__original=oldUndo;
      window.undoLastAction=wrappedUndo;
      try{undoLastAction=wrappedUndo;}catch(_){}
    }
    return true;
  }

  function wrapServer(){
    var current=window.server;
    if(typeof current!=='function')return false;
    if(chainHas(current,'__jmUniversalUndoServerV20884'))return true;

    var wrapped=async function(name,args){
      var method=String(name||'');
      var undoable=isUndoableName(method);
      var before=undoable?clone(authoritative||currentState()):null;
      var beforeSig=before?sig(before):'';
      try{
        var result=await current.apply(this,arguments);
        var returned=stateFromResult(result);
        if(undoable&&before){
          var after=clone(returned||currentState());
          var afterSig=after?sig(after):'';
          if(after&&afterSig&&afterSig!==beforeSig)pushUndo(before);
          if(after)authoritative=after;
        }else if(returned){
          authoritative=clone(returned);
        }
        return result;
      }catch(error){
        throw error;
      }
    };
    try{Object.keys(current).forEach(function(k){if(k.indexOf('__jm')===0&&k!=='__original')wrapped[k]=current[k];});}catch(_){}
    wrapped.__jmUniversalUndoServerV20884=true;
    wrapped.__original=current;
    window.server=wrapped;
    try{server=wrapped;}catch(_){}
    return true;
  }

  function install(){
    installTries+=1;
    wrapUndoFunctions();
    var ok=wrapServer();
    if(!authoritative)authoritative=clone(currentState());
    return ok&&typeof window.setUndoState==='function'&&typeof window.undoLastAction==='function';
  }

  install();
  var timer=setInterval(function(){
    if(install()&&installTries>20){clearInterval(timer);return;}
    if(installTries>120)clearInterval(timer);
  },250);
})();
</script>
'''

if html.count('</body>') != 1:
    raise SystemExit('</body> anchor not unique')
html = html.replace('</body>', SCRIPT + '</body>', 1)

for required in (
    MARKER,
    '__jmUniversalUndoServerV20884',
    '__jmUniversalUndoDedupV20884',
    '__jmUniversalUndoRefreshV20884',
    "name==='undoLastAction'",
    "name==='sendMemberMessage'",
    "name==='createManualBackup'",
    "name==='changeMemberPassword'",
    '/^(add|update|set|clear|delete|assign|smartAssign|finish|swap|move|adjust|decrease|reset|restore|dismiss)/',
    "authoritative||currentState()",
    'pushUndo(before)',
):
    if required not in html:
        raise SystemExit('v208.84 requirement missing: ' + required)

path.write_text(html, encoding='utf-8')
print('ADMIN_UNIVERSAL_UNDO_V20884_OK')
