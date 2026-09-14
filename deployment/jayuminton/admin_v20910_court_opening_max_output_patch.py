#!/usr/bin/env python3
"""Replace v209.09's heuristic opening lift with deterministic court-call maximization.

Only NativeVoice requests whose id starts with ``court_finish_`` and whose text
starts with ``N번 코트`` are affected.  The text is not changed.

The Android TTS engine may report the exact PCM frame at which each text range
starts through UtteranceProgressListener.onRangeStart().  When available, that
mapping is used to isolate the first ``N번 코트``.  If an engine omits range
timing, a conservative speech-onset + 1.05 second fallback is used.

The selected region is processed completely before MediaPlayer starts:

* reduce its crest factor with a court-opening-only compressor;
* raise its active RMS toward -9 dBFS, capped at +12 dB;
* clamp it to the existing -2 dBFS safety ceiling;
* hold full gain through ``코트`` and release over 100 ms afterward.

Thus the first number is already maximized in the WAV at playback sample zero;
there is no runtime ramp that can miss it.  The ineffective 0.45 second silent
lead-in is also removed.  v209.09's marker is retained for build lineage, but
its threshold-driven generic upward-expander code is removed.
"""

from pathlib import Path
import sys


java_path = Path(sys.argv[1] if len(sys.argv) > 1 else
                 "app/src/main/java/com/jayuminton/admin/MainActivity.java")
text = java_path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_COURT_OPENING_MAX_OUTPUT_V20910"
if MARKER in text:
    print("ADMIN_COURT_OPENING_MAX_OUTPUT_V20910_ALREADY_OK")
    raise SystemExit(0)

for required in (
    "JAYUMINTON_NATIVE_AUDIO_WARMUP_LEAD_IN_V20907",
    "JAYUMINTON_VOICE_DEHISS_LOWPASS_V20908",
    "JAYUMINTON_VOICE_OPENING_LIFT_V20909",
    "normalizeAndLimitVoiceWav(File file)",
    "currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();",
):
    if required not in text:
        raise SystemExit("v209.10 prerequisite missing: " + required)

# Keep the old marker only as lineage. Remove every tuning value used by the
# generic, content-agnostic v209.09 opening expander.
old_constants = '''    private static final String VOICE_OPENING_LIFT = "JAYUMINTON_VOICE_OPENING_LIFT_V20909";
    // A leading number/counter word ("3번") is often synthesized quieter than
    // the rest of the sentence. Lift only the opening, only while it stays this
    // quiet -- never a normal quiet consonant or pause later on.
    private static final double VOICE_UPWARD_LOW_THRESHOLD_DBFS = -22.0;
    private static final double VOICE_UPWARD_RATIO = 2.5;
    private static final double VOICE_UPWARD_MAX_GAIN_DB = 8.0;
    private static final double VOICE_UPWARD_MIN_FLOOR_DBFS = -35.0;
    private static final double VOICE_UPWARD_MAX_LEAD_IN_SECONDS = 1.0;
    private static final double VOICE_UPWARD_LOOKAHEAD_MS = 5.0;
'''
new_constants = '''    private static final String VOICE_OPENING_LIFT = "JAYUMINTON_VOICE_OPENING_LIFT_V20909";
    private static final String COURT_OPENING_MAX_OUTPUT = "JAYUMINTON_COURT_OPENING_MAX_OUTPUT_V20910";
    // The critical first "N번 코트" must be at maximum safe digital output
    // before playback begins. No wording changes and no content-wide heuristic.
    private static final double COURT_OPENING_TARGET_RMS_DBFS = -9.0;
    private static final double COURT_OPENING_MAX_GAIN_DB = 12.0;
    private static final double COURT_OPENING_COMP_THRESHOLD_DBFS = -18.0;
    private static final double COURT_OPENING_COMP_RATIO = 6.0;
    private static final double COURT_OPENING_FALLBACK_SECONDS = 1.05;
    private static final double COURT_OPENING_RELEASE_SECONDS = 0.100;
    private static final double COURT_OPENING_ONSET_THRESHOLD_DBFS = -42.0;
'''
if text.count(old_constants) != 1:
    raise SystemExit("v209.10 opening constants anchor mismatch: " + str(text.count(old_constants)))
