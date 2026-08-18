#!/usr/bin/env python3
"""Admin vNext member metadata patch. Development branch only; never deploys user production."""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
p = root / 'Code.js'
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(label + ' anchor not found')
    s = s.replace(old, new, 1)

# Complete the 8 -> 12 column migration for every write path.  The backend
# patch already widens readMembers_/writeMembers_ row output; these anchors
# cover append and clear ranges that must not remain at 8 columns.
s = s.replace(
    "getRange(sheet.getLastRow() + 1, 1, 1, 8)",
    "getRange(sheet.getLastRow() + 1, 1, 1, 12)"
)
s = s.replace(
    "getRange(2, 1, lastRow - 1, 8)\n      .clearContent();",
    "getRange(2, 1, lastRow - 1, 12)\n      .clearContent();"
)

rep(
"""      member.grade || '',
      member.experience || ''
    ]]);""",
"""      member.grade || '',
      member.experience || '',
      member.isNew ? '1' : '',
      member.publicMemo || '',
      member.isSponsor ? '1' : '',
      member.bundleId || ''
    ]]);""",
'append member metadata'
)

# Registration accepts one optional object. Existing five-argument callers stay
# compatible, while the new admin UI can send isNew/publicMemo/isSponsor.
rep(
"function addMemberUnlocked_(pin, name, gender, grade, experience) {",
"function addMemberUnlocked_(pin, name, gender, grade, experience, extra) {",
'add member unlocked signature'
)
rep(
"""  experience = String(experience == null ? '' : experience).trim();

  if (!name || name.length > 20) {""",
"""  experience = String(experience == null ? '' : experience).trim();
  extra = extra && typeof extra === 'object' ? extra : {};
  const isNew = Boolean(extra.isNew);
  const publicMemo = String(extra.publicMemo == null ? '' : extra.publicMemo).trim().slice(0, 40);
  const isSponsor = Boolean(extra.isSponsor);

  if (!name || name.length > 20) {""",
'add member metadata normalization'
)
rep(
"""    grade: grade,
    experience: experience,
    level: grade,
    career: experience
  };""",
"""    grade: grade,
    experience: experience,
    isNew: isNew,
    publicMemo: publicMemo,
    isSponsor: isSponsor,
    bundleId: '',
    level: grade,
    career: experience
  };""",
'new member metadata object'
)
rep(
"function addMember(pin, name, gender, grade, experience) {",
"function addMember(pin, name, gender, grade, experience, extra) {",
'add member public signature'
)
rep(
"""        gender,
        grade,
        experience
      );""",
"""        gender,
        grade,
        experience,
        extra
      );""",
'add member public forwarding'
)

# Admin edit API carries the same optional object and preserves placement,
# status, game count and bundle id unless explicitly changed elsewhere.
rep(
"function updateMemberProfile(pin, memberId, name, gender, grade, experience) {",
"function updateMemberProfile(pin, memberId, name, gender, grade, experience, extra) {",
'update member signature'
)
rep(
"""    experience = String(experience == null ? '' : experience).trim();

    if (!memberId) throw new Error('수정할 멤버가 없습니다.');""",
"""    experience = String(experience == null ? '' : experience).trim();
    extra = extra && typeof extra === 'object' ? extra : {};

    if (!memberId) throw new Error('수정할 멤버가 없습니다.');""",
'update member metadata normalization'
)
rep(
"""    members[index].grade = grade;
    members[index].experience = experience;

    writeMembers_(members);""",
"""    members[index].grade = grade;
    members[index].experience = experience;
    if (Object.prototype.hasOwnProperty.call(extra, 'isNew')) members[index].isNew = Boolean(extra.isNew);
    if (Object.prototype.hasOwnProperty.call(extra, 'publicMemo')) members[index].publicMemo = String(extra.publicMemo == null ? '' : extra.publicMemo).trim().slice(0, 40);
    if (Object.prototype.hasOwnProperty.call(extra, 'isSponsor')) members[index].isSponsor = Boolean(extra.isSponsor);

    writeMembers_(members);""",
'update member metadata fields'
)

# Undo must restore all vNext member metadata; otherwise one undo would silently
# erase new/sponsor/memo/bundle information.
rep(
"""          grade: String(member.grade || '').slice(0, 12),
          experience: String(member.experience || '').slice(0, 20)
        };""",
"""          grade: String(member.grade || '').slice(0, 12),
          experience: String(member.experience || '').slice(0, 20),
          isNew: Boolean(member.isNew),
          publicMemo: String(member.publicMemo || '').slice(0, 40),
          isSponsor: Boolean(member.isSponsor),
          bundleId: String(member.bundleId || '')
        };""",
'undo member metadata'
)

p.write_text(s, encoding='utf-8')
print('admin vNext member metadata persistence patch prepared')
