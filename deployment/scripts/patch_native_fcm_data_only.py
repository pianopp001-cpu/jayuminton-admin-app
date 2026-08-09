#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_NATIVE_DATA_ONLY_V1"

if marker not in s:
    old = """    targets.push({
      token: record.token,
      member: member
    });"""
    new = """    targets.push({
      token: record.token,
      member: member,
      userAgent: String(record.userAgent || '')
    });"""
    if s.count(old) != 1:
        raise SystemExit("target userAgent insertion point missing")
    s = s.replace(old, new, 1)

    old = """      target.token,
      accessToken
    );"""
    new = """      target.token,
      accessToken,
      target.userAgent
    );"""
    if s.count(old) != 1:
        raise SystemExit("request userAgent insertion point missing")
    s = s.replace(old, new, 1)

    old = "function makeWebFcmRequest_(event, member, token, accessToken) {"
    new = """/* JAYUMINTON_NATIVE_DATA_ONLY_V1
 * Native Android tokens receive data-only high-priority FCM so
 * FirebaseMessagingService always runs in the background and owns the
 * persistent notification, sound and explicit strong vibration waveform.
 * Browser tokens keep the existing web notification payload unchanged.
 */
function makeWebFcmRequest_(event, member, token, accessToken, userAgent) {
  const nativeAndroid = /JayumintonNativeAndroid\\//i.test(String(userAgent || ''));"""
    if s.count(old) != 1:
        raise SystemExit("FCM request function anchor missing")
    s = s.replace(old, new, 1)

    old = """  return {
    url: JAYUMINTON_PUSH_CONFIG.fcmUrl,"""
    new = """  if (nativeAndroid) {
    // A notification payload would be consumed by Android while the app is
    // backgrounded, skipping onMessageReceived and therefore skipping the
    // app's explicit strong vibrator waveform.
    delete payload.message.android.notification;
    delete payload.message.webpush;
  }

  return {
    url: JAYUMINTON_PUSH_CONFIG.fcmUrl,"""
    # The file may contain another request builder before this one. Insert
    # only inside makeWebFcmRequest_ by locating its block's return anchor.
    start = s.find("function makeWebFcmRequest_(")
    pos = s.find(old, start)
    if start < 0 or pos < 0:
        raise SystemExit("native data-only payload insertion point missing")
    s = s[:pos] + s[pos:].replace(old, new, 1)

for required in (
    marker,
    "userAgent: String(record.userAgent || '')",
    "target.userAgent",
    "const nativeAndroid = /JayumintonNativeAndroid",
    "delete payload.message.android.notification",
):
    if required not in s:
        raise SystemExit("missing native data-only marker: " + required)

path.write_text(s, encoding="utf-8")
print("Prepared native data-only FCM while preserving browser push payloads.")
