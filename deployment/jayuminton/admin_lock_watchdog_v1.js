(function installJayumintonAdminLockWatchdogV1(){
'use strict';
if(window.__JAYUMINTON_ADMIN_LOCK_WATCHDOG_V1__)return;
window.__JAYUMINTON_ADMIN_LOCK_WATCHDOG_V1__=true;
/* Two independent "saving" locks exist in this app and both block every
   button/tap while engaged: the base page's own ACTION_IN_FLIGHT (toggles
   body.action-busy) and the JAYUMINTON_ADMIN_CLOUDFLARE_SAVE_LOCK_V24
   overlay's busyCount (toggles body.jm-admin-saving via
   window.__JAYUMINTON_ADMIN_SAVING__). Both wrap window.server on their own
   independent setInterval poll, re-wrapping whatever is currently assigned
   there without recognizing wrappers added by OTHER scripts (including
   admin_server_timeout_v1.js) -- so window.server can end up wrapped by the
   same lock logic more than once, nested. When that happens, a single RPC
   call can increment the lock more times than the eventual settle
   decrements it, or an inner nested layer can keep waiting on the real
   (possibly still-hung) request even after an outer layer's promise has
   already settled -- leaving the lock permanently engaged and every button
   dead, with no way to recover except a full reinstall (which hits the
   same nested-wrap race again on next load). Rather than trying to
   perfectly untangle every possible wrap ordering, watch the lock STATE
   directly: if either lock has been continuously engaged for longer than
   any real save could plausibly take, force both flags off. This is a
   safety net, not a fix for whatever made the underlying call slow --
   it just guarantees the UI can't stay dead forever. */
var STUCK_AFTER_MS=25000;
var actionSince=0, saveSince=0;
function isActionBusy(){ try{ return !!window.ACTION_IN_FLIGHT; }catch(e){ return false; } }
function isSaveBusy(){ try{ return !!window.__JAYUMINTON_ADMIN_SAVING__; }catch(e){ return false; } }
function forceClear(){
  try{ window.ACTION_IN_FLIGHT=false; }catch(e){}
  try{ window.__JAYUMINTON_ADMIN_SAVING__=false; }catch(e){}
  try{ document.body.classList.remove('action-busy'); }catch(e){}
  try{ document.body.classList.remove('jm-admin-saving'); }catch(e){}
  console.error('[jm-lock-watchdog] a saving lock was stuck for over '+(STUCK_AFTER_MS/1000)+'s -- force-released it so buttons respond again.');
}
setInterval(function(){
  var now=Date.now();
  if(isActionBusy()){ if(!actionSince)actionSince=now; else if(now-actionSince>STUCK_AFTER_MS){ forceClear(); actionSince=0; } }
  else actionSince=0;
  if(isSaveBusy()){ if(!saveSince)saveSince=now; else if(now-saveSince>STUCK_AFTER_MS){ forceClear(); saveSince=0; } }
  else saveSince=0;
},1000);
})();