text = text.replace(old_constants, new_constants, 1)

# Minimal lock-free callback state. TTS callbacks occur off the UI thread, so
# volatile visibility is required before prepareNormalizedAmplifiedPlayback().
old_fields = '''    private volatile String currentAmplifiedSynthId = "";
    private int ttsInitAttempts = 0;
'''
new_fields = '''    private volatile String currentAmplifiedSynthId = "";
    private volatile int courtOpeningTextEndIndex = -1;
    private volatile int courtOpeningStartFrame = -1;
    private volatile int courtOpeningEndFrame = -1;
    private int ttsInitAttempts = 0;
'''
if text.count(old_fields) != 1:
    raise SystemExit("v209.10 field anchor mismatch: " + str(text.count(old_fields)))
text = text.replace(old_fields, new_fields, 1)

# Capture text-to-frame timing when the installed TTS engine supplies it.
listener_anchor = '''            @Override
            public void onDone(String utteranceId) {
'''
listener_insert = '''            @Override
            public void onRangeStart(String utteranceId, int start, int end, int frame) {
                if (utteranceId == null || !utteranceId.equals(currentAmplifiedSynthId) ||
                        courtOpeningTextEndIndex <= 0 || frame < 0) return;
                if (courtOpeningStartFrame < 0) courtOpeningStartFrame = frame;
                // The first range beginning after "N번 코트" is its exact end frame.
                if (courtOpeningEndFrame < 0 && start >= courtOpeningTextEndIndex) {
                    courtOpeningEndFrame = frame;
                }
            }

            @Override
            public void onDone(String utteranceId) {
'''
if text.count(listener_anchor) != 1:
    raise SystemExit("v209.10 listener anchor mismatch: " + str(text.count(listener_anchor)))
text = text.replace(listener_anchor, listener_insert, 1)

# Arm exact court-opening tracking before the asynchronous synthesis request.
synth_anchor = '''            currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();
            Bundle synthParams = new Bundle();
'''
synth_replacement = '''            currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();
            courtOpeningTextEndIndex = firstCourtOpeningTextEnd(activeRepeatRequest);
            courtOpeningStartFrame = -1;
            courtOpeningEndFrame = -1;
            Bundle synthParams = new Bundle();
'''
if text.count(synth_anchor) != 1:
    raise SystemExit("v209.10 synth anchor mismatch: " + str(text.count(synth_anchor)))
text = text.replace(synth_anchor, synth_replacement, 1)

# Pass the known request type and any exact TTS frame mapping into offline DSP.
old_call = "        if (!normalizeAndLimitVoiceWav(amplifiedVoiceFile)) {\n"
new_call = '''        boolean maximizeCourtOpening = firstCourtOpeningTextEnd(activeRepeatRequest) > 0;
        if (!normalizeAndLimitVoiceWav(
                amplifiedVoiceFile, maximizeCourtOpening,
                courtOpeningStartFrame, courtOpeningEndFrame)) {
'''
if text.count(old_call) != 1:
    raise SystemExit("v209.10 normalize call anchor mismatch: " + str(text.count(old_call)))
text = text.replace(old_call, new_call, 1)

# Request ids are generated by the existing 경기종료 path. Checking both id and
# exact leading text makes it impossible for greetings or other TTS to be altered.
old_signature = "    private boolean normalizeAndLimitVoiceWav(File file) {\n"
new_signature = '''    private int firstCourtOpeningTextEnd(SpeakRequest request) {
        if (request == null || request.id == null || request.text == null ||
                !request.id.startsWith("court_finish_")) return -1;
        String spoken = request.text.trim();
        if (!spoken.matches("^[1-4]\\\\s*번\\\\s*코트.*")) return -1;
        int court = request.text.indexOf("코트");
        return court < 0 ? -1 : court + "코트".length();
    }

    private boolean normalizeAndLimitVoiceWav(
            File file, boolean maximizeCourtOpening,
            int reportedOpeningStartFrame, int reportedOpeningEndFrame) {
'''
if text.count(old_signature) != 1:
    raise SystemExit("v209.10 normalize signature mismatch: " + str(text.count(old_signature)))
