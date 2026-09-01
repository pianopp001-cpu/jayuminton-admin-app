(function installAdminTempTeamVisualV2048(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_TEMP_TEAM_VISUAL_V2048__)return;
  window.__JAYUMINTON_ADMIN_TEMP_TEAM_VISUAL_V2048__=true;
  var id='jayuminton-admin-temp-team-visual-v2048-style';
  function style(){
    var s=document.getElementById(id);
    if(!s){s=document.createElement('style');s.id=id;(document.head||document.documentElement).appendChild(s);}
    s.textContent=''
      +'#adminApp .jm-temp-team-v2047,'
      +'#adminApp .jm-temp-team-v2047.jm-temp-pair,'
      +'#adminApp .has-member-team.jm-temp-team-v2047,'
      +'#adminApp .has-member-team.jm-temp-team-v2047.jm-temp-pair{'
      +'box-shadow:0 0 0 4px #d4a017!important;'
      +'outline:2px solid rgba(212,160,23,.28)!important;outline-offset:1px!important}'
      +'#adminApp .jm-source-selected:not(.jm-temp-team-v2047),#adminApp .jm-target-selected:not(.jm-temp-team-v2047){box-shadow:0 0 0 4px #16a34a!important}'
      +'#adminApp .jm-temp-pair-pending{outline:none!important}'
      +'#adminApp .jm-temp-team-v2047 .member-team-badge{display:none!important}';
  }
  function scrub(){
    style();
    var app=document.getElementById('adminApp');if(!app)return;
    app.querySelectorAll('.jm-temp-team-v2047').forEach(function(card){card.style.removeProperty('--jm-temp-pair-color');});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scrub,{once:true});else scrub();
  var pending=false;
  new MutationObserver(function(){if(pending)return;pending=true;(window.requestAnimationFrame||setTimeout)(function(){pending=false;scrub();},16);}).observe(document.documentElement,{childList:true,subtree:true});
})();

