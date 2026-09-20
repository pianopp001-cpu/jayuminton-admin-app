#!/usr/bin/env python3
"""v209.34: make the leading 'N번 코트 나왔습니다' independently audible on Bluetooth.

The old v209.19 fix measured roughly 2.1 seconds as one RMS block. A loud tail of the
sentence could therefore prevent the actually-quiet leading number/syllables from being
boosted. This patch replaces that one-gain block with short-frame upward AGC over the
opening sentence only, after the full-announcement normalization gain is chosen.
"""

from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else
            "app/src/main/java/com/jayuminton/admin/MainActivity.java")
text = path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_BLUETOOTH_OPENING_SEGMENT_AGC_V20934"

if MARKER in text:
    print("ADMIN_V20934_BLUETOOTH_OPENING_SEGMENT_AGC_ALREADY_OK")
    raise SystemExit(0)

for required in (
    "JAYUMINTON_BLUETOOTH_COURT_OPENING_PRIORITY_V20919",
    "JAYUMINTON_REPORT_SQUARE_LAYOUT_V20933",
    "COURT_FINISH_OPENING_TARGET_RMS_DBFS = -4.5",
    "COURT_FINISH_OPENING_MAX_GAIN_DB = 12.0",
    "COURT_FINISH_OPENING_SECONDS = 2.10",
    "courtOpeningBoost",
    "double finalPeak = 0.0;",
):
    if required not in text:
        raise SystemExit("v209.34 prerequisite missing: " + required)

marker_anchor = (
    '    private static final String BLUETOOTH_COURT_OPENING_PRIORITY = '
    '"JAYUMINTON_BLUETOOTH_COURT_OPENING_PRIORITY_V20919";\n'
)
if text.count(marker_anchor) != 1:
    raise SystemExit("v209.34 marker anchor mismatch: " + str(text.count(marker_anchor)))
text = text.replace(
    marker_anchor,
    marker_anchor +
    '    private static final String BLUETOOTH_OPENING_SEGMENT_AGC = "' + MARKER + '";\n',
    1,
)

# Keep the lineage constant names, but make them describe the short-window AGC.
repls = {
    "    private static final double COURT_FINISH_OPENING_TARGET_RMS_DBFS = -4.5;\n":
        "    private static final double COURT_FINISH_OPENING_TARGET_RMS_DBFS = -6.0;\n",
    "    private static final double COURT_FINISH_OPENING_MAX_GAIN_DB = 12.0;\n":
        "    private static final double COURT_FINISH_OPENING_MAX_GAIN_DB = 18.0;\n",
    "    private static final double COURT_FINISH_OPENING_SECONDS = 2.10;\n":
        "    private static final double COURT_FINISH_OPENING_SECONDS = 2.30;\n",
    "    private static final double COURT_FINISH_OPENING_RELEASE_SECONDS = 0.14;\n":
        "    private static final double COURT_FINISH_OPENING_RELEASE_SECONDS = 0.16;\n",
    "    private static final double COURT_FINISH_OPENING_ONSET_DBFS = -44.0;\n":
        "    private static final double COURT_FINISH_OPENING_ONSET_DBFS = -46.0;\n"
        "    private static final double COURT_FINISH_OPENING_FRAME_SECONDS = 0.032;\n"
        "    private static final double COURT_FINISH_OPENING_MIN_SENTENCE_SECONDS = 0.70;\n"
        "    private static final double COURT_FINISH_OPENING_PAUSE_DBFS = -38.0;\n"
        "    private static final double COURT_FINISH_OPENING_PAUSE_SECONDS = 0.13;\n",
}
for old, new in repls.items():
    if text.count(old) != 1:
        raise SystemExit("v209.34 constant anchor mismatch: " + old.strip())
    text = text.replace(old, new, 1)

# Replace the old single-RMS opening boost calculation with a true short-window pass.
start = text.find("            int courtOpeningStartSample = -1;")
end = text.find("            double finalPeak = 0.0;", start)
if start < 0 or end < 0:
    raise SystemExit("v209.34 old opening boost block boundaries missing")
old_block = text[start:end]
if "courtOpeningBoost" not in old_block or "openingSquares" not in old_block:
    raise SystemExit("v209.34 unexpected old opening boost block")

