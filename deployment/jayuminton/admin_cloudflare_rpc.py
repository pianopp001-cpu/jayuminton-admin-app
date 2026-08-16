#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ALLOWED = [
    'createAdminSession','resumeAdminSession','getCurrentMemberPassword','getPublicState','getSystemStatus',
    'addMember','setMemberStatus','updateMember','updateMemberProfile','deleteMember','deleteMembers','changeMemberPassword',
    'assignMembersToCourt','assignMembersToWaitGroup','assignWaitGroupToCourt',
    'autoFillCourt','autoFillWaitGroup','moveOrSwapMember','finishCourt',
    'swapCourts','swapWaitGroups','undoLastAction','decreaseSelectedGameCounts','resetSelectedGameCounts',
    'removeFromCourt','removeFromWaitGroup','adjustCourtMembers','adjustWaitGroupMembers',
    'resetAll','resetAllOperationData','createBackup','restoreBackup','createManualBackup','restoreManualBackup'
]

def rpc_helper():
    cases='\n'.join("    else if (name === %s) result = %s.apply(null,args);"%(json.dumps(n),n) for n in ALLOWED[1:])
    allowed=',\n    '.join('%s: true'%n for n in ALLOWED)
    return r'''
function adminCloudflareRpc_(e) {
  ensureSetup_();
  const p=e&&e.parameter?e.parameter:{};
  const callback=String(p.callback||''); const name=String(p.rpc||'');
  const allowed={__ALLOWED__};
  if(!/^[A-Za-z_$][A-Za-z0-9_$]{0,80}$/.test(callback)) throw new Error('잘못된 callback입니다.');
  if(!allowed[name]) return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:false,error:'허용되지 않은 관리자 함수입니다.'})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  let args=[];
  try { const encoded=String(p.payload||''); if(encoded){const normalized=encoded.replace(/-/g,'+').replace(/_/g,'/');const pad='='.repeat((4-normalized.length%4)%4);args=JSON.parse(Utilities.newBlob(Utilities.base64Decode(normalized+pad)).getDataAsString('UTF-8'));} if(!Array.isArray(args)) throw new Error('args'); }
  catch(error){return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:false,error:'요청 데이터를 읽을 수 없습니다.'})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);}
  try { let result; if(name==='createAdminSession') result=createAdminSession.apply(null,args);
__CASES__
    else throw new Error('허용되지 않은 관리자 함수입니다.');
    return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:true,result:result})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  } catch(error){return ContentService.createTextOutput(callback+'('+JSON.stringify({ok:false,error:String(error&&error.message||error||'서버 오류')})+');').setMimeType(ContentService.MimeType.JAVASCRIPT);}
}
'''.replace('__ALLOWED__',allowed).replace('__CASES__',cases)

