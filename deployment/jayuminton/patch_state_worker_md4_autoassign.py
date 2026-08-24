#!/usr/bin/env python3
from pathlib import Path
import sys


def find_function_end(text: str, start: int) -> int:
    open_pos = text.find('{', start)
    if open_pos < 0:
        raise SystemExit('autoAssignMutation opening brace missing')
    depth = 0
    quote = ''
    escape = False
    for i in range(open_pos, len(text)):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = ''
            continue
        if ch in ('"', "'", '`'):
            quote = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i + 1
    raise SystemExit('autoAssignMutation closing brace missing')


REPLACEMENT = r'''export function autoAssignMutation(input, candidateIds, destinations) {
  let state = normalizeState(input);
  const memberById = new Map(state.members.map(m => [String(m.id), m]));
  const available = uniqueIds(candidateIds, 200).filter(id => {
    const location = locationOf(state, id);
    return memberById.has(id) && (!location || location.type === 'active');
  });

  const isMale = id => {
    const gender = String(memberById.get(String(id))?.gender || '').toLowerCase();
    return gender === '남' || gender === 'male' || gender.startsWith('m');
  };

  // MD(4): when a four-person group can be completed, prefer a valid
  // doubles composition (2M+2F, 4M, or 4F).  If no such composition can be
  // completed, do not strand the remaining members: fill as many selected
  // empty positions as possible regardless of gender.
  function chooseIds(destination, remaining, free) {
    if (free <= 0 || !remaining.length) return [];
    const currentIds = [...container(state, destination)];
    const currentMale = currentIds.filter(isMale).length;
    const currentFemale = currentIds.length - currentMale;
    const men = remaining.filter(isMale);
    const women = remaining.filter(id => !isMale(id));

    const targets = [
      { male: 2, female: 2 },
      { male: 4, female: 0 },
      { male: 0, female: 4 },
    ];
    for (const target of targets) {
      const needMale = target.male - currentMale;
      const needFemale = target.female - currentFemale;
      if (needMale < 0 || needFemale < 0 || needMale + needFemale !== free) continue;
      if (men.length >= needMale && women.length >= needFemale) {
        return men.slice(0, needMale).concat(women.slice(0, needFemale));
      }
    }

    // Remainder fallback required by MD(4): even fewer than four members are
    // assigned, and a non-standard final composition is allowed.
    return remaining.slice(0, Math.min(free, remaining.length));
  }

  const remaining = [...available];
  const assigned = [];
  for (const destination of Array.isArray(destinations) ? destinations : []) {
    const free = Math.max(0, 4 - container(state, destination).length);
    const ids = chooseIds(destination, remaining, free);
    if (!ids.length) continue;
    state = moveMutation(state, ids, destination).state;
    for (const id of ids) {
      const index = remaining.indexOf(id);
      if (index >= 0) remaining.splice(index, 1);
    }
    assigned.push({ destination, memberIds: ids });
  }
  return { state, event: { type: 'auto_assigned', assigned } };
}'''


def patch(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    start = text.find('export function autoAssignMutation(')
    if start < 0:
        raise SystemExit('autoAssignMutation missing')
    end = find_function_end(text, start)
    text = text[:start] + REPLACEMENT + text[end:]
    required = [
        'MD(4): when a four-person group can be completed',
        '{ male: 2, female: 2 }',
        '{ male: 4, female: 0 }',
        '{ male: 0, female: 4 }',
        'Remainder fallback required by MD(4)',
        'remaining.slice(0, Math.min(free, remaining.length))',
    ]
    for marker in required:
        if marker not in text:
            raise SystemExit('MD4 auto-assign marker missing: ' + marker)
    path.write_text(text, encoding='utf-8')
    print('STATE_WORKER_MD4_AUTOASSIGN_OK')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: patch_state_worker_md4_autoassign.py WORKER_JS')
    patch(Path(sys.argv[1]))
