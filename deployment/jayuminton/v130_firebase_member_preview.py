#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ALLOWED = [
    'getPublicState',
    'getMemberPasswordVersion',
    'verifyMemberPassword',
    'resumeMemberSession',
]

RPC_HELPER = r'''
function memberFirebasePreviewRpc_(e) {
  ensureSetup_();
  const p = e && e.parameter ? e.parameter : {};
  const callback = String(p.callback || '');
  const name = String(p.rpc || '');
  const allowed = {
    getPublicState: true,
    getMemberPasswordVersion: true,
    verifyMemberPassword: true,
    resumeMemberSession: true
  };
  if (!/^[A-Za-z_$][A-Za-z0-9_$]{0,80}$/.test(callback)) {
    throw new Error('잘못된 callback입니다.');
  }
  if (!allowed[name]) {
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:false,error:'허용되지 않은 서버 함수입니다.'}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  let args = [];
  try {
    const encoded = String(p.payload || '');
    if (encoded) {
      const normalized = encoded.replace(/-/g, '+').replace(/_/g, '/');
      const pad = '='.repeat((4 - normalized.length % 4) % 4);
      args = JSON.parse(
        Utilities.newBlob(Utilities.base64Decode(normalized + pad)).getDataAsString('UTF-8')
      );
    }
    if (!Array.isArray(args)) throw new Error('args');
  } catch (error) {
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:false,error:'요청 데이터를 읽을 수 없습니다.'}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  try {
    let result;
    if (name === 'getPublicState') result = getPublicState.apply(null, args);
    else if (name === 'getMemberPasswordVersion') result = getMemberPasswordVersion.apply(null, args);
    else if (name === 'verifyMemberPassword') result = verifyMemberPassword.apply(null, args);
    else if (name === 'resumeMemberSession') result = resumeMemberSession.apply(null, args);
    else throw new Error('허용되지 않은 서버 함수입니다.');
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:true,result:result}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  } catch (error) {
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:false,error:String(error && error.message || error || '서버 오류')}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
}
'''

BRIDGE = r'''<script>
/* jayuminton-v130-firebase-member-preview */
(function(){
  var endpoint=RPC_URL_JSON, seq=0;
  function enc(args){
    var bytes=new TextEncoder().encode(JSON.stringify(args||[])), s='';
    for(var i=0;i<bytes.length;i++)s+=String.fromCharCode(bytes[i]);
    return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function invoke(name,args,success,failure){
    var cb='__jmPrev'+Date.now()+'_'+(++seq), sc=document.createElement('script'), done=false;
    var timer=setTimeout(function(){finish(new Error('서버 응답 시간이 초과되었습니다.'));},20000);
    function cleanup(){clearTimeout(timer);try{delete window[cb];}catch(e){window[cb]=undefined;}if(sc.parentNode)sc.parentNode.removeChild(sc);}
    function finish(err,val){if(done)return;done=true;cleanup();try{if(err){if(typeof failure==='function')failure(err);}else if(typeof success==='function')success(val);}catch(e){}}
    window[cb]=function(packet){if(packet&&packet.ok)finish(null,packet.result);else finish(new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.')));};
    sc.onerror=function(){finish(new Error('서버에 연결할 수 없습니다.'));};
    sc.src=endpoint+'?rpc='+encodeURIComponent(String(name))+'&callback='+encodeURIComponent(cb)+'&payload='+encodeURIComponent(enc(args))+'&nonce='+Date.now()+'_'+seq;
    document.head.appendChild(sc);
  }
  function runner(success,failure){
    return new Proxy({}, {get:function(_,prop){
      if(prop==='withSuccessHandler')return function(fn){return runner(fn,failure);};
      if(prop==='withFailureHandler')return function(fn){return runner(success,fn);};
      if(prop==='then')return undefined;
      return function(){invoke(String(prop),Array.prototype.slice.call(arguments),success,failure);};
    }});
  }
  window.google=window.google||{};
  window.google.script=window.google.script||{};
  window.google.script.run=runner(null,null);
  window.__JAYUMINTON_V130_FIREBASE_MEMBER_PREVIEW__=true;
})();
</script>'''


def patch_backend(work: Path):
    code = work / 'Code.js'
    text = code.read_text(encoding='utf-8')
    marker = "function doGet(e) {\n  ensureSetup_();"
    replacement = "function doGet(e) {\n  if (e && e.parameter && e.parameter.rpc) {\n    return memberFirebasePreviewRpc_(e);\n  }\n  ensureSetup_();"
    if marker not in text:
        raise SystemExit('doGet marker missing')
    text = text.replace(marker, replacement, 1)
    include_marker = 'function include(filename) {'
    if include_marker not in text:
        raise SystemExit('include marker missing')
    text = text.replace(include_marker, RPC_HELPER + '\n' + include_marker, 1)
    code.write_text(text, encoding='utf-8')


def build_frontend(work: Path, out: Path, rpc_url: str):
    out.mkdir(parents=True, exist_ok=True)
    index = (work / 'Index.html').read_text(encoding='utf-8')
    style = (work / 'Style.html').read_text(encoding='utf-8')
    script = (work / 'Script.html').read_text(encoding='utf-8')

    index = index.replace("<?!= include('Style'); ?>", style)
    index = index.replace(
        "window.JAYUMINTON_MEMBER_PAGE_URL = <?!= JSON.stringify(memberPageUrl || '') ?>;",
        "window.JAYUMINTON_MEMBER_PAGE_URL = window.location.origin + '/';"
    )
    index = index.replace(
        "window.JAYUMINTON_PUSH_RETURN = <?!= pushReturn || '{\"connected\":false,\"memberId\":\"\",\"memberName\":\"\"}' ?>;",
        "window.JAYUMINTON_PUSH_RETURN = {connected:false,memberId:'',memberName:''};"
    )
    marker = '<script>\nconst IS_ADMIN = false;\n</script>'
    if marker not in index:
        raise SystemExit('IS_ADMIN marker missing')
    bridge = BRIDGE.replace('RPC_URL_JSON', json.dumps(rpc_url))
    index = index.replace(marker, marker + '\n' + bridge, 1)
    index = index.replace("<?!= include('Script'); ?>", script)

    if '<?!=' in index:
        raise SystemExit('Apps Script template marker remains')
    if '<iframe' in index.lower():
        raise SystemExit('iframe remains in preview page')
    if 'jayuminton-v130-firebase-member-preview' not in index:
        raise SystemExit('preview marker missing')

    (out / 'index.html').write_text(index, encoding='utf-8')
    (out / 'manifest.webmanifest').write_text(json.dumps({
        'name':'자유민턴 코트배정 현황 Preview',
        'short_name':'자유민턴 Preview',
        'start_url':'/',
        'scope':'/',
        'display':'standalone',
        'background_color':'#ffffff',
        'theme_color':'#315efb'
    }, ensure_ascii=False), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    p1 = sub.add_parser('patch-backend'); p1.add_argument('--work', required=True)
    p2 = sub.add_parser('build-frontend'); p2.add_argument('--work', required=True); p2.add_argument('--out', required=True); p2.add_argument('--rpc-url', required=True)
    args = parser.parse_args()
    if args.cmd == 'patch-backend':
        patch_backend(Path(args.work))
    else:
        build_frontend(Path(args.work), Path(args.out), args.rpc_url)

if __name__ == '__main__':
    main()