new_block = '''            // v209.34: the opening sentence is NOT one RMS bucket anymore.
            // Apply short-window upward AGC so a quiet first number/syllable is
            // corrected even when "코트 나왔습니다" later in the same sentence is loud.
            if (maximizeFullCourtFinish) {
                applyCourtOpeningSegmentAgc(pcm, makeup, sampleRate, channels);
            }

'''
text = text[:start] + new_block + text[end:]

old_loop_boost = '''                if (maximizeFullCourtFinish && courtOpeningStartSample >= 0 &&
                        i >= courtOpeningStartSample && i < courtOpeningReleaseEndSample) {
                    double localBoost = courtOpeningBoost;
                    if (i >= courtOpeningEndSample && courtOpeningReleaseEndSample > courtOpeningEndSample) {
                        double t = (i - courtOpeningEndSample) /
                                (double) (courtOpeningReleaseEndSample - courtOpeningEndSample);
                        localBoost = 1.0 + (courtOpeningBoost - 1.0) * Math.max(0.0, 1.0 - t);
                    }
                    y *= localBoost;
                }
'''
if text.count(old_loop_boost) != 1:
    raise SystemExit("v209.34 old per-sample opening boost anchor mismatch: " +
                     str(text.count(old_loop_boost)))
text = text.replace(old_loop_boost, "", 1)

helper_anchor = "    private double dbToLinear(double db) {\n"
if text.count(helper_anchor) != 1:
    raise SystemExit("v209.34 helper anchor mismatch: " + str(text.count(helper_anchor)))

helper = r'''    private void applyCourtOpeningSegmentAgc(
            float[] pcm, double makeup, int sampleRate, int channels) {
        if (pcm == null || pcm.length == 0 || !Double.isFinite(makeup) || makeup <= 0.0 ||
                sampleRate < 8000 || channels < 1) return;

        final int samplesPerSecond = Math.max(channels, sampleRate * channels);
        final int frameSamples = Math.max(
                channels,
                (int) Math.round(COURT_FINISH_OPENING_FRAME_SECONDS * samplesPerSecond));
        final int onsetSearchEnd = Math.min(pcm.length, samplesPerSecond * 2);
        final double onsetThreshold = dbToLinear(COURT_FINISH_OPENING_ONSET_DBFS);

        int openingStart = -1;
        for (int pos = 0; pos < onsetSearchEnd; pos += frameSamples) {
            int limit = Math.min(onsetSearchEnd, pos + frameSamples);
            double squares = 0.0;
            int count = 0;
            for (int i = pos; i < limit; i++) {
                double v = pcm[i] * makeup;
                squares += v * v;
                count++;
            }
            if (count > 0 && Math.sqrt(squares / count) >= onsetThreshold) {
                openingStart = pos;
                break;
            }
        }
        if (openingStart < 0) return;

        final int hardEnd = Math.min(
                pcm.length,
                openingStart + (int) Math.round(
                        COURT_FINISH_OPENING_SECONDS * samplesPerSecond));
        final int minSentenceEnd = Math.min(
                hardEnd,
                openingStart + (int) Math.round(
                        COURT_FINISH_OPENING_MIN_SENTENCE_SECONDS * samplesPerSecond));
        final double pauseThreshold = dbToLinear(COURT_FINISH_OPENING_PAUSE_DBFS);
        final int pauseFramesNeeded = Math.max(
                2,
                (int) Math.ceil(
                        COURT_FINISH_OPENING_PAUSE_SECONDS /
                        COURT_FINISH_OPENING_FRAME_SECONDS));

        // Prefer the first real pause after "N번 코트 나왔습니다".
        int openingEnd = hardEnd;
        int quietFrames = 0;
        for (int pos = openingStart; pos < hardEnd; pos += frameSamples) {
            int limit = Math.min(hardEnd, pos + frameSamples);
            double squares = 0.0;
            int count = 0;
            for (int i = pos; i < limit; i++) {
                double v = pcm[i] * makeup;
                squares += v * v;
                count++;
            }
            double rms = count > 0 ? Math.sqrt(squares / count) : 0.0;
            if (pos >= minSentenceEnd && rms < pauseThreshold) {
                quietFrames++;
                if (quietFrames >= pauseFramesNeeded) {
                    openingEnd = Math.max(
                            minSentenceEnd,
                            pos - (quietFrames - 1) * frameSamples);
                    break;
                }
            } else {
                quietFrames = 0;
            }
        }
        if (openingEnd <= openingStart) return;

        final double targetRms = dbToLinear(COURT_FINISH_OPENING_TARGET_RMS_DBFS);
        final double maxGain = dbToLinear(COURT_FINISH_OPENING_MAX_GAIN_DB);
        final double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
        final int releaseSamples = Math.max(
                frameSamples,
                (int) Math.round(
                        COURT_FINISH_OPENING_RELEASE_SECONDS * samplesPerSecond));

        double smoothedGain = 1.0;
        for (int pos = openingStart; pos < openingEnd; pos += frameSamples) {
            int limit = Math.min(openingEnd, pos + frameSamples);
            double squares = 0.0;
            double peak = 0.0;
            int count = 0;
            for (int i = pos; i < limit; i++) {
                double v = pcm[i] * makeup;
                squares += v * v;
                peak = Math.max(peak, Math.abs(v));
                count++;
            }
            if (count <= 0) continue;

            double rms = Math.sqrt(squares / count);
            double desiredGain = 1.0;
            // Never lift true silence/noise. Only voiced frames receive upward gain.
            if (rms >= onsetThreshold && rms > 1.0e-9) {
                desiredGain = Math.max(1.0, Math.min(maxGain, targetRms / rms));
                if (peak > 1.0e-9) {
                    desiredGain = Math.min(desiredGain, ceiling / peak);
                }
                desiredGain = Math.max(1.0, desiredGain);
            }

            // Fast enough to catch the first number, smooth enough to avoid frame clicks.
            double blend = desiredGain > smoothedGain ? 0.48 : 0.16;
            double nextGain = smoothedGain + (desiredGain - smoothedGain) * blend;

            // Fade the extra gain back to unity at the end of the opening sentence.
            int remaining = openingEnd - pos;
            if (remaining < releaseSamples) {
                double tail = Math.max(0.0, Math.min(1.0, remaining / (double) releaseSamples));
                nextGain = 1.0 + (nextGain - 1.0) * tail;
            }

            int span = Math.max(1, limit - pos);
            for (int i = pos; i < limit; i++) {
                double t = (i - pos) / (double) span;
                double gain = smoothedGain + (nextGain - smoothedGain) * t;
                pcm[i] = (float) (pcm[i] * gain);
            }
            smoothedGain = nextGain;
        }
    }

'''
text = text.replace(helper_anchor, helper + helper_anchor, 1)

