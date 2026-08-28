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
  var steps=[renderCourts,renderWaitGroups,renderActive,renderExcluded,renderInactive,renderStats,updateCourtTimers,renderWebPushMemberOptions,renderMemberSelfSettings,renderSelectionCount,renderQuickRoster,renderQuickMoveBar,renderWholeSwapBar];
  steps.forEach(function(fn){
    try{fn();}catch(err){console.error('[jm-render-resilience] '+(fn&&fn.name||'render step')+' failed, continuing',err);}
  });
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
