#!/usr/bin/env python3
"""Admin vNext member metadata patch; preserves legacy user-web callers."""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
p = root / 'Code.js'
s = p.read_text(encoding='utf-8')

def bounds(text, name, next_name):
    start = text.find('function ' + name)
    end = text.find('\nfunction ' + next_name, start + 1)
    if start < 0 or end < 0:
        raise SystemExit(name + ' function boundary not found')
    return start, end

# Existing production may have either 8 or 9 columns. Keep the first nine
# columns unchanged and append the three admin-only metadata columns.
for width in ('8', '9'):
    s = s.replace(
        'getRange(sheet.getLastRow() + 1, 1, 1, ' + width + ')',
        'getRange(sheet.getLastRow() + 1, 1, 1, 12)'
    )
    s = s.replace(
        'getRange(2, 1, lastRow - 1, ' + width + ')\n      .clearContent();',
        'getRange(2, 1, lastRow - 1, 12)\n      .clearContent();'
    )

# Canonicalize appendMember_ by function bounds instead of formatting anchors.
a, b = bounds(s, 'appendMember_(', 'writeMembers_(')
block = s[a:b]
values_start = block.find('.setValues([[')
values_end = block.find(']]);', values_start)
if values_start < 0 or values_end < 0:
    raise SystemExit('append member values bounds not found')
canonical_values = """.setValues([[
      member.id,
      member.name,
      member.gender,
      Number(member.games) || 0,
      member.status || 'active',
      member.createdAt || new Date().toISOString(),
      member.grade || '',
      member.experience || '',
      member.isNew ? '1' : '',
      member.publicMemo || '',
      member.isSponsor ? '1' : '',
      member.bundleId || ''
    ]]);"""
block = block[:values_start] + canonical_values + block[values_end + 4:]
s = s[:a] + block + s[b:]

# Registration keeps legacy boolean isNew callers compatible while accepting
# the admin-vNext metadata object.
a, b = bounds(s, 'addMemberUnlocked_(', 'setMemberStatusUnlocked_(')
block = s[a:b]
for old in (
    'function addMemberUnlocked_(pin, name, gender, grade, experience) {',
    'function addMemberUnlocked_(pin, name, gender, grade, experience, isNew) {'
):
    block = block.replace(
        old,
        'function addMemberUnlocked_(pin, name, gender, grade, experience, extra) {',
        1
    )
legacy_normalize = "  isNew = isNew === true || String(isNew || '').toLowerCase() === 'true';"
metadata_normalize = """  extra = extra && typeof extra === 'object' ? extra : {isNew: extra};
  const isNew = Boolean(extra.isNew);
  const publicMemo = String(extra.publicMemo == null ? '' : extra.publicMemo).trim().slice(0, 40);
  const isSponsor = Boolean(extra.isSponsor);"""
if legacy_normalize in block:
    block = block.replace(legacy_normalize, metadata_normalize, 1)
elif 'const publicMemo =' not in block:
    marker = "  experience = String(experience == null ? '' : experience).trim();"
    if marker not in block:
        raise SystemExit('add member normalization anchor not found')
    block = block.replace(marker, marker + '\n' + metadata_normalize, 1)
if 'isNew: isNew' in block:
    block = block.replace(
        'isNew: isNew',
        "isNew: isNew,\n    publicMemo: publicMemo,\n    isSponsor: isSponsor,\n    bundleId: ''",
        1
    )
elif 'publicMemo: publicMemo' not in block:
    marker = '    experience: experience,'
    if marker not in block:
        raise SystemExit('new member object anchor not found')
    block = block.replace(
        marker,
        marker + "\n    isNew: isNew,\n    publicMemo: publicMemo,\n    isSponsor: isSponsor,\n    bundleId: '',",
        1
    )
s = s[:a] + block + s[b:]

a, b = bounds(s, 'addMember(', 'setMemberStatus(')
block = s[a:b]
for old in (
    'function addMember(pin, name, gender, grade, experience) {',
    'function addMember(pin, name, gender, grade, experience, isNew) {'
):
    block = block.replace(
        old,
        'function addMember(pin, name, gender, grade, experience, extra) {',
        1
    )
