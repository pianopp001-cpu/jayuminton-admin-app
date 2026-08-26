#!/usr/bin/env python3
"""Expose reliable 3x8 vibration and carry the v2048 temporary-team visual guard into the admin APK."""
from pathlib import Path

path = Path('app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')
text = text.replace('import android.os.Bundle;\n', 'import android.os.Bundle;\nimport android.os.VibrationEffect;\nimport android.os.Vibrator;\n', 1)
text = text.replace(
    '        webView.addJavascriptInterface(new VoiceBridge(), "NativeVoice");\n',
    '        webView.addJavascriptInterface(new VoiceBridge(), "NativeVoice");\n        webView.addJavascriptInterface(new MemberAlertBridge(), "NativeMemberAlert");\n', 1)

anchor = '''        @JavascriptInterface
        public boolean isSpeaking() {
            return speaking.get() || (tts != null && tts.isSpeaking());
        }
'''
addition = anchor + '''
        @JavascriptInterface
        public void vibrate() { runOnUiThread(MainActivity.this::startThreeByEightVibration); }

        @JavascriptInterface
        public void cancelVibration() { runOnUiThread(MainActivity.this::cancelAlertVibration); }
'''
if text.count(anchor) != 1: raise SystemExit('VoiceBridge vibration anchor mismatch')
text = text.replace(anchor, addition, 1)

browser = '    public final class BrowserBridge {\n'
member = '''    public final class MemberAlertBridge {
        @JavascriptInterface
        public void vibrateThreeByEight() { runOnUiThread(MainActivity.this::startThreeByEightVibration); }
        @JavascriptInterface
        public void stop() { runOnUiThread(MainActivity.this::cancelAlertVibration); }
    }

    private void startThreeByEightVibration() {
        Vibrator vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
        if (vibrator == null || !vibrator.hasVibrator()) return;
        ArrayList<Long> values = new ArrayList<>(); values.add(0L);
        for (int group = 0; group < 8; group++) for (int pulse = 0; pulse < 3; pulse++) {
            values.add(360L);
            if (!(group == 7 && pulse == 2)) values.add(pulse == 2 ? 520L : 150L);
        }
        long[] pattern = new long[values.size()];
        for (int i = 0; i < values.size(); i++) pattern[i] = values.get(i);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1));
        else vibrator.vibrate(pattern, -1);
    }

    private void cancelAlertVibration() {
        Vibrator vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
        if (vibrator != null) vibrator.cancel();
    }

'''
if text.count(browser) != 1: raise SystemExit('BrowserBridge anchor mismatch')
text = text.replace(browser, member + browser, 1)
for marker in ['new MemberAlertBridge(), "NativeMemberAlert"','public void vibrateThreeByEight()','public void cancelVibration()','VibrationEffect.createWaveform(pattern, -1)']:
    if marker not in text: raise SystemExit('native vibration contract missing: ' + marker)
path.write_text(text, encoding='utf-8')

admin_html = Path('app/src/main/assets/admin/index.html')
visual_js = Path(__file__).with_name('admin_temp_team_visual_v2048.js')
if admin_html.exists() and visual_js.exists():
    html = admin_html.read_text(encoding='utf-8')
    marker = '__JAYUMINTON_ADMIN_TEMP_TEAM_VISUAL_V2048__'
    while marker in html:
        pos = html.find(marker)
        start = html.rfind('<script', 0, pos)
        end = html.find('</script>', pos)
        if start < 0 or end < 0: raise SystemExit('v2048 visual marker outside script')
        html = html[:start] + html[end + len('</script>'):]
    js = visual_js.read_text(encoding='utf-8')
    tag = '<script>\n' + js + '\n</script>\n'
    html = html.replace('</body>', tag + '</body>', 1) if '</body>' in html else html + tag
    admin_html.write_text(html, encoding='utf-8')
    final_html = admin_html.read_text(encoding='utf-8')
    for required in (marker, '#d4a017', '.has-member-team.jm-temp-team-v2047.jm-temp-pair'):
        if required not in final_html: raise SystemExit('v2048 visual guard missing: ' + required)
    print('BUNDLED_ADMIN_TEMP_TEAM_VISUAL_V2048_OK')

print('NATIVE_VIBRATION_V2023_OK 3x8 finish+wait1+court')
