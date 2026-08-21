#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

ALLOWED = [
    'getPublicState',
    'getMemberPasswordVersion',
    'verifyMemberPassword',
    'resumeMemberSession',
    'memberMoveToWaitGroup',
    'memberLeaveWaitGroup',
    'memberRequestWaitSwap',
    'memberGetWaitSwapRequest',
    'memberRespondWaitSwap',
]


def rpc_helper():
    allowed = ',\n    '.join('%s: true' % name for name in ALLOWED)
    cases = '\n'.join(
        "    %sif (name === %s) result = %s.apply(null, args);" % (
            '' if i == 0 else 'else ', json.dumps(name), name
        )
        for i, name in enumerate(ALLOWED)
    )
    return r'''
function memberCloudflareRpc_(e) {
  ensureSetup_();
  const p = e && e.parameter ? e.parameter : {};
  const callback = String(p.callback || '');
  const name = String(p.rpc || '');
  const allowed = {__ALLOWED__};
  if (!/^[A-Za-z_$][A-Za-z0-9_$]{0,80}$/.test(callback)) {
    throw new Error('잘못된 callback입니다.');
  }
  if (!allowed[name]) {
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:false,error:'허용되지 않은 사용자 함수입니다.'}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  let args = [];
  try {
    const encoded = String(p.payload || '');
    if (encoded) {
      const normalized = encoded.replace(/-/g,'+').replace(/_/g,'/');
      const pad = '='.repeat((4 - normalized.length % 4) % 4);
      args = JSON.parse(Utilities.newBlob(Utilities.base64Decode(normalized + pad)).getDataAsString('UTF-8'));
    }
    if (!Array.isArray(args)) throw new Error('args');
  } catch (error) {
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:false,error:'요청 데이터를 읽을 수 없습니다.'}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  try {
    let result;
__CASES__
    else throw new Error('허용되지 않은 사용자 함수입니다.');
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:true,result:result}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  } catch (error) {
    return ContentService.createTextOutput(
      callback + '(' + JSON.stringify({ok:false,error:String(error && error.message || error || '서버 오류')}) + ');'
    ).setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
}
'''.replace('__ALLOWED__', allowed).replace('__CASES__', cases)


BRIDGE = r'''<script id="jayuminton-user-cloudflare-rpc">
(function(){
  var endpoint = RPC_URL_JSON, seq = 0;
  function enc(args){
    var bytes = new TextEncoder().encode(JSON.stringify(args || [])), s = '';
    for (var i=0;i<bytes.length;i++) s += String.fromCharCode(bytes[i]);
    return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function invoke(name,args,success,failure){
    var cb='__jmUser'+Date.now()+'_'+(++seq), sc=document.createElement('script'), done=false;
    var timer=setTimeout(function(){finish(new Error('서버 응답 시간이 초과되었습니다.'));},12000);
    function cleanup(){clearTimeout(timer);try{delete window[cb];}catch(e){window[cb]=undefined;}if(sc.parentNode)sc.parentNode.removeChild(sc);}
    function finish(err,val){if(done)return;done=true;cleanup();if(err){if(typeof failure==='function')failure(err);}else if(typeof success==='function')success(val);}
    window[cb]=function(packet){if(packet&&packet.ok)finish(null,packet.result);else finish(new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.')));};
    sc.onerror=function(){finish(new Error('Cloudflare 사용자 서버에 연결할 수 없습니다.'));};
    var sep=endpoint.indexOf('?')>=0?'&':'?';
    sc.src=endpoint+sep+'rpc='+encodeURIComponent(String(name))+'&callback='+encodeURIComponent(cb)+'&payload='+encodeURIComponent(enc(args))+'&nonce='+Date.now()+'_'+seq;
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
  window.__JAYUMINTON_USER_CLOUDFLARE__=true;
  window.__JAYUMINTON_USER_RPC_URL__=endpoint;
})();
</script>'''

NATIVE_SYNC = r'''<script id="jayuminton-user-native-sync">
(function(){
  function selected(){
    try {
      var value=JSON.parse(localStorage.getItem('jayuminton_web_push_selected_member_v1')||'null');
      return value&&value.id?{id:String(value.id),name:String(value.name||'')}:null;
    } catch(e){ return null; }
  }
  window.syncNativeUserPushBridge=function(){
    if(!window.NativeUserApp)return;
    try {
      var m=selected();
      if(m) window.NativeUserApp.setMember(m.id,m.name);
      else window.NativeUserApp.clearMember();
    } catch(e){}
    try { window.NativeUserApp.setPushEnabled(localStorage.getItem('jayuminton_member_alert_enabled_v1')!=='false'); } catch(e){}
    try { window.NativeUserApp.setVibrationEnabled(localStorage.getItem('jayuminton_member_vibration_enabled_v1')!=='false'); } catch(e){}
  };
  document.addEventListener('click',function(){setTimeout(window.syncNativeUserPushBridge,0);},true);
  document.addEventListener('change',function(){setTimeout(window.syncNativeUserPushBridge,0);},true);
  window.addEventListener('load',function(){setTimeout(window.syncNativeUserPushBridge,50);});
})();
</script>'''


