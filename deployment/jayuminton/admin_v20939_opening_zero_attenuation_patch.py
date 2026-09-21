#!/usr/bin/env python3
"""v209.39: zero app-side attenuation for the critical opening phrase.

For verified court-finish announcements, the opening "N번 코트 나왔습니다"
must never be made quieter by the app DSP.

v209.38 already lifts weak openings after processing, but the earlier downward
compressor can still use gain < 1.0 and the whole-file makeup can also be < 1.0.
This patch removes those attenuation paths for the detected opening phrase and
adds a final byte-level floor against the post-dehiss / pre-compressor baseline.

The de-hiss low-pass remains intentionally preserved. The baseline is captured
AFTER de-hiss, so this patch does not reintroduce the high-frequency hiss that
v209.08 intentionally removed.

Contracts:
- compressor gain for the opening is never < 1.0;
- whole-file makeup for the opening is never < 1.0;
- after every existing v209.38 final-WAV lift/balance step, each opening sample
  is restored if its magnitude is below the post-dehiss baseline magnitude;
- final restoration is bounded only by valid signed 16-bit PCM full scale, not
  the older -2 dBFS mastering ceiling, because restoring the original TTS sample
  is not amplification beyond the source;
- no validation failure can suppress playback.
"""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
java = java_path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_OPENING_ZERO_ATTENUATION_V20939"
if MARKER in java:
    print("ADMIN_V20939_OPENING_ZERO_ATTENUATION_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_COURT_OPENING_GAP_CLOSURE_V20938",
    "JAYUMINTON_VOICE_DEHISS_LOWPASS_V20908",
    "boolean maximizeFullCourtFinish",
    "double y = x * gain;",
    "double y = pcm[i] * makeup;",
    "balanceExactCourtNumberFinalWavV20935(",
    "normalizingPhraseEndFrameV20938",
    "writeFinalSampleV20935(",
):
    if token not in java:
        raise SystemExit("v209.39 prerequisite missing: " + token)

# Marker.
field_anchor = '    private static final String COURT_OPENING_GAP_CLOSURE = "JAYUMINTON_COURT_OPENING_GAP_CLOSURE_V20938";\n'
field_insert = field_anchor + '    private static final String OPENING_ZERO_ATTENUATION = "' + MARKER + '";\n'
if java.count(field_anchor) != 1:
    raise SystemExit("v209.39 marker anchor mismatch: " + str(java.count(field_anchor)))
java = java.replace(field_anchor, field_insert, 1)

# Capture a baseline AFTER v209.08 de-hiss but BEFORE any downward compressor.
compressor_anchor = """            // Envelope compressor: reduce short peaks first so the average speech
            // energy can be raised without crushing consonant transients into 0 dBFS.
"""
baseline_insert = """            // JAYUMINTON_OPENING_ZERO_ATTENUATION_V20939
            // Snapshot AFTER de-hiss and BEFORE compressor/makeup. This is the
            // minimum amplitude the critical opening is allowed to have in the
            // final played WAV.
            final float[] courtOpeningBaselineV20939 =
                    maximizeFullCourtFinish ? pcm.clone() : null;
            final int[] courtOpeningRangeV20939 = maximizeFullCourtFinish
                    ? detectCourtOpeningRangePcmV20939(
                            courtOpeningBaselineV20939, sampleRate, channels,
                            normalizingPhraseEndFrameV20938)
                    : null;
            final int courtOpeningStartV20939 =
                    courtOpeningRangeV20939 != null ? courtOpeningRangeV20939[0] : -1;
            final int courtOpeningEndV20939 =
                    courtOpeningRangeV20939 != null ? courtOpeningRangeV20939[1] : -1;

""" + compressor_anchor
if java.count(compressor_anchor) != 1:
    raise SystemExit("v209.39 compressor baseline anchor mismatch: " + str(java.count(compressor_anchor)))
java = java.replace(compressor_anchor, baseline_insert, 1)

# Downward compressor / fast peak guard / old opening logic may calculate a net
# gain below 1.0. The critical phrase is not allowed to be attenuated.
gain_anchor = """                double y = x * gain;
                pcm[i] = (float) y;
"""
gain_new = """                if (maximizeFullCourtFinish &&
                        courtOpeningStartV20939 >= 0 &&
                        i >= courtOpeningStartV20939 && i < courtOpeningEndV20939) {
                    // ZERO_DOWNWARD_COMPRESSOR_V20939
                    gain = Math.max(1.0, gain);
                }
                double y = x * gain;
                pcm[i] = (float) y;
"""
if java.count(gain_anchor) != 1:
    raise SystemExit("v209.39 compressor gain anchor mismatch: " + str(java.count(gain_anchor)))
