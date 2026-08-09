#!/usr/bin/env python3
"""Add privacy-safe native device path acknowledgements to the live relay."""

from pathlib import Path
import re
import sys


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "Code.js"
source = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_NATIVE_DEVICE_ACK_V2"

if marker not in source:
    # The endpoint must stay public to the installed APK, but accepts only a
    # strict allow-list of non-PII diagnostic fields below.
    if "action === 'native_delivery_ack'" not in source:
        anchor = "    verifyAdminSecret_(e);"
        branch = """    if (action === 'native_delivery_ack') {
      return jsonOutput_(recordNativeDeliveryAck_(body));
    }

"""
        if source.count(anchor) != 1:
            raise SystemExit("native ack doPost insertion point missing")
        source = source.replace(anchor, branch + anchor, 1)

    function_anchor = "function verifyPushConfiguration() {"
    if source.count(function_anchor) != 1:
        raise SystemExit("native ack function insertion point missing")

    helper = r'''/* JAYUMINTON_NATIVE_DEVICE_ACK_V2 */
const JAYUMINTON_LAST_NATIVE_ACK_KEY_ = 'JAYUMINTON_LAST_NATIVE_ACK_V2';
const JAYUMINTON_NATIVE_ACK_HISTORY_KEY_ = 'JAYUMINTON_NATIVE_ACK_HISTORY_V2';

function nativeAckBool_(value) {
  return value === true || String(value || '').toLowerCase() === 'true';
}

function nativeAckHash_(value) {
  value = String(value || '').trim().toLowerCase();
  return /^[0-9a-f]{8,64}$/.test(value) ? value : '';
}

function nativeAckCourt_(value) {
  value = String(value || '').trim();
  return /^[0-4]$/.test(value) ? value : '';
}

function nativeAckHistory_() {
  try {
    const raw = PropertiesService.getScriptProperties()
      .getProperty(JAYUMINTON_NATIVE_ACK_HISTORY_KEY_);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.slice(-80) : [];
  } catch (_) {
    return [];
  }
}

function recordNativeDeliveryAck_(body) {
  const allowedStages = {
    member_changed: true,
    token_register_requested: true,
    token_register_http_ok: true,
    token_register_http_failed: true,
    fcm_received: true,
    member_rejected: true,
    member_accepted: true,
    notification_posted: true,
    full_screen_capability: true,
    full_screen_attempted: true,
    vibration_started: true,
    confirm_action: true,
    dismiss_action: true,
    notification_deleted: true,
    vibration_cancelled: true,
    vibration_timeout: true
  };
  const stage = cleanText_(body.stage, 60);
  if (!allowedStages[stage]) throw new Error('Invalid native ack stage.');

  const record = {
    recordedAt: new Date().toISOString(),
    stage: stage,
    appVersion: cleanText_(body.appVersion, 30),
    eventType: cleanText_(body.eventType, 40),
    courtNo: nativeAckCourt_(body.courtNo),
    targetMemberHash: nativeAckHash_(body.targetMemberHash),
    selectedMemberHash: nativeAckHash_(body.selectedMemberHash),
    selectedMemberMatches: nativeAckBool_(body.selectedMemberMatches),
    notificationPosted: nativeAckBool_(body.notificationPosted),
    fullScreenAllowed: nativeAckBool_(body.fullScreenAllowed),
    fullScreenAttempted: nativeAckBool_(body.fullScreenAttempted),
    vibrationActive: nativeAckBool_(body.vibrationActive),
    vibrationCancelled: nativeAckBool_(body.vibrationCancelled),
    source: cleanText_(body.source, 50),
    traceHash: nativeAckHash_(body.traceHash)
  };

  // Raw token, member name and raw member id are deliberately never stored.
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) throw new Error('Native ack lock busy.');
  try {
    const props = PropertiesService.getScriptProperties();
    let history = [];
    try {
      const raw = props.getProperty(JAYUMINTON_NATIVE_ACK_HISTORY_KEY_);
      const parsed = raw ? JSON.parse(raw) : [];
      if (Array.isArray(parsed)) history = parsed;
    } catch (_) {}
    history.push(record);
    history = history.slice(-80);
    props.setProperties({
      JAYUMINTON_LAST_NATIVE_ACK_V2: JSON.stringify(record),
      JAYUMINTON_NATIVE_ACK_HISTORY_V2: JSON.stringify(history)
    }, false);
  } finally {
    lock.releaseLock();
  }
  return {ok: true, stage: stage};
}

'''

    # Upgrade the earlier V1 helper in-place so there is exactly one public
    # recordNativeDeliveryAck_ implementation on the live relay.
    v1 = source.find("/* JAYUMINTON_NATIVE_DEVICE_ACK_V1 */")
    if v1 >= 0:
        end = source.find(function_anchor, v1)
        if end < 0:
            raise SystemExit("native ack V1 helper end missing")
        source = source[:v1] + helper + source[end:]
    else:
        source = source.replace(function_anchor, helper + function_anchor, 1)

    # Extend the existing privacy-safe summary with the ordered device path.
    m = re.search(r"function\s+nativeDeliverySummary_\s*\(\)\s*\{", source)
    if not m:
        raise SystemExit("nativeDeliverySummary_ function missing")
    i = m.end()
    depth = 1
    quote = None
    escape = False
    while i < len(source) and depth:
        ch = source[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
        else:
            if ch in ("'", '"', '`'):
                quote = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
        i += 1
    if depth != 0:
        raise SystemExit("nativeDeliverySummary_ parse failed")
    body_start = m.end()
    body_end = i - 1
    body = source[body_start:body_end]
    if "deviceAckHistory" not in body:
        return_pos = body.rfind("  return summary;")
        if return_pos < 0:
            raise SystemExit("nativeDeliverySummary_ return missing")
        load = """  try {
    summary.deviceAckHistory = nativeAckHistory_();
    if (summary.deviceAckHistory.length) {
      summary.lastDeviceAck = summary.deviceAckHistory[summary.deviceAckHistory.length - 1];
    }
  } catch (_) {
    summary.deviceAckHistory = [];
  }
"""
        body = body[:return_pos] + load + body[return_pos:]
        source = source[:body_start] + body + source[body_end:]

for required in (
    marker,
    "action === 'native_delivery_ack'",
    "function recordNativeDeliveryAck_(body)",
    "deviceAckHistory",
    "targetMemberHash",
    "selectedMemberHash",
    "full_screen_capability",
    "notification_posted",
    "confirm_action",
    "vibration_cancelled",
):
    if required not in source:
        raise SystemExit("missing native ack marker: " + required)

path.write_text(source, encoding="utf-8")
print("Added privacy-safe native device path acknowledgements V2.")
