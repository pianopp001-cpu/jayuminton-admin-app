(function installJayumintonAdminSmartPlacementV2081(){
'use strict';
if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
if(window.__JAYUMINTON_ADMIN_SMART_PLACEMENT_V2081__)return;
window.__JAYUMINTON_ADMIN_SMART_PLACEMENT_V2081__=true;
/* v2081.1 EMERGENCY ROLLBACK: the order-preserving one-member-per-slot
   placement (and its independent .jm-unlimited-check tracking) caused real
   incidents in production -- the wrong member got moved, and stray clicks
   moved leftover/unintended selections, because tracking could pick up
   checkmarks left on-screen by unrelated selection UI elsewhere in #adminApp
   (e.g. the game-count adjustment panel) instead of only the member the
   admin just meant to move. That entire mechanism has been removed. This
   file now ONLY carries the purely-visual, non-data-affecting fixes: hiding
   the checkmark badge (it was rendering visible and covering member names),
   forcing the "new" badge to stay in normal flow instead of overlapping
   names, and pinning the bottom action row so it does not scroll away.
   Placement/selection behavior is left untouched -- v2073's own
   installDirectPlacement (which reads selection fresh from the DOM on every
   click, so it cannot go stale) is intentionally NOT disabled here. */
function root(){return document.getElementById('adminApp');}
function fixCheckOverlap(){var r=root();if(!r)return;r.querySelectorAll('.jm-unlimited-check').forEach(function(b){b.style.setProperty('display','none','important');});}
function fixNewBadges(){var r=root();if(!r)return;Array.from(r.querySelectorAll('.new-badge,.member-vnext-badge')).forEach(function(el){el.style.setProperty('position','static','important');el.style.setProperty('top','auto','important');el.style.setProperty('right','auto','important');el.style.setProperty('display','inline-flex','important');el.style.setProperty('vertical-align','middle','important');el.style.setProperty('margin','0 4px 2px 0','important');el.style.setProperty('float','none','important');});Array.from(r.querySelectorAll('span,small,b,strong,em,div')).forEach(function(n){if(n.children.length!==0)return;var t=String(n.textContent||'').replace(/\s+/g,' ').trim();if(!/^(new\s*)?신규[.!·]?$/i.test(t))return;var cs=getComputedStyle(n);if(cs.position==='absolute'||cs.position==='fixed'){n.style.setProperty('position','static','important');n.style.setProperty('top','auto','important');n.style.setProperty('right','auto','important');}var p=n.parentElement;if(p){var pcs=getComputedStyle(p);if(pcs.position==='absolute'||pcs.position==='fixed'){p.style.setProperty('position','static','important');p.style.setProperty('top','auto','important');p.style.setProperty('right','auto','important');p.style.setProperty('display','inline-flex','important');}}});}
function fixBottomBar(){var row=document.getElementById('jmBottomActionRowV2079');if(!row)return;row.style.setProperty('position','fixed','important');row.style.setProperty('left','0','important');row.style.setProperty('right','0','important');row.style.setProperty('bottom','0','important');row.style.setProperty('z-index','2147483000','important');row.style.setProperty('background','#fff','important');row.style.setProperty('box-shadow','0 -4px 14px rgba(0,0,0,.18)','important');row.style.setProperty('padding','6px 8px calc(6px + env(safe-area-inset-bottom))','important');row.style.setProperty('margin','0 auto','important');row.style.setProperty('max-width','640px','important');row.style.setProperty('box-sizing','border-box','important');var h=row.getBoundingClientRect().height;if(h>0)document.body.style.setProperty('padding-bottom',(h+10)+'px','important');}
function fixExcludedNames(){var c=document.getElementById('excludedMembers');if(!c)return;Array.from(c.querySelectorAll('.member')).forEach(function(card){card.style.setProperty('flex-direction','column','important');card.style.setProperty('align-items','flex-start','important');card.style.setProperty('gap','2px','important');card.style.setProperty('text-align','left','important');var name=card.querySelector('.name');if(name){name.style.setProperty('white-space','normal','important');name.style.setProperty('overflow','visible','important');name.style.setProperty('text-overflow','clip','important');name.style.setProperty('max-width','100%','important');name.style.setProperty('width','100%','important');}var meta=card.querySelector('.meta');if(meta){meta.style.setProperty('white-space','normal','important');}});}
/* Spec (관리자_사용자.md): "신규가 아니더라도 모든 목록 이름(닉네임)까지
   항상 다 출력한다." The base app's adminVnextCardName truncated any
   non-isNew member to a 2-character compact name, dropping the
   parenthetical nickname entirely -- ambiguous and inconsistent with
   every other card in the app. Every card now always shows the complete
   stored name on a single line (no forced two-line break), which also
   removes the main source of the oversized "new member" card height. */
function fixDuplicateNameDisplay(){if(window.__jmDuplicateNameFixV1||typeof window.adminVnextCardName!=='function'||typeof window.escapeMemberInfo!=='function')return;window.__jmDuplicateNameFixV1=true;var original=window.adminVnextCardName,escapeInfo=window.escapeMemberInfo;window.adminVnextCardName=function(member){
/* Any unexpected data shape here must never be able to break card
   rendering (a render-loop throw can blank out an entire section, e.g.
   a wait group, instead of just this one card) -- fall straight back to
   the original implementation on any error rather than risk that. */
try{
if(!member)return '';var storedName=String(member.name||'').trim();return '<span class="member-vnext-full-name">'+escapeInfo(storedName)+'</span>';
}catch(_){try{return original(member);}catch(__){return '';}}
};}
/* The general-purpose memberCard() builder (used by court/wait/other
   lists, separate from the quick-roster path above) independently calls
   compactMemberName() to make the same 2-character truncation decision.
   compactMemberName is a plain top-level function declaration, so
   reassigning it here changes what every caller sees on their next
   invocation -- the same technique already relied on above for
   adminVnextCardName. */
function fixGlobalCompactName(){if(window.__jmFullNameEverywhereV1||typeof window.compactMemberName!=='function')return;window.__jmFullNameEverywhereV1=true;window.compactMemberName=function(name){return String(name||'').trim();};}
/* markAdminNewCards() (in the separate <script id="adminVnextNewCardSizer">
   IIFE) is a THIRD, independent name-decoration path, driven by its own
   requestAnimationFrame-scheduled pass over every rendered card -- it
   re-applies usesAdminFullName()'s isNew/isDuplicate gate AFTER initial
   render and directly overwrites the name element's textContent/innerHTML,
   silently undoing both fixes above the instant it next runs. It was the
   actual reason members kept losing their full name (including the
   parenthetical nickname) even after adminVnextCardName/compactMemberName
   were fixed here. UNLIKE those two, usesAdminFullName/fullAdminNameHtml
   are declared *inside* that IIFE's closure, not at the top level of the
   shared script -- window.usesAdminFullName=... only creates an unrelated
   global property and never reaches what markAdminNewCards() actually
   calls. That decorator's only real fix point is its own source text, so
   it is patched directly in build-admin-toolbar-v2073.yml
   (jmMarkAdminNewCardsFullNameFixV1) rather than here. */
/* Spec: "한줄에 5명 나오게 해주라고. 이름과 설명 다 가리지 않고 세로가
   약간 길어지게 하면 되잖아." Always 5 columns, regardless of width --
   the previous responsive stepping (3 columns, only 5 above 520px) left
   narrow phones stuck at 2-3. Height stays auto and text wraps instead of
   clipping, so a narrower card just grows taller rather than hiding
   anything. */
function ensureQuickRosterGridStyle(){if(document.getElementById('jmQuickRosterGridV1'))return;var style=document.createElement('style');style.id='jmQuickRosterGridV1';style.textContent='#quickActiveRoster.v4-quick-roster{grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:4px!important;align-items:start!important}#quickActiveRoster .quick-member{padding:4px 3px!important;min-height:40px!important;height:auto!important;gap:2px!important}#quickActiveRoster .quick-member-name{font-size:clamp(8.5px,2.3vw,11px)!important;line-height:1.15!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:keep-all!important}#quickActiveRoster .quick-member-games{font-size:6.5px!important;margin-top:-1px!important}#quickActiveRoster .member-info-detail{font-size:6.5px!important;margin-top:1px!important;white-space:normal!important}#quickActiveRoster .member-vnext-memo{font-size:6.5px!important;white-space:normal!important}#quickActiveRoster .member-vnext-badge.new-badge{position:static!important;display:inline-flex!important;width:auto!important;margin:1px auto 0!important;padding:1px 3px!important;font-size:6.5px!important;box-shadow:none!important}';(document.head||document.documentElement).appendChild(style);}
function maintain(){try{fixCheckOverlap();}catch(_){}try{fixNewBadges();}catch(_){}try{fixBottomBar();}catch(_){}try{fixExcludedNames();}catch(_){}try{fixDuplicateNameDisplay();}catch(_){}try{fixGlobalCompactName();}catch(_){}try{ensureQuickRosterGridStyle();}catch(_){}}
function boot(){var tries=0;(function retry(){tries++;maintain();if(tries<150)setTimeout(retry,100);})();var r=root();if(r&&!r.__jmV2081Obs){var q=false;r.__jmV2081Obs=new MutationObserver(function(){if(q)return;q=true;setTimeout(function(){q=false;maintain();},50);});r.__jmV2081Obs.observe(r,{childList:true,subtree:true,attributes:true,attributeFilter:['class','style']});}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
