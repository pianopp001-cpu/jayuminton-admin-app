(function installJayumintonAdminV2074(){
'use strict';
if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
if(window.__JAYUMINTON_ADMIN_V2074__)return;
window.__JAYUMINTON_ADMIN_V2074__=true;

function root(){return document.getElementById('adminApp');}
function toolbar(){return document.getElementById('jmUnlimitedToolbar');}
function updateToolbar(){
  var bar=toolbar(); if(!bar)return false;
  var title=bar.querySelector('.jm-u-head strong'); if(title)title.textContent='멤버 팀, 교환, 메세지';
  var statusButton=bar.querySelector('[data-a="status"]'); if(statusButton)statusButton.remove();
  var statusSelect=bar.querySelector('#jmUnlimitedStatus'); if(statusSelect)statusSelect.remove();
  return true;
}
function cardForCheck(check){return check&&check.closest('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member],.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player');}
function syncSelectionVisual(){
  var r=root();if(!r)return;
  Array.prototype.forEach.call(r.querySelectorAll('.jm-v2074-selected'),function(c){c.classList.remove('jm-v2074-selected');});
  Array.prototype.forEach.call(r.querySelectorAll('.jm-unlimited-check'),function(check){var card=cardForCheck(check);if(card)card.classList.add('jm-v2074-selected');});
}
function wait4Container(){
  var r=root();if(!r)return null;
  var nodes=r.querySelectorAll('section,div,.card');
  for(var i=0;i<nodes.length;i++){
    var n=nodes[i],txt=String(n.textContent||'').replace(/\s+/g,' ').trim();
    if(!/(^|\s)대기\s*4(\s|$)/.test(txt))continue;
    var childHeaders=n.querySelectorAll('h1,h2,h3,h4,strong,.title,.wait-title');
    var own=false;
    for(var j=0;j<childHeaders.length;j++){if(/^대기\s*4\b/.test(String(childHeaders[j].textContent||'').trim())){own=true;break;}}
    if(own)return n;
  }
  return null;
}
function normalizeWait4SecondSlot(){
  var box=wait4Container();if(!box)return false;
  var empties=box.querySelectorAll('.empty,.quick-empty-slot,[class*="empty"]');
  var slot=null;
  if(empties.length>=2)slot=empties[1];
  if(!slot){
    var all=box.querySelectorAll('button,[onclick],.member,.person,.quick-member,.member-card,.member-item,.wait-card,.wait-item');
    var emptyList=[];Array.prototype.forEach.call(all,function(el){if(/비어\s*있음/.test(String(el.textContent||'')))emptyList.push(el);});
    if(emptyList.length>=2)slot=emptyList[1];
  }
  if(!slot)return false;
  slot.disabled=false;
  slot.removeAttribute('disabled');slot.removeAttribute('aria-disabled');slot.removeAttribute('inert');
  slot.classList.remove('disabled','is-disabled','inactive','non-clickable');
  slot.style.setProperty('pointer-events','auto','important');slot.style.setProperty('opacity','1','important');slot.style.setProperty('cursor','pointer','important');
  var raw=String(slot.getAttribute('onclick')||'');
  if(!raw||!/handleEmptySlotTap|handleMemberWaitEmptyTap/.test(raw))slot.setAttribute('onclick',"handleEmptySlotTap('wait','3',1)");
  slot.setAttribute('data-jm-wait4-second-fixed','1');
  return true;
}
function installClickFallback(){
  var r=root();if(!r||r.__jmWait4ClickV2074)return;r.__jmWait4ClickV2074=true;
  r.addEventListener('click',function(e){
    var slot=e.target&&e.target.closest&&e.target.closest('[data-jm-wait4-second-fixed="1"]');if(!slot)return;
    if(typeof window.handleEmptySlotTap==='function'){
      e.preventDefault();e.stopImmediatePropagation();
      try{window.handleEmptySlotTap('wait','3',1);}catch(err){console.error(err);}
    }
  },true);
}
function installStyle(){
  if(document.getElementById('jmAdminV2074Style'))return;
  var s=document.createElement('style');s.id='jmAdminV2074Style';
  s.textContent=''
    +'#adminApp .jm-unlimited-check{display:none!important}'
    +'#adminApp .jm-v2074-selected{outline:3px solid #16a34a!important;outline-offset:2px!important;filter:brightness(.97)!important}'
    +'#adminApp [data-jm-wait4-second-fixed="1"]{pointer-events:auto!important;opacity:1!important;cursor:pointer!important}'
    +'#jmUnlimitedToolbar [data-a="status"],#jmUnlimitedToolbar #jmUnlimitedStatus{display:none!important}';
  (document.head||document.documentElement).appendChild(s);
}
function maintain(){updateToolbar();normalizeWait4SecondSlot();syncSelectionVisual();}
function boot(){
  installStyle();installClickFallback();
  var tries=0;(function retry(){tries++;maintain();if(tries<80)setTimeout(retry,100);})();
  var r=root();if(r&&!r.__jmV2074Observer){var queued=false;r.__jmV2074Observer=new MutationObserver(function(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;maintain();});});r.__jmV2074Observer.observe(r,{childList:true,subtree:true,attributes:true,attributeFilter:['class','disabled','aria-disabled','onclick']});}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
