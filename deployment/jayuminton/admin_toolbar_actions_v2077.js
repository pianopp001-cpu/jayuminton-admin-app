(function(){
'use strict';
if(typeof IS_ADMIN!=='undefined'&&!IS_ADMIN)return;
if(window.__JAYUMINTON_ADMIN_TOOLBAR_ACTIONS_V2077__)return;
window.__JAYUMINTON_ADMIN_TOOLBAR_ACTIONS_V2077__=true;
function root(){return document.getElementById('adminApp');}
function cardId(card){if(!card)return '';for(var a of ['data-member-id','data-memberid','data-player-id','data-id','data-member']){var id=String(card.getAttribute&&card.getAttribute(a)||'');if(id)return id;}var n=card.querySelector&&card.querySelector('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member]');return n?cardId(n):'';}
function selectedIds(){var ids=[];try{document.querySelectorAll('#adminApp .jm-unlimited-check').forEach(function(check){var card=check.closest('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member],.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player');var id=cardId(card);if(id&&ids.indexOf(id)<0)ids.push(id);});}catch(_){}return ids;}
function toast(text,bad){var old=document.getElementById('jmV2077Toast');if(old)old.remove();var n=document.createElement('div');n.id='jmV2077Toast';n.textContent=String(text||'');n.style.cssText='position:fixed;left:50%;top:max(10px,env(safe-area-inset-top));transform:translateX(-50%);z-index:2147483647;padding:8px 12px;border-radius:10px;background:'+(bad?'#991b1b':'#111827')+';color:#fff;font-size:12px;font-weight:900;box-shadow:0 6px 20px rgba(0,0,0,.22)';document.body.appendChild(n);setTimeout(function(){n.remove();},1700);}
async function setStatus(status,label){var ids=selectedIds();if(!ids.length)return toast('멤버를 먼저 선택하세요.',true);if(typeof window.server!=='function')return toast('서버 연결을 찾을 수 없습니다.',true);try{var r=await window.server('setMemberStatus',[null,ids,status]);var s=r&&r.state?r.state:r;if(s&&typeof renderState==='function')renderState(s);var clear=document.querySelector('#jmUnlimitedToolbar [data-a="clear"]');if(clear)clear.click();toast(ids.length+'명 '+label+' 처리 완료');}catch(e){toast(String(e&&e.message||e||label+' 실패'),true);}}
function ensureButton(grid,a,text,cls){var b=grid.querySelector('[data-a="'+a+'"]');if(!b){b=document.createElement('button');b.type='button';b.setAttribute('data-a',a);b.textContent=text;grid.appendChild(b);}else if(b.textContent!==text)b.textContent=text;if(cls&&!b.classList.contains(cls))b.classList.add(cls);return b;}
function bindStatusButton(b,status,label){if(!b||b.__jmV2077)return;b.__jmV2077=true;b.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();setStatus(status,label);},true);}
function arrange(){var bar=document.getElementById('jmUnlimitedToolbar');if(!bar)return false;var grid=bar.querySelector('.jm-u-grid');if(!grid)return false;var title=bar.querySelector('.jm-u-head strong');if(title&&title.textContent!=='멤버 팀, 교환, 메세지')title.textContent='멤버 팀, 교환, 메세지';var all=ensureButton(grid,'all','모두선택','jm-v2077-important');var before=ensureButton(grid,'before','도착전','jm-v2077-important');var away=ensureButton(grid,'away','귀가','jm-v2077-important');var del=ensureButton(grid,'delete','회원삭제','jm-v2077-important');var msg=ensureButton(grid,'message','메시지보내기','jm-v2077-important');var active=ensureButton(grid,'active','배정대기','jm-v2077-active');var perm=ensureButton(grid,'perm','영구팀설정');var pc=ensureButton(grid,'perm-clear','영구팀해제');var temp=ensureButton(grid,'temp','임시팀설정');var tc=ensureButton(grid,'temp-clear','임시팀해제');var clear=ensureButton(grid,'clear','선택해제');bindStatusButton(before,'before','도착전');bindStatusButton(away,'away','귀가');
  /* Sequential idempotent reorder -- same rationale as v2076's bottom():
     grid.appendChild(b) unconditionally moves b to the end even when it is
     already correctly placed, which fed this file's own MutationObserver
     (childList) on every single cycle for all 11 buttons. Only move a
     button if it isn't immediately after the previously-placed one (or
     isn't first). Reconstructs the exact same final order as the old
     unconditional loop, but is a true no-op once already arranged. */
  var __order=[all,before,away,del,msg,active,perm,pc,temp,tc,clear];
  var __prevBtn=null;
  __order.forEach(function(b){
    var expectedPrevSibling=__prevBtn?__prevBtn.nextElementSibling:grid.firstElementChild;
    if(b.parentNode!==grid||expectedPrevSibling!==b)grid.appendChild(b);
    __prevBtn=b;
  });
  Array.from(grid.children).forEach(function(el){if(el.tagName==='SELECT'||(el.getAttribute&&['status','move'].indexOf(el.getAttribute('data-a'))>=0))el.remove();});
  return true;
}
function style(){if(document.getElementById('jmToolbarV2077Style'))return;var s=document.createElement('style');s.id='jmToolbarV2077Style';s.textContent=''
+'#jmUnlimitedToolbar{padding:7px!important;margin:6px 0 8px!important}'
+'#jmUnlimitedToolbar .jm-u-head{margin-bottom:3px!important}'
+'#jmUnlimitedToolbar .jm-u-mode{font-size:10px!important;margin-bottom:5px!important}'
+'#jmUnlimitedToolbar .jm-u-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:4px!important}'
+'#jmUnlimitedToolbar .jm-u-grid button{min-height:31px!important;height:31px!important;padding:3px 2px!important;border-radius:7px!important;font-size:10px!important;font-weight:900!important;line-height:1.05!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}'
+'#jmUnlimitedToolbar [data-a="before"]{background:#0f766e!important;border-color:#0f766e!important;color:#fff!important}'
+'#jmUnlimitedToolbar [data-a="away"]{background:#475569!important;border-color:#475569!important;color:#fff!important}'
+'#jmUnlimitedToolbar [data-a="delete"]{background:#b91c1c!important;border-color:#b91c1c!important;color:#fff!important}'
+'#jmUnlimitedToolbar [data-a="message"]{background:#0891b2!important;border-color:#0891b2!important;color:#fff!important}'
+'#jmUnlimitedToolbar [data-a="active"]{background:#2563eb!important;border-color:#2563eb!important;color:#fff!important}'
+'#jmUnlimitedToolbar [data-a="all"]{background:#111827!important;border-color:#111827!important;color:#fff!important}'
+'#jmUnlimitedToolbar [data-a="perm"],#jmUnlimitedToolbar [data-a="perm-clear"],#jmUnlimitedToolbar [data-a="temp"],#jmUnlimitedToolbar [data-a="temp-clear"],#jmUnlimitedToolbar [data-a="clear"]{font-size:9.5px!important}'
+'@media(max-width:380px){#jmUnlimitedToolbar .jm-u-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}#jmUnlimitedToolbar .jm-u-grid button{font-size:9px!important}}';(document.head||document.documentElement).appendChild(s);}
function boot(){style();var tries=0;(function go(){tries++;arrange();if(tries<80)setTimeout(go,100);})();var r=root();if(r&&!r.__jmV2077Obs){var q=false;r.__jmV2077Obs=new MutationObserver(function(){if(q)return;q=true;requestAnimationFrame(function(){q=false;arrange();});});r.__jmV2077Obs.observe(r,{childList:true,subtree:true});}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else setTimeout(boot,0);
})();
