from pathlib import Path

HTML = Path('app/src/main/assets/admin/index.html')
s = HTML.read_text(encoding='utf-8')
login_marker = '__JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050__'
reply_marker = '__JAYUMINTON_ADMIN_MEMBER_REPLIES_V1__'
changed = False

# JAYUMINTON_ADMIN_RPC_FETCH_TIMEOUT_V1: the original directServer() below had
# no timeout on its fetch() call. On a real device, a flaky WiFi/LTE hop, the
# WebView being backgrounded mid-request, or a slow Cloudflare Worker cold
# start can leave that fetch's promise pending forever -- it never resolves
# AND never rejects. Every button that awaits window.server(...) (새로고침,
# 실행취소-enabling actions, 자동배정, ...) then stays stuck disabled/"갱신
# 중..." permanently, with no error shown and no way to recover short of
# force-closing the app, because nothing ever calls its .then()/.catch().
# This is exactly the "실행취소/새로고침 버튼이 아예 안 먹힌다" bug reported
# in production. login_marker is already baked into the live BASE apk from
# a much earlier build (this script's own block was never re-run since), so
# a plain `if login_marker not in s` guard would make this fix a permanent
# no-op against that already-baked HTML -- same trap documented in
# patch_member_pair_play_v1.py. login_new_marker distinguishes "the timeout
# fix is already live" from "some version of this login script is already
# live", so an updated script body always forces a real re-application: the
# stale pre-timeout block is stripped and rebuilt from scratch.
login_new_marker = '__JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050_FETCH_TIMEOUT_V1__'


def _strip_marked_script_block(source, marker_comment):
    pos = source.find(marker_comment)
    if pos < 0:
        return source
    start = source.rfind('<script', 0, pos)
    end = source.find('</script>', pos)
    if start < 0 or end < 0:
        raise SystemExit('stale login script block boundary missing for ' + marker_comment)
    end += len('</script>')
    return source[:start] + source[end:]


