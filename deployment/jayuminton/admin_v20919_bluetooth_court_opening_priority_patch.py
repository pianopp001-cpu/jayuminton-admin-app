#!/usr/bin/env python3
"""Restore a dedicated high-loudness opening on top of full court-finish normalization."""

from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else
            "app/src/main/java/com/jayuminton/admin/MainActivity.java")
text = path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_BLUETOOTH_COURT_OPENING_PRIORITY_V20919"

if MARKER in text:
    print("ADMIN_V20919_BLUETOOTH_OPENING_PRIORITY_ALREADY_OK")
    raise SystemExit(0)

for required in (
    "JAYUMINTON_FULL_COURT_VOICE_MAX_MUSIC_RESTORE_V20911",
    "JAYUMINTON_BLUETOOTH_OPENING_CARROT_EXPORT_V20914",
    "COURT_FINISH_TARGET_RMS_DBFS = -9.0",
    "COURT_FINISH_COMP_RATIO = 6.0",
    "boolean maximizeFullCourtFinish",
    "double finalPeak = 0.0;",
    "COURT_FINISH_PREROLL_SECONDS = 0.60",
    "COURT_FINISH_PREROLL_DBFS = -38.0",
):
    if required not in text:
        raise SystemExit("v209.19 prerequisite missing: " + required)

# Add a dedicated opening profile. v209.11 removed the v209.10 opening-only pass
# when it changed to full-sentence normalization; this restores opening priority
# while retaining the full-announcement processing.
anchor = '    private static final String BLUETOOTH_OPENING_CARROT_EXPORT = "JAYUMINTON_BLUETOOTH_OPENING_CARROT_EXPORT_V20914";\n'
insert = anchor + (
    '    private static final String BLUETOOTH_COURT_OPENING_PRIORITY = "' + MARKER + '";\n'
    '    private static final double COURT_FINISH_OPENING_TARGET_RMS_DBFS = -4.5;\n'
    '    private static final double COURT_FINISH_OPENING_MAX_GAIN_DB = 12.0;\n'
    '    private static final double COURT_FINISH_OPENING_SECONDS = 2.10;\n'
    '    private static final double COURT_FINISH_OPENING_RELEASE_SECONDS = 0.14;\n'
    '    private static final double COURT_FINISH_OPENING_ONSET_DBFS = -44.0;\n'
)
if text.count(anchor) != 1:
    raise SystemExit("v209.19 marker anchor mismatch: " + str(text.count(anchor)))
text = text.replace(anchor, insert, 1)

# The old pre-roll was so quiet that a Bluetooth gate could still ignore it.
# Keep it short/faint, but above the typical gate floor so the same playback
# session is already active when the first court number arrives.
text = text.replace(
    "    private static final double COURT_FINISH_PREROLL_SECONDS = 0.60;\n"
    "    private static final double COURT_FINISH_PREROLL_DBFS = -38.0;\n",
    "    private static final double COURT_FINISH_PREROLL_SECONDS = 0.50;\n"
    "    private static final double COURT_FINISH_PREROLL_DBFS = -28.0;\n",
    1,
)

# Calculate a second, opening-only gain after the full-sentence compressor and
# makeup gain have already been chosen. This specifically targets
# "N번 코트 나왔습니다" (roughly the first 2.1 seconds of voiced content).
final_anchor = '''            double finalPeak = 0.0;
            double finalSquares = 0.0;
            for (int i = 0; i < pcm.length; i++) {
                double y = pcm[i] * makeup;
'''
opening_block = '''            int courtOpeningStartSample = -1;
            int courtOpeningEndSample = -1;
            int courtOpeningReleaseEndSample = -1;
            double courtOpeningBoost = 1.0;
            if (maximizeFullCourtFinish) {
                final int samplesPerSecond = Math.max(channels, sampleRate * channels);
                final int onsetWindow = Math.max(channels, (sampleRate / 100) * channels);
                final int onsetSearchEnd = Math.min(pcm.length, samplesPerSecond * 2);
                final double onsetThreshold = dbToLinear(COURT_FINISH_OPENING_ONSET_DBFS);
                for (int scanPos = 0; scanPos + onsetWindow <= onsetSearchEnd; scanPos += onsetWindow) {
                    double sq = 0.0;
                    for (int k = scanPos; k < scanPos + onsetWindow; k++) {
                        double v = pcm[k] * makeup;
                        sq += v * v;
                    }
                    if (Math.sqrt(sq / onsetWindow) >= onsetThreshold) {
                        courtOpeningStartSample = scanPos;
                        break;
                    }
                }
                if (courtOpeningStartSample >= 0) {
                    courtOpeningEndSample = Math.min(
                            pcm.length,
                            courtOpeningStartSample + (int) Math.round(
                                    COURT_FINISH_OPENING_SECONDS * samplesPerSecond));
                    courtOpeningReleaseEndSample = Math.min(
                            pcm.length,
                            courtOpeningEndSample + (int) Math.round(
                                    COURT_FINISH_OPENING_RELEASE_SECONDS * samplesPerSecond));
                    double openingSquares = 0.0;
                    int openingCount = 0;
                    for (int i = courtOpeningStartSample; i < courtOpeningEndSample; i++) {
                        double v = pcm[i] * makeup;
                        openingSquares += v * v;
                        openingCount++;
                    }
                    if (openingCount > 0 && openingSquares > 1.0e-12) {
                        double openingRms = Math.sqrt(openingSquares / openingCount);
                        double openingTarget = dbToLinear(COURT_FINISH_OPENING_TARGET_RMS_DBFS);
                        courtOpeningBoost = Math.max(
                                1.0,
                                Math.min(
                                        dbToLinear(COURT_FINISH_OPENING_MAX_GAIN_DB),
                                        openingTarget / openingRms));
                    }
                }
            }

            double finalPeak = 0.0;
            double finalSquares = 0.0;
            for (int i = 0; i < pcm.length; i++) {
                double y = pcm[i] * makeup;
                if (maximizeFullCourtFinish && courtOpeningStartSample >= 0 &&
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
if text.count(final_anchor) != 1:
    raise SystemExit("v209.19 final-loop anchor mismatch: " + str(text.count(final_anchor)))
text = text.replace(final_anchor, opening_block, 1)

# Extend diagnostics so the packaged classes.dex proves the patch is present.
status_old = '+ ":" + BLUETOOTH_OPENING_CARROT_EXPORT + ":ready="'
status_new = '+ ":" + BLUETOOTH_OPENING_CARROT_EXPORT + ":" + BLUETOOTH_COURT_OPENING_PRIORITY + ":ready="'
if status_old not in text:
    raise SystemExit("v209.19 status anchor missing")
text = text.replace(status_old, status_new, 1)

for required in (
    MARKER,
    "COURT_FINISH_OPENING_TARGET_RMS_DBFS = -4.5",
    "COURT_FINISH_OPENING_SECONDS = 2.10",
    "courtOpeningBoost",
    "COURT_FINISH_PREROLL_SECONDS = 0.50",
    "COURT_FINISH_PREROLL_DBFS = -28.0",
    'BLUETOOTH_COURT_OPENING_PRIORITY + ":ready="',
):
    if required not in text:
        raise SystemExit("v209.19 output missing: " + required)

path.write_text(text, encoding="utf-8")
print("ADMIN_V20919_BLUETOOTH_OPENING_PRIORITY_OK")
