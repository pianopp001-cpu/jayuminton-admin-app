#!/usr/bin/env python3
"""Fix Bluetooth-masked court opening and generate readable marketplace exports."""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else
                 "app/src/main/java/com/jayuminton/admin/MainActivity.java")
text = java_path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_BLUETOOTH_OPENING_CARROT_EXPORT_V20914"
if MARKER in text:
    print("ADMIN_V20914_ALREADY_OK")
    raise SystemExit(0)

for required in (
    "JAYUMINTON_FULL_COURT_VOICE_MAX_MUSIC_RESTORE_V20911",
    "JAYUMINTON_REPORT_PIXELCOPY_CAPTURE_V20906",
    "boolean maximizeFullCourtFinish",
    "private void jmReportFinishCapture(boolean success)",
):
    if required not in text:
        raise SystemExit("v209.14 prerequisite missing: " + required)

constant_anchor = '''    private static final double COURT_FINISH_COMP_RATIO = 6.0;
'''
constant_new = '''    private static final double COURT_FINISH_COMP_RATIO = 6.0;
    private static final String BLUETOOTH_OPENING_CARROT_EXPORT = "''' + MARKER + '''";
    // Non-zero pre-roll is intentionally used: Bluetooth/audio HALs may discard
    // true silence and then ramp over the first spoken syllable.
    private static final double COURT_FINISH_PREROLL_SECONDS = 0.60;
    private static final double COURT_FINISH_PREROLL_DBFS = -38.0;
'''
if text.count(constant_anchor) != 1:
    raise SystemExit("v209.14 constant anchor mismatch")
text = text.replace(constant_anchor, constant_new, 1)

write_anchor = '''            // v209.10: no disproved 0.45 s warm-up padding. Playback begins with
            // the already-maximized court number in this processed WAV.
            raf.seek(0);
            raf.write(wav);
            raf.setLength(wav.length);
            return true;
'''
write_new = '''            byte[] outputWav = wav;
            if (maximizeFullCourtFinish) {
                // Prime the exact same AudioTrack/MediaPlayer session with a very
                // quiet low-frequency signal. Unlike zero PCM, Bluetooth mixers do
                // not gate it away, so their startup ramp finishes before the court
                // number. Speech samples and their mastered gain remain unchanged.
                int preFrames = Math.max(1, (int) Math.round(
                        sampleRate * COURT_FINISH_PREROLL_SECONDS));
                int preBytes = preFrames * channels * 2;
                outputWav = new byte[dataOffset + preBytes + dataSize];
                System.arraycopy(wav, 0, outputWav, 0, dataOffset);
                double preAmp = dbToLinear(COURT_FINISH_PREROLL_DBFS);
                for (int frame = 0; frame < preFrames; frame++) {
                    double fade = Math.min(1.0, frame / Math.max(1.0, sampleRate * 0.08));
                    double tail = Math.min(1.0, (preFrames - frame) /
                            Math.max(1.0, sampleRate * 0.08));
                    double sample = Math.sin(2.0 * Math.PI * 185.0 * frame / sampleRate)
                            * preAmp * fade * tail;
                    int value = (int) Math.round(sample * 32767.0);
                    for (int ch = 0; ch < channels; ch++) {
                        int off = dataOffset + (frame * channels + ch) * 2;
                        outputWav[off] = (byte) (value & 0xff);
                        outputWav[off + 1] = (byte) ((value >>> 8) & 0xff);
                    }
                }
                System.arraycopy(wav, dataOffset, outputWav,
                        dataOffset + preBytes, dataSize);
                writeLeInt(outputWav, 4, outputWav.length - 8);
                writeLeInt(outputWav, dataOffset - 4, dataSize + preBytes);
            }
            raf.seek(0);
            raf.write(outputWav);
            raf.setLength(outputWav.length);
            return true;
'''
if text.count(write_anchor) != 1:
    raise SystemExit("v209.14 WAV write anchor mismatch")
text = text.replace(write_anchor, write_new, 1)

finish_anchor = '''                jmReportSaveBitmap(jmReportBitmap, jmReportRequestedName);
'''
finish_new = '''                jmReportSaveBitmap(jmReportBitmap, jmReportRequestedName);
                jmReportSaveMarketplaceParts(jmReportBitmap, jmReportRequestedName);
'''
if text.count(finish_anchor) != 1:
    raise SystemExit("v209.14 report save anchor mismatch")
text = text.replace(finish_anchor, finish_new, 1)

helper_anchor = '''    private void jmReportFinishCapture(boolean success) {
'''
helper = r'''    private void jmReportSaveMarketplaceParts(Bitmap full, String requestedName) throws Exception {
        if (full == null || full.isRecycled()) return;
        // A very tall single image is aggressively resized by marketplace apps.
        // Save 4:5 panels as well; each panel keeps the original pixels and text.
        int panelHeight = Math.max(1, Math.round(full.getWidth() * 1.25f));
        if (full.getHeight() <= panelHeight) return;
        int count = (full.getHeight() + panelHeight - 1) / panelHeight;
        String base = requestedName == null ? "자유민턴_게임통계" : requestedName;
        if (base.toLowerCase(Locale.ROOT).endsWith(".png")) {
            base = base.substring(0, base.length() - 4);
        }
        for (int part = 0; part < count; part++) {
            int top = part * panelHeight;
            int height = Math.min(panelHeight, full.getHeight() - top);
            Bitmap panel = Bitmap.createBitmap(full, 0, top, full.getWidth(), height);
            try {
                jmReportSaveBitmap(panel, base + "_당근용_" + (part + 1) + "-" + count + ".png");
            } finally {
                if (panel != full && !panel.isRecycled()) panel.recycle();
            }
        }
    }

'''
if text.count(helper_anchor) != 1:
    raise SystemExit("v209.14 report helper anchor mismatch")
text = text.replace(helper_anchor, helper + helper_anchor, 1)

text = text.replace(
    'ok ? "전체 이미지 저장 완료" : "전체 이미지 저장 실패",',
    'ok ? "전체 이미지와 당근용 분할 이미지 저장 완료" : "전체 이미지 저장 실패",',
    1,
)

status_old = '+ ":" + FULL_COURT_VOICE_MAX_MUSIC_RESTORE + ":ready="'
status_new = '+ ":" + FULL_COURT_VOICE_MAX_MUSIC_RESTORE + ":" + BLUETOOTH_OPENING_CARROT_EXPORT + ":ready="'
if status_old not in text:
    raise SystemExit("v209.14 status anchor missing")
text = text.replace(status_old, status_new, 1)

for required in (
    MARKER,
    "COURT_FINISH_PREROLL_SECONDS = 0.60",
    "COURT_FINISH_PREROLL_DBFS = -38.0",
    "jmReportSaveMarketplaceParts(jmReportBitmap",
    '"_당근용_"',
):
    if required not in text:
        raise SystemExit("v209.14 output missing: " + required)

java_path.write_text(text, encoding="utf-8")
print("ADMIN_V20914_BLUETOOTH_OPENING_CARROT_EXPORT_OK")