java = java.replace(gain_anchor, gain_new, 1)

# Whole-file makeup can be <1 when another peak controls the peak-safe gain.
# Never apply that attenuation to the opening phrase.
makeup_anchor = """                double y = pcm[i] * makeup;
                // Final brick-wall sample limiter"""
makeup_new = """                double localMakeupV20939 = makeup;
                if (maximizeFullCourtFinish &&
                        courtOpeningStartV20939 >= 0 &&
                        i >= courtOpeningStartV20939 && i < courtOpeningEndV20939) {
                    // ZERO_DOWNWARD_MAKEUP_V20939
                    localMakeupV20939 = Math.max(1.0, makeup);
                }
                double y = pcm[i] * localMakeupV20939;
                // Final brick-wall sample limiter"""
if java.count(makeup_anchor) != 1:
    raise SystemExit("v209.39 makeup anchor mismatch: " + str(java.count(makeup_anchor)))
java = java.replace(makeup_anchor, makeup_new, 1)

# v209.35/v209.38 balancing is the last DSP family. Restore the post-dehiss
# baseline AFTER it, so no earlier compressor/makeup/limiter decision can leave
# the opening quieter than the synthesized baseline.
call_anchor = """                balanceExactCourtNumberFinalWavV20935(
                        wav, dataOffset, dataSize, sampleRate, channels,
                        normalizingNumberStartFrameV20938, normalizingNumberEndFrameV20938,
                        normalizingPhraseEndFrameV20938);
"""
call_new = call_anchor + """                enforceCourtOpeningNoAttenuationV20939(
                        wav, dataOffset, dataSize,
                        courtOpeningBaselineV20939,
                        courtOpeningStartV20939, courtOpeningEndV20939);
"""
if java.count(call_anchor) != 1:
    raise SystemExit("v209.39 final guard anchor mismatch: " + str(java.count(call_anchor)))
java = java.replace(call_anchor, call_new, 1)

helper_anchor = "    private double frameRmsV20938(\n"
if java.count(helper_anchor) != 1:
    raise SystemExit("v209.39 helper anchor mismatch: " + str(java.count(helper_anchor)))