BRIDGE=r'''<script id="jayuminton-admin-cloudflare-rpc">
(function(){
  var endpoint=RPC_URL_JSON,seq=0;
  function loginBox(){return document.getElementById('adminLoginBox');}
  function adminApp(){return document.getElementById('adminApp');}
  function hideAppUntilAuthenticated(){var a=adminApp();if(a){a.classList.add('hidden');a.hidden=true;a.style.setProperty('display','none','important');}var b=loginBox();if(b){b.classList.remove('hidden');b.hidden=false;b.removeAttribute('hidden');b.style.setProperty('display','block','important');}}
  function revealAuthenticatedApp(){var a=adminApp();if(a){a.hidden=false;a.removeAttribute('hidden');a.style.removeProperty('display');a.classList.remove('hidden');}var b=loginBox();if(b){b.classList.add('hidden');b.hidden=true;b.style.setProperty('display','none','important');}}
  function enc(args){var bytes=new TextEncoder().encode(JSON.stringify(args||[])),s='';for(var i=0;i<bytes.length;i++)s+=String.fromCharCode(bytes[i]);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  function invoke(name,args,success,failure){var cb='__jmAdmin'+Date.now()+'_'+(++seq),sc=document.createElement('script'),done=false;var timer=setTimeout(function(){finish(new Error('서버 응답 시간이 초과되었습니다.'));},20000);function cleanup(){clearTimeout(timer);try{delete window[cb];}catch(e){window[cb]=undefined;}if(sc.parentNode)sc.parentNode.removeChild(sc);}function finish(err,val){if(done)return;done=true;cleanup();if(err){if(typeof failure==='function')failure(err);}else if(typeof success==='function')success(val);}window[cb]=function(packet){if(packet&&packet.ok)finish(null,packet.result);else finish(new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.')));};sc.onerror=function(){finish(new Error('서버에 연결할 수 없습니다.'));};var sep=endpoint.indexOf('?')>=0?'&':'?';sc.src=endpoint+sep+'rpc='+encodeURIComponent(String(name))+'&callback='+encodeURIComponent(cb)+'&payload='+encodeURIComponent(enc(args))+'&nonce='+Date.now()+'_'+seq;document.head.appendChild(sc);}
  function runner(success,failure){return new Proxy({}, {get:function(_,prop){if(prop==='withSuccessHandler')return function(fn){return runner(fn,failure);};if(prop==='withFailureHandler')return function(fn){return runner(success,fn);};if(prop==='then')return undefined;return function(){invoke(String(prop),Array.prototype.slice.call(arguments),success,failure);};}});}
  window.google=window.google||{};window.google.script=window.google.script||{};window.google.script.run=runner(null,null);window.__JAYUMINTON_ADMIN_CLOUDFLARE__=true;
  function ensureStatus(){var box=loginBox();if(!box||document.getElementById('adminCloudflareLoginStatus'))return;var el=document.createElement('div');el.id='adminCloudflareLoginStatus';el.setAttribute('role','status');el.setAttribute('aria-live','polite');el.style.cssText='margin-top:10px;font-size:13px;font-weight:700;text-align:center';box.appendChild(el);}
  function status(text,error){var el=document.getElementById('adminCloudflareLoginStatus');if(el){el.textContent=String(text||'');el.style.color=error?'#b42318':'#667085';}}
  function resetLoginButton(){var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=false;b.textContent='로그인';}}
  function standaloneLogin(){var input=document.getElementById('adminPinInput'),pin=String(input&&input.value||'').trim();if(!pin){status('관리자 PIN을 입력하세요.',true);return;}var b=document.getElementById('adminCloudflareLoginButton');if(b){b.disabled=true;b.textContent='확인 중…';}status('관리자 서버에 연결하고 있습니다.',false);invoke('createAdminSession',[pin],function(result){if(!result||!result.ok){status('관리자 PIN이 틀렸습니다.',true);resetLoginButton();return;}var token=String(result.token||'');try{localStorage.setItem('jayuminton_admin_session_v1',token);}catch(e){}if(typeof window.openAdminApp!=='function'){status('관리자 화면 초기화 함수가 없습니다.',true);resetLoginButton();return;}Promise.resolve(window.openAdminApp(token)).then(function(){revealAuthenticatedApp();status('',false);resetLoginButton();}).catch(function(e){hideAppUntilAuthenticated();status(String(e&&e.message||e||'관리자 화면을 불러오지 못했습니다.'),true);resetLoginButton();});},function(e){hideAppUntilAuthenticated();status(String(e&&e.message||e||'서버에 연결할 수 없습니다.'),true);resetLoginButton();});}
  function bindLogin(){hideAppUntilAuthenticated();ensureStatus();var b=document.getElementById('adminCloudflareLoginButton'),input=document.getElementById('adminPinInput');if(b&&!b.__jmBound){b.__jmBound=true;b.addEventListener('click',standaloneLogin);}if(input&&!input.__jmBound){input.__jmBound=true;input.addEventListener('keydown',function(ev){if(ev.key==='Enter'){ev.preventDefault();standaloneLogin();}});}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bindLogin,{once:true});else setTimeout(bindLogin,0);
})();
</script>'''

def patch_backend(work):
    p=Path(work)/'Code.js'; text=p.read_text(encoding='utf-8')
    marker='function doGet(e) {\n  ensureSetup_();'
    repl="function doGet(e) {\n  if (e && e.parameter && e.parameter.adminRpc === '1' && e.parameter.rpc) {\n    return adminCloudflareRpc_(e);\n  }\n  ensureSetup_();"
    if marker not in text: raise SystemExit('doGet marker missing')
    text=text.replace(marker,repl,1)
    inc='function include(filename) {'
    if inc not in text: raise SystemExit('include marker missing')
    text=text.replace(inc,rpc_helper()+'\n'+inc,1);p.write_text(text,encoding='utf-8')

def build_frontend(work,out,rpc_url):
    work=Path(work);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    index=(work/'Admin.html').read_text(encoding='utf-8')
    def include(name,s):
        marker="<?!= include('%s'); ?>"%name
        if marker in s:s=s.replace(marker,(work/(name+'.html')).read_text(encoding='utf-8'))
        return s
    for n in ['Style']: index=include(n,index)
    index=index.replace('class="primary"\n      onclick="adminLogin()"','id="adminCloudflareLoginButton"\n      class="primary"\n      type="button"',1)
    bridge=BRIDGE.replace('RPC_URL_JSON',json.dumps(rpc_url.rstrip('/')+'/?adminRpc=1'))
    marker='<script>const IS_ADMIN = true;</script>'
    if marker not in index: marker='<script>\nconst IS_ADMIN = true;\n</script>'
    if marker not in index: raise SystemExit('IS_ADMIN admin marker missing')
    index=index.replace(marker,marker+'\n'+bridge,1)
    for n in ['Script','MemberSwapClient','MemberSwapAction','MemberControls','MemberSwapInbox']: index=include(n,index)
    if '<?!=' in index: raise SystemExit('Apps Script template marker remains')
    if 'script.google.com/macros/s/' in index: raise SystemExit('direct Apps Script URL remains')
    if 'adminCloudflareLoginButton' not in index: raise SystemExit('standalone admin login button patch missing')
    (out/'index.html').write_text(index,encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('patch-backend');p.add_argument('--work',required=True)
    p=sub.add_parser('build-frontend');p.add_argument('--work',required=True);p.add_argument('--out',required=True);p.add_argument('--rpc-url',required=True)
    a=ap.parse_args();patch_backend(a.work) if a.cmd=='patch-backend' else build_frontend(a.work,a.out,a.rpc_url)
if __name__=='__main__':main()
