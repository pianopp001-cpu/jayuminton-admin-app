#!/usr/bin/env python3
from pathlib import Path
import sys

MARKER = 'JAYUMINTON_ADMIN_SELF_ALERT_NATIVE_V1'

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
if MARKER in text:
    raise SystemExit(0)

text = text.replace(
    'import android.os.Bundle;\n',
    'import android.os.Bundle;\nimport android.os.VibrationEffect;\nimport android.os.Vibrator;\n',
    1,
)
text = text.replace(
    '        webView.addJavascriptInterface(new BrowserBridge(), "NativeBrowser");\n',
    '        webView.addJavascriptInterface(new BrowserBridge(), "NativeBrowser");\n'
    '        webView.addJavascriptInterface(new MemberAlertBridge(), "NativeMemberAlert"); // JAYUMINTON_ADMIN_SELF_ALERT_NATIVE_V1\n',
    1,
)
text = text.replace(
    '            webView.removeJavascriptInterface("NativeBrowser");\n',
    '            webView.removeJavascriptInterface("NativeBrowser");\n'
    '            webView.removeJavascriptInterface("NativeMemberAlert");\n'
    '            try { Vibrator v = (Vibrator) getSystemService(VIBRATOR_SERVICE); if (v != null) v.cancel(); } catch (Exception ignored) {}\n',
    1,
)
anchor = '''    public final class BrowserBridge {
        @JavascriptInterface
        public void openPwa() {
            runOnUiThread(() -> openMemberPwaInBrowser(MEMBER_PWA_URL));
        }
    }
}'''
replacement = '''    public final class BrowserBridge {
        @JavascriptInterface
        public void openPwa() {
            runOnUiThread(() -> openMemberPwaInBrowser(MEMBER_PWA_URL));
        }
    }

    public final class MemberAlertBridge {
        @JavascriptInterface
        public void vibrateThreeByEight() {
            runOnUiThread(() -> {
                try {
                    Vibrator vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
                    if (vibrator == null || !vibrator.hasVibrator()) return;
                    int pulseCount = 8 * 3;
                    long[] timings = new long[1 + pulseCount * 2 - 1];
                    int[] amplitudes = new int[timings.length];
                    timings[0] = 0L;
                    amplitudes[0] = 0;
                    int index = 1;
                    for (int group = 0; group < 8; group++) {
                        for (int pulse = 0; pulse < 3; pulse++) {
                            timings[index] = 360L;
                            amplitudes[index] = 255;
                            index++;
                            if (index < timings.length) {
                                timings[index] = pulse == 2 ? 520L : 150L;
                                amplitudes[index] = 0;
                                index++;
                            }
                        }
                    }
                    vibrator.cancel();
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        vibrator.vibrate(VibrationEffect.createWaveform(timings, amplitudes, -1));
                    } else {
                        vibrator.vibrate(timings, -1);
                    }
                } catch (Exception ignored) {}
            });
        }

        @JavascriptInterface
        public void stop() {
            runOnUiThread(() -> {
                try {
                    Vibrator vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
                    if (vibrator != null) vibrator.cancel();
                } catch (Exception ignored) {}
            });
        }
    }
}'''
if anchor not in text:
    raise SystemExit('BrowserBridge anchor missing')
text = text.replace(anchor, replacement, 1)

for needle in (MARKER, 'NativeMemberAlert', 'vibrateThreeByEight()', 'VibrationEffect.createWaveform'):
    if needle not in text:
        raise SystemExit('admin native self alert patch missing: ' + needle)
path.write_text(text, encoding='utf-8')
