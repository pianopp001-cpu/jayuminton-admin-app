#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ALLOWED = ['getPublicState','verifyMemberPassword','resumeMemberSession','getMemberPasswordVersion']
RPC = r'''
function memberV130JsonpRpc_(e) {
  ensureSetup_();
  const p = e && e.parameter ? e.parameter : {};
  const callback = String(p.callback || '');
  const name = String(p.rpc || '');
  if (!/^[A-Za-z_$][A-Za-z0-9_$]{0,80}$/.test(callback)) throw new Error('invalid callback');
  const allowed = {getPublicState:true,verifyMemberPassword:true,resumeMemberSession:true,getMemberPasswordVersion:true};
  const out = function(packet) { return ContentService.createTextOutput(callback + '(' + JSON.stringify(packet) + ');').setMimeType(ContentService.MimeType.JAVASCRIPT); };
  if (!allowed[name]) return out({ok:false,error:'허용되지 않은 서버 함수입니다.'});
  let args = [];
  try {
    const encoded = String(p.payload || '');
    if (encoded) {
      const normalized = encoded.replace(/-/g, '+').replace(/_/g, '/');
      const pad = '='.repeat((4 - normalized.length % 4) % 4);
      args = JSON.parse(Utilities.newBlob(Utilities.base64Decode(normalized + pad)).getDataAsString('UTF-8'));
    }
    if (!Array.isArray(args)) throw new Error('args');
  } catch (error) { return out({ok:false,error:'요청 데이터를 읽을 수 없습니다.'}); }
  try {
    let result;
    if (name === 'getPublicState') result = getPublicState.apply(null,args);
    else if (name === 'verifyMemberPassword') result = verifyMemberPassword.apply(null,args);
    else if (name === 'resumeMemberSession') result = resumeMemberSession.apply(null,args);
    else if (name === 'getMemberPasswordVersion') result = getMemberPasswordVersion.apply(null,args);
    return out({ok:true,result:result});
  } catch (error) { return out({ok:false,error:String(error && error.message || error || '서버 오류')}); }
}

'''
BRIDGE = r'''<script id="v130-direct-rpc">
(function(){
  const endpoint=__RPC_URL__, timeoutMs=25000; let seq=0, loginBusy=false;
  function enc(args){const bytes=new TextEncoder().encode(JSON.stringify(args||[]));let s='';for(const b of bytes)s+=String.fromCharCode(b);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  function invoke(name,args,success,failure){
    const cb='__jmV130_'+Date.now()+'_'+(++seq), sc=document.createElement('script'); let done=false;
    const timer=setTimeout(()=>finish(new Error('서버 응답 시간이 초과되었습니다.')),timeoutMs);
    function clean(){clearTimeout(timer);try{delete window[cb];}catch(e){window[cb]=undefined;}sc.remove();}
    function finish(err,val){if(done)return;done=true;clean();if(err){if(failure)failure(err);}else if(success)success(val);}
    window[cb]=packet=>packet&&packet.ok?finish(null,packet.result):finish(new Error(String(packet&&packet.error||'서버 요청 실패')));
    sc.onerror=()=>finish(new Error('서버에 연결할 수 없습니다.'));
    sc.src=endpoint+'?rpc='+encodeURIComponent(name)+'&callback='+encodeURIComponent(cb)+'&payload='+encodeURIComponent(enc(args))+'&nonce='+Date.now();
    document.head.appendChild(sc);
  }
  function runner(success,failure){return new Proxy({}, {get(_,prop){if(prop==='withSuccessHandler')return fn=>runner(fn,failure);if(prop==='withFailureHandler')return fn=>runner(success,fn);if(prop==='then')return undefined;return function(){invoke(String(prop),Array.from(arguments),success,failure);};}});}
  window.google=window.google||{}; window.google.script=window.google.script||{}; window.google.script.run=runner(null,null);
  window.__JAYUMINTON_V130_DIRECT_RPC__=true;
  window.memberV130LoginClick_=async function(button){
    if(loginBusy)return;
    const input=document.getElementById('memberPasswordInput');
    if(!input||!String(input.value||'').trim()){if(input)input.focus();alert('멤버 비밀번호를 입력하세요.');return;}
    loginBusy=true;
    const oldText=button&&button.textContent||'확인';
    if(button){button.disabled=true;button.textContent='확인 중…';}
    try {
      await window.memberLogin();
    } catch(error) {
      alert('서버 연결 중 오류가 발생했습니다.\n'+String(error&&error.message||error||'서버 연결 오류'));
    } finally {
      loginBusy=false;
      if(button){button.disabled=false;button.textContent=oldText;}
    }
  };
})();
</script>'''

def patch(work):
    p=work/'Code.js'; s=p.read_text(encoding='utf-8')
    old='function doGet(e) {\n  ensureSetup_();'
    if 'function memberV130JsonpRpc_' not in s:
        if old not in s: raise SystemExit('doGet marker missing')
        s=s.replace(old,"function doGet(e) {\n  if (e && e.parameter && e.parameter.rpc) return memberV130JsonpRpc_(e);\n  ensureSetup_();",1)
        marker='function include(filename) {'
        if marker not in s: raise SystemExit('include marker missing')
        s=s.replace(marker,RPC+marker,1)
    p.write_text(s,encoding='utf-8')

def build(work,out,rpc_url,hosting_url):
    out.mkdir(parents=True,exist_ok=True)
    s=(work/'Index.html').read_text(encoding='utf-8')
    s=s.replace("<?!= include('Style'); ?>",(work/'Style.html').read_text(encoding='utf-8'))
    s=s.replace("<?!= JSON.stringify(memberPageUrl || '') ?>",json.dumps(hosting_url.rstrip('/')+'/'))
    s=s.replace("<?!= pushReturn || '{\"connected\":false,\"memberId\":\"\",\"memberName\":\"\"}' ?>",'{"connected":false,"memberId":"","memberName":""}')
    s=s.replace('<script>\nconst IS_ADMIN = false;\n</script>','<script>\nconst IS_ADMIN = false;\n</script>\n'+BRIDGE.replace('__RPC_URL__',json.dumps(rpc_url)),1)
    s=s.replace('onclick="memberLogin()"','onclick="memberV130LoginClick_(this)"',1)
    s=s.replace("<?!= include('Script'); ?>",(work/'Script.html').read_text(encoding='utf-8'),1)
    if '<?!=' in s or '<iframe' in s: raise SystemExit('template or iframe remains')
    if 'memberV130LoginClick_(this)' not in s: raise SystemExit('safe login handler missing')
    s=s.replace('</head>','<meta name="jayuminton-v130-direct" content="1"></head>',1)
    (out/'index.html').write_text(s,encoding='utf-8')
    (out/'badminton.html').write_text(s,encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('patch'); a.add_argument('--work',required=True)
    b=sub.add_parser('build'); b.add_argument('--work',required=True); b.add_argument('--out',required=True); b.add_argument('--rpc-url',required=True); b.add_argument('--hosting-url',required=True)
    x=ap.parse_args(); work=Path(x.work)
    patch(work) if x.cmd=='patch' else build(work,Path(x.out),x.rpc_url,x.hosting_url)
if __name__=='__main__': main()