text = text.replace(old_signature, new_signature, 1)

# Remove v209.09's cold-start lookahead and threshold gate from the general
# compressor. The deterministic court-only pass below replaces it completely.
old_decl = '''            // JAYUMINTON_VOICE_OPENING_LIFT_V20909: look ahead a few ms so the
            // envelope does not start its own artificial silence-to-full ramp at
            // sample 0 -- that cold-start ramp would otherwise get mistaken for a
            // genuinely quiet opening and momentarily over-boosted.
            final int lookaheadCount = (int) Math.min(
                    pcm.length, Math.round(effectiveRate * VOICE_UPWARD_LOOKAHEAD_MS / 1000.0));
            double envInit = 0.0;
            if (lookaheadCount > 0) {
                double lookaheadSum = 0.0;
                for (int k = 0; k < lookaheadCount; k++) lookaheadSum += Math.abs(pcm[k]);
                envInit = lookaheadSum / lookaheadCount;
            }
            final double upwardLowThreshold = dbToLinear(VOICE_UPWARD_LOW_THRESHOLD_DBFS);
            final double upwardMinFloor = dbToLinear(VOICE_UPWARD_MIN_FLOOR_DBFS);
            final double upwardMaxGain = dbToLinear(VOICE_UPWARD_MAX_GAIN_DB);
            final int maxLeadInSamples = (int) Math.round(effectiveRate * VOICE_UPWARD_MAX_LEAD_IN_SECONDS);
            boolean stillOpening = true;
            double env = envInit;
'''
new_decl = '''            double env = 0.0;
'''
if text.count(old_decl) != 1:
    raise SystemExit("v209.10 old opening declaration mismatch: " + str(text.count(old_decl)))
text = text.replace(old_decl, new_decl, 1)

old_lift = '''                // JAYUMINTON_VOICE_OPENING_LIFT_V20909: some TTS syntheses render
                // the very first word (e.g. a leading number/counter like "3번")
                // noticeably quieter than the rest of the sentence. A single flat
                // makeup gain later cannot fix that -- it preserves whatever
                // relative gap already exists. This lifts only the OPENING, only
                // while it stays this quiet, and turns itself off for good the
                // moment the utterance becomes loud enough (or after
                // VOICE_UPWARD_MAX_LEAD_IN_SECONDS), so it never touches a normal
                // quiet consonant or pause later in the sentence.
                if (stillOpening) {
                    if (i >= maxLeadInSamples) {
                        stillOpening = false;
                    } else if (env >= upwardLowThreshold) {
                        stillOpening = false;
                    } else if (env > upwardMinFloor) {
                        double upGain = Math.pow(
                                env / upwardLowThreshold, (1.0 / VOICE_UPWARD_RATIO) - 1.0);
                        upGain = Math.min(upGain, upwardMaxGain);
                        gain *= upGain;
                    }
                }
'''
if text.count(old_lift) != 1:
    raise SystemExit("v209.10 old opening lift mismatch: " + str(text.count(old_lift)))
text = text.replace(old_lift, "", 1)

# Run the targeted pass before the existing full-utterance makeup calculation,
# then recompute statistics so the existing peak-safe gain sees the new maximum.
stats_anchor = '''            if (peak <= 1.0e-9 || sumSquares <= 1.0e-12) return false;

            double rms = Math.sqrt(sumSquares / pcm.length);
'''
stats_replacement = '''            if (maximizeCourtOpening) {
                maximizeCourtOpeningPcm(
                        pcm, sampleRate, channels,
                        reportedOpeningStartFrame, reportedOpeningEndFrame);
                sumSquares = 0.0;
                peak = 0.0;
                for (float sample : pcm) {
                    double value = sample;
                    sumSquares += value * value;
                    peak = Math.max(peak, Math.abs(value));
                }
            }
            if (peak <= 1.0e-9 || sumSquares <= 1.0e-12) return false;

            double rms = Math.sqrt(sumSquares / pcm.length);
'''
if text.count(stats_anchor) != 1:
    raise SystemExit("v209.10 stats anchor mismatch: " + str(text.count(stats_anchor)))
