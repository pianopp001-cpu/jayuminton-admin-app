#!/usr/bin/env python3
"""v209.12: vibrate the admin APK when a new member message popup appears.

This reuses the existing member-message popup/inbox. It adds a native vibration
bridge to NativeVoice and starts the established strong 3-pulse x 8-round alert
when #jmAdminReplyPopup is shown. Confirming/opening the inbox stops it.
"""
from pathlib import Path
import sys

MARKER = "JAYUMINTON_ADMIN_MEMBER_MESSAGE_VIBRATION_V20912"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v209.12 {label} anchor mismatch: {count}")
    return text.replace(old, new, 1)


def patch_java(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    if "import android.os.VibrationEffect;" not in text:
        text = replace_once(
            text,
            "import android.os.Bundle;\n",
            "import android.os.Bundle;\nimport android.os.VibrationEffect;\nimport android.os.Vibrator;\n",
            "vibration imports",
        )

    voice_anchor = '''        @JavascriptInterface
        public boolean isSpeaking() {
            return speaking.get() || (tts != null && tts.isSpeaking());
        }
'''
    voice_new = voice_anchor + '''
        /* JAYUMINTON_ADMIN_MEMBER_MESSAGE_VIBRATION_V20912 */
        @JavascriptInterface
        public void vibrate() {
            runOnUiThread(MainActivity.this::startAdminMessageVibration);
        }

        @JavascriptInterface
        public void cancelVibration() {
            runOnUiThread(MainActivity.this::stopAdminMessageVibration);
        }
'''
    text = replace_once(text, voice_anchor, voice_new, "VoiceBridge")

    browser_anchor = "    public final class BrowserBridge {\n"
    helper = '''    private void startAdminMessageVibration() {
        Vibrator vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
        if (vibrator == null || !vibrator.hasVibrator()) return;
        ArrayList<Long> values = new ArrayList<>();
        values.add(0L);
        for (int round = 0; round < 8; round++) {
            for (int pulse = 0; pulse < 3; pulse++) {
                values.add(360L);
                if (!(round == 7 && pulse == 2)) {
                    values.add(pulse == 2 ? 520L : 150L);
                }
            }
        }
        long[] pattern = new long[values.size()];
        for (int i = 0; i < values.size(); i++) pattern[i] = values.get(i);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1));
        } else {
            vibrator.vibrate(pattern, -1);
        }
    }

    private void stopAdminMessageVibration() {
        try {
            Vibrator vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
            if (vibrator != null) vibrator.cancel();
        } catch (Exception ignored) {}
    }

'''
    text = replace_once(text, browser_anchor, helper + browser_anchor, "vibration helpers")

    destroy_old = '''        restoreAudio();
        if (webView != null) {
'''
    destroy_new = '''        restoreAudio();
        stopAdminMessageVibration();
        if (webView != null) {
'''
    text = replace_once(text, destroy_old, destroy_new, "onDestroy vibration stop")

    required = [
        MARKER,
        "public void vibrate()",
        "public void cancelVibration()",
        "VibrationEffect.createWaveform(pattern, -1)",
        "stopAdminMessageVibration();",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit("v209.12 Java marker missing: " + needle)
    path.write_text(text, encoding="utf-8")


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    hide_old = "  function hidePopup(){var p=document.getElementById('jmAdminReplyPopup');if(p)p.style.display='none';popupId='';}"
    hide_new = '''  function hidePopup(){
    /* JAYUMINTON_ADMIN_MEMBER_MESSAGE_VIBRATION_V20912 */
    try{
      if(window.NativeVoice&&typeof window.NativeVoice.cancelVibration==='function')window.NativeVoice.cancelVibration();
      else if(navigator.vibrate)navigator.vibrate(0);
    }catch(_){}
    var p=document.getElementById('jmAdminReplyPopup');if(p)p.style.display='none';popupId='';
  }'''
    text = replace_once(text, hide_old, hide_new, "hidePopup")

    show_old = "    p.querySelector('.jm-admin-reply-popup-text').textContent=(item.kind==='pair'?'':'쪽지: ')+item.text;\n    p.style.display='block';"
    show_new = '''    p.querySelector('.jm-admin-reply-popup-text').textContent=(item.kind==='pair'?'':'쪽지: ')+item.text;
    p.style.display='block';
    try{
      if(window.NativeVoice&&typeof window.NativeVoice.vibrate==='function')window.NativeVoice.vibrate();
      else if(navigator.vibrate)navigator.vibrate([360,150,360,150,360,520,360,150,360,150,360,520,360,150,360]);
    }catch(_){}'''
    text = replace_once(text, show_old, show_new, "showPopup")

    required = [
        MARKER,
        "window.NativeVoice.vibrate()",
        "window.NativeVoice.cancelVibration()",
        "jmAdminReplyPopup",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit("v209.12 HTML marker missing: " + needle)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    java_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
    html_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/assets/admin/index.html")
    patch_java(java_path)
    patch_html(html_path)
    print("ADMIN_V20912_MEMBER_MESSAGE_VIBRATION_OK")
