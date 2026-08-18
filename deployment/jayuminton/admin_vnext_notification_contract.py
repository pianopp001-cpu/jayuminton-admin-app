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

public_anchor = """    maxMembers: MAX_MEMBERS
  };
}

function makeState_(members, courts, waitGroups, courtStartedAt) {"""
public_replacement = """    maxMembers: MAX_MEMBERS,
    adminVnextEvents: readAdminVnextEvents_()
  };
}

function makeState_(members, courts, waitGroups, courtStartedAt) {"""
if public_anchor not in source:
    raise SystemExit('public-state anchor missing')
source = source.replace(public_anchor, public_replacement, 1)

make_anchor = """    updatedAt: new Date().toISOString(),
    maxMembers: MAX_MEMBERS
  };
}

function smartAssignSelected"""
make_replacement = """    updatedAt: new Date().toISOString(),
    maxMembers: MAX_MEMBERS,
    adminVnextEvents: readAdminVnextEvents_()
  };
}

function smartAssignSelected"""
if make_anchor not in source:
    raise SystemExit('make-state anchor missing')
source = source.replace(make_anchor, make_replacement, 1)

finish_anchor = """  writeCourts_(courts, startedAt);
  writeMembers_(members);
  touch_();

  return getPublicState();
}

function removeFromCourtUnlocked_"""
finish_replacement = """  writeCourts_(courts, startedAt);
  writeMembers_(members);
  const transitionEvents = [
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
  touch_();

  return getPublicState();
}

function removeFromCourtUnlocked_"""
if finish_anchor not in source:
    raise SystemExit('finish-court event anchor missing')
source = source.replace(finish_anchor, finish_replacement, 1)

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
