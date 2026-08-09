#!/usr/bin/env python3
"""Add privacy-safe native registration and FCM send diagnostics."""

from pathlib import Path
import re
import sys


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "Code.js"
source = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_NATIVE_DELIVERY_DIAGNOSTICS_V1"

if marker not in source:
    match = re.search(r"function\s+doGet\s*\(e\)\s*\{", source)
    if not match:
        raise SystemExit("doGet function not found")
    branch = r'''
  const nativeDiagnosticRequest_ = arguments[0] || {};\n  if (String(nativeDiagnosticRequest_.parameter && nativeDiagnosticRequest_.parameter.action || '') === 'native_delivery_summary') {
    return ContentService.createTextOutput(JSON.stringify(nativeDeliverySummary_()))
      .setMimeType(ContentService.MimeType.JSON);
  }
'''
    source = source[:match.end()] + branch + source[match.end():]

    send_match = re.search(r"function\s+sendAssignmentEvent_\s*\(", source)
    if not send_match:
        raise SystemExit("sendAssignmentEvent_ function not found")
    source = source[:send_match.start()] + source[send_match.start():].replace(
        "function sendAssignmentEvent_(", "function sendAssignmentEventWithoutDiagnostics_(", 1
    )

    anchor = "function verifyPushConfiguration() {"
    if source.count(anchor) != 1:
        raise SystemExit("diagnostic helper insertion anchor not found")
    helper = r'''/* JAYUMINTON_NATIVE_DELIVERY_DIAGNOSTICS_V1 */
const JAYUMINTON_LAST_DELIVERY_DIAGNOSTIC_KEY_ = 'JAYUMINTON_LAST_DELIVERY_DIAGNOSTIC_V1';

function nativeTokenKind_(userAgent) {
  const value = String(userAgent || '');
  if (/JayumintonNativeAndroid\//i.test(value)) return 'nativeUser';
  if (/JayumintonMemberNative\//i.test(value)) return 'nativeMember';
  return 'browser';
}

function nativeDeliverySummary_() {
  const records = loadWebPushTokens_();
  const now = Date.now();
  const summary = {
    ok: true,
    generatedAt: new Date(now).toISOString(),
    totalTokens: records.length,
    nativeUserTokens: 0,
    nativeMemberTokens: 0,
    browserTokens: 0,
    newestNativeUserAgeSeconds: null,
    lastDelivery: null
  };
  let newestNativeUser = 0;
  records.forEach(function(record) {
    const kind = nativeTokenKind_(record && record.userAgent);
    if (kind === 'nativeUser') {
      summary.nativeUserTokens += 1;
      newestNativeUser = Math.max(newestNativeUser, Number(record && record.updatedAt || 0));
    } else if (kind === 'nativeMember') {
      summary.nativeMemberTokens += 1;
    } else {
      summary.browserTokens += 1;
    }
  });
  if (newestNativeUser) {
    summary.newestNativeUserAgeSeconds = Math.max(0, Math.floor((now - newestNativeUser) / 1000));
  }
  try {
    const saved = PropertiesService.getScriptProperties()
      .getProperty(JAYUMINTON_LAST_DELIVERY_DIAGNOSTIC_KEY_);
    if (saved) summary.lastDelivery = JSON.parse(saved);
  } catch (_) {}
  return summary;
}

function sendAssignmentEvent_(event) {
  const records = loadWebPushTokens_();
  const memberIds = {};
  (event && event.members || []).forEach(function(member) {
    memberIds[String(member && member.id || '')] = true;
  });
  let matchedTokens = 0;
  let nativeUserTargets = 0;
  records.forEach(function(record) {
    if (!memberIds[String(record && record.memberId || '')]) return;
    matchedTokens += 1;
    if (nativeTokenKind_(record && record.userAgent) === 'nativeUser') nativeUserTargets += 1;
  });

  let result;
  try {
    result = sendAssignmentEventWithoutDiagnostics_(event);
    PropertiesService.getScriptProperties().setProperty(
      JAYUMINTON_LAST_DELIVERY_DIAGNOSTIC_KEY_,
      JSON.stringify({
        recordedAt: new Date().toISOString(),
        eventType: String(event && event.type || ''),
        eventMemberCount: Object.keys(memberIds).filter(function(id) { return Boolean(id); }).length,
        matchedTokens: matchedTokens,
        nativeUserTargets: nativeUserTargets,
        sent: Number(result && result.sent || 0),
        failed: Number(result && result.failed || 0),
        ok: Boolean(result && result.ok)
      })
    );
    return result;
  } catch (error) {
    PropertiesService.getScriptProperties().setProperty(
      JAYUMINTON_LAST_DELIVERY_DIAGNOSTIC_KEY_,
      JSON.stringify({
        recordedAt: new Date().toISOString(),
        eventType: String(event && event.type || ''),
        eventMemberCount: Object.keys(memberIds).filter(function(id) { return Boolean(id); }).length,
        matchedTokens: matchedTokens,
        nativeUserTargets: nativeUserTargets,
        sent: 0,
        failed: matchedTokens,
        ok: false,
        exception: true
      })
    );
    throw error;
  }
}

'''
    source = source.replace(anchor, helper + anchor, 1)

required = (
    marker,
    "action || '') === 'native_delivery_summary'",
    "function sendAssignmentEventWithoutDiagnostics_(",
    "function sendAssignmentEvent_(event)",
    "nativeUserTargets",
    "newestNativeUserAgeSeconds",
)
for item in required:
    if item not in source:
        raise SystemExit("missing diagnostic marker: " + item)

path.write_text(source, encoding="utf-8")
print("Added privacy-safe native delivery diagnostics.")
