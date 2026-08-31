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
/* Spec: "함께 경기통계 누르면 아래에 떠있는 버튼들이... 번쩍번쩍
   깜빡여." maintain() (this function included) reruns on every debounced
   DOM mutation, and rendering the pair-statistics rows fires many
   mutations in a burst -- previously this function unconditionally wrote
   ~10 style properties AND read row.getBoundingClientRect() (which forces
   a synchronous layout) on every single one of those reruns, several
   times a frame during that burst. That read-after-write-after-read
   pattern is textbook layout thrashing; skip the positioning writes once
   they are already applied (checked via a marker attribute, since
   style.getPropertyValue on a shorthand-adjacent set of properties is not
   a reliable one-shot check) and only touch body's padding-bottom when
   the measured height actually changed, instead of on every call. */
function fixBottomBar(){var row=document.getElementById('jmBottomActionRowV2079');if(!row)return;if(row.getAttribute('data-jm-bottom-bar-fixed')!=='1'){row.style.setProperty('position','fixed','important');row.style.setProperty('left','0','important');row.style.setProperty('right','0','important');row.style.setProperty('bottom','0','important');row.style.setProperty('z-index','2147483000','important');row.style.setProperty('background','#fff','important');row.style.setProperty('box-shadow','0 -4px 14px rgba(0,0,0,.18)','important');row.style.setProperty('padding','6px 8px calc(6px + env(safe-area-inset-bottom))','important');row.style.setProperty('margin','0 auto','important');row.style.setProperty('max-width','640px','important');row.style.setProperty('box-sizing','border-box','important');row.setAttribute('data-jm-bottom-bar-fixed','1');}var h=row.getBoundingClientRect().height;if(h>0&&h!==window.__jmLastBottomBarHeight){window.__jmLastBottomBarHeight=h;document.body.style.setProperty('padding-bottom',(h+10)+'px','important');}}
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
/* markAdminNewCards() adds is-new-member to every genuinely new/duplicate
   member's card, and the base app's .quick-member.is-new-member{grid-
   column:1/-1!important} makes that ONE card span the entire row -- correct
   in the base app's original 2-column layout, but it collapses a 5-column
   grid down to one card per row for that member. Cancel it back to normal
   auto-placement so a new member's card fits the same 5-column grid as
   everyone else's, without touching is-new-member itself (still needed
   elsewhere, e.g. for badge styling). */
/* The base app ALREADY carries a hidden, higher-specificity cascade for
   this exact grid -- "#adminApp .v4-quick-roster ..." rules (1 ID + 2
   classes, e.g. #adminApp .v4-quick-roster .quick-member-name{white-
   space:nowrap!important;font-size:14px!important;...}) that a plain grep
   for ".v4-quick-roster{" never surfaces, because the class is not the
   selector's leftmost/only token. Those rules silently beat the previous
   version of this style block (#quickActiveRoster .quick-member-name, only
   1 ID + 1 class) on specificity, forcing white-space:nowrap and a fixed
   line-height back on regardless of what was written here -- confirmed by
   rendering the actual shipped HTML and reading getComputedStyle, which
   showed white-space:"nowrap" and a 230px scrollWidth clipped into a 34px
   card by the ancestor's overflow:hidden. Every selector below is
   therefore anchored to two IDs -- "#adminApp #quickActiveRoster..."
   (the container's own id plus its #adminApp ancestor) -- which always
   outranks a single-ID selector regardless of how many extra classes that
   selector adds. */
