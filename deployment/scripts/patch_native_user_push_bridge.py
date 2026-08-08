#!/usr/bin/env python3
from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
p = root / 'Script.html'
s = p.read_text(encoding='utf-8')

s = re.sub(
    r"const MEMBER_USER_APK_URL\s*=\s*\n\s*'[^']+';",
    "const MEMBER_USER_APK_URL =\n  'https://raw.githubusercontent.com/pianopp001-cpu/jayuminton-admin-app/main/releases/jayuminton-courtstatus-v1.1.0-fresh-install.apk';",
    s,
    count=1,
)
s = re.sub(
    r"/JayumintonUserNative\\/1\\\.0\\\.0/i",
    r"/JayumintonUserNative\\/1\\\.1\\\.0/i",
    s,
    count=1,
)

marker = '/* JAYUMINTON_NATIVE_USER_PUSH_SYNC_V110 */'
if marker not in s:
    insert = s.rfind('</script>')
    if insert < 0:
        raise SystemExit('Script closing tag missing')
    bridge = r'''

/* JAYUMINTON_NATIVE_USER_PUSH_SYNC_V110 */
function syncNativeUserPushBridge() {
  if (IS_ADMIN || !window.NativeUserApp) return;
  try {
    if (typeof window.NativeUserApp.setPushEnabled === 'function') {
      window.NativeUserApp.setPushEnabled(!!memberAlertEnabled());
    }
    if (typeof window.NativeUserApp.setVibrationEnabled === 'function') {
      window.NativeUserApp.setVibrationEnabled(!!memberVibrationEnabled());
    }
    const member = currentStoredWebPushMember();
    if (member && member.id) {
      if (typeof window.NativeUserApp.setMember === 'function') {
        window.NativeUserApp.setMember(String(member.id), String(member.name || ''));
      }
    } else if (typeof window.NativeUserApp.clearMember === 'function') {
      window.NativeUserApp.clearMember();
    }
  } catch (error) {}
}

(function installNativeUserPushSyncV110() {
  if (window.__JAYUMINTON_NATIVE_USER_PUSH_SYNC_V110__) return;
  window.__JAYUMINTON_NATIVE_USER_PUSH_SYNC_V110__ = true;
  const originalRender = renderMemberSelfSettings;
  renderMemberSelfSettings = function() {
    const result = originalRender.apply(this, arguments);
    setTimeout(syncNativeUserPushBridge, 0);
    return result;
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(syncNativeUserPushBridge, 250);
    }, {once:true});
  } else {
    setTimeout(syncNativeUserPushBridge, 250);
  }
})();
'''
    s = s[:insert] + bridge + s[insert:]

checks = [
    'jayuminton-courtstatus-v1.1.0-fresh-install.apk',
    marker,
    'window.NativeUserApp.setMember',
    'window.NativeUserApp.clearMember',
    'window.NativeUserApp.setPushEnabled',
    'window.NativeUserApp.setVibrationEnabled',
]
for check in checks:
    if check not in s:
        raise SystemExit('native user push bridge verification failed: ' + check)

p.write_text(s, encoding='utf-8')
print('Patched user page for fresh-install native push APK v1.1.0 without changing CSS/design.')
