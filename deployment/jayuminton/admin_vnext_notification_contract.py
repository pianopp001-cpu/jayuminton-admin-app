#!/usr/bin/env python3
"""Persist admin-vNext court transition events in the state contract.

Development only. This patch does not edit or deploy the user frontend/app.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Code.js'
source = path.read_text(encoding='utf-8')

anchor = "const SHEET_PAIR_HISTORY = 'PairHistory';"
if anchor not in source:
    raise SystemExit('pair history anchor missing')

insert = r"""
const ADMIN_VNEXT_EVENTS = Object.freeze({
  COURT_FINISHED: 'COURT_FINISHED',
  COURT_PROMOTED: 'COURT_PROMOTED',
  WAIT_ONE_PROMOTED: 'WAIT_ONE_PROMOTED'
});
const ADMIN_VNEXT_EVENT_SETTING = 'ADMIN_VNEXT_EVENTS';

function buildAdminVnextEvent_(type, memberIds, courtNo) {
  return {
    eventId: Utilities.getUuid(),
    type: String(type || ''),
    memberIds: normalizeIds_(memberIds),
    courtNo: String(courtNo || ''),
    at: new Date().toISOString()
  };
}

function publishAdminVnextEvents_(events) {
  const normalized = (Array.isArray(events) ? events : [])
    .filter(function(event) {
      return event && event.type;
    })
    .slice(-3);
  setSetting_(ADMIN_VNEXT_EVENT_SETTING, JSON.stringify(normalized));
  return normalized;
}

function readAdminVnextEvents_() {
  const raw = getSetting_(ADMIN_VNEXT_EVENT_SETTING);
  if (!raw) return [];
  try {
    const events = JSON.parse(raw);
    return Array.isArray(events) ? events.slice(-3) : [];
  } catch (error) {
    return [];
  }
}
"""

if 'const ADMIN_VNEXT_EVENTS = Object.freeze({' not in source:
    source = source.replace(anchor, anchor + insert, 1)

def add_events_to_state_function_(text, function_name, next_function_name):
    start_marker = 'function ' + function_name
    end_marker = '\nfunction ' + next_function_name
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise SystemExit(function_name + ' boundary missing')
    block = text[start:end]
    if 'adminVnextEvents: readAdminVnextEvents_()' in block:
        return text
    marker = 'maxMembers: MAX_MEMBERS'
    marker_at = block.rfind(marker)
    if marker_at < 0:
        raise SystemExit(function_name + ' maxMembers anchor missing')
    absolute = start + marker_at
    return (
        text[:absolute]
        + 'maxMembers: MAX_MEMBERS,\n    adminVnextEvents: readAdminVnextEvents_()'
        + text[absolute + len(marker):]
    )

source = add_events_to_state_function_(
    source, 'getPublicState()', 'makeState_('
)
source = add_events_to_state_function_(
    source, 'makeState_(', 'smartAssignSelected('
)

finish_start = source.find('function finishCourtUnlocked_(')
finish_end = source.find('\nfunction removeFromCourtUnlocked_(', finish_start)
if finish_start < 0 or finish_end < 0:
    raise SystemExit('finish-court function boundary missing')
finish_block = source[finish_start:finish_end]
if 'buildAdminVnextEvent_(ADMIN_VNEXT_EVENTS.COURT_FINISHED' not in finish_block:
    touch_anchor = '  touch_();'
    touch_at = finish_block.rfind(touch_anchor)
    if touch_at < 0:
        raise SystemExit('finish-court touch anchor missing')
    transition_insert = """  const transitionEvents = [
    buildAdminVnextEvent_(ADMIN_VNEXT_EVENTS.COURT_FINISHED, finished, courtNo)
  ];
  if (waitOne.length) {
    transitionEvents.push(
      buildAdminVnextEvent_(ADMIN_VNEXT_EVENTS.COURT_PROMOTED, waitOne, courtNo)
    );
  }
  const nextWaitOne = (waitGroups[1] || []).slice();
  if (nextWaitOne.length) {
    transitionEvents.push(
      buildAdminVnextEvent_(ADMIN_VNEXT_EVENTS.WAIT_ONE_PROMOTED, nextWaitOne, '')
    );
  }
  publishAdminVnextEvents_(transitionEvents);
"""
    absolute = finish_start + touch_at
    source = source[:absolute] + transition_insert + source[absolute:]

required = [
    "WAIT_ONE_PROMOTED: 'WAIT_ONE_PROMOTED'",
    'function publishAdminVnextEvents_(events)',
    'function readAdminVnextEvents_()',
    'adminVnextEvents: readAdminVnextEvents_()',
    'buildAdminVnextEvent_(ADMIN_VNEXT_EVENTS.COURT_FINISHED',
    'buildAdminVnextEvent_(ADMIN_VNEXT_EVENTS.COURT_PROMOTED',
    'buildAdminVnextEvent_(ADMIN_VNEXT_EVENTS.WAIT_ONE_PROMOTED'
]
missing = [item for item in required if item not in source]
if missing:
    raise SystemExit('notification contract incomplete: ' + ' | '.join(missing))

path.write_text(source, encoding='utf-8')
print('admin vNext persistent transition event contract prepared')
