(function installJayumintonAdminRenderResilienceV1(){
'use strict';
if(window.__JAYUMINTON_ADMIN_RENDER_RESILIENCE_V1__)return;
window.__JAYUMINTON_ADMIN_RENDER_RESILIENCE_V1__=true;
if(typeof window.renderState!=='function')return;
/* renderState() calls renderCourts/renderWaitGroups/renderActive/... back to
   back with no try/catch between them. If ANY one throws -- e.g. one bad
   member record with an unexpected field shape, from a partially-saved
   registration -- every call AFTER it in that sequence never runs either,
   so the whole app goes blank (courts, wait1-5, and the member list all
   disappear together) and stays blank on every future load, since the bad
   record is still sitting in state. Wrapping each call so one failure can't
   take down the sections after it -- the broken section stays empty (or
   stale) instead of the entire app going dark, and the error is visible in
   the console instead of silently swallowing the rest of the render. */
var original=window.renderState;
window.renderState=function(state){
  /* STATE and QUICK_PICK are `let`-declared at the base page's top-level
     script scope, not `var`/`function` -- unlike window.adminVnextCardName
     etc. (plain function declarations, which DO alias window.*), a `let`
     binding is NOT a window property. Assigning window.STATE here would
     silently create an unrelated, ignored property while renderCourts/
     renderQuickRoster/etc. keep reading the real (untouched) STATE they
     close over, leaving every section showing stale/empty data with no
     error. Classic (non-module) <script> tags in the same document DO all
     share one top-level lexical environment for let/const, so assigning
     the BARE identifier here reaches the same binding the base page's own
     renderState() would have updated -- confirmed against this page's
     AUTO_ASSIGN_TARGET/SELECTED overlay pattern used elsewhere already. */
  if(state){
    try{STATE=normalizeStateMemberProfiles(state);}
    catch(err){console.error('[jm-render-resilience] normalizeStateMemberProfiles failed',err);STATE=state;}
  }else{
    try{normalizeStateMemberProfiles(STATE);}catch(err){console.error('[jm-render-resilience] normalizeStateMemberProfiles failed',err);}
  }
  if(!IS_ADMIN&&window.parent!==window){
    try{
      window.parent.postMessage({type:'JAYUMINTON_MEMBER_LIST',members:(STATE.members||[]).map(function(item){return {id:String(item.id),name:String(item.name||'')};})},'*');
    }catch(err){console.error('[jm-render-resilience] postMessage failed',err);}
  }
  /* jmRenderResilienceChainFixV1: `original` used to be captured and then
     never called -- this wrapper always ran ITS OWN hardcoded step list
     instead, which silently discarded every wrapper installed BEFORE this
     one in document order (admin-self-alert's popup+3x8-vibration detector,
     the yellow-team-stable wrapper, and anything else that wraps
     window.renderState earlier). Confirmed live: arming the admin's own
     "내 알림" member and simulating their 대기2->대기1 move produced no
     popup and no vibrate() call, even though the popup/vibration code
     itself is present and correct -- because window.renderState by then was
     THIS function, and this function never invoked the chain that leads
     back to it. Fix: try the full chain first (so every earlier wrapper's
     side effects still run), and only fall back to the manual per-step
     resilient render -- this file's actual original purpose -- if the
     chain throws synchronously, which is the exact failure mode this file
     was written to guard against in the first place. */
  var ranViaChain=false;
  if(typeof original==='function'){
    try{
      original.apply(this,arguments);
      ranViaChain=true;
    }catch(err){
      console.error('[jm-render-resilience] chained renderState threw, falling back to per-step resilient render',err);
    }
  }
  if(!ranViaChain){
    var steps=[renderCourts,renderWaitGroups,renderActive,renderExcluded,renderInactive,renderStats,updateCourtTimers,renderWebPushMemberOptions,renderMemberSelfSettings,renderSelectionCount,renderQuickRoster,renderQuickMoveBar,renderWholeSwapBar];
    steps.forEach(function(fn){
      try{fn();}catch(err){console.error('[jm-render-resilience] '+(fn&&fn.name||'render step')+' failed, continuing',err);}
    });
  }
  try{
    if(QUICK_PICK){
      document.querySelectorAll('[data-member-id="'+QUICK_PICK.memberId+'"]').forEach(function(element){element.classList.add('quick-picked');});
    }
  }catch(err){console.error('[jm-render-resilience] QUICK_PICK highlight failed',err);}
  try{
    var count=document.getElementById('memberCount');
    if(count)count.textContent=STATE.members.length+'/'+(STATE.maxMembers||500)+'명';
  }catch(err){console.error('[jm-render-resilience] memberCount failed',err);}
  try{
    var updated=document.getElementById('updatedAt');
    if(updated)updated.textContent='최근 반영: '+new Date().toLocaleTimeString('ko-KR');
  }catch(err){console.error('[jm-render-resilience] updatedAt failed',err);}
};
window.renderState.__jmRenderResilienceV1Original=original;
})();