if login_new_marker not in s:
    # No-op (find() returns -1 inside the helper) the first time this ever
    # runs against a page that never had the v2050 login script at all.
    s = _strip_marked_script_block(s, '/* ' + login_marker + ' */')
    changed = True
    script = r'''
<script>
/* __JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050__ __JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050_FETCH_TIMEOUT_V1__ */
(function(){
  'use strict';
  var ENDPOINT='https://jayuminton-state.pianopp001.workers.dev/api/compat/rpc';
  var ADMIN_KEY='jayuminton_admin_session_v1';
  var RPC_TIMEOUT_MS=20000;

  function token(){
    try{return String(localStorage.getItem(ADMIN_KEY)||'');}catch(_){return '';}
  }
  function directServer(name,args){
    var values=Array.isArray(args)?args:[];
    var t=(name==='createAdminSession'||name==='verifyMemberPassword'||name==='getMemberPasswordVersion')?'':token();
    /* jmAdminRpcFetchTimeoutV1: a hung mobile-network request left this
       fetch() pending forever -- it never resolved and never rejected -- so
       every button awaiting window.server(...) (새로고침, 자동배정, and any
       action that only re-enables 실행취소 on success) stayed stuck disabled
       with no error and no recovery. Force a rejection after RPC_TIMEOUT_MS
       so callers' .catch()/try-catch always eventually run. */
    var controller=(typeof AbortController!=='undefined')?new AbortController():null;
    var timedOut=false;
    var timer=controller?setTimeout(function(){timedOut=true;try{controller.abort();}catch(_){}},RPC_TIMEOUT_MS):null;
    return fetch(ENDPOINT,{
      method:'POST',cache:'no-store',credentials:'omit',
      headers:Object.assign({'content-type':'application/json'},t?{'authorization':'Bearer '+t}:{}),
      body:JSON.stringify({name:String(name||''),args:values}),
      signal:controller?controller.signal:undefined
    }).then(function(r){
      if(timer)clearTimeout(timer);
      return r.text().then(function(text){
        var packet;try{packet=JSON.parse(text);}catch(_){throw new Error('서버 응답 오류 ('+r.status+')');}
        if(!r.ok||!packet||packet.ok!==true)throw new Error(String(packet&&packet.error||('서버 요청 실패 ('+r.status+')')));
        return packet.result;
      });
    }).catch(function(error){
      if(timer)clearTimeout(timer);
      if(timedOut||(error&&error.name==='AbortError'))throw new Error('서버 응답이 없습니다. 네트워크 상태를 확인하고 다시 시도해주세요.');
      throw error;
    });
  }

  window.server=directServer;

  async function refreshCurrentMemberPassword(){
    var app=document.getElementById('adminApp');if(!app||app.style.display==='none')return;
    var value=document.getElementById('currentMemberPassword');
    if(!value)return;
    try{var pw=await directServer('getCurrentMemberPassword',[null]);if(value)value.textContent=String(pw||'(설정 안 됨)');}
    catch(e){if(value)value.textContent='불러오기 실패';}
  }
  window.__JM_REFRESH_CURRENT_MEMBER_PASSWORD__=refreshCurrentMemberPassword;

  window.adminLogin=async function(){
    var input=document.getElementById('adminPinInput');
    var button=document.querySelector('#adminLoginBox button.primary');
    var pin=String(input&&input.value||'').trim();
    if(!pin){alert('관리자 PIN을 입력하세요.');if(input)input.focus();return;}
    if(button){button.disabled=true;button.textContent='로그인 중…';}
    try{
      try{localStorage.removeItem(ADMIN_KEY);}catch(_){}
      var result=await directServer('createAdminSession',[pin]);
      if(!result||result.ok!==true||!result.token)throw new Error('관리자 PIN이 틀렸습니다.');
      try{localStorage.setItem(ADMIN_KEY,String(result.token));}catch(_){}
      if(typeof openAdminApp!=='function')throw new Error('관리자 화면 함수를 찾을 수 없습니다.');
      await openAdminApp(String(result.token));
      setTimeout(refreshCurrentMemberPassword,50);
    }catch(error){
      try{localStorage.removeItem(ADMIN_KEY);}catch(_){}
      alert(String(error&&error.message||error||'로그인에 실패했습니다.'));
      if(input)input.focus();
    }finally{
      if(button){button.disabled=false;button.textContent='로그인';}
    }
  };

  var input=document.getElementById('adminPinInput');
  if(input&&!input.__jmDirectEnter){
    input.__jmDirectEnter=true;
    input.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();window.adminLogin();}});
  }
  document.addEventListener('click',function(e){
    var t=e.target&&e.target.closest&&e.target.closest('button');if(!t)return;
    if(/비밀번호.*변경|변경.*비밀번호/.test(String(t.textContent||'')))setTimeout(refreshCurrentMemberPassword,700);
  },true);
  window.__JAYUMINTON_ADMIN_SINGLE_MEMBER_PASSWORD_V2064__=true;
  window.__JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050__=true;
  window.__JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050_FETCH_TIMEOUT_V1__=true;
})();
</script>
'''
    anchor='</body>'
    if anchor not in s:
        raise SystemExit('body closing tag not found')
    s=s.replace(anchor,script+'\n'+anchor,1)
    changed=True

