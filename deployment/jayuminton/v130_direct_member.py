#!/usr/bin/env python3
import argparse, html, json
from pathlib import Path

POST_LOGIN = r'''
function doPost(e) {
  ensureSetup_();
  const p = e && e.parameter ? e.parameter : {};
  const password = String(p.memberPassword || '');
  const requestedReturn = String(p.returnUrl || '');
  const allowedReturns = {
    'https://jayuminton-push.firebaseapp.com/': true,
    'https://jayuminton-push.web.app/': true
  };
  const returnUrl = allowedReturns[requestedReturn]
    ? requestedReturn
    : 'https://jayuminton-push.firebaseapp.com/';
  const result = verifyMemberPassword(password);
  let destination;
  if (result && result.ok && result.sessionToken) {
    destination = (ScriptApp.getService().getUrl() || '') +
      '?memberSession=' + encodeURIComponent(String(result.sessionToken));
  } else {
    destination = returnUrl + '?loginError=1&t=' + Date.now();
  }
  const safe = JSON.stringify(destination);
  return HtmlService.createHtmlOutput(
    '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<meta charset="utf-8"><title>자유민턴</title></head><body>' +
    '<p style="font-family:sans-serif;padding:24px">확인 중입니다...</p>' +
    '<script>window.top.location.replace(' + safe + ');<\/script></body></html>'
  );
}

'''

def patch(work):
    p = work / 'Code.js'
    s = p.read_text(encoding='utf-8')
    if 'function doPost(e)' not in s:
        marker = 'function include(filename) {'
        if marker not in s:
            raise SystemExit('include marker missing')
        s = s.replace(marker, POST_LOGIN + marker, 1)
    p.write_text(s, encoding='utf-8')

def build(work, out, rpc_url, hosting_url):
    out.mkdir(parents=True, exist_ok=True)
    action = html.escape(rpc_url, quote=True)
    return_url = 'https://jayuminton-push.firebaseapp.com/'
    page = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="jayuminton-v130-top-level-login" content="1">
<title>자유민턴 코트배정 현황</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:#14213d;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.wrap{{max-width:520px;margin:0 auto;padding:18px}}.hero{{margin-top:12px;padding:26px 20px;border-radius:24px;background:#102a43;color:#fff;box-shadow:0 12px 30px rgba(16,42,67,.18)}}
.hero h1{{margin:0;font-size:28px;letter-spacing:-1px}}.hero p{{margin:9px 0 0;opacity:.86;font-size:14px}}.card{{margin-top:18px;padding:22px;border-radius:22px;background:#fff;box-shadow:0 10px 28px rgba(15,23,42,.09)}}
.card h2{{margin:0 0 9px;font-size:22px}}.hint{{margin:0 0 18px;color:#64748b;font-size:14px;line-height:1.55}}input{{width:100%;height:52px;border:1px solid #cbd5e1;border-radius:14px;padding:0 15px;font-size:18px;outline:none}}
input:focus{{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12)}}button{{width:100%;height:52px;margin-top:12px;border:0;border-radius:14px;background:#2563eb;color:#fff;font-weight:800;font-size:17px}}
.err{{display:none;margin:0 0 14px;padding:12px 14px;border-radius:12px;background:#fff1f2;color:#be123c;font-size:14px}}.foot{{text-align:center;margin-top:16px;color:#94a3b8;font-size:12px}}
</style>
</head>
<body>
<div class="wrap">
  <section class="hero"><h1>자유민턴 코트배정 현황</h1><p>멤버 전용 화면</p></section>
  <section class="card">
    <div id="loginError" class="err">멤버 비밀번호가 틀렸습니다.</div>
    <h2>멤버 전용</h2>
    <p class="hint">관리자가 알려준 멤버 열람 비밀번호를 입력하세요.</p>
    <form id="memberLoginForm" method="post" action="{action}">
      <input type="hidden" name="returnUrl" value="{return_url}">
      <input id="memberPasswordInput" name="memberPassword" type="password" inputmode="numeric" autocomplete="current-password" placeholder="비밀번호" required>
      <button id="memberLoginButton" type="submit">확인</button>
    </form>
    <div class="foot">입력 후 원래 자유민턴 회원 화면으로 이동합니다.</div>
  </section>
</div>
<script>
(function(){{
  const p=new URLSearchParams(location.search||'');
  if(p.get('loginError')==='1') document.getElementById('loginError').style.display='block';
  document.getElementById('memberLoginForm').addEventListener('submit',function(){{
    const b=document.getElementById('memberLoginButton');
    b.disabled=true;b.textContent='확인 중…';
  }});
}})();
</script>
</body></html>'''
    (out / 'index.html').write_text(page, encoding='utf-8')
    (out / 'badminton.html').write_text(page, encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('patch'); a.add_argument('--work', required=True)
    b = sub.add_parser('build'); b.add_argument('--work', required=True); b.add_argument('--out', required=True); b.add_argument('--rpc-url', required=True); b.add_argument('--hosting-url', required=True)
    x = ap.parse_args(); work = Path(x.work)
    if x.cmd == 'patch': patch(work)
    else: build(work, Path(x.out), x.rpc_url, x.hosting_url)

if __name__ == '__main__':
    main()