block = block.replace('\n        isNew\n      );', '\n        extra\n      );', 1)
if 'function addMember(pin, name, gender, grade, experience, extra)' not in block:
    raise SystemExit('add member public signature not normalized')
if '\n        extra\n      );' not in block:
    # Legacy five-argument forwarding.
    block = block.replace('\n        experience\n      );', '\n        experience,\n        extra\n      );', 1)
s = s[:a] + block + s[b:]

# Admin edit API: legacy isNew boolean is accepted as {isNew: ...}.
a, b = bounds(s, 'updateMemberProfile(', 'addMember(')
block = s[a:b]
for old in (
    'function updateMemberProfile(pin, memberId, name, gender, grade, experience) {',
    'function updateMemberProfile(pin, memberId, name, gender, grade, experience, isNew) {'
):
    block = block.replace(
        old,
        'function updateMemberProfile(pin, memberId, name, gender, grade, experience, extra) {',
        1
    )
marker = "    experience = String(experience == null ? '' : experience).trim();"
if marker not in block:
    raise SystemExit('update member normalization anchor not found')
if "extra = extra && typeof extra === 'object'" not in block:
    block = block.replace(
        marker,
        marker + "\n    extra = extra && typeof extra === 'object' ? extra : {isNew: extra};",
        1
    )
legacy_assignment = "    members[index].isNew = isNew === true || String(isNew || '').toLowerCase() === 'true';"
metadata_assignment = """    if (Object.prototype.hasOwnProperty.call(extra, 'isNew')) members[index].isNew = Boolean(extra.isNew);
    if (Object.prototype.hasOwnProperty.call(extra, 'publicMemo')) members[index].publicMemo = String(extra.publicMemo == null ? '' : extra.publicMemo).trim().slice(0, 40);
    if (Object.prototype.hasOwnProperty.call(extra, 'isSponsor')) members[index].isSponsor = Boolean(extra.isSponsor);"""
if legacy_assignment in block:
    block = block.replace(legacy_assignment, metadata_assignment, 1)
elif metadata_assignment not in block:
    marker = '    members[index].experience = experience;'
    if marker not in block:
        raise SystemExit('update member metadata fields anchor not found')
    block = block.replace(marker, marker + '\n' + metadata_assignment, 1)
s = s[:a] + block + s[b:]

# Undo must retain every appended metadata field.
undo_start = s.find('const members = state.members.map(function(member) {')
undo_end = s.find('}).filter(function(member) {', undo_start)
if undo_start < 0 or undo_end < 0:
    raise SystemExit('undo member mapping not found')
undo_chunk = s[undo_start:undo_end]
grade_start = undo_chunk.find("          grade: String(member.grade || '')")
object_end = undo_chunk.find('        };', grade_start)
if grade_start < 0 or object_end < 0:
    raise SystemExit('undo member metadata bounds not found')
canonical = """          grade: String(member.grade || '').slice(0, 12),
          experience: String(member.experience || '').slice(0, 20),
          isNew: Boolean(member.isNew),
          publicMemo: String(member.publicMemo || '').slice(0, 40),
          isSponsor: Boolean(member.isSponsor),
          bundleId: String(member.bundleId || '')
"""
undo_chunk = undo_chunk[:grade_start] + canonical + undo_chunk[object_end:]
s = s[:undo_start] + undo_chunk + s[undo_end:]

required = [
    'function addMemberUnlocked_(pin, name, gender, grade, experience, extra)',
    'function updateMemberProfile(pin, memberId, name, gender, grade, experience, extra)',
    "publicMemo: String(member.publicMemo || '').slice(0, 40)",
    "bundleId: String(member.bundleId || '')"
]
missing = [item for item in required if item not in s]
if missing:
    raise SystemExit('member metadata normalization incomplete: ' + ' | '.join(missing))

p.write_text(s, encoding='utf-8')
print('admin vNext member metadata persistence patch prepared')