if reply_marker not in s:
    reply_ui = r'''
<style id="jayuminton-admin-member-replies-v1-style">
#jmAdminReplyButton{position:fixed;right:8px;top:70px;z-index:2147483638;border:1px solid #cbd5e1;border-radius:999px;background:#fff;color:#0f172a;min-height:34px;padding:0 10px;font:800 12px/1.1 inherit;box-shadow:0 5px 18px rgba(15,23,42,.14);display:none;align-items:center;gap:5px}
#jmAdminReplyButton .jm-reply-count{display:none;min-width:18px;height:18px;border-radius:999px;background:#dc2626;color:#fff;align-items:center;justify-content:center;font-size:10px;padding:0 4px;box-sizing:border-box}
#jmAdminReplyShade{position:fixed;inset:0;z-index:2147483644;background:rgba(15,23,42,.40);display:none;align-items:flex-end;justify-content:center;padding:10px;box-sizing:border-box}
#jmAdminReplyPanel{width:min(560px,100%);max-height:min(76vh,720px);overflow:hidden;background:#fff;border-radius:18px;box-shadow:0 18px 60px rgba(15,23,42,.30);display:flex;flex-direction:column}
.jm-admin-reply-head{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 14px;border-bottom:1px solid #e2e8f0}.jm-admin-reply-head strong{font-size:16px}.jm-admin-reply-close{border:0;background:#f1f5f9;border-radius:9px;padding:7px 10px;font-weight:800}
#jmAdminReplyList{padding:10px;overflow:auto;display:flex;flex-direction:column;gap:8px}.jm-admin-reply-empty{padding:26px 10px;text-align:center;color:#64748b;font-size:13px}.jm-admin-reply-card{border:1px solid #e2e8f0;border-radius:13px;padding:10px;background:#fff}.jm-admin-reply-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px}.jm-admin-reply-name{font-size:14px;font-weight:900;color:#111827}.jm-admin-reply-time{font-size:10px;color:#64748b;white-space:nowrap}.jm-admin-reply-line{font-size:12px;line-height:1.45;color:#475569;margin-top:4px;word-break:break-word}.jm-admin-reply-line b{color:#0f172a}.jm-admin-reply-text{margin-top:6px;padding:8px 9px;border-radius:9px;background:#eff6ff;color:#1e3a8a;font-size:13px;font-weight:750;line-height:1.45;word-break:break-word}
#jmAdminReplyPopup{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:2147483647;width:min(420px,calc(100vw - 24px));display:none;background:#fff;border-radius:17px;padding:14px;box-shadow:0 20px 70px rgba(15,23,42,.36);border:1px solid #dbeafe}.jm-admin-reply-popup-title{font-size:15px;font-weight:950;margin-bottom:8px}.jm-admin-reply-popup-meta{font-size:12px;font-weight:800;color:#334155;margin-bottom:6px}.jm-admin-reply-popup-original{font-size:12px;color:#64748b;line-height:1.4;margin-bottom:7px;word-break:break-word}.jm-admin-reply-popup-text{font-size:14px;line-height:1.45;font-weight:850;color:#0f172a;background:#eff6ff;border-radius:10px;padding:9px;word-break:break-word}.jm-admin-reply-popup-ok{width:100%;margin-top:10px;min-height:38px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:900}
</style>
<script id="jayuminton-admin-member-replies-v1">
/* __JAYUMINTON_ADMIN_MEMBER_REPLIES_V1__ */
(function(){
  'use strict';
  if(window.__JAYUMINTON_ADMIN_MEMBER_REPLIES_V1__)return;
  window.__JAYUMINTON_ADMIN_MEMBER_REPLIES_V1__=true;
  var SEEN_KEY='jayuminton_admin_seen_member_replies_v1';
  var popupId='';

  function state(){try{return typeof STATE!=='undefined'?STATE:null;}catch(_){return null;}}
  function seen(){try{var v=JSON.parse(localStorage.getItem(SEEN_KEY)||'[]');return Array.isArray(v)?v.map(String):[];}catch(_){return [];}}
  function saveSeen(ids){try{localStorage.setItem(SEEN_KEY,JSON.stringify(ids.slice(-250)));}catch(_){}}
  function esc(value){return String(value==null?'':value).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function timeText(value){var d=new Date(value||0);if(!Number.isFinite(d.getTime()))return '';try{return d.toLocaleString('ko-KR',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});}catch(_){return '';}}
  function flatten(){
    var st=state();if(!st||!Array.isArray(st.memberMessages))return [];
    var names={};(Array.isArray(st.members)?st.members:[]).forEach(function(m){names[String(m&&m.id||'')]=String(m&&m.name||'회원');});
    var out=[];
    st.memberMessages.forEach(function(message){
      (Array.isArray(message&&message.replies)?message.replies:[]).forEach(function(reply){
        if(!reply||!reply.id)return;
        out.push({id:String(reply.id),memberId:String(reply.memberId||''),memberName:names[String(reply.memberId||'')]||'회원',original:String(message.text||''),text:String(reply.text||''),createdAt:String(reply.createdAt||''),messageId:String(message.id||'')});
      });
    });
    out.sort(function(a,b){return new Date(a.createdAt||0).getTime()-new Date(b.createdAt||0).getTime();});
    return out;
  }
  function ensure(){
    if(!document.getElementById('jmAdminReplyButton')){
      var b=document.createElement('button');b.type='button';b.id='jmAdminReplyButton';b.innerHTML='회원 답장 <span class="jm-reply-count"></span>';b.onclick=openPanel;document.body.appendChild(b);
    }
    if(!document.getElementById('jmAdminReplyShade')){
      var shade=document.createElement('div');shade.id='jmAdminReplyShade';shade.innerHTML='<div id="jmAdminReplyPanel"><div class="jm-admin-reply-head"><strong>회원 답장</strong><button type="button" class="jm-admin-reply-close">닫기</button></div><div id="jmAdminReplyList"></div></div>';document.body.appendChild(shade);
      shade.querySelector('.jm-admin-reply-close').onclick=closePanel;shade.addEventListener('click',function(e){if(e.target===shade)closePanel();});
    }
    if(!document.getElementById('jmAdminReplyPopup')){
      var p=document.createElement('div');p.id='jmAdminReplyPopup';p.innerHTML='<div class="jm-admin-reply-popup-title">회원 답장 도착</div><div class="jm-admin-reply-popup-meta"></div><div class="jm-admin-reply-popup-original"></div><div class="jm-admin-reply-popup-text"></div><button type="button" class="jm-admin-reply-popup-ok">확인</button>';document.body.appendChild(p);p.querySelector('.jm-admin-reply-popup-ok').onclick=confirmPopup;
    }
  }
  function isAdminVisible(){var app=document.getElementById('adminApp');return !!(app&&app.style.display!=='none');}
  function renderButton(){
    ensure();var all=flatten(),set=new Set(seen()),unseen=all.filter(function(x){return !set.has(x.id);});var b=document.getElementById('jmAdminReplyButton');
    b.style.display=isAdminVisible()?'inline-flex':'none';var c=b.querySelector('.jm-reply-count');if(unseen.length){c.style.display='inline-flex';c.textContent=String(Math.min(99,unseen.length));}else{c.style.display='none';c.textContent='';}
    return unseen;
  }
  function renderList(){
    var list=document.getElementById('jmAdminReplyList'),all=flatten().slice(-30).reverse();if(!list)return;
    if(!all.length){list.innerHTML='<div class="jm-admin-reply-empty">아직 받은 답장이 없습니다.</div>';return;}
    list.innerHTML=all.map(function(x){return '<div class="jm-admin-reply-card"><div class="jm-admin-reply-meta"><span class="jm-admin-reply-name">'+esc(x.memberName)+'</span><span class="jm-admin-reply-time">'+esc(timeText(x.createdAt))+'</span></div><div class="jm-admin-reply-line"><b>관리자 원문</b> · '+esc(x.original)+'</div><div class="jm-admin-reply-text"><b>답장</b> · '+esc(x.text)+'</div></div>';}).join('');
  }
  function openPanel(){ensure();renderList();document.getElementById('jmAdminReplyShade').style.display='flex';var ids=flatten().map(function(x){return x.id;});saveSeen(Array.from(new Set(seen().concat(ids))));renderButton();hidePopup();}
  function closePanel(){var e=document.getElementById('jmAdminReplyShade');if(e)e.style.display='none';}
  function hidePopup(){var p=document.getElementById('jmAdminReplyPopup');if(p)p.style.display='none';popupId='';}
  function showPopup(item){
    ensure();var p=document.getElementById('jmAdminReplyPopup');if(!p||!item)return;popupId=item.id;p.querySelector('.jm-admin-reply-popup-meta').textContent=item.memberName+' · '+timeText(item.createdAt);p.querySelector('.jm-admin-reply-popup-original').textContent='관리자 원문: '+item.original;p.querySelector('.jm-admin-reply-popup-text').textContent='답장: '+item.text;p.style.display='block';
  }
  function confirmPopup(){if(popupId){var ids=seen();if(ids.indexOf(popupId)<0){ids.push(popupId);saveSeen(ids);}}hidePopup();tick();}
  function tick(){
    if(!isAdminVisible()){renderButton();hidePopup();return;}
    var unseen=renderButton();var p=document.getElementById('jmAdminReplyPopup');if(unseen.length&&p&&p.style.display!=='block')showPopup(unseen[0]);
  }
  window.__JM_ADMIN_RENDER_MEMBER_REPLIES_V1=tick;
  document.addEventListener('DOMContentLoaded',function(){ensure();tick();},{once:true});
  setInterval(tick,1400);ensure();tick();
})();
</script>
'''
    anchor='</body>'
    if anchor not in s:
        raise SystemExit('body closing tag not found')
    s=s.replace(anchor,reply_ui+'\n'+anchor,1)
    changed=True

if changed:
    HTML.write_text(s,encoding='utf-8')
    print('ADMIN_DIRECT_LOGIN_AND_MEMBER_REPLIES_OK')
else:
    print('ADMIN_DIRECT_LOGIN_AND_MEMBER_REPLIES_ALREADY')
