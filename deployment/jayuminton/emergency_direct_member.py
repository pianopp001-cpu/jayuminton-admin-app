#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

RPC_HELPER = r'''
function memberFirebaseJsonpRpc_(e) {
  ensureSetup_();
  const p = e && e.parameter ? e.parameter : {};
  const callback = String(p.callback || '');
  const name = String(p.rpc || '');
  if (!/^[A-Za-z_$][A-Za-z0-9_$]{0,80}$/.test(callback)) {
    throw new Error('잘못된 callback입니다.');
  }
  if (!/^[A-Za-z][A-Za-z0-9]{0,80}$/.test(name) || /_$/.test(name)) {
    return ContentService.createTextOutput(callback + '(' + JSON.stringify({ok:false,error:'허용되지 않은 서버 함수입니다.'}) + ');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  const blocked = {doGet:true, doPost:true, include:true};
  if (blocked[name]) {
    return ContentService.createTextOutput(callback + '(' + JSON.stringify({ok:false,error:'허용되지 않은 서버 함수입니다.'}) + ');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  let args = [];
  try {
    const encoded = String(p.payload || '');
    if (encoded) {
      const normalized = encoded.replace(/-/g, '+').replace(/_/g, '/');
      const pad = '='.repeat((4 - normalized.length % 4) % 4);
      args = JSON.parse(Utilities.newBlob(Utilities.base64Decode(normalized + pad)).getDataAsString('UTF-8'));
    }
    if (!Array.isArray(args)) throw new Error('args');
  } catch (error) {
    return ContentService.createTextOutput(callback + '(' + JSON.stringify({ok:false,error:'요청 데이터를 읽을 수 없습니다.'}) + ');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  try {
    const fn = eval(name);
    if (typeof fn !== 'function') throw new Error('함수를 찾을 수 없습니다.');
    const result = fn.apply(null, args);
    return ContentService.createTextOutput(callback + '(' + JSON.stringify({ok:true,result:result}) + ');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  } catch (error) {
    return ContentService.createTextOutput(callback + '(' + JSON.stringify({ok:false,error:String(error && error.message || error || '서버 오류')}) + ');').setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
}

'''

BRIDGE = r'''<script>
/* firebase-direct-rpc-v2 */
(function(){
  var endpoint=RPC_URL_JSON,seq=0;
  function enc(args){var b=new TextEncoder().encode(JSON.stringify(args||[])),s='';for(var i=0;i<b.length;i++)s+=String.fromCharCode(b[i]);return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  function invoke(name,args,success,failure){
    var cb='__jmRpc'+Date.now()+'_'+(++seq),sc=document.createElement('script'),done=false;
    var t=setTimeout(function(){finish(new Error('서버 응답 시간이 초과되었습니다.'));},20000);
    function clean(){clearTimeout(t);try{delete window[cb];}catch(e){window[cb]=undefined;}if(sc.parentNode)sc.parentNode.removeChild(sc);}
    function finish(err,val){if(done)return;done=true;clean();try{if(err){if(typeof failure==='function')failure(err);}else if(typeof success==='function')success(val);}catch(e){}}
    window[cb]=function(packet){if(packet&&packet.ok)finish(null,packet.result);else finish(new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.')));};
    sc.onerror=function(){finish(new Error('서버에 연결할 수 없습니다.'));};
    sc.src=endpoint+'?rpc='+encodeURIComponent(String(name))+'&callback='+encodeURIComponent(cb)+'&payload='+encodeURIComponent(enc(args))+'&nonce='+Date.now()+'_'+seq;
    document.head.appendChild(sc);
  }
  function runner(success,failure){return new Proxy({}, {get:function(_,prop){if(prop==='withSuccessHandler')return function(fn){return runner(fn,failure);};if(prop==='withFailureHandler')return function(fn){return runner(success,fn);};if(prop==='then')return undefined;return function(){invoke(String(prop),Array.prototype.slice.call(arguments),success,failure);};}});}
  window.google=window.google||{};
  window.google.script=window.google.script||{};
  window.google.script.run=runner(null,null);
  window.__JAYUMINTON_FIREBASE_DIRECT_RPC__=true;

  var loginBusy=false;
  window.memberFirebaseLoginClick_=function(event){
    if(event){try{event.preventDefault();event.stopPropagation();}catch(e){}}
    if(loginBusy)return;
    var button=document.getElementById('memberLoginButton');
    var input=document.getElementById('memberPasswordInput');
    if(!input)return;
    if(!String(input.value||'').trim()){
      try{input.focus();}catch(e){}
      alert('멤버 비밀번호를 입력하세요.');
      return;
    }
    loginBusy=true;
    if(button){button.disabled=true;button.textContent='확인 중…';}
    var task;
    try{
      if(typeof window.memberLogin!=='function')throw new Error('로그인 기능을 불러오지 못했습니다.');
      task=window.memberLogin();
    }catch(error){
      task=Promise.reject(error);
    }
    Promise.resolve(task).catch(function(error){
      alert('로그인 처리 중 오류가 발생했습니다.\n'+String(error&&error.message||error||'서버 연결 오류'));
    }).finally(function(){
      loginBusy=false;
      if(button){button.disabled=false;button.textContent='확인';}
    });
  };

  function bindLogin(){
    var button=document.getElementById('memberLoginButton');
    var input=document.getElementById('memberPasswordInput');
    if(button&&!button.__jmLoginBound){
      button.__jmLoginBound=true;
      button.addEventListener('click',window.memberFirebaseLoginClick_,false);
    }
    if(input&&!input.__jmLoginBound){
      input.__jmLoginBound=true;
      input.addEventListener('keydown',function(event){
        if(event.key==='Enter'){window.memberFirebaseLoginClick_(event);}
      },false);
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bindLogin,{once:true});
  else setTimeout(bindLogin,0);
})();
</script>'''


