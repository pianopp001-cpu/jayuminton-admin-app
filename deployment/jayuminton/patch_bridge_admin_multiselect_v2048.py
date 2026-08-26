from pathlib import Path
import re
import subprocess

p = Path('deployment/jayuminton/cloudflare_v6_frontend_bridge.js')
s = p.read_text(encoding='utf-8')
original = s

# Cloudflare shared temp-team state is a 2-4 member group, not a two-person pair.
pat = re.compile(r"  function validTempPairs\(value\)\{.*?\n  \}\n  function loadLegacyTempPairs", re.S)
replacement = """  function validTempPairs(value){
    var used={};
    return (Array.isArray(value)?value:[]).map(function(x){
      if(!x||['wait','court'].indexOf(String(x.zone))<0)return null;
      var raw=(Array.isArray(x.members)&&x.members.length?x.members:[]).concat(Array.isArray(x.pairA)?x.pairA:[]).concat(Array.isArray(x.pairB)?x.pairB:[]);
      var ids=[];raw.forEach(function(v){v=String(v||'');if(v&&ids.indexOf(v)<0)ids.push(v);});ids=ids.slice(0,4);
      if(ids.length<2||ids.some(function(id){return !!used[id];}))return null;
      ids.forEach(function(id){used[id]=1;});
      return {members:ids,pairA:ids.slice(0,2),pairB:ids.slice(2,4),zone:String(x.zone),createdAt:Number(x.createdAt)||Date.now()};
    }).filter(Boolean);
  }
  function tempTeamIds(group){
    var raw=(Array.isArray(group&&group.members)?group.members:[]).concat(Array.isArray(group&&group.pairA)?group.pairA:[]).concat(Array.isArray(group&&group.pairB)?group.pairB:[]);
    var ids=[];raw.forEach(function(v){v=String(v||'');if(v&&ids.indexOf(v)<0)ids.push(v);});return ids.slice(0,4);
  }
  function loadLegacyTempPairs"""
s, n = pat.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('validTempPairs block not found')

s = s.replace("loadTempPairs().forEach(function(group,index){var color=TEMP_PAIR_COLORS[index%TEMP_PAIR_COLORS.length];group.pairA.forEach(function(id){desired[String(id)]=color;});});",
              "loadTempPairs().forEach(function(group){tempTeamIds(group).forEach(function(id){desired[String(id)]='#d4a017';});});")

login_anchor = """    }).then(function(response){return response.json();}).then(function(packet){
      if(!packet||packet.ok!==true)throw new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.'));
      if(packet.result){"""
login_replacement = """    }).then(function(response){return response.json();}).then(function(packet){
      if(!packet||packet.ok!==true)throw new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.'));
      if(name==='createAdminSession'&&packet.result&&packet.result.ok&&packet.result.token){try{localStorage.setItem('jayuminton_admin_session_v1',String(packet.result.token));}catch(_){}}
      if(name==='verifyMemberPassword'&&packet.result&&packet.result.ok&&packet.result.sessionToken){try{localStorage.setItem('jayuminton_member_session_token_v1',String(packet.result.sessionToken));localStorage.setItem('jayuminton_member_session_token_v164',String(packet.result.sessionToken));}catch(_){}}
      if(packet.result){"""
if login_anchor not in s:
    raise SystemExit('Cloudflare login response anchor not found')
s = s.replace(login_anchor, login_replacement, 1)

s = s.replace("function handlePairClick(event){\n      if(event.defaultPrevented||event.button>0)return;",
              "function handlePairClick(event){\n      if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;\n      if(event.defaultPrevented||event.button>0)return;")
s = s.replace("function installAdminTeamSafetyStyle(){\n      if(document.getElementById('jayuminton-admin-team-safety-v2037'))return;",
              "function installAdminTeamSafetyStyle(){\n      if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;\n      if(document.getElementById('jayuminton-admin-team-safety-v2037'))return;")
s = s.replace("function recordTempPair(first,second,group){",
              "function recordTempPair(first,second,group){\n      if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;")

