#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

# The Cloudflare push worker (cloudflare/user-push/worker-do.js textFor()) already
# builds the exact correct spec wording -- "대기 1순위는 {roster}님입니다..." /
# "{courtNo}번 코트가 나왔습니다. {roster}님, 코트로 입장해 주세요." -- with every
# other member's name baked in via event.rosterNames, and sends it as data.title/
# data.body on every FCM message. But JayumintonFirebaseMessagingService never read
# those two fields -- it only read type/memberId/courtNo/assignmentId and rebuilt
# its own generic, name-less strings from scratch, silently discarding the roster
# the server had already computed. Confirmed by reading the deployed
# jayuminton-user-play-v1.3.1-code131.aab: its onMessageReceived has no
# value(data, "title", ...) or value(data, "body", ...) call at all. Read the
# server-provided text first and only fall back to the generic wording if it's
# ever missing (defensive, e.g. an older server build).
for old, new in (
    ('v1.3.1-code131.aab', 'v1.3.2-code132.aab'),
    ('user-play-aab-v1.3.1.txt', 'user-play-aab-v1.3.2.txt'),
    ('VERSION="1.3.1"', 'VERSION="1.3.2"'),
    ('VERSION_CODE="131"', 'VERSION_CODE="132"'),
    ('versionCode 131', 'versionCode 132'),
    ("versionCode='131'", "versionCode='132'"),
    ("versionName '1.3.1'", "versionName '1.3.2'"),
    ("versionName='1.3.1'", "versionName='1.3.2'"),
    ('USER_APP_VERSION = "1.3.1"', 'USER_APP_VERSION = "1.3.2"'),
    ('JayumintonUserNative/1.3.1', 'JayumintonUserNative/1.3.2'),
    ('JayumintonNativeAndroid/1.3.1', 'JayumintonNativeAndroid/1.3.2'),
    ('APP_VERSION = "1.3.1"', 'APP_VERSION = "1.3.2"'),
    ('version=1.3.1', 'version=1.3.2'),
    ('version_code=131', 'version_code=132'),
):
    s = s.replace(old, new)

old_text = (
    '        String courtNo = value(data, "courtNo", "");\n'
    '        String title = court ? "코트 입장 안내" : "대기 1순위 안내";\n'
    '        String body = court\n'
    '                ? (courtNo.isEmpty() ? "코트로 들어가세요." : courtNo + "번 코트로 들어가세요.")\n'
    '                : "대기 1순위입니다. 라켓 들고 준비하세요.";\n'
)
if old_text not in s:
    raise SystemExit('v132 title/body construction anchor not found -- source has drifted')
new_text = (
    '        String courtNo = value(data, "courtNo", "");\n'
    '        // jmRosterTextFixV1: use the server-computed title/body (already includes\n'
    '        // every other member\'s name via rosterNames -- see worker-do.js textFor())\n'
    '        // instead of rebuilding a generic, name-less string here.\n'
    '        String title = value(data, "title", court ? "코트 입장 안내" : "대기 1순위 안내");\n'
    '        String body = value(data, "body", court\n'
    '                ? (courtNo.isEmpty() ? "코트로 들어가세요." : courtNo + "번 코트로 들어가세요.")\n'
    '                : "대기 1순위입니다. 라켓 들고 준비하세요.");\n'
)
s = s.replace(old_text, new_text, 1)

for required in (
    'VERSION="1.3.2"',
    'VERSION_CODE="132"',
    'jmRosterTextFixV1',
    'String title = value(data, "title", court ? "코트 입장 안내" : "대기 1순위 안내");',
    'String body = value(data, "body", court',
):
    if required not in s:
        raise SystemExit('missing v1.3.2 roster-text marker: ' + required)

path.write_text(s, encoding='utf-8')
print('Prepared v1.3.2 code132: read server-provided title/body (with roster names) instead of rebuilding generic name-less text client-side.')