def patch_backend(work):
    p = Path(work) / 'Code.js'
    text = p.read_text(encoding='utf-8')
    if 'function memberCloudflareRpc_(e)' not in text:
        include_marker = 'function include(filename) {'
        if include_marker not in text:
            raise SystemExit('include marker missing')
        text = text.replace(include_marker, rpc_helper() + '\n' + include_marker, 1)
    branch = "  if (e && e.parameter && e.parameter.memberRpc === '1' && e.parameter.rpc) {\n    return memberCloudflareRpc_(e);\n  }\n"
    if branch not in text:
        marker = 'function doGet(e) {'
        if marker not in text:
            raise SystemExit('doGet marker missing')
        text = text.replace(marker, marker + '\n' + branch, 1)
    p.write_text(text, encoding='utf-8')


def build_frontend(snapshot, out, rpc_url):
    snapshot = Path(snapshot)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    index = (snapshot / 'Index.html').read_text(encoding='utf-8')
    style = (snapshot / 'Style.html').read_text(encoding='utf-8')
    script = (snapshot / 'Script.html').read_text(encoding='utf-8')

    index = index.replace("<?!= include('Style'); ?>", style, 1)
    index = index.replace(
        "window.JAYUMINTON_MEMBER_PAGE_URL = <?!= JSON.stringify(memberPageUrl || '') ?>;",
        "window.JAYUMINTON_MEMBER_PAGE_URL = '';",
        1,
    )
    index = index.replace(
        "window.JAYUMINTON_PUSH_RETURN = <?!= pushReturn || '{\"connected\":false,\"memberId\":\"\",\"memberName\":\"\"}' ?>;",
        "window.JAYUMINTON_PUSH_RETURN = {connected:false,memberId:'',memberName:''};",
        1,
    )

    bridge = BRIDGE.replace('RPC_URL_JSON', json.dumps(rpc_url.rstrip('/') + '/?memberRpc=1'))
    marker = '<script>\nconst IS_ADMIN = false;\n</script>'
    if marker not in index:
        raise SystemExit('user IS_ADMIN marker missing')
    index = index.replace(marker, marker + '\n' + bridge, 1)

    # User Cloudflare page is the canonical top-level user page. Remove stale Firebase host coupling.
    script = script.replace("const UNIFIED_MEMBER_APP_URL =\n  'https://jayuminton-push.web.app/';", "const UNIFIED_MEMBER_APP_URL = window.location.origin + '/';")
    script = script.replace("const UNIFIED_MEMBER_APP_ORIGIN = 'https://jayuminton-push.web.app';", "const UNIFIED_MEMBER_APP_ORIGIN = window.location.origin;")
    script = script.replace("const target = 'https://jayuminton-push.web.app/';", "const target = window.location.origin + '/';")

    if "<?!= include('Script'); ?>" not in index:
        raise SystemExit('Script include marker missing')
    index = index.replace("<?!= include('Script'); ?>", script + '\n' + NATIVE_SYNC, 1)

    forbidden = [
        '<?!=',
        '관리자 화면을 불러오는 중입니다',
        'jayuminton-push.web.app',
        'script.google.com/macros/s/',
    ]
    for value in forbidden:
        if value in index:
            raise SystemExit('forbidden user Cloudflare frontend marker remains: ' + value)
    for required in [
        '자유민턴 코트배정 현황',
        'const IS_ADMIN = false;',
        'jayuminton-user-cloudflare-rpc',
        'jayuminton-user-native-sync',
        'NativeUserApp.setMember',
        'getPublicState',
    ]:
        if required not in index:
            raise SystemExit('missing user Cloudflare frontend marker: ' + required)
    (out / 'index.html').write_text(index, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('patch-backend')
    p.add_argument('--work', required=True)
    p = sub.add_parser('build-frontend')
    p.add_argument('--snapshot', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--rpc-url', required=True)
    a = ap.parse_args()
    if a.cmd == 'patch-backend':
        patch_backend(a.work)
    else:
        build_frontend(a.snapshot, a.out, a.rpc_url)


if __name__ == '__main__':
    main()
