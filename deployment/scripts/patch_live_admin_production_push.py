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
  return /(배정|이동|교환|종료|대기|코트)/.test(String(actionName || ''));
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

# Keep the relay URL and authentication key synchronized even when only one
# side of a previous production deployment survived.
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

for marker in (
    main_marker, "sendStateTransitionPushes_", "type: 'wait1_ready'",
    "type: 'court_assignment'", "UrlFetchApp.fetch",
):
    if marker not in main:
        raise SystemExit("missing main marker: " + marker)
for marker in (push_marker, "action === 'main_state_event'", "Invalid main event key"):
    if marker not in push:
        raise SystemExit("missing push marker: " + marker)

main_path.write_text(main, encoding="utf-8")
push_path.write_text(push, encoding="utf-8")
print("Connected live admin state transitions to authenticated production FCM relay.")
