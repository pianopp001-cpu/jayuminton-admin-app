#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_NATIVE_HOST_PUSH_BRIDGE_V111"

if marker not in source:
    selection = """        nameInput.value = shortName(member.name);
      } else if (data.type === 'JAYUMINTON_MEMBER_SELECTED') {
"""
    selection_replacement = """        nameInput.value = shortName(member.name);
        syncNativeHostPushMember();
      } else if (data.type === 'JAYUMINTON_MEMBER_SELECTED') {
"""
    setup = """      connectAlarm();
    } else if (data.type === 'JAYUMINTON_PUSH_DISCONNECT_REQUEST') {
"""
    setup_replacement = """      syncNativeHostPushMember();
      syncNativeHostPushPreferences(true, true);
      connectAlarm();
    } else if (data.type === 'JAYUMINTON_MEMBER_ALERT_PREFERENCE') {
      syncNativeHostPushPreferences(!!data.enabled, null);
    } else if (data.type === 'JAYUMINTON_MEMBER_VIBRATION_PREFERENCE') {
      syncNativeHostPushPreferences(null, !!data.enabled);
    } else if (data.type === 'JAYUMINTON_PUSH_DISCONNECT_REQUEST') {
      syncNativeHostPushPreferences(false, null);
"""
    anchor = """  function sendBootstrap() {
"""
    helpers = """  /* JAYUMINTON_NATIVE_HOST_PUSH_BRIDGE_V111 */
  function syncNativeHostPushMember() {
    if (!window.NativeUserApp) return;
    if (member && member.id) {
      try { window.NativeUserApp.setMember(String(member.id), String(member.name || '')); }
      catch (_) {}
    } else {
      try { window.NativeUserApp.clearMember(); } catch (_) {}
    }
  }

  function syncNativeHostPushPreferences(pushEnabled, vibrationEnabled) {
    if (!window.NativeUserApp) return;
    if (pushEnabled !== null && pushEnabled !== undefined) {
      try { window.NativeUserApp.setPushEnabled(!!pushEnabled); } catch (_) {}
    }
    if (vibrationEnabled !== null && vibrationEnabled !== undefined) {
      try { window.NativeUserApp.setVibrationEnabled(!!vibrationEnabled); } catch (_) {}
    }
  }

"""
    for needle, replacement in (
        (selection, selection_replacement),
        (setup, setup_replacement),
        (anchor, helpers + anchor),
    ):
        if needle not in source:
            raise SystemExit("native host bridge insertion point not found")
        source = source.replace(needle, replacement, 1)

for required in (
    marker,
    "window.NativeUserApp.setMember",
    "window.NativeUserApp.setPushEnabled",
    "window.NativeUserApp.setVibrationEnabled",
    "JAYUMINTON_MEMBER_VIBRATION_PREFERENCE",
):
    if required not in source:
        raise SystemExit("missing native host bridge marker: " + required)

path.write_text(source, encoding="utf-8")
print("Patched Hosting shell to register native member and push preferences directly.")
