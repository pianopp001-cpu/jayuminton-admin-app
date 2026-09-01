#!/usr/bin/env python3
"""When the app is open (foreground), the WebView's own JS already shows a
styled in-page alert (#memberForegroundAlert) for wait1/court-assignment
events and vibrates via a native bridge (see the parallel
member-foreground-alert vibration patch). Showing the native full-screen
overlay/notification for the SAME event on top of that produced two
separate popups in a row (native "ugly" one, then the web "pretty" one).

Per explicit decision: while the app is foregrounded, show ONLY the
in-page alert; the native full-screen overlay/notification (and its
vibration) is reserved for when the app is backgrounded/killed, which is
exactly when the in-page JS cannot run at all. Admin direct messages are
untouched -- this only gates wait1_ready/court_assignment.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

field_old = '    private boolean fullScreenPromptShown;'
field_new = ('    private boolean fullScreenPromptShown;\n'
             '    public static volatile boolean isAppInForeground = false;')
if field_old not in source:
    raise SystemExit('fullScreenPromptShown field anchor missing')
source = source.replace(field_old, field_new, 1)

resume_old = '''    protected void onResume() {
        super.onResume();
        NativePushRegistrar.ensureToken(this);
        requestOverlayAlertAccessIfNeeded();
        syncSelectedMemberFromWebStorage();
    }'''
resume_new = '''    protected void onResume() {
        super.onResume();
        isAppInForeground = true;
        NativePushRegistrar.ensureToken(this);
        requestOverlayAlertAccessIfNeeded();
        syncSelectedMemberFromWebStorage();
    }

    @Override
    protected void onPause() {
        super.onPause();
        isAppInForeground = false;
    }'''
if resume_old not in source:
    raise SystemExit('onResume anchor missing')
source = source.replace(resume_old, resume_new, 1)

trigger_old = '''        String assignmentId = value(data, "assignmentId", String.valueOf(System.currentTimeMillis()));
        // Post a non-vibrating persistent/full-screen notification first.
        // Then start one explicit waveform so the notification subsystem cannot
        // replace the intended 3-group/5-group vibration with a short pattern.
        configureAlertVolumes();'''
trigger_new = '''        String assignmentId = value(data, "assignmentId", String.valueOf(System.currentTimeMillis()));
        if (!adminMessage && MainActivity.isAppInForeground) {
            NativeDeliveryReporter.report("foreground_native_alert_suppressed", type,
                    hasTargetMemberId, true, false, false, false);
            return;
        }
        // Post a non-vibrating persistent/full-screen notification first.
        // Then start one explicit waveform so the notification subsystem cannot
        // replace the intended 3-group/5-group vibration with a short pattern.
        configureAlertVolumes();'''
if trigger_old not in source:
    raise SystemExit('onMessageReceived trigger anchor missing')
source = source.replace(trigger_old, trigger_new, 1)

required = (
    'public static volatile boolean isAppInForeground = false;',
    'isAppInForeground = true;',
    'protected void onPause() {',
    'isAppInForeground = false;',
    'foreground_native_alert_suppressed',
)
for marker in required:
    if marker not in source:
        raise SystemExit('foreground-suppress patch failed: ' + marker)

path.write_text(source, encoding='utf-8')
print('FOREGROUND_SUPPRESS_V1_OK')
