#!/usr/bin/env python3
from pathlib import Path
import re
import sys

main_path = Path(sys.argv[1])
push_path = Path(sys.argv[2])
relay_url = sys.argv[3]
internal_key = sys.argv[4]

main = main_path.read_text(encoding="utf-8")
push = push_path.read_text(encoding="utf-8")

main_marker = "JAYUMINTON_SERVER_STATE_PUSH_V1"
push_marker = "JAYUMINTON_MAIN_EVENT_RELAY_V1"

if main_marker not in main:
    anchor = "function withDocumentLock_(actionName, callback) {"
    helper = r'''/* JAYUMINTON_SERVER_STATE_PUSH_V1 */
const JAYUMINTON_STATE_PUSH_RELAY_URL_ = __RELAY_URL__;
const JAYUMINTON_STATE_PUSH_INTERNAL_KEY_ = __INTERNAL_KEY__;

function shouldCheckStatePush_(actionName) {
  /* JAYUMINTON_WAIT1_ALL_MUTATIONS_V1
   * This is intentionally unconditional. An older working production fix
   * proved that filtering by action labels misses real wait1 transitions.
   * Emission still happens only when the before/after state actually changes.
   */
  return true;
}

function captureStatePushSnapshot_() {
  return {
    members: readMembers_(),
    courts: readCourts_(),
    waitGroups: readWaitGroups_()
  };
}

function statePushMemberMap_(state) {
  const result = {};
  (state && state.members || []).forEach(function(member) {
    result[String(member.id)] = member;
  });
  return result;
}

function statePushCourtMap_(state) {
  const result = {};
  Object.keys(state && state.courts || {}).forEach(function(courtNo) {
    (state.courts[courtNo] || []).forEach(function(id) {
      result[String(id)] = String(courtNo);
    });
  });
  return result;
}

function postStatePushEvent_(event) {
  try {
    event.action = 'main_state_event';
    event.internalKey = JAYUMINTON_STATE_PUSH_INTERNAL_KEY_;
    UrlFetchApp.fetch(JAYUMINTON_STATE_PUSH_RELAY_URL_, {
      method: 'post',
      contentType: 'application/x-www-form-urlencoded; charset=utf-8',
      payload: {payload: JSON.stringify(event)},
      followRedirects: true,
      muteHttpExceptions: true
    });
  } catch (error) {
    console.error('State push failed: ' + String(error && error.message || error));
  }
}

function sendStateTransitionPushes_(before, after) {
  if (!before || !after) return;
  const members = statePushMemberMap_(after);
  const beforeWait1 = {};
  (before.waitGroups && before.waitGroups[0] || []).forEach(function(id) {
    beforeWait1[String(id)] = true;
  });
  const wait1Entrants = [];
  (after.waitGroups && after.waitGroups[0] || []).forEach(function(id) {
    id = String(id);
    if (!beforeWait1[id] && members[id]) wait1Entrants.push(members[id]);
  });
  if (wait1Entrants.length) {
    postStatePushEvent_({
      type: 'wait1_ready',
      assignmentId: 'wait1-' + Date.now() + '-' + wait1Entrants.map(function(x) { return x.id; }).join('-'),
      courtNo: '',
      expectedCourtNo: '',
      members: wait1Entrants
    });
  }

  const beforeCourts = statePushCourtMap_(before);
  const afterCourts = statePushCourtMap_(after);
  const byCourt = {};
  Object.keys(afterCourts).forEach(function(id) {
    const courtNo = afterCourts[id];
    if (beforeCourts[id] !== courtNo && members[id]) {
      if (!byCourt[courtNo]) byCourt[courtNo] = [];
      byCourt[courtNo].push(members[id]);
    }
  });
  Object.keys(byCourt).forEach(function(courtNo) {
    postStatePushEvent_({
      type: 'court_assignment',
      assignmentId: 'court-' + courtNo + '-' + Date.now() + '-' + byCourt[courtNo].map(function(x) { return x.id; }).join('-'),
      courtNo: courtNo,
      expectedCourtNo: courtNo,
      members: byCourt[courtNo]
    });
  });
}

'''.replace("__RELAY_URL__", repr(relay_url)).replace("__INTERNAL_KEY__", repr(internal_key))
    if main.count(anchor) != 1:
        raise SystemExit("main lock anchor missing")
    main = main.replace(anchor, helper + anchor, 1)

    old = """  try {
    ensureSetup_();

    const result = callback();"""
    new = """  try {
    ensureSetup_();
    const pushBefore = shouldCheckStatePush_(actionName)
      ? captureStatePushSnapshot_()
      : null;

    const result = callback();
    if (pushBefore) {
      sendStateTransitionPushes_(pushBefore, captureStatePushSnapshot_());
    }"""
    if main.count(old) != 1:
        raise SystemExit("main callback insertion point missing")
    main = main.replace(old, new, 1)