def patch(work: Path):
    p = work / 'Code.js'
    s = p.read_text(encoding='utf-8')
    old = "function doGet(e) {\n  ensureSetup_();"
    new = "function doGet(e) {\n  if (e && e.parameter && e.parameter.rpc) {\n    return memberFirebaseJsonpRpc_(e);\n  }\n  ensureSetup_();"
    if 'function memberFirebaseJsonpRpc_' not in s:
        if old not in s:
            raise SystemExit('doGet marker missing')
        s = s.replace(old, new, 1)
        marker = 'function include(filename) {'
        if marker not in s:
            raise SystemExit('include marker missing')
        s = s.replace(marker, RPC_HELPER + marker, 1)
    p.write_text(s, encoding='utf-8')


def build(work: Path, out: Path, rpc_url: str, hosting_url: str):
    out.mkdir(parents=True, exist_ok=True)
    index = (work / 'Index.html').read_text(encoding='utf-8')
    index = index.replace("<?!= include('Style'); ?>", (work / 'Style.html').read_text(encoding='utf-8'))
    hosting_url = hosting_url.rstrip('/') + '/'
    index = index.replace("<?!= JSON.stringify(memberPageUrl || '') ?>", json.dumps(hosting_url))
    index = index.replace("<?!= pushReturn || '{\"connected\":false,\"memberId\":\"\",\"memberName\":\"\"}' ?>", json.dumps('{"connected":false,"memberId":"","memberName":""}'))
    bridge = BRIDGE.replace('RPC_URL_JSON', json.dumps(rpc_url))
    marker = '<script>const IS_ADMIN = false;</script>'
    if marker not in index:
        raise SystemExit('IS_ADMIN marker missing')
    index = index.replace(marker, marker + '\n' + bridge, 1)
    for name in ['Script','MemberSwapClient','MemberSwapAction','MemberControls','MemberSwapInbox']:
        token = "<?!= include('%s'); ?>" % name
        if token not in index:
            raise SystemExit('include token missing: ' + name)
        index = index.replace(token, (work / (name + '.html')).read_text(encoding='utf-8'), 1)
    if '<?!=' in index or '<iframe' in index or 'window.location.replace' in index:
        raise SystemExit('unsafe template/iframe/redirect remains')
    (out / 'index.html').write_text(index, encoding='utf-8')
    (out / 'manifest.webmanifest').write_text(json.dumps({
        'name':'자유민턴 코트현황','short_name':'자유민턴','start_url':'/','scope':'/',
        'display':'standalone','background_color':'#ffffff','theme_color':'#315efb'
    }, ensure_ascii=False), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p1 = sub.add_parser('patch'); p1.add_argument('--work', required=True)
    p2 = sub.add_parser('build'); p2.add_argument('--work', required=True); p2.add_argument('--out', required=True); p2.add_argument('--rpc-url', required=True); p2.add_argument('--hosting-url', required=True)
    a = ap.parse_args()
    if a.cmd == 'patch': patch(Path(a.work))
    else: build(Path(a.work), Path(a.out), a.rpc_url, a.hosting_url)

if __name__ == '__main__':
    main()
