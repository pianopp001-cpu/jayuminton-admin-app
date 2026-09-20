#!/usr/bin/env python3
"""v209.37 guaranteed opening floor.

Purpose:
- Keep v209.34/v209.35 full-announcement loudness exactly intact.
- Never attenuate the leading court-number/opening region: every corrective gain
  is >= 1.0 and is applied offline before playback.
- If Android TTS exposes an exact N번 -> 코트 frame boundary, rebalance that
  exact N번 region against the following phrase.
- If the engine does NOT expose that boundary, do not skip protection: detect
  the first voiced onset in the final WAV and protect the first 0.52 s lead.
- If peak headroom prevents the first correction from reaching the RMS floor,
  run bounded additional offline lift passes with the same -2 dBFS ceiling.
- NEVER suppress playback. If a target still cannot be reached, play the best
  final WAV available. No "validation failure => silence" path is introduced.

No runtime AGC, no attack envelope, no release envelope, no re-synthesis.
"""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
java = java_path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_GUARANTEED_COURT_OPENING_FLOOR_V20937"
if MARKER in java:
    print("ADMIN_V20937_GUARANTEED_OPENING_FLOOR_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_EXACT_COURT_NUMBER_RANGE_V20935",
    "balanceExactCourtNumberFinalWavV20935(",
    "activeRmsFinalWavV20935(",
    "writeFinalSampleV20935(",
    "VOICE_PEAK_CEILING_DBFS = -2.0",
    "JAYUMINTON_BLUETOOTH_OPENING_FIXED_GAIN_V20934",
    "No attack. No release. No runtime AGC.",
):
    if token not in java:
        raise SystemExit("v209.37 prerequisite missing: " + token)

field_anchor = '    private static final String EXACT_COURT_NUMBER_RANGE = "JAYUMINTON_EXACT_COURT_NUMBER_RANGE_V20935";\n'
field_insert = field_anchor + '    private static final String GUARANTEED_COURT_OPENING_FLOOR = "' + MARKER + '";\n'
if java.count(field_anchor) != 1:
    raise SystemExit("v209.37 marker field anchor mismatch: " + str(java.count(field_anchor)))
java = java.replace(field_anchor, field_insert, 1)

start = java.find("    private void balanceExactCourtNumberFinalWavV20935(")
end = java.find("    private void applyCourtOpeningFixedGain(", start)
if start < 0 or end < 0:
    raise SystemExit("v209.37 balance method boundaries missing")

