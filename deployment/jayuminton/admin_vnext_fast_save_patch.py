#!/usr/bin/env python3
"""Make admin member save return/render only the changed member.

Admin/Cloudflare only. User frontend is not modified.
"""
from pathlib import Path
import re, sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
code_path = root / 'Code.js'
script_path = root / 'Script.html'
code = code_path.read_text(encoding='utf-8')
script = script_path.read_text(encoding='utf-8')


def function_block(text, signature):
    start = text.find(signature)
    if start < 0:
        raise SystemExit('function not found: ' + signature)
    brace = text.find('{', start)
    if brace < 0:
        raise SystemExit('opening brace missing: ' + signature)
    depth = 0
    quote = None
    escape = False
    i = brace
    while i < len(text):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"`":
            quote = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return start, i + 1, text[start:i + 1]
        i += 1
    raise SystemExit('unbalanced function: ' + signature)

# Registration already appends one row. Returning a complete state snapshot makes
# the admin wait for another full spreadsheet read. Return only the row that was
# actually saved; the admin card is already rendered optimistically.
a, b, block = function_block(code, 'function addMemberUnlocked_(')
if 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1' not in block:
    if 'appendMember_(member);' not in block:
        raise SystemExit('addMemberUnlocked_ append anchor missing')
    replaced = False
    for old in ('return getPublicState();', 'return makeState_();'):
        pos = block.rfind(old)
        if pos >= 0:
            new = "return {ok: true, member: member, updatedAt: new Date().toISOString(), fastAdminSave: 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1'};"
            block = block[:pos] + new + block[pos + len(old):]
            replaced = True
            break
    if not replaced:
        raise SystemExit('addMemberUnlocked_ full-state return anchor missing')
    code = code[:a] + block + code[b:]

# Keep legacy callers compatible: if addMember() itself rebuilds a full state
# after the unlocked call, return the lightweight result directly instead.
a, b, public_block = function_block(code, 'function addMember(')
if 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1' not in public_block and 'addMemberUnlocked_' in public_block:
    # No rewrite is required when the wrapper simply returns the unlocked result.
    pass

# Admin add flow: replace the optimistic temporary card with the saved row rather
# than waiting for/rendering a full state object. Support both await and Promise
# styles used by older GAS snapshots.
a, b, add_block = function_block(script, 'async function addMember()')
if 'JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1' not in add_block:
    await_match = re.search(r"const\s+([A-Za-z_$][\w$]*)\s*=\s*await\s+server\((['\"])addMember\2", add_block)
    if await_match:
        var = await_match.group(1)
        old = 'renderState(' + var + ');'
        if old not in add_block:
            raise SystemExit('addMember await renderState anchor missing')
        new = """if (VAR && VAR.member) {
      const savedMember = normalizeMemberProfile(VAR.member);
      let savedIndex = STATE.members.findIndex(function(item) { return String(item.id) === String(savedMember.id); });
      if (savedIndex < 0 && typeof temporaryId !== 'undefined') {
        savedIndex = STATE.members.findIndex(function(item) { return String(item.id) === String(temporaryId); });
      }
      if (savedIndex >= 0) STATE.members[savedIndex] = savedMember;
      else STATE.members.push(savedMember);
      renderState();
    } else {
      renderState(VAR);
    }
    window.__JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1__ = true;""".replace('VAR', var)
        add_block = add_block.replace(old, new, 1)
    else:
        promise_match = re.search(r"\.then\(function\(([A-Za-z_$][\w$]*)\)\s*\{", add_block)
        if not promise_match or "server('addMember'" not in add_block and 'server("addMember"' not in add_block:
            raise SystemExit('addMember client response style not recognized')
        var = promise_match.group(1)
        old = 'renderState(' + var + ');'
        if old not in add_block:
            raise SystemExit('addMember promise renderState anchor missing')
        new = """if (VAR && VAR.member) {
        const savedMember = normalizeMemberProfile(VAR.member);
        let savedIndex = STATE.members.findIndex(function(item) { return String(item.id) === String(savedMember.id); });
        if (savedIndex < 0 && typeof temporaryId !== 'undefined') savedIndex = STATE.members.findIndex(function(item) { return String(item.id) === String(temporaryId); });
        if (savedIndex >= 0) STATE.members[savedIndex] = savedMember; else STATE.members.push(savedMember);
        renderState();
      } else renderState(VAR);
      window.__JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1__ = true;""".replace('VAR', var)
        add_block = add_block.replace(old, new, 1)
    script = script[:a] + add_block + script[b:]

if 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1' not in code:
    raise SystemExit('fast add-member backend marker missing')
if '__JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1__' not in script:
    raise SystemExit('fast add-member client marker missing')

code_path.write_text(code, encoding='utf-8')
script_path.write_text(script, encoding='utf-8')
print('ADMIN_VNEXT_FAST_SAVE_OK')