function ensureQuickRosterGridStyle(){if(document.getElementById('jmQuickRosterGridV1'))return;var style=document.createElement('style');style.id='jmQuickRosterGridV1';style.textContent='#adminApp #quickActiveRoster.v4-quick-roster{grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:4px!important;align-items:start!important}#adminApp #quickActiveRoster.v4-quick-roster .quick-member.is-new-member{grid-column:auto!important;width:auto!important}#adminApp #quickActiveRoster.v4-quick-roster .quick-member{padding:4px 3px!important;min-height:46px!important;height:auto!important;overflow:visible!important;gap:2px!important}#adminApp #quickActiveRoster.v4-quick-roster .quick-member-name{overflow:visible!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:keep-all!important;font-size:clamp(10.5px,2.9vw,13px)!important;line-height:1.2!important;height:auto!important;max-height:none!important}#adminApp #quickActiveRoster.v4-quick-roster .quick-member-games{font-size:7.5px!important;margin-top:-1px!important}#adminApp #quickActiveRoster.v4-quick-roster .member-info-detail{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:anywhere!important;word-break:keep-all!important;height:auto!important;font-size:7.5px!important;margin-top:1px!important}#adminApp #quickActiveRoster.v4-quick-roster .member-vnext-memo{font-size:7.5px!important;white-space:normal!important}#adminApp #quickActiveRoster.v4-quick-roster .member-vnext-badge.new-badge{position:static!important;display:inline-flex!important;width:auto!important;margin:1px auto 0!important;padding:1px 3px!important;font-size:7.5px!important;box-shadow:none!important}';(document.head||document.documentElement).appendChild(style);}
/* Spec: "대기의 카드안에서는 멤버의 이름이 잘려서 들어가고". Same
   specificity-archaeology shape as the quick-roster fix above: the base
   app's "#adminApp .v4-wait-card .person" carries a FIXED height (not
   min-height) plus overflow:hidden!important, and ".v4-wait-card .person
   .name" gets white-space:nowrap!important from a media-query variant at
   the same 1-ID+3-class specificity -- so even though fixGlobalCompactName
   already stopped shortening the name STRING, the full name still gets
   clipped by its own fixed-height, overflow-hidden container. Matching
   selector + later source order (this <style> is appended at runtime, so
   it always sorts after every rule already in the document) resolves the
   tie without needing to go to 2 IDs like quick-roster did. */
function ensureWaitCardNameStyle(){if(document.getElementById('jmWaitCardNameFixV1'))return;var style=document.createElement('style');style.id='jmWaitCardNameFixV1';style.textContent='#adminApp .v4-wait-card .person{height:auto!important;overflow:visible!important}#adminApp .v4-wait-card .person .name{white-space:normal!important;overflow:visible!important;overflow-wrap:anywhere!important;word-break:keep-all!important}';(document.head||document.documentElement).appendChild(style);}
/* Spec: "화면 스크롤만 해도 멤버카드를 길게 누르면 나오는... 버튼이 떠..
   너무너무 방해된다." startMemberLongPress()'s only cancel-guard is
   moveMemberLongPress(), which cancels the 600ms timer only once the
   pointer has moved more than 12px from its start position. Confirmed live
   (synthetic pointerdown + a scroll event with no matching pointermove):
   the timer fires and adds the long-pressed class regardless -- when a
   touch-drag-to-scroll gesture starts on a member card and the browser
   takes over the gesture for native scrolling, pointermove is not
   guaranteed to keep arriving with tracked deltas past that point, so the
   12px check alone is not a reliable cancel signal. A capture-phase
   scroll listener is reliable across ALL of this app's scrollable regions
   (the whole page, or an inner panel like #quickActiveRoster) even though
   scroll does not bubble -- capture fires while the event is still
   travelling down to its target, independent of the bubbles flag.
   Re-verified after adding this: the same synthetic scroll now correctly
   cancels the pending timer before it can fire. */
function installLongPressScrollCancel(){if(window.__jmLongPressScrollCancelV1)return;window.__jmLongPressScrollCancelV1=true;window.addEventListener('scroll',function(){if(typeof window.finishMemberLongPress==='function')window.finishMemberLongPress();},true);}
function maintain(){try{fixCheckOverlap();}catch(_){}try{fixNewBadges();}catch(_){}try{fixBottomBar();}catch(_){}try{fixExcludedNames();}catch(_){}try{fixDuplicateNameDisplay();}catch(_){}try{fixGlobalCompactName();}catch(_){}try{ensureQuickRosterGridStyle();}catch(_){}try{ensureWaitCardNameStyle();}catch(_){}try{installLongPressScrollCancel();}catch(_){}}
function boot(){var tries=0;(function retry(){tries++;maintain();if(tries<150)setTimeout(retry,100);})();var r=root();if(r&&!r.__jmV2081Obs){var q=false;r.__jmV2081Obs=new MutationObserver(function(){if(q)return;q=true;setTimeout(function(){q=false;maintain();},50);});r.__jmV2081Obs.observe(r,{childList:true,subtree:true,attributes:true,attributeFilter:['class','style']});}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
