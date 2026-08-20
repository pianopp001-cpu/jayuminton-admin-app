#!/usr/bin/env python3
"""Admin-only: avoid rereading the full spreadsheet after finishCourt.

finishCourtUnlocked_ already has members/courts/waitGroups/startedAt in memory.
Return makeState_ from those values instead of getPublicState(), which rereads all sheets.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Code.js'
text = path.read_text(encoding='utf-8')

sig = 'function finishCourtUnlocked_('
start = text.find(sig)
if start < 0:
    raise SystemExit('finishCourtUnlocked_ missing')
brace = text.find('{', start)
depth = 0
quote = None
escape = False
end = -1
for i in range(brace, len(text)):
    ch = text[i]
    if quote:
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == quote:
            quote = None
        continue
    if ch in "'\"`":
        quote = ch
    elif ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
if end < 0:
    raise SystemExit('finishCourtUnlocked_ unbalanced')
block = text[start:end]

if 'JAYUMINTON_ADMIN_FAST_FINISH_RETURN_V1' not in block:
    if 'const waitGroups = readWaitGroups_();' in block:
        block = block.replace('const waitGroups = readWaitGroups_();', 'let waitGroups = readWaitGroups_();', 1)
    elif 'let waitGroups = readWaitGroups_();' not in block:
        raise SystemExit('finish waitGroups anchor missing')

    if 'writeWaitGroups_(shifted);' in block:
        block = block.replace('writeWaitGroups_(shifted);', 'waitGroups = shifted;\n    writeWaitGroups_(waitGroups);', 1)

    pos = block.rfind('return getPublicState();')
    if pos < 0:
        raise SystemExit('finish getPublicState return missing')
    replacement = "return makeState_(members, courts, waitGroups, startedAt); // JAYUMINTON_ADMIN_FAST_FINISH_RETURN_V1"
    block = block[:pos] + replacement + block[pos + len('return getPublicState();'):]
    text = text[:start] + block + text[end:]

if 'JAYUMINTON_ADMIN_FAST_FINISH_RETURN_V1' not in text:
    raise SystemExit('fast finish marker missing')
path.write_text(text, encoding='utf-8')
print('ADMIN_FAST_FINISH_RETURN_OK')