from pathlib import Path

HTML = Path('app/src/main/assets/admin/index.html')
s = HTML.read_text(encoding='utf-8')
marker = '__JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050__'
if marker in s:
    print('ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050_ALREADY')
    raise SystemExit(0)

script = r'''
<script>
/* __JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050__ */
(function(){
  'use strict';
  var ENDPOINT='https://jayuminton-state.pianopp001.workers.dev/api/compat/rpc';
  var ADMIN_KEY='jayuminton_admin_session_v1';

  function token(){
    try{return String(localStorage.getItem(ADMIN_KEY)||'');}catch(_){return '';}
  }
  function directServer(name,args){
    var values=Array.isArray(args)?args:[];
    var t=(name==='createAdminSession'||name==='verifyMemberPassword'||name==='getMemberPasswordVersion')?'':token();
    return fetch(ENDPOINT,{
      method:'POST',cache:'no-store',credentials:'omit',
      headers:Object.assign({'content-type':'application/json'},t?{'authorization':'Bearer '+t}:{}),
      body:JSON.stringify({name:String(name||''),args:values})
    }).then(function(r){
      return r.text().then(function(text){
        var packet;try{packet=JSON.parse(text);}catch(_){throw new Error('서버 응답 오류 ('+r.status+')');}
        if(!r.ok||!packet||packet.ok!==true)throw new Error(String(packet&&packet.error||('서버 요청 실패 ('+r.status+')')));
        return packet.result;
      });
    });
  }

  window.server=directServer;

  function passwordHost(){
    var app=document.getElementById('adminApp');if(!app)return null;
    var nodes=app.querySelectorAll('summary,h2,h3,label,.card,.section');
    for(var i=0;i<nodes.length;i++){
      var text=String(nodes[i].textContent||'');
      if(text.indexOf('비밀번호')>=0){return nodes[i].closest('.card,details,.section')||nodes[i].parentElement||app;}
    }
    return app;
  }
  async function refreshCurrentMemberPassword(){
    var app=document.getElementById('adminApp');if(!app||app.style.display==='none')return;
    var box=document.getElementById('jm-current-member-password-box');
    if(!box){
      box=document.createElement('div');box.id='jm-current-member-password-box';
      box.style.cssText='margin:8px 0;padding:10px 12px;border:1px solid #cbd5e1;border-radius:12px;background:#f8fafc;font-size:13px;font-weight:800;color:#334155;display:flex;gap:8px;align-items:center;flex-wrap:wrap';
      box.innerHTML='<span>현재 사용자 비밀번호</span><strong id="jm-current-member-password-value" style="font-size:15px;color:#111827">불러오는 중…</strong><button type="button" id="jm-current-member-password-refresh" style="border:0;border-radius:9px;padding:6px 9px;font-weight:800">새로고침</button>';
      var host=passwordHost();if(host)host.insertBefore(box,host.firstChild);
      var b=document.getElementById('jm-current-member-password-refresh');if(b)b.onclick=function(e){e.preventDefault();e.stopPropagation();refreshCurrentMemberPassword();};
    }
    var value=document.getElementById('jm-current-member-password-value');
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
  window.__JAYUMINTON_ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050__=true;
})();
</script>
'''

anchor='</body>'
if anchor not in s:
    raise SystemExit('body closing tag not found')
s=s.replace(anchor,script+'\n'+anchor,1)
HTML.write_text(s,encoding='utf-8')
print('ADMIN_DIRECT_CLOUDFLARE_LOGIN_V2050_OK current-member-password=visible')
