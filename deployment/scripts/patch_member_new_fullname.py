#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {count}')
    return text.replace(old, new, 1)


# Admin form: one checkbox only. No existing controls or layout are changed.
admin_path = root / 'Admin.html'
admin = admin_path.read_text(encoding='utf-8')
if 'id="newIsNew"' not in admin:
    anchor = '''      <input
        id="newExperience"
        maxlength="20"
        placeholder="구력(선택, 예: 3년)"
      >
'''
    admin = replace_once(admin, anchor, anchor + '''
      <label class="new-member-check">
        <input id="newIsNew" type="checkbox">
        신규
      </label>
''', 'admin new checkbox')
admin_path.write_text(admin, encoding='utf-8')


script_path = root / 'Script.html'
script = script_path.read_text(encoding='utf-8')

# Normalize the persisted flag without changing legacy member fields.
old = '''  member.level = grade;
  member.career = experience;
  return member;
}'''
new = '''  member.level = grade;
  member.career = experience;
  member.isNew = member.isNew === true || String(member.isNew || '').toLowerCase() === 'true';
  return member;
}'''
if 'member.isNew = member.isNew === true' not in script:
    script = replace_once(script, old, new, 'normalize isNew')

# Missing grade/experience never produces placeholder text on any card.
old = '''  if (!IS_ADMIN) {
    const parts = [];
    if (grade) parts.push(escapeMemberInfo(grade));
    if (experience) parts.push(escapeMemberInfo('구력 ' + experience));
    if (!parts.length) return '';
    return '<span class="member-info-detail">' + parts.join(' · ') + '</span>';
  }

  if (!grade && !experience) {
    return '<span class="member-info-detail is-missing">급수·구력 미입력</span>';
  }

  const gradeText = grade || '급수 미입력';
  const experienceText = experience ? '구력 ' + experience : '구력 미입력';

  return '<span class="member-info-detail' +
    ((!grade || !experience) ? ' is-missing' : '') + '">' +
    escapeMemberInfo(gradeText) + ' · ' + escapeMemberInfo(experienceText) +
    '</span>';'''
new = '''  const parts = [];
  if (grade) parts.push(escapeMemberInfo(grade));
  if (experience) parts.push(escapeMemberInfo('구력 ' + experience));
  if (!parts.length) return '';
  return '<span class="member-info-detail">' + parts.join(' · ') + '</span>';'''
if '급수·구력 미입력' in script:
    script = replace_once(script, old, new, 'hide missing profile text')

# Existing members stay compact. Only checked new members keep the complete name,
# including any parenthesized text entered by the administrator.
if 'function memberCardDisplayName(member)' not in script:
    anchor = '''function escapeMemberInfo(value) {'''
    helper = '''function memberCardDisplayName(member) {
  if (!member) return '';
  return member.isNew ? String(member.name || '').trim() : compactMemberName(member.name);
}

'''
    script = replace_once(script, anchor, helper + anchor, 'display name helper')

script = script.replace('compactMemberName(member.name)', 'memberCardDisplayName(member)')
script = script.replace(
    "return member.isNew ? String(member.name || '').trim() : memberCardDisplayName(member);",
    "return member.isNew ? String(member.name || '').trim() : compactMemberName(member.name);",
    1,
)

# The generic card previously showed the full name for everyone; apply the same rule.
old = '''    escapeMemberInfo(member.name) +
    '</span>' +'''
new = '''    escapeMemberInfo(memberCardDisplayName(member)) +
    '</span>' +'''
if old in script:
    script = replace_once(script, old, new, 'generic card display name')

# Edit form load/reset/save.
old = '''  const experience = document.getElementById('newExperience');
  const updateButton = document.getElementById('updateMemberButton');
  if (!name || !gender || !grade || !experience || !updateButton) {'''
new = '''  const experience = document.getElementById('newExperience');
  const isNew = document.getElementById('newIsNew');
  const updateButton = document.getElementById('updateMemberButton');
  if (!name || !gender || !grade || !experience || !isNew || !updateButton) {'''
