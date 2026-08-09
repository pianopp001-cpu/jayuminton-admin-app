#!/usr/bin/env python3
"""Add privacy-safe native device delivery acknowledgements to live relay."""

from pathlib import Path
import sys


root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "Code.js"
source = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_NATIVE_DEVICE_ACK_V1"

if marker not in source:
    anchor = "    verifyAdminSecret_(e);"
    branch = """    if (action === 'native_delivery_ack') {
      return jsonOutput_(recordNativeDeliveryAck_(body));
    }

"""
    if source.count(anchor) != 1:
        raise SystemExit("native ack doPost insertion point missing")
    source = source.replace(anchor, branch + anchor, 1)

    function_anchor = "function verifyPushConfiguration() {"
    helper = r'''/* JAYUMINTON_NATIVE_DEVICE_ACK_V1 */
const JAYUMINTON_LAST_NATIVE_ACK_KEY_ = 'JAYUMINTON_LAST_NATIVE_ACK_V1';

function recordNativeDeliveryAck_(body) {
  const allowedStages = {
    fcm_received: true,
    member_rejected: true,
    member_accepted: true,
    notification_posted: true,
    full_screen_attempted: true,
    dismiss_action: true,
    vibration_cancelled: true
  };
  const stage = cleanText_(body.stage, 60);
  if (!allowedStages[stage]) throw new Error('Invalid native ack stage.');
  const record = {
    recordedAt: new Date().toISOString(),
    stage: stage,
    appVersion: cleanText_(body.appVersion, 30),
    eventType: cleanText_(body.eventType, 40),
    hasTargetMemberId: String(body.hasTargetMemberId || '') === 'true',
    selectedMemberMatches: String(body.selectedMemberMatches || '') === 'true',
    notificationPosted: String(body.notificationPosted || '') === 'true',
    fullScreenAllowed: String(body.fullScreenAllowed || '') === 'true',
    vibrationCancelled: String(body.vibrationCancelled || '') === 'true'
  };
  PropertiesService.getScriptProperties().setProperty(
    JAYUMINTON_LAST_NATIVE_ACK_KEY_, JSON.stringify(record)
  );
  return {ok: true, stage: stage};
}

'''
    if source.count(function_anchor) != 1:
        raise SystemExit("native ack function insertion point missing")
    source = source.replace(function_anchor, helper + function_anchor, 1)

    # Extend the already deployed privacy-safe summary when present.
    old = "    lastDelivery: null\n  };"
    new = "    lastDelivery: null,\n    lastDeviceAck: null\n  };"
    if source.count(old) != 1:
        raise SystemExit("native ack summary field insertion point missing")
    source = source.replace(old, new, 1)

    old = "  } catch (_) {}\n  return summary;\n}"
    new = """  } catch (_) {}
  try {
    const ack = PropertiesService.getScriptProperties().getProperty(JAYUMINTON_LAST_NATIVE_ACK_KEY_);
    if (ack) summary.lastDeviceAck = JSON.parse(ack);
  } catch (_) {}
  return summary;
}"""
    if source.count(old) < 1:
        raise SystemExit("native ack summary load insertion point missing")
    source = source.replace(old, new, 1)

for required in (
    marker,
    "action === 'native_delivery_ack'",
    "function recordNativeDeliveryAck_(body)",
    "lastDeviceAck",
    "vibration_cancelled",
):
    if required not in source:
        raise SystemExit("missing native ack marker: " + required)

path.write_text(source, encoding="utf-8")
print("Added privacy-safe native device delivery acknowledgements.")