if push_marker not in push:
    anchor = "const JAYUMINTON_PUSH_CONFIG = Object.freeze({"
    declaration = (
        "/* JAYUMINTON_MAIN_EVENT_RELAY_V1 */\n"
        "const JAYUMINTON_MAIN_EVENT_KEY_ = " + repr(internal_key) + ";\n\n"
    )
    if push.count(anchor) != 1:
        raise SystemExit("push config anchor missing")
    push = push.replace(anchor, declaration + anchor, 1)

    old = """    if (action === 'test_native_push') {
      return jsonOutput_(testNativePush_(body));
    }

    verifyAdminSecret_(e);"""
    new = """    if (action === 'test_native_push') {
      return jsonOutput_(testNativePush_(body));
    }
    if (action === 'main_state_event') {
      if (String(body.internalKey || '') !== JAYUMINTON_MAIN_EVENT_KEY_) {
        throw new Error('Invalid main event key.');
      }
      return jsonOutput_(sendAssignmentEvent_(cleanEvent_(body)));
    }

    verifyAdminSecret_(e);"""
    if push.count(old) != 1:
        raise SystemExit("push handler insertion point missing")
    push = push.replace(old, new, 1)

# Restore the historical production behavior that inspected every locked
# mutation. This fixed missed wait1 transitions on 2026-08-10.
canonical_should_check = """function shouldCheckStatePush_(actionName) {
  /* JAYUMINTON_WAIT1_ALL_MUTATIONS_V1 */
  return true;
}"""
main, should_check_count = re.subn(
    r"function shouldCheckStatePush_\(actionName\) \{.*?\n\}",
    canonical_should_check,
    main,
    count=1,
    flags=re.S,
)
if should_check_count != 1:
    raise SystemExit("production state-push action detector could not be canonicalized")

# Keep the relay URL and authentication key synchronized.
main, main_url_count = re.subn(
    r"const JAYUMINTON_STATE_PUSH_RELAY_URL_ = .*?;",
    "const JAYUMINTON_STATE_PUSH_RELAY_URL_ = " + repr(relay_url) + ";",
    main,
    count=1,
)
main, main_key_count = re.subn(
    r"const JAYUMINTON_STATE_PUSH_INTERNAL_KEY_ = .*?;",
    "const JAYUMINTON_STATE_PUSH_INTERNAL_KEY_ = " + repr(internal_key) + ";",
    main,
    count=1,
)
push, push_key_count = re.subn(
    r"const JAYUMINTON_MAIN_EVENT_KEY_ = .*?;",
    "const JAYUMINTON_MAIN_EVENT_KEY_ = " + repr(internal_key) + ";",
    push,
    count=1,
)
if (main_url_count, main_key_count, push_key_count) != (1, 1, 1):
    raise SystemExit("production relay constants could not be synchronized")

canonical_handler = """    if (action === 'main_state_event') {
      if (String(body.internalKey || '') !== JAYUMINTON_MAIN_EVENT_KEY_) {
        throw new Error('Invalid main event key.');
      }
      return jsonOutput_(sendAssignmentEvent_(cleanEvent_(body)));
    }

    verifyAdminSecret_"""
push, handler_count = re.subn(
    r"    if \(action === 'main_state_event'\) \{\n.*?\n    \}\n\n    verifyAdminSecret_",
    canonical_handler,
    push,
    count=1,
    flags=re.S,
)
if handler_count != 1:
    raise SystemExit("production main_state_event handler could not be canonicalized")

# Restore the known-good wait1 contract: entering wait1 does not yet have a
# court number, so expectedCourtNo may be empty/0.
wait1_old = """  const expectedCourtNo = Number(body.expectedCourtNo);
  if ([1, 2, 3, 4].indexOf(expectedCourtNo) === -1 ||
      members.length < 1 || members.length > 4) {
    throw new Error('Wait-1 notification requires one expected court and one to four members.');
  }
  return {
    type: type,
    assignmentId: assignmentId,
    courtNo: 0,
    expectedCourtNo: expectedCourtNo,
    members: members
  };"""
wait1_new = """  /* JAYUMINTON_WAIT1_NO_COURT_REQUIRED_V1 */
  const expectedCourtNo = Number(body.expectedCourtNo) || 0;
  if (members.length < 1 || members.length > 4) {
    throw new Error('Wait-1 notification requires one to four members.');
  }
  return {
    type: type,
    assignmentId: assignmentId,
    courtNo: 0,
    expectedCourtNo: expectedCourtNo,
    members: members
  };"""
if wait1_old in push:
    push = push.replace(wait1_old, wait1_new, 1)
elif "JAYUMINTON_WAIT1_NO_COURT_REQUIRED_V1" not in push and "const expectedCourtNo = Number(body.expectedCourtNo) || 0;" not in push:
    raise SystemExit("wait1 no-court validation contract not found")

for marker in (
    main_marker,
    "JAYUMINTON_WAIT1_ALL_MUTATIONS_V1",
    "sendStateTransitionPushes_",
    "type: 'wait1_ready'",
    "type: 'court_assignment'",
    "UrlFetchApp.fetch",
):
    if marker not in main:
        raise SystemExit("missing main marker: " + marker)
for marker in (
    push_marker,
    "action === 'main_state_event'",
    "Invalid main event key",
    "sendAssignmentEvent_(cleanEvent_(body))",
    "const expectedCourtNo = Number(body.expectedCourtNo) || 0;",
):
    if marker not in push:
        raise SystemExit("missing push marker: " + marker)

main_path.write_text(main, encoding="utf-8")
push_path.write_text(push, encoding="utf-8")
print("Restored known-good wait1/court transition detection and relay validation contracts.")
