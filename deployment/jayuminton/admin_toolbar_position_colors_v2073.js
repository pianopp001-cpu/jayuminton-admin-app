(function installJayumintonAdminToolbarV2073(){
'use strict';
if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
if(window.__JAYUMINTON_ADMIN_TOOLBAR_V2073__)return;
window.__JAYUMINTON_ADMIN_TOOLBAR_V2073__=true;

function root(){return document.getElementById('adminApp');}
function selectedIds(){
  try{
    var checks=document.querySelectorAll('#adminApp .jm-unlimited-check');
    var ids=[];
    Array.prototype.forEach.call(checks,function(check){
      var card=check.closest('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member],.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player');
      if(!card)return;
      var attrs=['data-member-id','data-memberid','data-player-id','data-id','data-member'],id='';
      for(var i=0;i<attrs.length;i++){id=String(card.getAttribute&&card.getAttribute(attrs[i])||'');if(id)break;}
      if(!id&&card.querySelector){var n=card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');if(n){for(var j=0;j<attrs.length;j++){id=String(n.getAttribute(attrs[j])||'');if(id)break;}}}
      if(id&&ids.indexOf(id)<0)ids.push(id);
    });
    return ids;
  }catch(_){return [];}
}
function toast(text,bad){
  var old=document.getElementById('jmV2073Toast');if(old)old.remove();
  var n=document.createElement('div');n.id='jmV2073Toast';n.textContent=String(text||'');
  n.style.cssText='position:fixed;left:50%;top:max(10px,env(safe-area-inset-top));transform:translateX(-50%);z-index:2147483647;padding:9px 13px;border-radius:11px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:13px;font-weight:900;box-shadow:0 8px 24px rgba(0,0,0,.25)';
  document.body.appendChild(n);setTimeout(function(){n.remove();},1900);
}
function syncLegacySelected(ids){
  try{
    if(typeof SELECTED!=='undefined'&&SELECTED&&typeof SELECTED.clear==='function'&&typeof SELECTED.add==='function'){
      SELECTED.clear();ids.forEach(function(id){SELECTED.add(String(id));});
    }
  }catch(_){}
}
function messageSelected(){
  var ids=selectedIds();
  if(!ids.length){toast('멤버를 먼저 선택하세요.',true);return;}
  syncLegacySelected(ids);
  try{
    if(typeof window.openQuickMemberMessage==='function'){window.openQuickMemberMessage();return;}
  }catch(_){}
  var text=window.prompt('선택한 '+ids.length+'명에게 보낼 메시지를 입력하세요.','');
  if(!text)return;
  if(typeof window.server!=='function'){toast('메시지 기능을 찾을 수 없습니다.',true);return;}
  window.server('sendMemberMessage',[null,ids,String(text)]).then(function(){toast(ids.length+'명에게 메시지 전송 완료');}).catch(function(e){toast(String(e&&e.message||e||'메시지 전송 실패'),true);});
}
function quickCard(){
  var quick=document.getElementById('quickSelectedCount');
  if(quick){var card=quick.closest('.card');if(card)return card;}
  var r=root();if(!r)return null;
  var heads=r.querySelectorAll('h1,h2,h3,strong');
  for(var i=0;i<heads.length;i++)if(String(heads[i].textContent||'').indexOf('빠른 코트배정')>=0)return heads[i].closest('.card')||heads[i].parentElement;
  return null;
}
function quickHeader(card){
  if(!card)return null;
  return card.querySelector('.quick-roster-header')||Array.prototype.find.call(card.children,function(el){return /빠른 코트배정/.test(String(el.textContent||''));})||card.firstElementChild;
}
function ensureMessageButton(bar){
  var grid=bar&&bar.querySelector('.jm-u-grid');if(!grid)return;
  if(!grid.querySelector('[data-a="message"]')){
    var button=document.createElement('button');button.type='button';button.setAttribute('data-a','message');button.textContent='메시지보내기';
    var clear=grid.querySelector('[data-a="clear"]');if(clear)grid.insertBefore(button,clear);else grid.appendChild(button);
    button.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();messageSelected();},true);
  }
  var del=grid.querySelector('[data-a="delete"]');if(del){del.classList.add('jm-u-delete');}
}
function moveToolbar(){
  var bar=document.getElementById('jmUnlimitedToolbar');if(!bar)return false;
  ensureMessageButton(bar);
  var card=quickCard(),head=quickHeader(card);if(!card)return false;
  if(head&&head.parentNode===card){
    if(head.nextSibling!==bar)card.insertBefore(bar,head.nextSibling);
  }else if(bar.parentNode!==card){card.insertBefore(bar,card.firstChild);}
  bar.classList.add('jm-toolbar-under-quick-title');
  return true;
}
function installStyle(){
  if(document.getElementById('jmToolbarV2073Style'))return;
  var s=document.createElement('style');s.id='jmToolbarV2073Style';
  s.textContent=''
    +'#jmUnlimitedToolbar.jm-toolbar-under-quick-title{margin:7px 0 10px!important;padding:9px!important;border:1px solid #dbe4f0!important;border-radius:12px!important;background:#f8fafc!important;box-shadow:none!important}'
    +'#jmUnlimitedToolbar .jm-u-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:5px!important}'
    +'#jmUnlimitedToolbar .jm-u-grid button,#jmUnlimitedToolbar .jm-u-grid select{min-width:0!important;min-height:38px!important;padding:5px 3px!important;border-radius:9px!important;font-size:10px!important;font-weight:900!important;line-height:1.1!important;white-space:normal!important}'
    +'#jmUnlimitedToolbar [data-a="all"]{background:#334155!important;border-color:#334155!important;color:#fff!important}'
    +'#jmUnlimitedToolbar [data-a="active"]{background:#2563eb!important;border-color:#2563eb!important;color:#fff!important}'
    +'#jmUnlimitedToolbar [data-a="perm"]{background:#7c3aed!important;border-color:#7c3aed!important;color:#fff!important}'
    +'#jmUnlimitedToolbar [data-a="perm-clear"]{background:#ede9fe!important;border-color:#a78bfa!important;color:#5b21b6!important}'
    +'#jmUnlimitedToolbar [data-a="temp"]{background:#d4a017!important;border-color:#b98a10!important;color:#fff!important}'
    +'#jmUnlimitedToolbar [data-a="temp-clear"]{background:#fff7d6!important;border-color:#d4a017!important;color:#7a5a00!important}'
    +'#jmUnlimitedToolbar [data-a="move"]{background:#059669!important;border-color:#059669!important;color:#fff!important}'
    +'#jmUnlimitedToolbar [data-a="swap"]{background:#ea580c!important;border-color:#ea580c!important;color:#fff!important}'
    +'#jmUnlimitedToolbar [data-a="message"]{background:#0891b2!important;border-color:#0891b2!important;color:#fff!important}'
    +'#jmUnlimitedToolbar [data-a="clear"]{background:#e2e8f0!important;border-color:#cbd5e1!important;color:#334155!important}'
    +'#jmUnlimitedToolbar [data-a="status"],#jmUnlimitedToolbar #jmUnlimitedStatus{background:#e0f2fe!important;border-color:#7dd3fc!important;color:#075985!important}'
    +'#jmUnlimitedToolbar [data-a="delete"]{background:#b91c1c!important;border-color:#b91c1c!important;color:#fff!important}'
    +'@media(max-width:620px){#jmUnlimitedToolbar .jm-u-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}}';
  (document.head||document.documentElement).appendChild(s);
}
function boot(){
  installStyle();
  var tries=0;function place(){tries++;if(moveToolbar())return;if(tries<80)setTimeout(place,100);}place();
  var r=root();if(r&&!r.__jmToolbarV2073Observer){var queued=false;r.__jmToolbarV2073Observer=new MutationObserver(function(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;moveToolbar();});});r.__jmToolbarV2073Observer.observe(r,{childList:true,subtree:true});}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