replacement = r'''    private int detectFinalVoicedOnsetV20937(
            byte[] wav, int dataOffset, int sampleCount, int sampleRate, int channels) {
        if (wav == null || sampleCount <= 0 || sampleRate < 8000 || channels < 1) return -1;
        final int frameSamples = Math.max(
                channels, (int) Math.round(sampleRate * channels * 0.020));
        final int searchEnd = Math.min(
                sampleCount, (int) Math.round(sampleRate * channels * 1.20));
        final double threshold = dbToLinear(-46.0);
        for (int pos = 0; pos < searchEnd; pos += frameSamples) {
            int limit = Math.min(searchEnd, pos + frameSamples);
            double sq = 0.0;
            int count = 0;
            for (int i = pos; i < limit; i++) {
                int off = dataOffset + i * 2;
                if (off < 0 || off + 1 >= wav.length) break;
                short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
                double v = sample / 32768.0;
                sq += v * v;
                count++;
            }
            if (count > 0 && Math.sqrt(sq / count) >= threshold) return pos;
        }
        return -1;
    }

    private void liftFinalRegionOnlyUpV20937(
            byte[] wav, int dataOffset, int sampleCount,
            int start, int end, double gain, double ceiling) {
        if (wav == null || sampleCount <= 0 || end <= start ||
                !Double.isFinite(gain) || gain <= 1.000001) return;
        start = Math.max(0, Math.min(sampleCount, start));
        end = Math.max(start, Math.min(sampleCount, end));
        gain = Math.max(1.0, gain);
        for (int i = start; i < end; i++) {
            int off = dataOffset + i * 2;
            if (off < 0 || off + 1 >= wav.length) break;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            double original = sample / 32768.0;
            // Gain is NEVER below 1.0. Clamp only to the existing -2 dBFS
            // ceiling, so this corrective pass cannot intentionally attenuate
            // any sample in the protected region.
            writeFinalSampleV20935(
                    wav, dataOffset, i, original * gain, ceiling);
        }
    }

    private void protectOpeningRegionV20937(
            byte[] wav, int dataOffset, int sampleCount,
            int protectedStart, int protectedEnd,
            int referenceStart, int referenceEnd,
            int sampleRate, int channels) {
        if (wav == null || sampleCount <= 0 ||
                protectedEnd <= protectedStart || referenceEnd <= referenceStart) return;

        protectedStart = Math.max(0, Math.min(sampleCount, protectedStart));
        protectedEnd = Math.max(protectedStart, Math.min(sampleCount, protectedEnd));
        referenceStart = Math.max(protectedEnd, Math.min(sampleCount, referenceStart));
        referenceEnd = Math.max(referenceStart, Math.min(sampleCount, referenceEnd));
        if (protectedEnd <= protectedStart || referenceEnd <= referenceStart) return;

        final double activeThreshold = dbToLinear(-46.0);
        final double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
        final double maxPassGain = dbToLinear(9.0);

        // Bounded OFFLINE correction only. No attack/release/runtime AGC.
        // Multiple bounded passes allow the active RMS to rise even when a few
        // peaks are already near the -2 dBFS ceiling; samples are only lifted
        // or ceiling-clamped, never intentionally reduced.
        for (int pass = 0; pass < 3; pass++) {
            double protectedRms = activeRmsFinalWavV20935(
                    wav, dataOffset, sampleCount,
                    protectedStart, protectedEnd, activeThreshold);
            double referenceRms = activeRmsFinalWavV20935(
                    wav, dataOffset, sampleCount,
                    referenceStart, referenceEnd, activeThreshold);
            if (protectedRms <= 1.0e-9 || referenceRms <= 1.0e-9) return;

            double gapDb = 20.0 * Math.log10(referenceRms / protectedRms);
            if (!Double.isFinite(gapDb) || gapDb <= 1.5) break;

            double desiredGain = referenceRms / protectedRms;
            double gain = Math.max(1.0, Math.min(maxPassGain, desiredGain));
            if (!Double.isFinite(gain) || gain <= 1.0001) break;
            liftFinalRegionOnlyUpV20937(
                    wav, dataOffset, sampleCount,
                    protectedStart, protectedEnd, gain, ceiling);
        }

        // Tiny post-boundary gain-only taper prevents a click. It starts above
        // 1.0 and ends at 1.0; it never creates an attack on the protected lead.
        double protectedRms = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount,
                protectedStart, protectedEnd, activeThreshold);
        double referenceRms = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount,
                referenceStart, referenceEnd, activeThreshold);
        if (protectedRms > 1.0e-9 && referenceRms > protectedRms) {
            double edgeGain = Math.max(
                    1.0, Math.min(dbToLinear(3.0), referenceRms / protectedRms));
            int fadeSamples = Math.max(
                    channels, (int) Math.round(sampleRate * channels * 0.012));
            int fadeEnd = Math.min(referenceEnd, protectedEnd + fadeSamples);
            for (int i = protectedEnd; i < fadeEnd; i++) {
                int off = dataOffset + i * 2;
                if (off < 0 || off + 1 >= wav.length) break;
                short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
                double original = sample / 32768.0;
                double t = (i - protectedEnd) /
                        (double) Math.max(1, fadeEnd - protectedEnd);
                double localGain = Math.max(1.0, edgeGain + (1.0 - edgeGain) * t);
                writeFinalSampleV20935(
                        wav, dataOffset, i, original * localGain, ceiling);
            }
        }

        // Diagnostic-only post condition. IMPORTANT: playback is NEVER blocked
        // even if pathological source audio cannot reach this floor.
        double afterProtected = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount,
                protectedStart, protectedEnd, activeThreshold);
        double afterReference = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount,
                referenceStart, referenceEnd, activeThreshold);
        boolean openingFloorReachedV20937 = true;
        if (afterProtected > 1.0e-9 && afterReference > 1.0e-9) {
            double afterGapDb = 20.0 * Math.log10(afterReference / afterProtected);
            openingFloorReachedV20937 =
                    Double.isFinite(afterGapDb) && afterGapDb <= 2.0;
        }
        if (!openingFloorReachedV20937) {
            // NEVER_SUPPRESS_PLAYBACK_V20937
            // Keep and play the strongest safe WAV produced above.
        }
    }

    private void balanceExactCourtNumberFinalWavV20935(
            byte[] wav, int dataOffset, int dataSize, int sampleRate, int channels,
            int numberStartFrame, int numberEndFrame, int phraseEndFrame) {
        if (wav == null || dataSize < 4 || sampleRate < 8000 || channels < 1) return;

        final int sampleCount = dataSize / 2;

        // Preferred path: Android TTS supplied the exact N번 -> 코트 frame
        // boundary. Protect exactly N번 against the following phrase.
        boolean exactBoundary =
                numberStartFrame >= 0 &&
                numberEndFrame > numberStartFrame &&
                phraseEndFrame > numberEndFrame;
        if (exactBoundary) {
            int numberStart = numberStartFrame * channels;
            int numberEnd = Math.min(sampleCount, numberEndFrame * channels);
            int phraseEnd = Math.min(sampleCount, phraseEndFrame * channels);
            if (numberStart >= 0 && numberEnd > numberStart &&
                    phraseEnd > numberEnd && numberStart < sampleCount) {
                protectOpeningRegionV20937(
                        wav, dataOffset, sampleCount,
                        numberStart, numberEnd,
                        numberEnd, phraseEnd,
                        sampleRate, channels);
                return;
            }
        }

        // v209.37 FALLBACK: some TTS engines merge "N번 코트" into one lexical
        // range and therefore never expose the exact boundary. v209.35 simply
        // returned here; v209.37 still protects the actual final WAV.
        //
        // The first 0.52 s from detected voiced onset safely covers the number
        // and may include the beginning of "코트". Boosting extra opening speech
        // is acceptable; attenuation is not. Compare it with the immediately
        // following opening phrase up to 1.80 s after onset.
        int onset = detectFinalVoicedOnsetV20937(
                wav, dataOffset, sampleCount, sampleRate, channels);
        if (onset < 0) return;
        int samplesPerSecond = Math.max(channels, sampleRate * channels);
        int leadEnd = Math.min(
                sampleCount,
                onset + (int) Math.round(0.52 * samplesPerSecond));
        int referenceEnd = Math.min(
                sampleCount,
                onset + (int) Math.round(1.80 * samplesPerSecond));
        if (leadEnd <= onset || referenceEnd <= leadEnd) return;

        protectOpeningRegionV20937(
                wav, dataOffset, sampleCount,
                onset, leadEnd,
                leadEnd, referenceEnd,
                sampleRate, channels);
    }

'''

