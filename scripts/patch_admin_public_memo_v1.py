#!/usr/bin/env python3
from pathlib import Path

script_path = Path('source-snapshot/current-main/Script.html')
style_path = Path('source-snapshot/current-main/Style.html')
script = script_path.read_text(encoding='utf-8')
style = style_path.read_text(encoding='utf-8')

marker = 'JAYUMINTON_ADMIN_PUBLIC_MEMO_V1'
if marker not in script:
    needle = """function memberInfoDetailHtml(member, locationOverride) {\n  normalizeMemberProfile(member);\n  const grade = String(member && member.grade || '').trim();\n  let experience = String(member && member.experience || '').trim();\n\n  experience = experience.replace(/^구력\\s*/i, '').trim();\n"""
    replacement = needle + """\n  /* JAYUMINTON_ADMIN_PUBLIC_MEMO_V1 */\n  const publicMemo = String(member && member.publicMemo || '').trim();\n  const publicMemoHtml = publicMemo\n    ? '<span class=\"member-public-memo\">' + escapeMemberInfo(publicMemo) + '</span>'\n    : '';\n"""
    if needle not in script:
        raise SystemExit('memberInfoDetailHtml anchor not found')
    script = script.replace(needle, replacement, 1)

    script = script.replace("""    if (!parts.length) return '';\n    return '<span class=\"member-info-detail\">' + parts.join(' · ') + '</span>';\n""", """    if (!parts.length) return publicMemoHtml;\n    return '<span class=\"member-info-detail\">' + parts.join(' · ') + '</span>' + publicMemoHtml;\n""", 1)

    script = script.replace("""  if (!grade && !experience) {\n    return '<span class=\"member-info-detail is-missing\">급수·구력 미입력</span>';\n  }\n""", """  if (!grade && !experience) {\n    return '<span class=\"member-info-detail is-missing\">급수·구력 미입력</span>' + publicMemoHtml;\n  }\n""", 1)

    old_final = """  return '<span class=\"member-info-detail' +\n    ((!grade || !experience) ? ' is-missing' : '') + '\">' +\n    escapeMemberInfo(gradeText) + ' · ' + escapeMemberInfo(experienceText) +\n    '</span>';\n}"""
    new_final = """  return '<span class=\"member-info-detail' +\n    ((!grade || !experience) ? ' is-missing' : '') + '\">' +\n    escapeMemberInfo(gradeText) + ' · ' + escapeMemberInfo(experienceText) +\n    '</span>' + publicMemoHtml;\n}"""
    if old_final not in script:
        raise SystemExit('memberInfoDetailHtml final return anchor not found')
    script = script.replace(old_final, new_final, 1)

style_marker = 'JAYUMINTON_ADMIN_PUBLIC_MEMO_STYLE_V1'
if style_marker not in style:
    style += """\n\n/* JAYUMINTON_ADMIN_PUBLIC_MEMO_STYLE_V1\n   User-entered public memo is shown on every admin/user member card at the same\n   compact information scale as grade/experience. */\n#adminApp .member-public-memo,\n#memberApp .member-public-memo,\n#memberApp .jm-public-memo{\n  display:block!important;\n  width:100%!important;\n  margin-top:2px!important;\n  font-size:clamp(7px,1.8vw,9px)!important;\n  line-height:1.12!important;\n  font-weight:750!important;\n  color:#536178!important;\n  text-align:center!important;\n  white-space:normal!important;\n  overflow-wrap:anywhere!important;\n  word-break:keep-all!important;\n}\n#adminApp .male .member-public-memo{color:#31598f!important}\n#adminApp .female .member-public-memo{color:#8c4569!important}\n"""

script_path.write_text(script, encoding='utf-8')
style_path.write_text(style, encoding='utf-8')
print('admin public memo patch applied')
