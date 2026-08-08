#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")

member_saved = """    member = {id: String(matches[0].id), name: String(matches[0].name)};
    saveJson(STORAGE.member, member);
    setConnecting();
"""

member_redirected = """    member = {id: String(matches[0].id), name: String(matches[0].name)};
    saveJson(STORAGE.member, member);

    // NAVER/Kakao/etc. embedded browsers cannot reliably create a Chrome FCM token.
    // Move only the notification setup to Chrome. PWA installation remains optional.
    if (androidDevice && embeddedBrowser) {
      openChromePushSetup(member);
      return;
    }

    setConnecting();
"""

helper_anchor = """  function isIOSSafari() {
"""

helper = """  function openChromePushSetup(selectedMember) {
    const target = new URL(window.location.origin + window.location.pathname);
    target.searchParams.set('source', 'chrome');
    target.searchParams.set('pushSetup', '1');
    target.searchParams.set('memberId', String(selectedMember.id || ''));
    target.searchParams.set('memberName', String(selectedMember.name || ''));

    const httpsUrl = target.toString();
    const intentPath = httpsUrl.replace(/^https:\\/\\//, '');
    const intentUrl = 'intent://' + intentPath +
      '#Intent;scheme=https;package=com.android.chrome;' +
      'S.browser_fallback_url=' + encodeURIComponent(httpsUrl) + ';end';

    setOff('Chrome으로 이동합니다. 앱 설치 없이 Chrome에서 완료를 한 번 더 눌러 알림을 허용해 주세요.');
    showToast('Chrome에서 완료를 한 번 더 눌러 주세요. 앱 설치는 필요 없습니다.');
    window.setTimeout(function() {
      window.location.href = intentUrl;
    }, 80);
  }

"""

entry_anchor = """  if ((installationEntryRequested || externalBrowserEntry) && !isStandaloneApp()) {
"""

entry = """  if (query.get('pushSetup') === '1' && androidDevice && !embeddedBrowser) {
    window.setTimeout(function() {
      setSetupCollapsed(false, false);
      setMessage('앱 설치는 필요 없습니다. 완료를 눌러 알림을 허용해 주세요.', 'success');
      showToast('이름 확인 후 완료를 눌러 알림을 연결해 주세요.');
      sendCourtMessage('JAYUMINTON_PUSH_CHROME_SETUP_READY', {
        member: member,
        message: '앱 설치 없이 알림 연결 가능'
      });
    }, 900);
  }

  if ((installationEntryRequested || externalBrowserEntry) && !isStandaloneApp()) {
"""

if "JAYUMINTON_EMBEDDED_PUSH_TO_CHROME_V1" not in source:
    if member_saved not in source:
        raise SystemExit("member registration insertion point not found")
    if helper_anchor not in source:
        raise SystemExit("Chrome handoff helper insertion point not found")
    if entry_anchor not in source:
        raise SystemExit("Chrome setup entry insertion point not found")
    source = source.replace(member_saved, member_redirected, 1)
    source = source.replace(helper_anchor, helper + helper_anchor, 1)
    source = source.replace(entry_anchor, entry, 1)
    source = source.replace(
        "  'use strict';\n",
        "  'use strict';\n  // JAYUMINTON_EMBEDDED_PUSH_TO_CHROME_V1: notification setup leaves embedded browsers without requiring PWA installation.\n",
        1,
    )

required = (
    "JAYUMINTON_EMBEDDED_PUSH_TO_CHROME_V1",
    "if (androidDevice && embeddedBrowser) {",
    "openChromePushSetup(member);",
    "target.searchParams.set('pushSetup', '1');",
    "package=com.android.chrome",
    "앱 설치는 필요 없습니다.",
)
for marker in required:
    if marker not in source:
        raise SystemExit("missing verification marker: " + marker)

path.write_text(source, encoding="utf-8")
print("Patched embedded-browser notification setup: Chrome token handoff, no PWA install requirement.")