login_fallback = r'''
  window.__JAYUMINTON_ADMIN_LOGIN_FALLBACK_V2050__=true;
  function jmIsAdminPage(){
    try{return (typeof IS_ADMIN!=='undefined'&&!!IS_ADMIN)||/(?:^|[?&])app=admin(?:&|$)/.test(String(location.search||''));}catch(_){return false;}
  }
  function jmLoginControl(node){
    if(!node||!node.closest)return null;
    var c=node.closest('button,input[type="submit"],input[type="button"],[role="button"]');
    if(!c)return null;
    var text=String((c.textContent||'')+' '+(c.value||'')+' '+(c.id||'')+' '+(c.name||'')+' '+(typeof c.className==='string'?c.className:'')).toLowerCase();
    if(/logout|로그아웃/.test(text))return null;
    return /login|로그인/.test(text)?c:null;
  }
  function jmPinInput(button){
    var scopes=[],cur=button;
    for(var i=0;cur&&i<6;i++,cur=cur.parentElement)scopes.push(cur);
    scopes.push(document);
    var selectors=['input[type="password"]','input[id*="pin" i]','input[name*="pin" i]','input[id*="password" i]','input[name*="password" i]','input[inputmode="numeric"]','input[type="tel"]','input[type="number"]'];
    for(var sidx=0;sidx<scopes.length;sidx++){
      var root=scopes[sidx];if(!root||!root.querySelector)continue;
      for(var j=0;j<selectors.length;j++){var el=root.querySelector(selectors[j]);if(el&&String(el.value||'').trim())return el;}
    }
    return document.querySelector('input[type="password"],input[id*="pin" i],input[name*="pin" i]');
  }
  function jmLoginStatus(button,text,bad){
    var id='jm-admin-login-fallback-status',el=document.getElementById(id);
    if(!el){el=document.createElement('div');el.id=id;el.style.cssText='margin-top:8px;text-align:center;font-size:13px;font-weight:800;';if(button&&button.parentElement)button.parentElement.appendChild(el);else document.body.appendChild(el);}
    el.textContent=String(text||'');el.style.color=bad?'#b91c1c':'#166534';
  }
  function jmDoAdminLogin(button){
    if(!jmIsAdminPage())return false;
    var input=jmPinInput(button),pin=String(input&&input.value||'').trim();
    if(!pin){jmLoginStatus(button,'관리자 PIN을 입력하세요.',true);if(input)input.focus();return true;}
    try{localStorage.removeItem('jayuminton_admin_session_v1');}catch(_){}
    if(button){button.disabled=true;button.setAttribute('data-jm-login-busy','1');}
    jmLoginStatus(button,'로그인 중...',false);
    invoke('createAdminSession',[pin],function(result){
      if(!result||result.ok!==true||!result.token){if(button){button.disabled=false;button.removeAttribute('data-jm-login-busy');}jmLoginStatus(button,'PIN을 확인하세요.',true);return;}
      try{localStorage.setItem('jayuminton_admin_session_v1',String(result.token));}catch(_){}
      invoke('getPublicState',[null],function(state){
        try{if(typeof STATE!=='undefined')STATE=state;}catch(_){}
        try{if(typeof renderState==='function')renderState();}catch(_){}
        jmLoginStatus(button,'로그인 완료',false);
        setTimeout(function(){location.reload();},30);
      },function(){setTimeout(function(){location.reload();},30);});
    },function(error){
      if(button){button.disabled=false;button.removeAttribute('data-jm-login-busy');}
      jmLoginStatus(button,String(error&&error.message||'로그인에 실패했습니다.'),true);
    });
    return true;
  }
  if(jmIsAdminPage()){
    window.addEventListener('click',function(event){
      var button=jmLoginControl(event.target);if(!button)return;
      event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();
      jmDoAdminLogin(button);
    },true);
    window.addEventListener('keydown',function(event){
      if(String(event.key)!=='Enter')return;
      var input=event.target;if(!input||!input.matches||!input.matches('input'))return;
      var button=null,root=input.closest&&input.closest('form,.card,.panel,.login,.login-card');
      if(root)button=Array.prototype.find.call(root.querySelectorAll('button,input[type="submit"],input[type="button"],[role="button"]'),function(x){return !!jmLoginControl(x);});
      if(!button)button=Array.prototype.find.call(document.querySelectorAll('button,input[type="submit"],input[type="button"],[role="button"]'),function(x){return !!jmLoginControl(x);});
      if(!button)return;
      event.preventDefault();event.stopPropagation();if(event.stopImmediatePropagation)event.stopImmediatePropagation();jmDoAdminLogin(button);
    },true);
  }
'''
if '__JAYUMINTON_ADMIN_LOGIN_FALLBACK_V2050__' not in s:
    close = s.rfind('\n})();')
    if close < 0:
        raise SystemExit('bridge IIFE closing anchor not found')
    s = s[:close] + '\n' + login_fallback + s[close:]

if s == original:
    raise SystemExit('bridge was not changed')
if "tempTeamIds(group).forEach" not in s or "#d4a017" not in s:
    raise SystemExit('2-4 yellow team bridge patch missing')
if "if(window.__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__)return;" not in s:
    raise SystemExit('legacy pair guard missing')
if "jayuminton_admin_session_v1" not in s or "name==='createAdminSession'" not in s:
    raise SystemExit('admin login session persistence patch missing')
if '__JAYUMINTON_ADMIN_LOGIN_FALLBACK_V2050__' not in s or "invoke('createAdminSession',[pin]" not in s or "localStorage.removeItem('jayuminton_admin_session_v1')" not in s:
    raise SystemExit('admin login click fallback missing')

p.write_text(s, encoding='utf-8')
subprocess.run(['node', '--check', str(p)], check=True)
print('PATCH_BRIDGE_ADMIN_MULTISELECT_V2050_LOGIN_OK')
