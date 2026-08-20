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


def replace_final_return_with_fast_member(block):
    new_return = "return {ok: true, member: member, updatedAt: new Date().toISOString(), fastAdminSave: 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1'};"
    for old in ('return getPublicState();', 'return makeState_();'):
        pos = block.rfind(old)
        if pos >= 0:
            return block[:pos] + new_return + block[pos + len(old):]
    # Current GAS snapshots may already return a compact object instead of a
    # complete state. Replace the last top-level return after appendMember_.
    append_pos = block.find('appendMember_(member);')
    if append_pos < 0:
        raise SystemExit('addMemberUnlocked_ append anchor missing')
    tail = block[append_pos:]
    matches = list(re.finditer(r'(?m)^\s*return\s+[^;]+;', tail))
    if matches:
        m = matches[-1]
        start = append_pos + m.start()
        end = append_pos + m.end()
        indent = re.match(r'\s*', block[start:end]).group(0)
        return block[:start] + indent + new_return + block[end:]
    # If the snapshot has no explicit return after append, add the compact
    # result immediately before the function closes. This keeps touch_/logging
    # statements that already occur after append intact.
    close = block.rfind('}')
    if close < 0:
        raise SystemExit('addMemberUnlocked_ closing brace missing')
    return block[:close] + "  " + new_return + "\n" + block[close:]


# Registration already appends one row. Never wait for another full spreadsheet
# state rebuild just to close the admin save overlay.
a, b, block = function_block(code, 'function addMemberUnlocked_(')
if 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1' not in block:
    block = replace_final_return_with_fast_member(block)
    code = code[:a] + block + code[b:]

# Keep legacy callers compatible: if addMember() simply returns the unlocked
# result, no wrapper rewrite is needed.
a, b, public_block = function_block(code, 'function addMember(')
if 'addMemberUnlocked_' not in public_block:
    raise SystemExit('addMember wrapper no longer calls addMemberUnlocked_')

# Admin add flow: replace the optimistic temporary card with the saved row rather
# than waiting for/rendering a full state object. Support await and Promise styles.
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
        if not promise_match or ("server('addMember'" not in add_block and 'server("addMember"' not in add_block):
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