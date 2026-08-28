(function(){
'use strict';
if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
if(window.__JAYUMINTON_ADMIN_DEAD_UI_CLEANUP_V2080__)return;
window.__JAYUMINTON_ADMIN_DEAD_UI_CLEANUP_V2080__=true;
function root(){return document.getElementById('adminApp');}
function installStyle(){
if(document.getElementById('jmDeadUiCleanupV2080Style'))return;
var s=document.createElement('style');
s.id='jmDeadUiCleanupV2080Style';
/* Permanent CSS hide (not a per-tick JS toggle) so these can never flash
   visible for a moment between renders: the dead/duplicate selection
   counters left over from the pre-v2072 legacy toolbar, and the big
   "코트배정 대기로 복귀" button (replaced by the per-member long-press
   menu's "코트배정" action). Elements stay in the DOM so any legacy code
   that still reads/writes their textContent does not throw on a removed
   node; they are just never rendered. */
s.textContent='#quickSelectedCount,#mobileSelectedCount,#mdBulkDeleteCount,.admin-member-bulk-panel,.jm-v2080-return-btn{display:none!important}';
(document.head||document.documentElement).appendChild(s);
}
function tagReturnButton(){
var r=root();if(!r)return;
Array.from(r.querySelectorAll('button')).forEach(function(b){
if(String(b.textContent||'').replace(/\s+/g,'').indexOf('코트배정대기로복귀')>=0&&!b.closest('#jmUnlimitedToolbar')){
b.classList.add('jm-v2080-return-btn');
}
});
}
function maintain(){tagReturnButton();}
function boot(){
installStyle();
var tries=0;
(function retry(){tries++;maintain();if(tries<80)setTimeout(retry,100);})();
var r=root();
if(r&&!r.__jmDeadUiCleanupV2080Observer){
var q=false;
r.__jmDeadUiCleanupV2080Observer=new MutationObserver(function(){
if(q)return;q=true;
requestAnimationFrame(function(){q=false;maintain();});
});
r.__jmDeadUiCleanupV2080Observer.observe(r,{childList:true,subtree:true});
}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
else setTimeout(boot,0);
})();
