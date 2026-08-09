#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "Code.js"
s = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_NATIVE_FCM_CONTRACT_V2"

if marker not in s:
    # Package restriction belongs only to native Android tokens. The previous
    # snake_case field was rejected by the HTTP v1 payload validator.
    old = "        restricted_package_name: 'com.jayuminton.user',\n"
    if s.count(old) != 1:
        raise SystemExit("legacy restricted package field not found exactly once")
    s = s.replace(old, "", 1)

    old = """  if (nativeAndroid) {
    // A notification payload would be consumed by Android while the app is
    // backgrounded, skipping onMessageReceived and therefore skipping the
    // app's explicit strong vibrator waveform.
    delete payload.message.android.notification;
    delete payload.message.webpush;
  }
"""
    new = """  if (nativeAndroid) {
    /* JAYUMINTON_NATIVE_FCM_CONTRACT_V2 */
    // HTTP v1 uses lowerCamelCase. Restrict only native tokens; applying an
    // Android package restriction to browser tokens makes FCM reject them.
    payload.message.android.restrictedPackageName = 'com.jayuminton.user';
    // Data-only high-priority delivery guarantees onMessageReceived owns the
    // overlay and explicit vibrator even while another app is in front.
    delete payload.message.android.notification;
    delete payload.message.webpush;
  } else {
    // Browser/PWA registrations receive only the webpush contract.
    delete payload.message.android;
  }
"""
    if s.count(old) != 1:
        raise SystemExit("native payload branch not found exactly once")
    s = s.replace(old, new, 1)

for required in (
    marker,
    "restrictedPackageName = 'com.jayuminton.user'",
    "delete payload.message.android.notification",
    "delete payload.message.webpush",
    "delete payload.message.android;",
):
    if required not in s:
        raise SystemExit("missing FCM contract marker: " + required)

if "restricted_package_name" in s:
    raise SystemExit("legacy restricted_package_name remains")

path.write_text(s, encoding="utf-8")
print("Corrected native/browser FCM HTTP v1 payload separation.")
