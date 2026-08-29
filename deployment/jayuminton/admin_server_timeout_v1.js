(function installJayumintonAdminServerTimeoutV1(){
'use strict';
if(window.__JAYUMINTON_ADMIN_SERVER_TIMEOUT_V1__)return;
window.__JAYUMINTON_ADMIN_SERVER_TIMEOUT_V1__=true;
/* The Cloudflare RPC call (directServer's fetch, wrapped by the save-lock
   layer above) has no timeout at all. If that fetch hangs -- a flaky mobile
   connection, a slow Worker cold start, a dropped WebView network request --
   the returned promise never resolves or rejects, so nothing downstream
   (setBusy(false), setActionBusy(false), the initial loadState() render)
   ever runs either: the "저장중" lock never lifts and no button responds,
   or the app just shows nothing forever with no error to explain why. This
   wraps whatever window.server currently is so its promise always settles
   within TIMEOUT_MS, surfacing a clear error and releasing every lock layer
   above it instead of freezing permanently. It does not (cannot, from out
   here) cancel the underlying fetch -- only bounds how long the UI waits
   on it. */
var TIMEOUT_MS=20000;
/* jmServerWrapChainFixV1: previously only checked the OUTERMOST window.server
   for cur.__jmServerTimeoutV1. If the save-lock or team-state wrappers
   re-wrapped window.server on top in between polls (each has its own
   independent setInterval, none aware of the others), the outer function
   lacked this flag, so this poll wrapped AGAIN underneath -- nesting this
   timeout layer multiple times per real call. Walk the chain via __jmInner
   instead of checking only the top, so this wrapper applies exactly once
   regardless of what else has wrapped window.server since. */
function jmChainHasTimeoutV1(fn){
  var depth=0;
  while(typeof fn==='function'&&depth<50){
    if(fn.__jmServerTimeoutV1)return true;
    fn=fn.__jmInner||fn.__original;
    depth++;
  }
  return false;
}
function wrap(){
  var cur=window.server;
  if(typeof cur!=='function'||jmChainHasTimeoutV1(cur))return;
  var wrapped=function(name,args){
    var call;
    try{call=cur.apply(this,arguments);}catch(err){return Promise.reject(err);}
    return new Promise(function(resolve,reject){
      var settled=false;
      var timer=setTimeout(function(){
        if(settled)return;settled=true;
        reject(new Error('서버 응답이 없습니다 ('+(TIMEOUT_MS/1000)+'초 초과). 네트워크를 확인하고 다시 시도하세요.'));
      },TIMEOUT_MS);
      Promise.resolve(call).then(function(result){
        if(settled)return;settled=true;clearTimeout(timer);resolve(result);
      },function(error){
        if(settled)return;settled=true;clearTimeout(timer);reject(error);
      });
    });
  };
  wrapped.__jmServerTimeoutV1=true;
  wrapped.__jmInner=cur;
  window.server=wrapped;
}
wrap();
var tries=0,timer=setInterval(function(){wrap();if(++tries>150)clearInterval(timer);},200);
})();
