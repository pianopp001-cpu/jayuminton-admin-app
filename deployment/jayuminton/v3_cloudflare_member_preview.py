#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ALLOWED = [
    'getPublicState',
    'getMemberPasswordVersion',
    'verifyMemberPassword',
    'resumeMemberSession',
    'memberRequestAnywhereSwap',
    'memberGetAnywhereSwapRequest',
    'memberGetAnywhereOutgoingSwap',
    'memberCancelAnywhereSwap',
    'memberAcceptAnywhereSwap',
    'memberRejectAnywhereSwap',
    'memberMoveSelf',
    'memberReturnSelfToWait',
    'memberMoveToWaitGroup',
    'memberLeaveWaitGroup',
    'memberRequestWaitSwap',
    'memberGetWaitSwapRequest',
    'memberRespondWaitSwap',
]


def rpc_helper():
    cases = '\n'.join(
        "    else if (name === %s) result = %s.apply(null, args);" % (json.dumps(name), name)
        for name in ALLOWED[1:]
    )
    allowed_obj = ',\n    '.join('%s: true' % name for name in ALLOWED)
    return r'''
function memberFirebasePreviewRpc_(e) {
  ensureSetup_();
  const p = e && e.parameter ? e.parameter : {};
  const callback = String(p.callback || '');
  const name = String(p.rpc || '');
  const allowed = {
    __ALLOWED__
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
    if (name === 'getPublicState') result = getPublicState.apply(null, args);
__CASES__
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
'''.replace('__ALLOWED__', allowed_obj).replace('__CASES__', cases)


BRIDGE = r'''<script>
/* jayuminton-v3-cloudflare-member-preview */
(function(){
  var endpoint=RPC_URL_JSON, seq=0;
  function enc(args){
    var bytes=new TextEncoder().encode(JSON.stringify(args||[])), s='';
    for(var i=0;i<bytes.length;i++)s+=String.fromCharCode(bytes[i]);
    return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  }
  function invoke(name,args,success,failure){
    var cb='__jmV3Prev'+Date.now()+'_'+(++seq), sc=document.createElement('script'), done=false;
    var timer=setTimeout(function(){finish(new Error('서버 응답 시간이 초과되었습니다.'));},20000);
    function cleanup(){clearTimeout(timer);try{delete window[cb];}catch(e){window[cb]=undefined;}if(sc.parentNode)sc.parentNode.removeChild(sc);}
    function finish(err,val){if(done)return;done=true;cleanup();try{if(err){if(typeof failure==='function')failure(err);}else if(typeof success==='function')success(val);}catch(e){}}
    window[cb]=function(packet){if(packet&&packet.ok)finish(null,packet.result);else finish(new Error(String(packet&&packet.error||'서버 요청에 실패했습니다.')));};
    sc.onerror=function(){finish(new Error('서버에 연결할 수 없습니다.'));};
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
  window.__JAYUMINTON_V3_CLOUDFLARE_PREVIEW__=true;

  function ensureLoginStatus(){
    var login=document.getElementById('memberLoginBox');
    if(!login||document.getElementById('memberPreviewLoginStatus'))return;
    var el=document.createElement('div');
    el.id='memberPreviewLoginStatus';el.setAttribute('role','status');el.setAttribute('aria-live','polite');
    el.style.cssText='margin-top:10px;font-size:13px;font-weight:700';login.appendChild(el);
  }
  function status(text,error){var el=document.getElementById('memberPreviewLoginStatus');if(el){el.textContent=String(text||'');el.style.color=error?'#b42318':'#667085';}}
  function bindLogin(){
    ensureLoginStatus();
    var b=document.getElementById('memberLoginButton'), input=document.getElementById('memberPasswordInput');
    if(b&&!b.__jmV3Bound){b.__jmV3Bound=true;b.addEventListener('click',function(ev){
      ev.preventDefault();ev.stopPropagation();if(b.disabled)return;
      b.disabled=true;var old=b.textContent;b.textContent='확인 중…';status('비밀번호를 확인하고 있습니다.',false);
      Promise.resolve().then(function(){return window.memberLogin();}).then(function(){status('',false);}).catch(function(e){status(String(e&&e.message||e||'서버 연결 오류'),true);}).finally(function(){b.disabled=false;b.textContent=old||'확인';});
    },false);}
    if(input&&!input.__jmV3Bound){input.__jmV3Bound=true;input.addEventListener('keydown',function(ev){if(ev.key==='Enter'&&b)b.click();},false);}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bindLogin,{once:true});else setTimeout(bindLogin,0);
})();
</script>'''

WRAP_STYLE = r'''<style id="jayuminton-v3-preview-wrap-fix">
#memberApp .member-info-detail,
#memberApp .meta,
#memberApp .person .meta,
#memberApp .member .meta{
  white-space:normal!important;
  overflow:visible!important;
  text-overflow:clip!important;
  max-width:none!important;
  height:auto!important;
  line-height:1.3!important;
  overflow-wrap:anywhere!important;
  word-break:keep-all!important;
}
</style>'''


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
    text = text.replace(include_marker, rpc_helper() + '\n' + include_marker, 1)
    code.write_text(text, encoding='utf-8')


def include_file(index: str, work: Path, name: str) -> str:
    marker = "<?!= include('%s'); ?>" % name
    if marker not in index:
        return index
    path = work / (name + '.html')
    if not path.exists():
        raise SystemExit('missing include file: ' + str(path))
    return index.replace(marker, path.read_text(encoding='utf-8'))


def build_frontend(work: Path, out: Path, rpc_url: str):
    out.mkdir(parents=True, exist_ok=True)
    index = (work / 'Index.html').read_text(encoding='utf-8')
    for name in ['Style']:
        index = include_file(index, work, name)

    index = index.replace(
        "window.JAYUMINTON_MEMBER_PAGE_URL = <?!= JSON.stringify(memberPageUrl || '') ?>;",
        "window.JAYUMINTON_MEMBER_PAGE_URL = window.location.origin + '/';"
    )
    index = index.replace(
        "window.JAYUMINTON_PUSH_RETURN = <?!= pushReturn || '{\"connected\":false,\"memberId\":\"\",\"memberName\":\"\"}' ?>;",
        "window.JAYUMINTON_PUSH_RETURN = {connected:false,memberId:'',memberName:''};"
    )

    marker = '<script>const IS_ADMIN = false;</script>'
    if marker not in index:
        marker = '<script>\nconst IS_ADMIN = false;\n</script>'
    if marker not in index:
        raise SystemExit('IS_ADMIN marker missing')
    bridge = BRIDGE.replace('RPC_URL_JSON', json.dumps(rpc_url))
    index = index.replace(marker, marker + '\n' + bridge + '\n' + WRAP_STYLE, 1)

    for name in ['Script','MemberSwapClient','MemberSwapAction','MemberControls','MemberSwapInbox']:
        index = include_file(index, work, name)

    if '<?!=' in index:
        raise SystemExit('Apps Script template marker remains')
    if '<iframe' in index.lower():
        raise SystemExit('iframe remains in preview page')
    if 'jayuminton-v3-cloudflare-member-preview' not in index:
        raise SystemExit('preview marker missing')
    for needle in ['memberAnywhereRequestSelected_', 'showSelfConfirm', 'showIncoming_']:
        if needle not in index:
            raise SystemExit('v3 feature missing: ' + needle)

    (out / 'index.html').write_text(index, encoding='utf-8')


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
