#!/usr/bin/env python3
"""Use FCM-provided Korean titles/bodies for swap and pair request/result pushes."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')
old = '''        boolean adminMessage = "admin_message".equals(type);
        String title = adminMessage
                ? value(data, "title", "관리자 메시지")
                : court ? "코트 입장 안내" : "대기 1순위 안내";
        String body = adminMessage
                ? value(data, "body", "")
                : court'''
new = '''        boolean adminMessage = "admin_message".equals(type);
        boolean interactionMessage = "swap_request".equals(type) || "swap_result".equals(type)
                || "pair_request".equals(type) || "pair_result".equals(type);
        String title = (adminMessage || interactionMessage)
                ? value(data, "title", adminMessage ? "관리자 메시지" : "요청 알림")
                : court ? "코트 입장 안내" : "대기 1순위 안내";
        String body = (adminMessage || interactionMessage)
                ? value(data, "body", "")
                : court'''
if old not in source:
    raise SystemExit('interaction push title/body anchor missing')
source = source.replace(old, new, 1)
for marker in ('"swap_request".equals(type)', '"swap_result".equals(type)', '"pair_request".equals(type)', '"pair_result".equals(type)', 'adminMessage || interactionMessage'):
    if marker not in source:
        raise SystemExit('interaction push patch failed: ' + marker)
path.write_text(source, encoding='utf-8')
print('INTERACTION_PUSH_V1_OK')
