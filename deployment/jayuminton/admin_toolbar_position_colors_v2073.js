(function installJayumintonAdminToolbarV2076(){
'use strict';
if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
if(window.__JAYUMINTON_ADMIN_TOOLBAR_V2076__)return;
window.__JAYUMINTON_ADMIN_TOOLBAR_V2076__=true;
window.__JAYUMINTON_ADMIN_TOOLBAR_V2075__=true;
window.__JAYUMINTON_ADMIN_TOOLBAR_V2074__=true;
window.__JAYUMINTON_ADMIN_TOOLBAR_V2073__=true;
var pendingSlots=[],assigning=false;
function root(){return document.getElementById('adminApp');}
function state(){try{return typeof STATE!=='undefined'&&STATE?STATE:null;}catch(_){return null;}}
function toast(text,bad){var old=document.getElementById('jmV2076Toast');if(old)old.remove();var n=document.createElement('div');n.id='jmV2076Toast';n.textContent=String(text||'');n.style.cssText='position:fixed;left:50%;top:max(10px,env(safe-area-inset-top));transform:translateX(-50%);z-index:2147483647;padding:9px 13px;border-radius:11px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:13px;font-weight:900;box-shadow:0 8px 24px rgba(0,0,0,.25)';document.body.appendChild(n);setTimeout(function(){n.remove();},1800);}
function cardId(card){if(!card)return '';for(var a of ['data-member-id','data-memberid','data-player-id','data-id','data-member']){var id=String(card.getAttribute&&card.getAttribute(a)||'');if(id)return id;}var n=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');return n?cardId(n):'';}
function selectedIds(){var ids=[];try{document.querySelectorAll('#adminApp .jm-unlimited-check').forEach(function(check){var card=check.closest('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member],.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player');var id=cardId(card);if(id&&ids.indexOf(id)<0)ids.push(id);});}catch(_){}return ids;}
function clearLegacySelection(){var b=document.querySelector('#jmUnlimitedToolbar [data-a="clear"]');if(b){try{b.click();return;}catch(_){}}try{if(typeof SELECTED!=='undefined'&&SELECTED&&SELECTED.clear)SELECTED.clear();}catch(_){} }
function messageSelected(){var ids=selectedIds();if(!ids.length)return toast('멤버를 먼저 선택하세요.',true);try{if(typeof SELECTED!=='undefined'&&SELECTED&&SELECTED.clear){SELECTED.clear();ids.forEach(function(id){SELECTED.add(String(id));});}}catch(_){}try{if(typeof window.openQuickMemberMessage==='function'){window.openQuickMemberMessage();return;}}catch(_){}var text=window.prompt('선택한 '+ids.length+'명에게 보낼 메시지를 입력하세요.','');if(!text)return;if(typeof window.server!=='function')return toast('메시지 기능을 찾을 수 없습니다.',true);window.server('sendMemberMessage',[null,ids,String(text)]).then(function(){toast(ids.length+'명에게 메시지 전송 완료');}).catch(function(e){toast(String(e&&e.message||e||'메시지 전송 실패'),true);});}
function quickCard(){var q=document.getElementById('quickSelectedCount');if(q){var c=q.closest('.card');if(c)return c;}var r=root();if(!r)return null;for(var h of r.querySelectorAll('h1,h2,h3,strong'))if(String(h.textContent||'').indexOf('빠른 코트배정')>=0)return h.closest('.card')||h.parentElement;return null;}
function quickHeader(card){if(!card)return null;return card.querySelector('.quick-roster-header')||Array.from(card.children).find(function(el){return /빠른 코트배정/.test(String(el.textContent||''));})||card.firstElementChild;}
function ensureToolbar(){var bar=document.getElementById('jmUnlimitedToolbar');if(!bar)return false;var title=bar.querySelector('.jm-u-head strong');if(title&&title.textContent!=='멤버 팀, 교환, 메세지')title.textContent='멤버 팀, 교환, 메세지';['status','move','swap'].forEach(function(a){var b=bar.querySelector('[data-a="'+a+'"]');if(b)b.style.display='none';});var ss=bar.querySelector('#jmUnlimitedStatus');if(ss)ss.remove();var grid=bar.querySelector('.jm-u-grid');if(grid&&!grid.querySelector('[data-a="message"]')){var b=document.createElement('button');b.type='button';b.setAttribute('data-a','message');b.textContent='메시지보내기';var clear=grid.querySelector('[data-a="clear"]');if(clear)grid.insertBefore(b,clear);else grid.appendChild(b);b.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();messageSelected();},true);}var card=quickCard(),head=quickHeader(card);if(card){if(head&&head.parentNode===card){if(head.nextSibling!==bar)card.insertBefore(bar,head.nextSibling);}else if(bar.parentNode!==card)card.insertBefore(bar,card.firstChild);if(!bar.classList.contains('jm-toolbar-under-quick-title'))bar.classList.add('jm-toolbar-under-quick-title');}return true;}
function syncSelectionVisual(){var r=root();if(!r)return;var shouldBeSelected=new Set();r.querySelectorAll('.jm-unlimited-check').forEach(function(check){var card=check.closest('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member],.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player');if(card)shouldBeSelected.add(card);});r.querySelectorAll('.jm-v2074-selected').forEach(function(c){if(!shouldBeSelected.has(c))c.classList.remove('jm-v2074-selected');});shouldBeSelected.forEach(function(card){if(!card.classList.contains('jm-v2074-selected'))card.classList.add('jm-v2074-selected');});}
function wait4Box(){
  /* jmWait4BoxScopeFixV1: the old version scanned CONTAINERS first (outer to
     inner, since querySelectorAll returns document order) and returned the
     FIRST one whose DESCENDANTS anywhere included a '대기4' heading -- for a
     large enough outer wrapper (e.g. the whole admin body), that's every
     ancestor of the real 대기4 card, including one that also contains the
     COURTS section. fixWait4Second() then treated a court's own empty slot
     as "대기4's second slot" and tagged it with the wrong onclick, making
     that court slot silently do nothing (or the wrong thing) when tapped.
     Find the '대기4' HEADING first instead (a small, specific element), then
     walk up to its own closest card/section -- same proven-safe pattern
     admin_layout_wait4_compact_v2076.js's wait4Row() already uses. */
  var r=root();if(!r)return null;
  var heads=r.querySelectorAll('h1,h2,h3,h4,strong,.title,.wait-title');
  for(var h of heads){
    if(!/^대기\s*4\b/.test(String(h.textContent||'').trim()))continue;
    var row=h.closest('.card,section,[class*="wait"]')||h.parentElement;
    if(row)return row;
  }
  return null;
}
function fixWait4Second(){var box=wait4Box();if(!box)return false;var list=Array.from(box.querySelectorAll('.empty,.quick-empty-slot,[class*="empty"],[onclick]')).filter(function(el){return /비어\s*있음/.test(String(el.textContent||''))||el.classList.contains('empty')||el.classList.contains('quick-empty-slot');});var slot=list[1];if(!slot)return false;slot.disabled=false;slot.removeAttribute('disabled');slot.removeAttribute('aria-disabled');slot.removeAttribute('inert');if(slot.classList.contains('disabled')||slot.classList.contains('is-disabled')||slot.classList.contains('inactive')||slot.classList.contains('non-clickable'))slot.classList.remove('disabled','is-disabled','inactive','non-clickable');slot.style.setProperty('pointer-events','auto','important');slot.style.setProperty('opacity','1','important');slot.style.setProperty('cursor','pointer','important');slot.setAttribute('data-jm-wait4-second-fixed','1');var raw=String(slot.getAttribute('onclick')||'');if(!/handleEmptySlotTap|handleMemberWaitEmptyTap/.test(raw))slot.setAttribute('onclick',"handleEmptySlotTap('wait','3',1)");return true;}
function findButton(text){var r=root();if(!r)return null;return Array.from(r.querySelectorAll('button')).find(function(b){return String(b.textContent||'').trim()===text;})||null;}
function ensureBottomMove(){/* jmManualAssignRenameV1: label only -- click behavior (proxy to the
hidden #jmUnlimitedToolbar [data-a="swap"] button, which starts the old
mode='swap' system) is unchanged. That mode is only needed for card-to-card
swap against an OCCUPIED member; placing selected members into an EMPTY
slot already works with no mode at all via installDirectPlacement()'s
document-level listener above, which always intercepts empty-slot clicks
first when something is selected -- so renaming this button to 수동배정
does not require any new placement logic, only the label. */
var r=root();if(!r)return false;var existing=document.getElementById('jmBottomMoveButton'),refresh=findButton('새로고침'),auto=findButton('자동배정');if(!refresh||!auto)return false;var parent=refresh.parentElement;if(!parent||auto.parentElement!==parent)return false;if(!existing){existing=document.createElement('button');existing.id='jmBottomMoveButton';existing.type='button';existing.textContent='수동배정';existing.className=refresh.className||'';existing.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();var swapBtn=document.querySelector('#jmUnlimitedToolbar [data-a="swap"]');if(swapBtn)swapBtn.click();else toast('멤버를 먼저 선택하세요.',true);});}if(existing.textContent!=='수동배정')existing.textContent='수동배정';if(existing.parentElement!==parent||existing.nextSibling!==refresh)parent.insertBefore(existing,refresh);if(!parent.classList.contains('jm-bottom-four-actions'))parent.classList.add('jm-bottom-four-actions');return true;}
function parseSlot(el){if(!el)return null;var raw=String(el.getAttribute&&el.getAttribute('onclick')||'');var m=raw.match(/handleEmptySlotTap\(['\"](court|wait)['\"],['\"]?([^,'\")]+)['\"]?,\s*(\d+)/);if(m)return {type:m[1],key:m[1]==='wait'?String(Number(m[2])+1):String(m[2]),slot:Number(m[3]),el:el};m=raw.match(/handleMemberWaitEmptyTap\((\d+),\s*(\d+)/);if(m)return {type:'wait',key:String(Number(m[1])+1),slot:Number(m[2]),el:el};if(el.getAttribute&&el.getAttribute('data-jm-wait4-second-fixed')==='1')return {type:'wait',key:'4',slot:1,el:el};return null;}
function slotKey(t){return t.type+'|'+t.key+'|'+t.slot;}
function paintSlots(){var r=root();if(!r)return;var shouldBeTargeted=new Set();pendingSlots.forEach(function(t){if(t.el&&document.contains(t.el))shouldBeTargeted.add(t.el);});r.querySelectorAll('.jm-v2076-target-slot').forEach(function(x){if(!shouldBeTargeted.has(x))x.classList.remove('jm-v2076-target-slot');});shouldBeTargeted.forEach(function(el){if(!el.classList.contains('jm-v2076-target-slot'))el.classList.add('jm-v2076-target-slot');});}
function freeAt(t){var s=state();if(!s)return 1;var list=t.type==='court'?(s.courts&&s.courts[String(t.key)]):((s.waitGroups||[])[Number(t.key)-1]);return Math.max(0,4-(Array.isArray(list)?list.length:0));}
async function assign(ids,targets){if(assigning||!ids.length||!targets.length||typeof window.server!=='function')return;assigning=true;var done=0;try{
/* jmBatchAssignSingleRpcV1: this used to await window.server('moveOrSwapMember',...)
   once per member in a for-loop -- for N selected members that's N sequential
   round-trips (visibly slow, "한자리씩... 너무 느리네"), and if the server
   rejected any call partway through (e.g. a capacity race), the members from
   earlier iterations were already committed on the server while the catch
   block below showed a single failure toast for the whole batch -- so the UI
   could report failure/success that didn't match what actually landed.
   All targets built by assignSelectedToClicked() share the same {type,key}
   (only the per-slot index differs), so the whole batch is really one
   placement into one court/wait group -- exactly what assignMembersToCourt /
   assignMembersToWaitGroup already do server-side as a single atomic call
   with one capacity check. Use that instead of the sequential loop. */
var t0=targets[0];var n=Math.min(ids.length,targets.length);var batchIds=ids.slice(0,n);
var method=t0.type==='court'?'assignMembersToCourt':'assignMembersToWaitGroup';
var key=t0.type==='wait'?String(Number(t0.key)-1):String(t0.key);
await window.server(method,[null,key,batchIds]);
done=n;
pendingSlots=pendingSlots.filter(function(p){return targets.indexOf(p)<0;});clearLegacySelection();try{var fresh=await window.server('getPublicState',[null]);if(typeof renderState==='function')renderState(fresh&&fresh.state?fresh.state:fresh);}catch(_){}toast(done+'명 빈자리에 배정 완료');}catch(e){toast(String(e&&e.message||e||'자리배정 실패'),true);}finally{assigning=false;setTimeout(function(){paintSlots();syncSelectionVisual();},0);}}
function assignSelectedToClicked(slot){var ids=selectedIds();if(!ids.length)return false;var free=freeAt(slot);if(free<=0)return toast('빈자리가 없습니다.',true),true;var n=Math.min(ids.length,free),targets=[];for(var i=0;i<n;i++)targets.push({type:slot.type,key:slot.key,slot:i,el:slot.el});assign(ids.slice(0,n),targets);return true;}
function togglePendingSlot(slot){var key=slotKey(slot),i=pendingSlots.findIndex(function(x){return slotKey(x)===key;});if(i>=0)pendingSlots.splice(i,1);else pendingSlots.push(slot);paintSlots();toast(pendingSlots.length+'개 빈자리 선택');}
function maybeAssignPendingAfterMember(){if(assigning||!pendingSlots.length)return;setTimeout(function(){var ids=selectedIds();if(!ids.length)return;var n=Math.min(ids.length,pendingSlots.length);assign(ids.slice(0,n),pendingSlots.slice(0,n));},0);}
function installDirectPlacement(){if(window.__jmDirectPlacementV2076)return;window.__jmDirectPlacementV2076=true;document.addEventListener('click',function(e){var r=root();if(!r||!r.contains(e.target)||assigning)return;var empty=e.target.closest&&e.target.closest('.empty,.quick-empty-slot,[class*="empty"],[onclick*="handleEmptySlotTap"],[onclick*="handleMemberWaitEmptyTap"],[data-jm-wait4-second-fixed="1"]');var slot=parseSlot(empty);if(slot){var ids=selectedIds();if(ids.length){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();assignSelectedToClicked(slot);}else{
/* Nothing selected in the current toolbar's own tracking: do NOT intercept,
   let the page's own handleEmptySlotTap run so it can set/toggle
   AUTO_ASSIGN_TARGET (the yellow highlight) -- both the real 자동배정
   button and picking a target seat before choosing members depend on that
   native state, and swallowing this click here silently broke 자동배정
   entirely. BUT handleEmptySlotTap's OWN "nothing selected" check reads
   the separate legacy SELECTED Set, not this toolbar's selection -- and
   other code (messageSelected(), to call the message-send RPC) populates
   that same legacy Set as a side effect and never clears it afterward. Left
   alone, its leftover contents make handleEmptySlotTap think members ARE
   selected and immediately auto-place them into whatever slot gets clicked
   next, with no button press and no confirmation. Clear it here so the
   native handler only ever takes the safe "mark target" branch. */
try{if(typeof SELECTED!=='undefined'&&SELECTED&&SELECTED.size)SELECTED.clear();}catch(_){}
}
return;}
/* v2073.1: there used to be a "select members after marking a target seat
   completes the placement automatically" shortcut here. Removed: it fired
   on ANY member-card click as long as AUTO_ASSIGN_TARGET was still set from
   some earlier, unrelated slot click (minutes ago, for a totally different
   purpose -- team setup, messaging, status change), silently shoving
   whoever got selected next into that stale target instead of wherever the
   admin actually clicked. Member-first placement (select, then click the
   slot you want) already works correctly below via the branch above and
   does not depend on AUTO_ASSIGN_TARGET at all -- use that. */
},true);}
function exclusionPanel(){var r=root();if(!r)return null;for(var h of r.querySelectorAll('h1,h2,h3,h4,strong,.title,summary')){if(String(h.textContent||'').trim().indexOf('코트배정 제외')===0)return h.closest('.card,section,details')||h.parentElement;}return null;}
function cleanQuickLayout(){var card=quickCard(),panel=exclusionPanel();if(card&&panel&&card.parentNode&&panel!==card){if(panel.nextSibling!==card)card.parentNode.insertBefore(panel,card);}var r=root();if(!r)return;Array.from(r.querySelectorAll('button')).forEach(function(b){if(String(b.textContent||'').replace(/\s+/g,'').indexOf('코트배정대기로복귀')>=0&&!b.closest('#jmUnlimitedToolbar'))b.style.display='none';});['quickSelectedCount','mobileSelectedCount','mdBulkDeleteCount'].forEach(function(id){var el=document.getElementById(id);if(el)el.style.display='none';});}
function installStyle(){if(document.getElementById('jmToolbarV2076Style'))return;var s=document.createElement('style');s.id='jmToolbarV2076Style';s.textContent=''
+'#jmUnlimitedToolbar.jm-toolbar-under-quick-title{margin:7px 0 10px!important;padding:9px!important;border:1px solid #dbe4f0!important;border-radius:12px!important;background:#f8fafc!important;box-shadow:none!important}'
+'#jmUnlimitedToolbar .jm-u-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:5px!important}'
+'#jmUnlimitedToolbar .jm-u-grid button{min-width:0!important;min-height:38px!important;padding:5px 3px!important;border-radius:9px!important;font-size:10px!important;font-weight:900!important;line-height:1.1!important;white-space:normal!important}'
+'#jmUnlimitedToolbar [data-a="all"]{background:#334155!important;border-color:#334155!important;color:#fff!important}#jmUnlimitedToolbar [data-a="active"]{background:#2563eb!important;border-color:#2563eb!important;color:#fff!important}#jmUnlimitedToolbar [data-a="perm"]{background:#7c3aed!important;border-color:#7c3aed!important;color:#fff!important}#jmUnlimitedToolbar [data-a="perm-clear"]{background:#ede9fe!important;border-color:#a78bfa!important;color:#5b21b6!important}#jmUnlimitedToolbar [data-a="temp"]{background:#d4a017!important;border-color:#b98a10!important;color:#fff!important}#jmUnlimitedToolbar [data-a="temp-clear"]{background:#fff7d6!important;border-color:#d4a017!important;color:#7a5a00!important}#jmUnlimitedToolbar [data-a="move"],#jmUnlimitedToolbar [data-a="swap"],#jmUnlimitedToolbar [data-a="status"],#jmUnlimitedToolbar #jmUnlimitedStatus{display:none!important}#jmUnlimitedToolbar [data-a="message"]{background:#0891b2!important;border-color:#0891b2!important;color:#fff!important}#jmUnlimitedToolbar [data-a="clear"]{background:#e2e8f0!important;border-color:#cbd5e1!important;color:#334155!important}#jmUnlimitedToolbar [data-a="delete"]{background:#b91c1c!important;border-color:#b91c1c!important;color:#fff!important}'
+'#adminApp .jm-unlimited-check{display:none!important}#adminApp .jm-v2074-selected{outline:3px solid #16a34a!important;outline-offset:2px!important;filter:brightness(.97)!important}#adminApp .jm-v2076-target-slot{outline:3px dashed #2563eb!important;outline-offset:2px!important;opacity:1!important;pointer-events:auto!important}#adminApp [data-jm-wait4-second-fixed="1"]{pointer-events:auto!important;opacity:1!important;cursor:pointer!important}'
+'#adminApp .jm-bottom-four-actions{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:6px!important}#adminApp #jmBottomMoveButton{background:#059669!important;border-color:#059669!important;color:#fff!important;font-weight:900!important}'
+'@media(max-width:620px){#jmUnlimitedToolbar .jm-u-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}}';(document.head||document.documentElement).appendChild(s);}
function maintain(){ensureToolbar();fixWait4Second();syncSelectionVisual();ensureBottomMove();cleanQuickLayout();paintSlots();}
function boot(){installStyle();installDirectPlacement();var tries=0;(function retry(){tries++;maintain();if(tries<120)setTimeout(retry,100);})();var r=root();if(r&&!r.__jmToolbarV2076Observer){var queued=false;r.__jmToolbarV2076Observer=new MutationObserver(function(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;maintain();});});r.__jmToolbarV2076Observer.observe(r,{childList:true,subtree:true,attributes:true,attributeFilter:['class','disabled','aria-disabled','onclick']});}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
