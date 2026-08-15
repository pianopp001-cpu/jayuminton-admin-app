from pathlib import Path

p = Path('deployment/jayuminton/v1637-web/index.html')
s = p.read_text(encoding='utf-8')

guard = '''
<script id="v130-frame-recovery">
(() => {
  const frame = document.getElementById('courtFrame');
  if (!frame) return;
  const recover = () => {
    const cfg = window.JAYUMINTON_PUSH_SETUP_CONFIG || {};
    const target = String(cfg.memberPageUrl || frame.getAttribute('src') || '').trim();
    const current = String(frame.getAttribute('src') || '').trim();
    if (target && (!current || current === 'about:blank')) {
      frame.setAttribute('src', target);
    }
  };
  recover();
  let count = 0;
  const timer = setInterval(() => {
    recover();
    if (++count >= 20) clearInterval(timer);
  }, 500);
})();
</script>
'''

if 'id="v130-frame-recovery"' not in s:
    if '</body>' not in s:
        raise SystemExit('body close tag missing')
    s = s.replace('</body>', guard + '</body>', 1)

p.write_text(s, encoding='utf-8')

out = p.read_text(encoding='utf-8')
if '<script id="v130-frame-recovery">' not in out:
    raise SystemExit('frame guard injection failed')
if '\\n<script id="v130-frame-recovery">' in out:
    raise SystemExit('literal newline escapes detected')
print('V130_FRAME_GUARD_INJECTED')