helpers = r'''    private double frameRmsPcmV20939(
            float[] pcm, int start, int end) {
        if (pcm == null || end <= start) return 0.0;
        start = Math.max(0, Math.min(pcm.length, start));
        end = Math.max(start, Math.min(pcm.length, end));
        double sq = 0.0;
        int count = 0;
        for (int i = start; i < end; i++) {
            double v = pcm[i];
            sq += v * v;
            count++;
        }
        return count > 0 ? Math.sqrt(sq / count) : 0.0;
    }

    private int[] detectCourtOpeningRangePcmV20939(
            float[] pcm, int sampleRate, int channels, int reportedPhraseEndFrame) {
        if (pcm == null || pcm.length == 0 || sampleRate < 8000 || channels < 1) {
            return null;
        }
        final int samplesPerSecond = Math.max(channels, sampleRate * channels);
        final int frameSamples = Math.max(
                channels, (int) Math.round(samplesPerSecond * 0.012));
        final int searchEnd = Math.min(
                pcm.length, (int) Math.round(samplesPerSecond * 2.00));
        final double sampleFloor = dbToLinear(-86.0);

        int onset = -1;
        for (int i = 0; i < searchEnd; i++) {
            if (Math.abs(pcm[i]) >= sampleFloor) {
                onset = Math.max(0, (i / channels) * channels);
                break;
            }
        }
        if (onset < 0) return null;

        final int minEnd = Math.min(
                pcm.length, onset + (int) Math.round(samplesPerSecond * 0.75));
        final int maxEnd = Math.min(
                pcm.length, onset + (int) Math.round(samplesPerSecond * 2.80));

        double probeSq = 0.0;
        long probeCount = 0L;
        for (int i = onset; i < maxEnd; i++) {
            double v = pcm[i];
            if (Math.abs(v) < sampleFloor) continue;
            probeSq += v * v;
            probeCount++;
        }
        double probeRms = probeCount > 0
                ? Math.sqrt(probeSq / probeCount) : 0.0;
        double quiet = Math.max(
                dbToLinear(-74.0),
                probeRms > 1.0e-9 ? probeRms * 0.10 : dbToLinear(-60.0));

        int quietFramesNeeded = Math.max(3, (int) Math.ceil(0.12 / 0.012));
        int quietFrames = 0;
        int end = maxEnd;
        for (int pos = minEnd; pos < maxEnd; pos += frameSamples) {
            int limit = Math.min(maxEnd, pos + frameSamples);
            double rms = frameRmsPcmV20939(pcm, pos, limit);
            if (rms <= quiet) {
                quietFrames++;
                if (quietFrames >= quietFramesNeeded) {
                    end = Math.max(
                            minEnd, pos - (quietFrames - 1) * frameSamples);
                    break;
                }
            } else {
                quietFrames = 0;
            }
        }

        // Prefer a trustworthy TTS lexical end when it extends the adaptive
        // boundary. It is immutable per completed synthesis in v209.38.
        if (reportedPhraseEndFrame > 0) {
            int reportedEnd = reportedPhraseEndFrame * channels;
            if (reportedEnd > onset && reportedEnd <= pcm.length) {
                end = Math.max(end, reportedEnd);
            }
        }
        end = Math.max(onset + channels, Math.min(pcm.length, end));
        return new int[]{onset, end};
    }

    private void enforceCourtOpeningNoAttenuationV20939(
            byte[] wav, int dataOffset, int dataSize,
            float[] baseline, int start, int end) {
        if (wav == null || baseline == null || dataSize < 4 ||
                start < 0 || end <= start) return;
        int sampleCount = Math.min(dataSize / 2, baseline.length);
        start = Math.max(0, Math.min(sampleCount, start));
        end = Math.max(start, Math.min(sampleCount, end));

        // Signed 16-bit safe full scale. Unlike the normal -2 dBFS mastering
        // ceiling, this permits restoration up to the ORIGINAL synthesized
        // amplitude. It never amplifies beyond max(final, original baseline).
        final double pcmSafeCeiling = 32767.0 / 32768.0;
        for (int i = start; i < end; i++) {
            int off = dataOffset + i * 2;
            if (off < 0 || off + 1 >= wav.length) break;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            double current = sample / 32768.0;
            double original = baseline[i];
            double originalAbs = Math.abs(original);
            if (originalAbs <= 1.0e-12) continue;

            // The compressor/makeup path is polarity-preserving. If current
            // magnitude fell below the post-dehiss source, restore source
            // magnitude exactly (bounded only by valid PCM full scale).
            if (Math.abs(current) + 1.0e-9 < originalAbs) {
                double restored = Math.copySign(
                        Math.min(pcmSafeCeiling, originalAbs), original);
                writeFinalSampleV20935(
                        wav, dataOffset, i, restored, pcmSafeCeiling);
            }
        }
    }

'''
java = java.replace(helper_anchor, helpers + helper_anchor, 1)

status_old = '+ ":" + GUARANTEED_COURT_OPENING_FLOOR + ":" + COURT_OPENING_GAP_CLOSURE + ":ready="'
status_new = '+ ":" + GUARANTEED_COURT_OPENING_FLOOR + ":" + COURT_OPENING_GAP_CLOSURE + ":" + OPENING_ZERO_ATTENUATION + ":ready="'
if status_old not in java:
    raise SystemExit("v209.39 status anchor missing")
java = java.replace(status_old, status_new, 1)

for required in (
    MARKER,
    "courtOpeningBaselineV20939",
    "detectCourtOpeningRangePcmV20939(",
    "ZERO_DOWNWARD_COMPRESSOR_V20939",
    "gain = Math.max(1.0, gain);",
    "ZERO_DOWNWARD_MAKEUP_V20939",
    "localMakeupV20939 = Math.max(1.0, makeup);",
    "enforceCourtOpeningNoAttenuationV20939(",
    "pcmSafeCeiling = 32767.0 / 32768.0",
    "Math.abs(current) + 1.0e-9 < originalAbs",
):
    if required not in java:
        raise SystemExit("v209.39 output missing: " + required)

for forbidden in (
    "ZERO_DOWNWARD_COMPRESSOR_V20939\n                    gain = Math.min",
    "ZERO_DOWNWARD_MAKEUP_V20939\n                    localMakeupV20939 = Math.min",
):
    if forbidden in java:
        raise SystemExit("v209.39 attenuation guard regression: " + forbidden)

java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20939_OPENING_ZERO_ATTENUATION_OK")