text = text.replace(stats_anchor, stats_replacement, 1)

# v209.07's 0.45 s padding was disproved on the target report. Write the
# processed speech directly, so every repeat starts immediately.
old_write = '''            // JAYUMINTON_NATIVE_AUDIO_WARMUP_LEAD_IN_V20907: prepend a short true-silence lead-in so a
            // slow-ramping speaker/audio-route warm-up (common on tablets right
            // after fully idle output) plays out before real speech, not during
            // it. This only ever adds silent samples ahead of the already-
            // validated audio -- it never touches a single spoken sample.
            int silenceFrames = (int) Math.round(sampleRate * AUDIO_WARMUP_LEAD_IN_SECONDS);
            int silenceBytes = silenceFrames * channels * 2;
            byte[] outWav = new byte[dataOffset + silenceBytes + dataSize];
            System.arraycopy(wav, 0, outWav, 0, dataOffset);
            // The silenceBytes region is already zero-filled by `new byte[]`.
            System.arraycopy(wav, dataOffset, outWav, dataOffset + silenceBytes, dataSize);
            writeLeInt(outWav, 4, outWav.length - 8);
            writeLeInt(outWav, dataOffset - 4, dataSize + silenceBytes);

            raf.seek(0);
            raf.write(outWav);
            raf.setLength(outWav.length);
'''
new_write = '''            // v209.10: no disproved 0.45 s warm-up padding. Playback begins with
            // the already-maximized court number in this processed WAV.
            raf.seek(0);
            raf.write(wav);
            raf.setLength(wav.length);
'''
if text.count(old_write) != 1:
    raise SystemExit("v209.10 warmup write anchor mismatch: " + str(text.count(old_write)))
text = text.replace(old_write, new_write, 1)