(function installAdminMemberReplyInboxV1(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_MEMBER_REPLY_INBOX_V1__)return;
  window.__JAYUMINTON_ADMIN_MEMBER_REPLY_INBOX_V1__=true;
  var SEEN_KEY='jayuminton_admin_seen_member_replies_v1';
  var latestState=null, polling=false, firstPoll=true;

  function isAdmin(){try{return typeof IS_ADMIN!=='undefined'&&!!IS_ADMIN;}catch(_){return false;}}
  function readSeen(){try{var v=JSON.parse(localStorage.getItem(SEEN_KEY)||'[]');return Array.isArray(v)?v.map(String):[];}catch(_){return [];}}
  function writeSeen(ids){try{localStorage.setItem(SEEN_KEY,JSON.stringify(ids.slice(-300)));}catch(_){}}
  function escapeHtml(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function timeText(v){if(!v)return '';try{var d=new Date(v);if(!isFinite(d.getTime()))return '';return d.toLocaleString('ko-KR',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});}catch(_){return '';}}
  function flatten(state){
    var names={};(Array.isArray(state&&state.members)?state.members:[]).forEach(function(m){if(m&&m.id!=null)names[String(m.id)]=String(m.name||'');});
    var out=[];(Array.isArray(state&&state.memberMessages)?state.memberMessages:[]).forEach(function(msg){
      (Array.isArray(msg&&msg.replies)?msg.replies:[]).forEach(function(r){
        if(!r||!r.id)return;var memberId=String(r.memberId||'');
        out.push({id:String(r.id),memberId:memberId,memberName:names[memberId]||'회원',text:String(r.text||''),createdAt:String(r.createdAt||''),original:String(msg.text||''),messageId:String(msg.id||'')});
      });
    });
    out.sort(function(a,b){return String(b.createdAt).localeCompare(String(a.createdAt));});return out.slice(0,40);
  }
  function ensureStyle(){
    if(document.getElementById('jm-admin-reply-inbox-style'))return;
    var s=document.createElement('style');s.id='jm-admin-reply-inbox-style';
    s.textContent='.jm-reply-inbox-btn{position:fixed;right:12px;top:72px;z-index:2147483643;border:0;border-radius:999px;background:#1d4ed8;color:#fff;padding:9px 12px;font-weight:900;font-size:13px;box-shadow:0 5px 18px rgba(15,23,42,.24)}.jm-reply-inbox-btn[data-unread="0"]{background:#475569}.jm-reply-mask{position:fixed;inset:0;z-index:2147483646;background:rgba(15,23,42,.46);display:flex;align-items:center;justify-content:center;padding:14px}.jm-reply-panel{width:min(520px,100%);max-height:78vh;background:#fff;border-radius:18px;box-shadow:0 20px 65px rgba(0,0,0,.3);display:flex;flex-direction:column;overflow:hidden}.jm-reply-head{display:flex;align-items:center;justify-content:space-between;padding:14px 15px;border-bottom:1px solid #e2e8f0}.jm-reply-title{font-size:17px;font-weight:950}.jm-reply-close{border:0;background:#f1f5f9;border-radius:9px;padding:7px 10px;font-weight:800}.jm-reply-list{overflow:auto;padding:10px}.jm-reply-item{border:1px solid #e2e8f0;border-radius:13px;padding:10px;margin-bottom:8px;background:#fff}.jm-reply-item.unread{border-color:#2563eb;background:#eff6ff}.jm-reply-meta{font-size:13px;font-weight:900;color:#0f172a}.jm-reply-time{font-size:11px;color:#64748b;margin-left:6px}.jm-reply-original{font-size:12px;color:#64748b;margin-top:6px}.jm-reply-text{font-size:15px;font-weight:800;color:#111827;margin-top:5px;white-space:pre-wrap;word-break:break-word}.jm-reply-foot{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px 12px;border-top:1px solid #e2e8f0}.jm-reply-foot button{border:0;border-radius:10px;min-height:42px;font-weight:900}.jm-reply-mark{background:#2563eb;color:#fff}.jm-reply-dismiss{background:#e2e8f0;color:#334155}';
    (document.head||document.documentElement).appendChild(s);
  }
  function ensureButton(){
    ensureStyle();var b=document.getElementById('jmAdminReplyInboxButton');if(b)return b;
    b=document.createElement('button');b.type='button';b.id='jmAdminReplyInboxButton';b.className='jm-reply-inbox-btn';b.textContent='회원 답장';b.onclick=function(){openInbox(false);};document.body.appendChild(b);return b;
  }
  function renderButton(){
    if(!latestState)return;var seen=readSeen(),all=flatten(latestState),unread=all.filter(function(x){return seen.indexOf(x.id)<0;});var b=ensureButton();b.dataset.unread=String(unread.length);b.textContent=unread.length?'회원 답장 '+unread.length:'회원 답장';
  }
  function markVisibleSeen(items){var seen=readSeen();items.forEach(function(x){if(seen.indexOf(x.id)<0)seen.push(x.id);});writeSeen(seen);renderButton();}
  function closeInbox(){var m=document.getElementById('jmAdminReplyInboxMask');if(m)m.remove();}
  function openInbox(auto){
    if(!latestState)return;closeInbox();var seen=readSeen(),items=flatten(latestState),unread=items.filter(function(x){return seen.indexOf(x.id)<0;});
    if(auto&&!unread.length)return;
    var shown=auto?unread.slice(0,10):items.slice(0,20);var mask=document.createElement('div');mask.id='jmAdminReplyInboxMask';mask.className='jm-reply-mask';
    var rows=shown.length?shown.map(function(x){var isUnread=seen.indexOf(x.id)<0;return '<div class="jm-reply-item '+(isUnread?'unread':'')+'"><div class="jm-reply-meta">'+escapeHtml(x.memberName)+'<span class="jm-reply-time">'+escapeHtml(timeText(x.createdAt))+'</span></div><div class="jm-reply-original">보낸 메시지: '+escapeHtml(x.original)+'</div><div class="jm-reply-text">'+escapeHtml(x.text)+'</div></div>';}).join(''):'<div style="padding:28px;text-align:center;color:#64748b">받은 회원 답장이 없습니다.</div>';
    mask.innerHTML='<div class="jm-reply-panel"><div class="jm-reply-head"><div class="jm-reply-title">회원 답장'+(unread.length?' · 새 답장 '+unread.length:'')+'</div><button type="button" class="jm-reply-close">닫기</button></div><div class="jm-reply-list">'+rows+'</div><div class="jm-reply-foot"><button type="button" class="jm-reply-mark">표시된 답장 확인</button><button type="button" class="jm-reply-dismiss">닫기</button></div></div>';
    document.body.appendChild(mask);mask.querySelector('.jm-reply-close').onclick=closeInbox;mask.querySelector('.jm-reply-dismiss').onclick=closeInbox;mask.querySelector('.jm-reply-mark').onclick=function(){markVisibleSeen(shown);closeInbox();};mask.addEventListener('click',function(e){if(e.target===mask)closeInbox();});
  }
  async function poll(){
    if(polling||!isAdmin()||typeof window.server!=='function')return;polling=true;
    try{var state=await window.server('getPublicState',[null]);if(state&&state.members&&state.memberMessages){latestState=state;var before=document.getElementById('jmAdminReplyInboxMask');renderButton();var unseen=flatten(state).filter(function(x){return readSeen().indexOf(x.id)<0;});if(unseen.length&&!before&&!firstPoll)openInbox(true);firstPoll=false;}}
    catch(_){}finally{polling=false;}
  }
  function start(){if(!isAdmin())return;ensureButton();poll();setInterval(poll,3000);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