status_old = '+ ":" + BLUETOOTH_COURT_OPENING_PRIORITY + ":ready="'
status_new = '+ ":" + BLUETOOTH_COURT_OPENING_PRIORITY + ":" + BLUETOOTH_OPENING_SEGMENT_AGC + ":ready="'
if status_old not in text:
    raise SystemExit("v209.34 status anchor missing")
text = text.replace(status_old, status_new, 1)

for required in (
    MARKER,
    "COURT_FINISH_OPENING_TARGET_RMS_DBFS = -6.0",
    "COURT_FINISH_OPENING_MAX_GAIN_DB = 18.0",
    "COURT_FINISH_OPENING_FRAME_SECONDS = 0.032",
    "COURT_FINISH_OPENING_PAUSE_SECONDS = 0.13",
    "applyCourtOpeningSegmentAgc(pcm, makeup, sampleRate, channels)",
    "desiredGain = Math.max(1.0, Math.min(maxGain, targetRms / rms))",
    'BLUETOOTH_OPENING_SEGMENT_AGC + ":ready="',
):
    if required not in text:
        raise SystemExit("v209.34 output missing: " + required)

for forbidden in (
    "courtOpeningBoost",
    "openingSquares",
    "courtOpeningStartSample",
    "courtOpeningReleaseEndSample",
):
    if forbidden in text:
        raise SystemExit("v209.34 obsolete one-bucket opening boost survived: " + forbidden)

path.write_text(text, encoding="utf-8")
print("ADMIN_V20934_BLUETOOTH_OPENING_SEGMENT_AGC_OK")
