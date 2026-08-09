#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.2.0-diagnostic.apk", "v1.2.1-fresh-install.apk"),
    ("user-native-push-v1.2.0-diagnostic.txt", "user-native-push-v1.2.1.txt"),
    ('VERSION="1.2.0"', 'VERSION="1.2.1"'),
    ('VERSION_CODE="120"', 'VERSION_CODE="121"'),
    ("versionCode 120", "versionCode 121"),
    ("versionCode='120'", "versionCode='121'"),
    ("versionName '1.2.0'", "versionName '1.2.1'"),
    ("versionName='1.2.0'", "versionName='1.2.1'"),
    ('USER_APP_VERSION = "1.2.0"', 'USER_APP_VERSION = "1.2.1"'),
    ("JayumintonUserNative/1.2.0", "JayumintonUserNative/1.2.1"),
    ("JayumintonNativeAndroid/1.2.0", "JayumintonNativeAndroid/1.2.1"),
    ('APP_VERSION = "1.2.0"', 'APP_VERSION = "1.2.1"'),
    ("version=1.2.0", "version=1.2.1"),
    ("version_code=120", "version_code=121"),
    ("jayuminton_wait1_native_v120_diag", "jayuminton_wait1_native_v121"),
    ("jayuminton_court_native_v120_diag", "jayuminton_court_native_v121"),
    ("jayuminton_wait1_system_v120_diag", "jayuminton_wait1_system_v121"),
    ("jayuminton_court_system_v120_diag", "jayuminton_court_system_v121"),
):
    s = s.replace(old, new)

# Android 14+ blocks full-screen intents until this special access is enabled.
# Show one clear in-app explanation and take the user to the exact system toggle.
import_anchor = "import android.app.Activity;\n"
imports = """import android.app.Activity;
import android.app.AlertDialog;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.provider.Settings;
"""
if s.count(import_anchor) < 1:
    raise SystemExit("v121 MainActivity import anchor missing")
s = s.replace(import_anchor, imports, 1)

field_anchor = "    private WebView webView;\n"
field_replacement = field_anchor + "    private boolean fullScreenPromptShown;\n"
if s.count(field_anchor) != 1:
    raise SystemExit("v121 Activity field anchor missing")
s = s.replace(field_anchor, field_replacement, 1)

resume_old = """    protected void onResume() {
        super.onResume();
        NativePushRegistrar.ensureToken(this);
    }"""
resume_new = """    protected void onResume() {
        super.onResume();
        NativePushRegistrar.ensureToken(this);
        requestFullScreenAlertAccessIfNeeded();
        syncSelectedMemberFromWebStorage();
    }

    private void requestFullScreenAlertAccessIfNeeded() {
        if (Build.VERSION.SDK_INT < 34 || fullScreenPromptShown) return;
        NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null || manager.canUseFullScreenIntent()) return;
        fullScreenPromptShown = true;
        new AlertDialog.Builder(this)
                .setTitle("중앙 알림 권한이 필요합니다")
                .setMessage("잠금 화면·다른 앱 위에서도 대기/코트 안내와 진동 끄기 버튼을 표시하려면 다음 화면에서 '전체 화면 알림'을 허용해 주세요.")
                .setCancelable(false)
                .setPositiveButton("권한 설정 열기", (dialog, which) -> {
                    Intent intent = new Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                            Uri.parse("package:" + getPackageName()));
                    startActivity(intent);
                })
                .setNegativeButton("나중에", null)
                .show();
    }

    private void syncSelectedMemberFromWebStorage() {
        if (webView == null) return;
        webView.evaluateJavascript(
                "(function(){try{" +
                "var m=JSON.parse(localStorage.getItem('jayuminton_web_push_selected_member_v1')||'null');" +
                "if(m&&m.id&&window.NativeUserApp){window.NativeUserApp.setMember(String(m.id),String(m.name||''));return String(m.id);}" +
                "}catch(e){}return '';})()", null);
    }"""
if s.count(resume_old) != 1:
    raise SystemExit("v121 onResume anchor missing")
s = s.replace(resume_old, resume_new, 1)

# The live page can re-render after its first load. Poll only the stored explicit
# selection so typing/autofill can never silently select another member.
sync_anchor = '"if(typeof syncNativeUserPushBridge===\'function\'){syncNativeUserPushBridge();}",'
sync_replacement = (
    '"if(typeof syncNativeUserPushBridge===\'function\'){syncNativeUserPushBridge();}" +\n'
    '                    "if(!window.__JAYUMINTON_NATIVE_MEMBER_SYNC_V121__){" +\n'
    '                    "window.__JAYUMINTON_NATIVE_MEMBER_SYNC_V121__=setInterval(function(){try{" +\n'
    '                    "var m=JSON.parse(localStorage.getItem(\'jayuminton_web_push_selected_member_v1\')||\'null\');" +\n'
    '                    "if(m&&m.id&&window.NativeUserApp){window.NativeUserApp.setMember(String(m.id),String(m.name||\'\'));}" +\n'
    '                    "}catch(e){}},2000);}",'
)
if s.count(sync_anchor) != 1:
    raise SystemExit("v121 web member sync anchor missing")
s = s.replace(sync_anchor, sync_replacement, 1)

# Restore repeat-until-confirm vibration now that every stop route is installed:
# center button, notification action, tapping notification, and swipe-delete.
s = s.replace(
    'VibrationEffect.createWaveform(timings, amplitudes, -1),\n                    vibrationAttributes',
    'VibrationEffect.createWaveform(timings, amplitudes, 0),\n                    vibrationAttributes',
    1,
)
s = s.replace('vibrator.vibrate(timings, -1);', 'vibrator.vibrate(timings, 0);', 1)

# Tapping the notification itself opens the center dialog; its confirmation and
# Back button already cancel vibration. The action and swipe use the receiver.
for marker in (
    'VERSION="1.2.1"', 'VERSION_CODE="121"',
    'JayumintonNativeAndroid/1.2.1',
    'Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT',
    'manager.canUseFullScreenIntent()',
    '중앙 알림 권한이 필요합니다',
    '__JAYUMINTON_NATIVE_MEMBER_SYNC_V121__',
    "jayuminton_web_push_selected_member_v1",
    'VibrationEffect.createWaveform(timings, amplitudes, 0)',
    '"확인 · 진동 끄기"',
    '"확인하고 닫기"',
    '.setDeleteIntent(dismissPending)',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    '"대기 1순위입니다. 라켓 들고 준비하세요."',
):
    if marker not in s:
        raise SystemExit("missing native v1.2.1 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared v1.2.1 with Android full-screen access flow and strict member resync.")