# Add the deterministic two-pass maximizer before the existing dB helper.
helper_anchor = '''    private double dbToLinear(double db) {
'''
helper = r'''    private void maximizeCourtOpeningPcm(
            float[] pcm, int sampleRate, int channels,
            int reportedStartFrame, int reportedEndFrame) {
        if (pcm == null || pcm.length == 0 || sampleRate <= 0 || channels <= 0) return;
        final int samplesPerSecond = sampleRate * channels;

        int start = reportedStartFrame >= 0
                ? reportedStartFrame * channels : -1;
        if (start < 0 || start >= pcm.length) {
            // Timing-free fallback: find the first 10 ms window containing speech.
            final int window = Math.max(channels, (sampleRate / 100) * channels);
            final int searchEnd = Math.min(pcm.length, samplesPerSecond * 2);
            final double onsetThreshold = dbToLinear(COURT_OPENING_ONSET_THRESHOLD_DBFS);
            for (int pos = 0; pos + window <= searchEnd; pos += window) {
                double squares = 0.0;
                for (int i = pos; i < pos + window; i++) {
                    double x = pcm[i];
                    squares += x * x;
                }
                if (Math.sqrt(squares / window) >= onsetThreshold) {
                    start = pos;
                    break;
                }
            }
        }
        if (start < 0 || start >= pcm.length) return;

        int end = reportedEndFrame > reportedStartFrame
                ? reportedEndFrame * channels : -1;
        final int minimum = start + (int) Math.round(0.30 * samplesPerSecond);
        if (end <= minimum || end > pcm.length) {
            end = start + (int) Math.round(
                    COURT_OPENING_FALLBACK_SECONDS * samplesPerSecond);
        }
        end = Math.max(start + channels, Math.min(end, pcm.length));

        // Court-opening-only crest reduction. It creates real average-loudness
        // headroom instead of letting one consonant peak block all useful gain.
        final double compThreshold = dbToLinear(COURT_OPENING_COMP_THRESHOLD_DBFS);
        final double effectiveRate = Math.max(8000.0, samplesPerSecond);
        final double attack = Math.exp(-1.0 / (0.002 * effectiveRate));
        final double release = Math.exp(-1.0 / (0.080 * effectiveRate));
        double env = 0.0;
        for (int i = start; i < end; i++) {
            double x = pcm[i];
            double ax = Math.abs(x);
            double coeff = ax > env ? attack : release;
            env = coeff * env + (1.0 - coeff) * ax;
            double gain = 1.0;
            if (env > compThreshold && env > 1.0e-9) {
                gain = Math.pow(
                        env / compThreshold,
                        (1.0 / COURT_OPENING_COMP_RATIO) - 1.0);
            }
            if (ax > compThreshold && ax > 1.0e-9) {
                double instant = Math.pow(
                        ax / compThreshold,
                        (1.0 / COURT_OPENING_COMP_RATIO) - 1.0);
                gain = Math.min(gain, instant);
            }
            pcm[i] = (float) (x * gain);
        }

        double squares = 0.0;
        for (int i = start; i < end; i++) {
            double x = pcm[i];
            squares += x * x;
        }
        double rms = Math.sqrt(squares / Math.max(1, end - start));
        if (!Double.isFinite(rms) || rms <= 1.0e-9) return;

        final double targetRms = dbToLinear(COURT_OPENING_TARGET_RMS_DBFS);
        final double maxGain = dbToLinear(COURT_OPENING_MAX_GAIN_DB);
        final double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
        final double boost = Math.max(1.0, Math.min(maxGain, targetRms / rms));
        final int releaseSamples = Math.max(
                channels, (int) Math.round(COURT_OPENING_RELEASE_SECONDS * samplesPerSecond));
        final int releaseEnd = Math.min(pcm.length, end + releaseSamples);

        // Full fixed gain starts with the first speech sample and remains through
        // "코트". Only after that boundary does it return smoothly to unity.
        for (int i = start; i < releaseEnd; i++) {
            double localGain = boost;
            if (i >= end) {
                double progress = (i - end) / (double) Math.max(1, releaseEnd - end);
                localGain = boost + (1.0 - boost) * progress;
            }
            double y = pcm[i] * localGain;
            if (y > ceiling) y = ceiling;
            if (y < -ceiling) y = -ceiling;
            pcm[i] = (float) y;
        }
    }

'''
if text.count(helper_anchor) != 1:
    raise SystemExit("v209.10 helper anchor mismatch: " + str(text.count(helper_anchor)))
text = text.replace(helper_anchor, helper + helper_anchor, 1)

# Extend the native diagnostics string without removing build-lineage markers.
old_status = '+ ":" + VOICE_DEHISS_LOWPASS + ":" + VOICE_OPENING_LIFT + ":ready="'
new_status = '+ ":" + VOICE_DEHISS_LOWPASS + ":" + VOICE_OPENING_LIFT + ":" + COURT_OPENING_MAX_OUTPUT + ":ready="'
if old_status not in text:
    raise SystemExit("v209.10 status anchor missing")
text = text.replace(old_status, new_status, 1)

for required in (
    MARKER,
    "COURT_OPENING_TARGET_RMS_DBFS = -9.0",
    "COURT_OPENING_MAX_GAIN_DB = 12.0",
    "public void onRangeStart(String utteranceId, int start, int end, int frame)",
    "firstCourtOpeningTextEnd(activeRepeatRequest)",
    "maximizeCourtOpeningPcm(",
    "raf.write(wav);",
    "COURT_OPENING_MAX_OUTPUT + \":ready=\"",
):
    if required not in text:
        raise SystemExit("v209.10 output requirement missing: " + required)

for forbidden in (
    "VOICE_UPWARD_LOW_THRESHOLD_DBFS",
    "boolean stillOpening = true;",
    "upGain = Math.min(upGain, upwardMaxGain);",
    "raf.write(outWav);",
):
    if forbidden in text:
        raise SystemExit("v209.10 obsolete behavior survived: " + forbidden)

java_path.write_text(text, encoding="utf-8")
print("ADMIN_COURT_OPENING_MAX_OUTPUT_V20910_OK")
