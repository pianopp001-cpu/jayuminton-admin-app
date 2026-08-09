#!/usr/bin/env python3
"""Add a device-owned FCM test endpoint to the live Apps Script relay."""

from pathlib import Path
import sys


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "Code.js"
source = path.read_text(encoding="utf-8")

marker = "JAYUMINTON_NATIVE_FCM_TEST_V1"
if marker not in source:
    old = """    if (action === 'unregister_web_token') {
      return jsonOutput_(unregisterWebToken_(body));
    }

    verifyAdminSecret_(e);"""
    new = """    if (action === 'unregister_web_token') {
      return jsonOutput_(unregisterWebToken_(body));
    }
    if (action === 'test_native_push') {
      return jsonOutput_(testNativePush_(body));
    }

    verifyAdminSecret_(e);"""
    if source.count(old) != 1:
        raise SystemExit("doPost native-test insertion point missing")
    source = source.replace(old, new, 1)

    anchor = "function verifyPushConfiguration() {"
    function = r'''/* JAYUMINTON_NATIVE_FCM_TEST_V1 */
function testNativePush_(body) {
  const memberId = cleanText_(body.memberId, 200);
  const memberName = cleanText_(body.memberName, 80) || '사용자';
  const token = cleanToken_(body.token);
  if (!memberId || !token) {
    throw new Error('memberId and token are required for native push test.');
  }

  const registeredForMember = loadWebPushTokens_().some(function(record) {
    return record && String(record.memberId || '') === memberId && record.token === token;
  });
  if (!registeredForMember) {
    return {
      ok: false,
      stage: 'registration_lookup',
      status: 0,
      messageId: '',
      error: 'TOKEN_NOT_REGISTERED_FOR_MEMBER'
    };
  }

  // Possession of the device FCM token is required.  The endpoint sends only
  // a fixed diagnostic message back to that same device; callers cannot
  // choose arbitrary notification content.
  const now = Date.now();
  const event = {
    type: 'court_assignment',
    assignmentId: 'native-test-' + now,
    courtNo: '테스트',
    expectedCourtNo: '',
    members: [{id: memberId, name: memberName}]
  };
  const member = {id: memberId, name: memberName};
  const request = makeWebFcmRequest_(event, member, token, getFcmAccessToken_());
  const requestOptions = Object.assign({}, request);
  delete requestOptions.url;
  const response = UrlFetchApp.fetch(request.url, requestOptions);
  const status = response.getResponseCode();
  const responseText = response.getContentText();
  let messageId = '';
  let fcmError = '';
  try {
    const parsed = JSON.parse(responseText || '{}');
    messageId = String(parsed.name || '');
    fcmError = String(parsed.error && (parsed.error.status || parsed.error.message) || '');
  } catch (_) {}
  return {
    ok: status >= 200 && status < 300 && Boolean(messageId),
    stage: 'fcm_send',
    status: status,
    messageId: messageId,
    error: fcmError
  };
}

'''
    if source.count(anchor) != 1:
        raise SystemExit("native-test function anchor missing")
    source = source.replace(anchor, function + anchor, 1)

required = (
    marker,
    "action === 'test_native_push'",
    "function testNativePush_(body)",
    "stage: 'fcm_send'",
    "stage: 'registration_lookup'",
    'TOKEN_NOT_REGISTERED_FOR_MEMBER',
    "response.getResponseCode()",
    "messageId: messageId",
)
for item in required:
    if item not in source:
        raise SystemExit("missing native FCM test marker: " + item)

path.write_text(source, encoding="utf-8")
print("Added native device FCM test endpoint with explicit response status.")