if "const isNew = document.getElementById('newIsNew');" not in script:
    script = replace_once(script, old, new, 'edit checkbox lookup')
    script = replace_once(script,
        "  experience.value = String(member.experience || '');\n  updateButton.disabled = false;",
        "  experience.value = String(member.experience || '');\n  isNew.checked = member.isNew === true;\n  updateButton.disabled = false;",
        'edit checkbox value')

script = replace_once(script,
    "  const experienceInput = document.getElementById('newExperience');\n  if (nameInput) nameInput.value = '';",
    "  const experienceInput = document.getElementById('newExperience');\n  const isNewInput = document.getElementById('newIsNew');\n  if (nameInput) nameInput.value = '';",
    'cancel checkbox lookup') if "const isNewInput = document.getElementById('newIsNew');" not in script else script
if "if (isNewInput) isNewInput.checked = false;" not in script:
    script = replace_once(script,
        "  if (experienceInput) experienceInput.value = '';\n}",
        "  if (experienceInput) experienceInput.value = '';\n  if (isNewInput) isNewInput.checked = false;\n}",
        'cancel checkbox reset')

old = '''  const experience = String(document.getElementById('newExperience')?.value || '').trim();
  if (!name)'''
new = '''  const experience = String(document.getElementById('newExperience')?.value || '').trim();
  const isNew = document.getElementById('newIsNew')?.checked === true;
  if (!name)'''
if 'const isNew = document.getElementById(\'newIsNew\')?.checked === true;' not in script:
    script = replace_once(script, old, new, 'update isNew value')
    script = replace_once(script,
        "server('updateMemberProfile', [ADMIN_PIN_VALUE, targetId, name, gender, grade, experience])",
        "server('updateMemberProfile', [ADMIN_PIN_VALUE, targetId, name, gender, grade, experience, isNew])",
        'update isNew server argument')

old = '''  const experienceInput = document.getElementById('newExperience');
  const button = document.getElementById('addMemberButton');'''
new = '''  const experienceInput = document.getElementById('newExperience');
  const isNewInput = document.getElementById('newIsNew');
  const button = document.getElementById('addMemberButton');'''
if script.count("const isNewInput = document.getElementById('newIsNew');") < 2:
    script = replace_once(script, old, new, 'add checkbox lookup')
    script = replace_once(script,
        "  const experience = experienceInput.value.trim();\n\n  if (!name)",
        "  const experience = experienceInput.value.trim();\n  const isNew = isNewInput.checked === true;\n\n  if (!name)",
        'add isNew value')
    script = replace_once(script,
        "    experience: experience,\n    createdAt:",
        "    experience: experience,\n    isNew: isNew,\n    createdAt:",
        'temporary isNew')
    script = replace_once(script,
        "          grade,\n          experience\n        );",
        "          grade,\n          experience,\n          isNew\n        );",
        'add isNew server argument')
    script = replace_once(script,
        "    experienceInput.value = '';\n\n    renderActive();",
        "    experienceInput.value = '';\n    isNewInput.checked = false;\n\n    renderActive();",
        'add checkbox reset')

script_path.write_text(script, encoding='utf-8')


code_path = root / 'Code.js'
code = code_path.read_text(encoding='utf-8')

# One new backward-compatible column stores the checkbox. Existing rows default false.
if "'IS_NEW'" not in code:
    code = replace_once(code,
        "  sheet.getRange(1, 1, 1, 8).setValues([[",
        "  sheet.getRange(1, 1, 1, 9).setValues([[",
        'member header width')
    code = replace_once(code,
        "    'GRADE',\n    'EXPERIENCE'",
        "    'GRADE',\n    'EXPERIENCE',\n    'IS_NEW'",
        'member header isNew')

code = code.replace('function addMemberUnlocked_(pin, name, gender, grade, experience) {',
                    'function addMemberUnlocked_(pin, name, gender, grade, experience, isNew) {')
