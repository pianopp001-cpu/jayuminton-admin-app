#!/usr/bin/env python3
import argparse, html
from pathlib import Path

POST_LOGIN = r'''
function memberV130Render_(sessionToken, loginError) {
  ensureSetup_();
  const template = HtmlService.createTemplateFromFile('Index');
  template.memberPageUrl = ScriptApp.getService().getUrl() || '';
  template.pushReturn = JSON.stringify({connected:false,memberId:'',memberName:''});
  template.memberBootstrapSession = String(sessionToken || '');
  template.memberBootstrapLoginError = Boolean(loginError);
  return template.evaluate()
    .setTitle('자유민턴 코트배정 현황')
    .addMetaTag('viewport','width=device-width,initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function doPost(e) {
  ensureSetup_();
  const p = e && e.parameter ? e.parameter : {};
  const result = verifyMemberPassword(String(p.memberPassword || ''));
  return memberV130Render_(
    result && result.ok ? String(result.sessionToken || '') : '',
    !(result && result.ok)
  );
}

'''

def patch(work):
    code = work / 'Code.js'
    s = code.read_text(encoding='utf-8')
    if 'function memberV130Render_' not in s:
        marker = 'function include(filename) {'
        if marker not in s:
            raise SystemExit('include marker missing')
        s = s.replace(marker, POST_LOGIN + marker, 1)
    # doGet must provide the extra template variables too.
    needle = "    template.pushReturn = JSON.stringify({\n      connected: Boolean(e && e.parameter && e.parameter.push === 'on'),"
    if needle in s and 'template.memberBootstrapSession' not in s.split('function doGet(e) {',1)[1].split('function include(filename)',1)[0]:
        anchor = "    template.pushReturn = JSON.stringify({\n      connected: Boolean(e && e.parameter && e.parameter.push === 'on'),\n      memberId: String(e && e.parameter && e.parameter.pushMemberId || ''),\n      memberName: String(e && e.parameter && e.parameter.pushMemberName || '')\n    });"
        replacement = anchor + "\n    template.memberBootstrapSession = '';\n    template.memberBootstrapLoginError = false;"
        if anchor not in s:
            raise SystemExit('doGet member template marker missing')
        s = s.replace(anchor, replacement, 1)
    code.write_text(s, encoding='utf-8')

    index = work / 'Index.html'
    i = index.read_text(encoding='utf-8')
    marker = '<script>\nconst IS_ADMIN = false;\n</script>'
    injected = '''<script>\nconst IS_ADMIN = false;\nconst MEMBER_BOOTSTRAP_SESSION = <?!= JSON.stringify(memberBootstrapSession || '') ?>;\nconst MEMBER_BOOTSTRAP_LOGIN_ERROR = <?!= memberBootstrapLoginError ? 'true' : 'false' ?>;\n</script>'''
    if 'MEMBER_BOOTSTRAP_SESSION' not in i:
        if marker not in i:
            raise SystemExit('Index bootstrap marker missing')
        i = i.replace(marker, injected, 1)
    index.write_text(i, encoding='utf-8')

    script = work / 'Script.html'
    js = script.read_text(encoding='utf-8')
    old = "const transferredSession = String(params.get('memberSession') || currentMemberSessionToken() || '');"
    new = "const transferredSession = String((typeof MEMBER_BOOTSTRAP_SESSION !== 'undefined' && MEMBER_BOOTSTRAP_SESSION) || params.get('memberSession') || currentMemberSessionToken() || '');"
    if old in js:
        js = js.replace(old, new, 1)
    if 'MEMBER_BOOTSTRAP_LOGIN_ERROR' not in js:
        anchor = "  if (loading) loading.classList.add('hidden');\n  if (app) app.classList.add('hidden');\n  if (login) login.classList.remove('hidden');"
        replacement = anchor + "\n  if (typeof MEMBER_BOOTSTRAP_LOGIN_ERROR !== 'undefined' && MEMBER_BOOTSTRAP_LOGIN_ERROR) {\n    setTimeout(function(){ alert('멤버 비밀번호가 틀렸습니다.'); }, 0);\n  }"
        if anchor not in js:
            raise SystemExit('initialize login fallback marker missing')
        js = js.replace(anchor, replacement, 1)
    script.write_text(js, encoding='utf-8')

def build(work, out, rpc_url, hosting_url):
    out.mkdir(parents=True, exist_ok=True)
    action = html.escape(rpc_url, quote=True)
    page = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="jayuminton-v130-top-level-login" content="2">
<title>자유민턴 코트배정 현황</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:#14213d;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.wrap{{max-width:520px;margin:0 auto;padding:18px}}.hero{{margin-top:12px;padding:26px 20px;border-radius:24px;background:#102a43;color:#fff;box-shadow:0 12px 30px rgba(16,42,67,.18)}}
.hero h1{{margin:0;font-size:28px;letter-spacing:-1px}}.hero p{{margin:9px 0 0;opacity:.86;font-size:14px}}.card{{margin-top:18px;padding:22px;border-radius:22px;background:#fff;box-shadow:0 10px 28px rgba(15,23,42,.09)}}
.card h2{{margin:0 0 9px;font-size:22px}}.hint{{margin:0 0 18px;color:#64748b;font-size:14px;line-height:1.55}}input{{width:100%;height:52px;border:1px solid #cbd5e1;border-radius:14px;padding:0 15px;font-size:18px;outline:none}}
input:focus{{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12)}}button{{width:100%;height:52px;margin-top:12px;border:0;border-radius:14px;background:#2563eb;color:#fff;font-weight:800;font-size:17px}}.foot{{text-align:center;margin-top:16px;color:#94a3b8;font-size:12px}}
</style>
</head>
<body>
<div class="wrap">
  <section class="hero"><h1>자유민턴 코트배정 현황</h1><p>멤버 전용 화면</p></section>
  <section class="card">
    <h2>멤버 전용</h2>
    <p class="hint">관리자가 알려준 멤버 열람 비밀번호를 입력하세요.</p>
    <form id="memberLoginForm" method="post" action="{action}">
      <input id="memberPasswordInput" name="memberPassword" type="password" inputmode="numeric" autocomplete="current-password" placeholder="비밀번호" required>
      <button id="memberLoginButton" type="submit">확인</button>
    </form>
    <div class="foot">확인 후 자유민턴 회원 화면으로 바로 연결됩니다.</div>
  </section>
</div>
<script>
document.getElementById('memberLoginForm').addEventListener('submit',function(){{
  const b=document.getElementById('memberLoginButton'); b.disabled=true; b.textContent='확인 중…';
}});
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