java = java[:start] + replacement + java[end:]

status_old = '+ ":" + EXACT_COURT_NUMBER_RANGE + ":ready="'
status_new = '+ ":" + EXACT_COURT_NUMBER_RANGE + ":" + GUARANTEED_COURT_OPENING_FLOOR + ":ready="'
if status_old not in java:
    raise SystemExit("v209.37 status anchor missing")
java = java.replace(status_old, status_new, 1)

for required in (
    MARKER,
    "detectFinalVoicedOnsetV20937(",
    "protectOpeningRegionV20937(",
    "NEVER_SUPPRESS_PLAYBACK_V20937",
    "for (int pass = 0; pass < 3; pass++)",
    "double gain = Math.max(1.0",
    "double localGain = Math.max(1.0",
    "0.52 * samplesPerSecond",
    "No attack. No release. No runtime AGC.",
):
    if required not in java:
        raise SystemExit("v209.37 output missing: " + required)

# Guard against the dangerous behavior the user explicitly rejected.
for forbidden in (
    "openingFloorReachedV20937) return false",
    "if (!openingFloorReachedV20937) return false",
    "validation failure => silence",
):
    if forbidden in java:
        raise SystemExit("v209.37 forbidden playback suppression found: " + forbidden)

java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20937_GUARANTEED_OPENING_FLOOR_OK")