if "isNew = isNew === true" not in code:
    code = replace_once(code,
        "function addMemberUnlocked_(pin, name, gender, grade, experience, isNew) {\n  auth_(pin);\n\n  name = String(name == null ? '' : name).trim();\n  gender = String(gender == null ? '' : gender).trim();\n  grade = String(grade == null ? '' : grade).trim();\n  experience = String(experience == null ? '' : experience).trim();",
        "function addMemberUnlocked_(pin, name, gender, grade, experience, isNew) {\n  auth_(pin);\n\n  name = String(name == null ? '' : name).trim();\n  gender = String(gender == null ? '' : gender).trim();\n  grade = String(grade == null ? '' : grade).trim();\n  experience = String(experience == null ? '' : experience).trim();\n  isNew = isNew === true || String(isNew || '').toLowerCase() === 'true';",
        'server normalize isNew')
    code = replace_once(code,
        "    career: experience\n  };",
        "    career: experience,\n    isNew: isNew\n  };",
        'new member isNew field')

code = code.replace('function updateMemberProfile(pin, memberId, name, gender, grade, experience) {',
                    'function updateMemberProfile(pin, memberId, name, gender, grade, experience, isNew) {')
if 'members[index].isNew = isNew === true' not in code:
    code = replace_once(code,
        "    members[index].experience = experience;\n\n    writeMembers_(members);",
        "    members[index].experience = experience;\n    members[index].isNew = isNew === true || String(isNew || '').toLowerCase() === 'true';\n\n    writeMembers_(members);",
        'update member isNew')

code = code.replace('function addMember(pin, name, gender, grade, experience) {',
                    'function addMember(pin, name, gender, grade, experience, isNew) {')
if "        experience,\n        isNew\n      );" not in code:
    code = replace_once(code,
        "function addMember(pin, name, gender, grade, experience, isNew) {\n  return withDocumentLock_(\n    '멤버 등록',\n    function() {\n      return addMemberUnlocked_(\n        pin,\n        name,\n        gender,\n        grade,\n        experience\n      );",
        "function addMember(pin, name, gender, grade, experience, isNew) {\n  return withDocumentLock_(\n    '멤버 등록',\n    function() {\n      return addMemberUnlocked_(\n        pin,\n        name,\n        gender,\n        grade,\n        experience,\n        isNew\n      );",
        'public add isNew argument')

code = code.replace('.getRange(2, 1, lastRow - 1, 8)', '.getRange(2, 1, lastRow - 1, 9)')
if "isNew: row[8] === true" not in code:
    code = replace_once(code,
        "        career: String(row[7] || '')\n      };",
        "        career: String(row[7] || ''),\n        isNew: row[8] === true || String(row[8] || '').toLowerCase() === 'true'\n      };",
        'read isNew')
code = code.replace('.getRange(sheet.getLastRow() + 1, 1, 1, 8)',
                    '.getRange(sheet.getLastRow() + 1, 1, 1, 9)')
code = code.replace('.getRange(2, 1, rows.length, 8)',
                    '.getRange(2, 1, rows.length, 9)')
if "member.isNew === true" not in code:
    code = replace_once(code,
        "      member.grade || '',\n      member.experience || ''\n    ]]);",
        "      member.grade || '',\n      member.experience || '',\n      member.isNew === true\n    ]]);",
        'append isNew')
    code = replace_once(code,
        "        member.grade || '',\n        member.experience || ''\n      ];",
        "        member.grade || '',\n        member.experience || '',\n        member.isNew === true\n      ];",
        'write isNew')

code_path.write_text(code, encoding='utf-8')

checks = {
    admin_path: ['id="newIsNew"'],
    script_path: ["memberCardDisplayName(member)", "if (!parts.length) return '';", "newIsNew"],
    code_path: ["'IS_NEW'", 'lastRow - 1, 9', 'member.isNew === true'],
}
for path, needles in checks.items():
    current = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in current:
            raise SystemExit(f'verification failed in {path.name}: {needle}')

print('Patched only missing profile text, new-member checkbox, and full new-member card name.')
