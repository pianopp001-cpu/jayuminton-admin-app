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
    close = block.rfind('}')
    if close < 0:
        raise SystemExit('addMemberUnlocked_ closing brace missing')
    return block[:close] + "  " + new_return + "\n" + block[close:]


def fast_client_merge(var, indent='    '):
    lines = [
        f"if ({var} && {var}.member) {{",
        f"  const savedMember = normalizeMemberProfile({var}.member);",
        "  let savedIndex = STATE.members.findIndex(function(item) { return String(item.id) === String(savedMember.id); });",
        "  if (savedIndex < 0 && typeof temporaryId !== 'undefined') savedIndex = STATE.members.findIndex(function(item) { return String(item.id) === String(temporaryId); });",
        "  if (savedIndex >= 0) STATE.members[savedIndex] = savedMember; else STATE.members.push(savedMember);",
        "  renderState();",
        f"}} else renderState({var});",
        "window.__JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1__ = true;",
    ]
    return ('\n' + indent).join(lines)


def replace_response_render(block, var, style):
    old = 'renderState(' + var + ');'
    if old not in block:
        raise SystemExit('addMember ' + style + ' renderState anchor missing')
    line_at = block.find(old)
    line_start = block.rfind('\n', 0, line_at) + 1
    indent = re.match(r'[ \t]*', block[line_start:line_at]).group(0)
    return block.replace(old, fast_client_merge(var, indent), 1)


# Registration already appends one row. Never rebuild/return the full spreadsheet
# state just to close the admin save overlay.
a, b, block = function_block(code, 'function addMemberUnlocked_(')
if 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1' not in block:
    block = replace_final_return_with_fast_member(block)
    code = code[:a] + block + code[b:]

# Keep wrapper compatibility.
a, b, public_block = function_block(code, 'function addMember(')
if 'addMemberUnlocked_' not in public_block:
    raise SystemExit('addMember wrapper no longer calls addMemberUnlocked_')

# Admin add flow: support all live response styles used by the native/GAS and
# Cloudflare bridges: await server(), Promise.then(), and google.script.run
# withSuccessHandler(). All three merge only the saved member into the optimistic
# local STATE instead of rendering a complete server state snapshot.
a, b, add_block = function_block(script, 'async function addMember()')
if 'JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1' not in add_block:
    patched = False

    await_match = re.search(r"const\s+([A-Za-z_$][\w$]*)\s*=\s*await\s+server\((['\"])addMember\2", add_block)
    if await_match:
        add_block = replace_response_render(add_block, await_match.group(1), 'await')
        patched = True

    if not patched:
        promise_match = re.search(r"\.then\(function\(([A-Za-z_$][\w$]*)\)\s*\{", add_block)
        if promise_match and ("server('addMember'" in add_block or 'server("addMember"' in add_block):
            add_block = replace_response_render(add_block, promise_match.group(1), 'promise')
            patched = True

    if not patched:
        # Current GAS/native admin source uses google.script.run chains. The
        # Cloudflare bridge deliberately emulates this exact API with a Proxy,
        # so this is also the live Cloudflare response path.
        success_patterns = [
            r"\.withSuccessHandler\(function\s*\(\s*([A-Za-z_$][\w$]*)\s*\)\s*\{",
            r"\.withSuccessHandler\(\s*\(\s*([A-Za-z_$][\w$]*)\s*\)\s*=>\s*\{",
            r"\.withSuccessHandler\(\s*([A-Za-z_$][\w$]*)\s*=>\s*\{",
        ]
        success_match = None
        for pattern in success_patterns:
            success_match = re.search(pattern, add_block)
            if success_match:
                break
        direct_add = re.search(r"\.addMember\s*\(", add_block)
        if success_match and direct_add:
            add_block = replace_response_render(add_block, success_match.group(1), 'withSuccessHandler')
            patched = True

    if not patched:
        # Last-resort structural path: if the addMember function clearly invokes
        # addMember and has exactly one renderState(responseVar), use that response
        # variable. This avoids brittle formatting assumptions while refusing an
        # ambiguous rewrite.
        if re.search(r"(?:server\s*\([^)]*addMember|\.addMember\s*\()", add_block):
            renders = re.findall(r"renderState\(\s*([A-Za-z_$][\w$]*)\s*\);", add_block)
            unique = []
            for item in renders:
                if item not in unique:
                    unique.append(item)
            if len(unique) == 1:
                add_block = replace_response_render(add_block, unique[0], 'structural')
                patched = True

    if not patched:
        raise SystemExit('addMember client response style not recognized')

    script = script[:a] + add_block + script[b:]

if 'JAYUMINTON_ADMIN_FAST_ADD_MEMBER_V1' not in code:
    raise SystemExit('fast add-member backend marker missing')
if '__JAYUMINTON_ADMIN_FAST_SAVE_CLIENT_V1__' not in script:
    raise SystemExit('fast add-member client marker missing')

code_path.write_text(code, encoding='utf-8')
script_path.write_text(script, encoding='utf-8')
print('ADMIN_VNEXT_FAST_SAVE_OK')