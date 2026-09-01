#!/usr/bin/env python3
"""Admin direct messages currently have NO push notification at all --
sendMemberMessage never calls sendPush, so vibration only ever came from
in-page WebView JS detecting the popup, which requires the app to be in
the foreground with its WebView actively rendering. If the user is in a
different app (backgrounded), that JS does not reliably run, so the
phone can vibrate (if it happens to still be running) with nothing
visible to explain why, and nothing to explain why once they check.

This adds a proper Android notification for admin_message pushes,
reusing the exact same proven vibration/overlay/notification pipeline
already used for court/wait alerts, but with the REAL title/body from
the push data instead of hardcoded court/wait text.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

old = '''        String courtNo = value(data, "courtNo", "");
        String title = court ? "코트 입장 안내" : "대기 1순위 안내";
        String body = court
                ? (courtNo.isEmpty() ? "코트로 들어가세요." : courtNo + "번 코트로 들어가세요.")
                : "대기 1순위입니다. 라켓 들고 준비하세요.";
        String assignmentId = value(data, "assignmentId", String.valueOf(System.currentTimeMillis()));'''
new = '''        String courtNo = value(data, "courtNo", "");
        boolean adminMessage = "admin_message".equals(type);
        String title = adminMessage
                ? value(data, "title", "관리자 메시지")
                : court ? "코트 입장 안내" : "대기 1순위 안내";
        String body = adminMessage
                ? value(data, "body", "")
                : court
                ? (courtNo.isEmpty() ? "코트로 들어가세요." : courtNo + "번 코트로 들어가세요.")
                : "대기 1순위입니다. 라켓 들고 준비하세요.";
        String assignmentId = value(data, "assignmentId", String.valueOf(System.currentTimeMillis()));'''
if old not in source:
    raise SystemExit('admin_message push anchor missing')
source = source.replace(old, new, 1)

required = (
    'boolean adminMessage = "admin_message".equals(type);',
    'value(data, "title", "관리자 메시지")',
    'value(data, "body", "")',
)
for marker in required:
    if marker not in source:
        raise SystemExit('admin_message push patch failed: ' + marker)

path.write_text(source, encoding='utf-8')
print('ADMIN_MESSAGE_PUSH_V1_OK')
