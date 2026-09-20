#!/usr/bin/env python3
"""v209.38 close remaining court-announcement gaps in one pass.

Fixes on top of v209.37:
1) Very quiet leading number is no longer skipped by the old -46 dBFS onset/RMS gate.
   Use adaptive near-digital-silence detection and a much lower measurement floor.
2) Apply BOTH relative balance and an absolute active-RMS floor, so an opening that
   is uniformly quiet is still lifted even when its internal dB gap looks "balanced".
3) Remove the fixed 0.52 s fallback assumption. Detect the opening phrase end from
   the final WAV using a sustained-pause boundary with bounded min/max duration.
4) Exact-range protection no longer returns blindly when exact measurements fail;
   it falls through to the adaptive final-WAV path.
5) Snapshot request/file/range state at TTS onDone and detach the completed file
   before posting to the UI thread, preventing a new announcement from deleting or
   reusing the previous completed WAV/range metadata.
6) A court-finish synthesized-path failure gets one fresh synth retry before direct
   TTS fallback. Direct TTS remains the final "always speak" path; playback is never
   suppressed because a loudness target cannot be reached.
7) Keep all correction gains >= 1.0. No runtime AGC, no attack envelope, no release
   envelope, and no validation-failure-to-silence behavior.

Bluetooth hardware/firmware DSP is outside app control, but every app-controlled
path either uses the processed final WAV or preserves an always-speak fallback.
"""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
java = java_path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_COURT_OPENING_GAP_CLOSURE_V20938"
if MARKER in java:
    print("ADMIN_V20938_COURT_OPENING_GAP_CLOSURE_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_GUARANTEED_COURT_OPENING_FLOOR_V20937",
    "JAYUMINTON_EXACT_COURT_NUMBER_RANGE_V20935",
    "detectFinalVoicedOnsetV20937(",
    "protectOpeningRegionV20937(",
    "prepareNormalizedAmplifiedPlayback()",
    "fallbackToDirectTts()",
    "currentAmplifiedSynthId",
    "courtNumberStartFrameV20935",
    "VOICE_PEAK_CEILING_DBFS = -2.0",
):
    if token not in java:
        raise SystemExit("v209.38 prerequisite missing: " + token)

# ---------------------------------------------------------------------------
# Marker + stable per-completed-synthesis state.
# ---------------------------------------------------------------------------
field_anchor = '    private static final String GUARANTEED_COURT_OPENING_FLOOR = "JAYUMINTON_GUARANTEED_COURT_OPENING_FLOOR_V20937";\n'
field_insert = field_anchor + '''    private static final String COURT_OPENING_GAP_CLOSURE = "''' + MARKER + '''";
    private volatile int normalizingNumberStartFrameV20938 = -1;
    private volatile int normalizingNumberEndFrameV20938 = -1;
    private volatile int normalizingPhraseEndFrameV20938 = -1;
    private int courtSynthRetryCountV20938 = 0;
    private volatile long voiceGenerationV20938 = 0L;
    private SpeakRequest ttsRecoveryRequestV20938;
    private int ttsEngineRecoveryBudgetV20938 = 1;
    private final java.util.ArrayDeque<SpeakRequest> courtVoiceQueueV20938 =
            new java.util.ArrayDeque<>();
'''
if java.count(field_anchor) != 1:
    raise SystemExit("v209.38 marker field anchor mismatch: " + str(java.count(field_anchor)))
java = java.replace(field_anchor, field_insert, 1)

# ---------------------------------------------------------------------------
# Replace synth onDone handoff with an immutable snapshot. Crucially detach the
# completed file from amplifiedVoiceFile before posting to UI; a new request's
# releaseAmplifiedVoice(true) can no longer delete the completed file.
# ---------------------------------------------------------------------------
done_old = '''                if (utteranceId != null && utteranceId.equals(currentAmplifiedSynthId)) {
                    currentAmplifiedSynthId = "";
                    runOnUiThread(MainActivity.this::prepareNormalizedAmplifiedPlayback);
                    return;
                }'''
done_new = '''                if (utteranceId != null && utteranceId.equals(currentAmplifiedSynthId)) {
                    final String completedSynthIdV20938 = utteranceId;
                    final File completedFileV20938 = amplifiedVoiceFile;
                    final SpeakRequest completedRequestV20938 = activeRepeatRequest;
                    final int completedNumberStartV20938 = courtNumberStartFrameV20935;
                    final int completedNumberEndV20938 = courtNumberEndFrameV20935;
                    final int completedPhraseEndV20938 = courtPhraseEndFrameV20935;
                    currentAmplifiedSynthId = "";
                    // Detach ownership before UI handoff. A newer request may call
                    // releaseAmplifiedVoice(true), but it must not delete this file.
                    amplifiedVoiceFile = null;
                    runOnUiThread(() -> prepareCompletedAmplifiedPlaybackV20938(
                            completedSynthIdV20938, completedFileV20938,
                            completedRequestV20938, completedNumberStartV20938,
                            completedNumberEndV20938, completedPhraseEndV20938));
                    return;
                }'''
if java.count(done_old) != 1:
    raise SystemExit("v209.38 synth-done anchor mismatch: " + str(java.count(done_old)))
java = java.replace(done_old, done_new, 1)

# Guard every non-synthesis TTS callback with request generation identity. Without
# this, tts.stop() from a newer announcement can deliver a stale onStop/onDone
# that tears down the new synthesis/audio ducking.
direct_done_old = '''                runOnUiThread(() -> {
                    if (activeRepeatRequest != null && remainingVoiceRepeats > 0) {
                        speakNextRepeat();
                    } else {
                        finishVoiceCycleV20938();
                    }
                });
            }

            @Override
            public void onError(String utteranceId) {'''
direct_done_new = '''                if (!isActiveDirectUtteranceV20938(utteranceId)) return;
                final String completedDirectIdV20938 = utteranceId;
                runOnUiThread(() -> {
                    if (!isActiveDirectUtteranceV20938(completedDirectIdV20938)) return;
                    if (activeRepeatRequest != null && remainingVoiceRepeats > 0) {
                        speakNextRepeat();
                    } else {
                        speaking.set(false);
                        activeRepeatRequest = null;
                        releaseAmplifiedVoice(true);
                        restoreAudio();
                    }
                });
            }

            @Override
            public void onError(String utteranceId) {'''
if java.count(direct_done_old) != 1:
    raise SystemExit("v209.38 direct done guard anchor mismatch: " + str(java.count(direct_done_old)))
java = java.replace(direct_done_old, direct_done_new, 1)

direct_error_old = '''                speaking.set(false);
                runOnUiThread(() -> {
                    releaseAmplifiedVoice(true);
                    restoreAudio();
                });
            }

            @Override
            public void onStop(String utteranceId, boolean interrupted) {'''
direct_error_new = '''                if (!isActiveDirectUtteranceV20938(utteranceId)) return;
                final String failedDirectIdV20938 = utteranceId;
                runOnUiThread(() -> {
                    if (!isActiveDirectUtteranceV20938(failedDirectIdV20938)) return;
                    if (remainingVoiceRepeats > 0) {
                        speakNextRepeat();
                    } else {
                        recoverTtsEngineOnceV20938();
                    }
                });
            }

            @Override
            public void onStop(String utteranceId, boolean interrupted) {'''
if java.count(direct_error_old) != 1:
    raise SystemExit("v209.38 direct error guard anchor mismatch: " + str(java.count(direct_error_old)))
java = java.replace(direct_error_old, direct_error_new, 1)

direct_stop_old = '''                speaking.set(false);
                runOnUiThread(() -> {
                    releaseAmplifiedVoice(true);
                    restoreAudio();
                });
            }
'''
direct_stop_new = '''                if (!isActiveDirectUtteranceV20938(utteranceId)) return;
                final String stoppedDirectIdV20938 = utteranceId;
                runOnUiThread(() -> {
                    if (!isActiveDirectUtteranceV20938(stoppedDirectIdV20938)) return;
                    if (remainingVoiceRepeats > 0) {
                        speakNextRepeat();
                    } else {
                        recoverTtsEngineOnceV20938();
                    }
                });
            }
'''
if java.count(direct_stop_old) != 1:
    raise SystemExit("v209.38 direct stop guard anchor mismatch: " + str(java.count(direct_stop_old)))
java = java.replace(direct_stop_old, direct_stop_new, 1)

# Tag direct utterances with a per-request generation, so even repeated court IDs
# cannot make a stale callback look current.
direct_id_old = 'activeRepeatRequest.id + "-repeat-" + repeatNumber'
direct_id_new = 'activeRepeatRequest.id + "-g" + voiceGenerationV20938 + "-repeat-" + repeatNumber'
if java.count(direct_id_old) != 1:
    raise SystemExit("v209.38 direct id anchor mismatch: " + str(java.count(direct_id_old)))
java = java.replace(direct_id_old, direct_id_new, 1)

# Install the new identity before tts.stop(). This also protects against a
# theoretically synchronous stop callback from the previous direct utterance.
pre_stop_old = '''        // Cancel any previous synthesis/playback without restoring the ducked music yet.
        currentAmplifiedSynthId = "";
        try { tts.stop(); } catch (Exception ignored) {}'''
pre_stop_new = '''        // Install new request identity BEFORE tts.stop().
        if (request != ttsRecoveryRequestV20938) {
            ttsEngineRecoveryBudgetV20938 = 1;
        } else {
            ttsRecoveryRequestV20938 = null;
        }
        activeRepeatRequest = request;
        remainingVoiceRepeats = VOICE_REPEAT_COUNT;
        courtSynthRetryCountV20938 = 0;
        voiceGenerationV20938++;
        // Cancel previous synthesis/playback without restoring ducked music yet.
        currentAmplifiedSynthId = "";
        try { tts.stop(); } catch (Exception ignored) {}'''
if java.count(pre_stop_old) != 1:
    raise SystemExit("v209.38 pre-stop generation anchor mismatch: " + str(java.count(pre_stop_old)))
java = java.replace(pre_stop_old, pre_stop_new, 1)


prepare_anchor = "    private void prepareNormalizedAmplifiedPlayback() {\n"
if java.count(prepare_anchor) != 1:
    raise SystemExit("v209.38 prepare anchor mismatch")

prepare_helper = r'''    private boolean isCourtFinishRequestV20938(SpeakRequest request) {
        return request != null && request.id != null &&
                request.id.startsWith("court_finish_");
    }

    private void enqueueCourtVoiceV20938(SpeakRequest request) {
        if (!isCourtFinishRequestV20938(request)) return;
        synchronized (courtVoiceQueueV20938) {
            courtVoiceQueueV20938.addLast(request);
        }
    }

    private SpeakRequest pollCourtVoiceV20938() {
        synchronized (courtVoiceQueueV20938) {
            return courtVoiceQueueV20938.pollFirst();
        }
    }

    private void clearCourtVoiceQueueV20938() {
        synchronized (courtVoiceQueueV20938) {
            courtVoiceQueueV20938.clear();
        }
    }

    private boolean startNextQueuedCourtVoiceV20938() {
        SpeakRequest next = pollCourtVoiceV20938();
        if (next == null) return false;
        speakNative(next);
        return true;
    }

    private void finishVoiceCycleV20938() {
        currentAmplifiedSynthId = "";
        releaseAmplifiedVoice(true);
        remainingVoiceRepeats = 0;
        speaking.set(false);
        activeRepeatRequest = null;
        if (!startNextQueuedCourtVoiceV20938()) {
            restoreAudio();
        }
    }

    private void recoverTtsEngineOnceV20938() {
        SpeakRequest request = activeRepeatRequest;
        if (request == null) {
            speaking.set(false);
            restoreAudio();
            return;
        }
        if (ttsEngineRecoveryBudgetV20938 <= 0) {
            speaking.set(false);
            activeRepeatRequest = null;
            releaseAmplifiedVoice(true);
            if (!startNextQueuedCourtVoiceV20938()) restoreAudio();
            return;
        }

        ttsEngineRecoveryBudgetV20938--;
        ttsRecoveryRequestV20938 = request;
        pendingRequest = request;
        remainingVoiceRepeats = 0;
        activeRepeatRequest = null;
        currentAmplifiedSynthId = "";
        releaseAmplifiedVoice(true);
        speaking.set(false);
        restoreAudio();
        ttsReady.set(false);
        ttsInitAttempts = 0;
        initTts(true);
    }

    private boolean isActiveDirectUtteranceV20938(String utteranceId) {
        SpeakRequest request = activeRepeatRequest;
        if (utteranceId == null || request == null || request.id == null) return false;
        String prefix = request.id + "-g" + voiceGenerationV20938 + "-repeat-";
        return utteranceId.startsWith(prefix);
    }

    private void prepareCompletedAmplifiedPlaybackV20938(
            String completedSynthId, File completedFile, SpeakRequest completedRequest,
            int numberStartFrame, int numberEndFrame, int phraseEndFrame) {
        // If another court announcement superseded this one before UI handoff,
        // discard only the stale completed file. Never touch the newer request.
        if (completedRequest == null || activeRepeatRequest != completedRequest) {
            if (completedFile != null) {
                try { completedFile.delete(); } catch (Exception ignored) {}
            }
            return;
        }

        if (completedFile == null || !completedFile.exists() || completedFile.length() <= 0) {
            fallbackToDirectTts();
            return;
        }

        amplifiedVoiceFile = completedFile;
        normalizingNumberStartFrameV20938 = numberStartFrame;
        normalizingNumberEndFrameV20938 = numberEndFrame;
        normalizingPhraseEndFrameV20938 = phraseEndFrame;
        try {
            prepareNormalizedAmplifiedPlayback();
        } finally {
            normalizingNumberStartFrameV20938 = -1;
            normalizingNumberEndFrameV20938 = -1;
            normalizingPhraseEndFrameV20938 = -1;
        }
    }

'''
java = java.replace(prepare_anchor, prepare_helper + prepare_anchor, 1)

# Court-finish announcements are critical and can be long. Do not let a later
# finishCourt directSpeak/QUEUE_FLUSH erase an announcement still synthesizing or
# playing. Keep only court-finish requests in a native FIFO; explicit stop clears it.
speak_entry_old = '''    private void speakNative(SpeakRequest request) {
        if (tts == null || !ttsReady.get()) {
            pendingRequest = request;
            if (!ttsInitializing) {
                ttsInitAttempts = 0;
                initTts(true);
            }
            return;
        }
'''
speak_entry_new = '''    private void speakNative(SpeakRequest request) {
        if (isCourtFinishRequestV20938(request)) {
            boolean busy = speaking.get() || activeRepeatRequest != null ||
                    amplifiedVoicePlayer != null ||
                    (currentAmplifiedSynthId != null && !currentAmplifiedSynthId.isEmpty());
            if (busy) {
                enqueueCourtVoiceV20938(request);
                return;
            }
        }

        if (tts == null || !ttsReady.get()) {
            if (isCourtFinishRequestV20938(request) && pendingRequest != null) {
                enqueueCourtVoiceV20938(request);
            } else {
                pendingRequest = request;
            }
            if (!ttsInitializing) {
                ttsInitAttempts = 0;
                initTts(true);
            }
            return;
        }
'''
if java.count(speak_entry_old) != 1:
    raise SystemExit("v209.38 speak queue anchor mismatch: " + str(java.count(speak_entry_old)))
java = java.replace(speak_entry_old, speak_entry_new, 1)

finish_old = '''    private void finishAmplifiedSpeech() {
        currentAmplifiedSynthId = "";
        releaseAmplifiedVoice(true);
        remainingVoiceRepeats = 0;
        speaking.set(false);
        activeRepeatRequest = null;
        restoreAudio();
    }'''
finish_new = '''    private void finishAmplifiedSpeech() {
        finishVoiceCycleV20938();
    }'''
if java.count(finish_old) != 1:
    raise SystemExit("v209.38 finish queue anchor mismatch: " + str(java.count(finish_old)))
java = java.replace(finish_old, finish_new, 1)

# Explicit user/app stop means stop everything, including queued court calls.
stop_queue_old = '''                remainingVoiceRepeats = 0;
                activeRepeatRequest = null;
                currentAmplifiedSynthId = "";
                releaseAmplifiedVoice(true);'''
stop_queue_new = '''                remainingVoiceRepeats = 0;
                activeRepeatRequest = null;
                clearCourtVoiceQueueV20938();
                currentAmplifiedSynthId = "";
                releaseAmplifiedVoice(true);'''
if java.count(stop_queue_old) != 1:
    raise SystemExit("v209.38 stop queue anchor mismatch: " + str(java.count(stop_queue_old)))
java = java.replace(stop_queue_old, stop_queue_new, 1)


# P135 used live collection fields during final DSP. Use the immutable snapshot
# while the completed WAV is being normalized.
old_range_call = '''                        courtNumberStartFrameV20935, courtNumberEndFrameV20935,
                        courtPhraseEndFrameV20935);'''
new_range_call = '''                        normalizingNumberStartFrameV20938, normalizingNumberEndFrameV20938,
                        normalizingPhraseEndFrameV20938);'''
if java.count(old_range_call) != 1:
    raise SystemExit("v209.38 final range call anchor mismatch: " + str(java.count(old_range_call)))
java = java.replace(old_range_call, new_range_call, 1)

# Reset retry budget for every genuinely new spoken request.
request_anchor = '''        activeRepeatRequest = request;
        remainingVoiceRepeats = VOICE_REPEAT_COUNT;
        startAmplifiedSynthesis();
'''
request_new = '''        activeRepeatRequest = request;
        remainingVoiceRepeats = VOICE_REPEAT_COUNT;
        courtSynthRetryCountV20938 = 0;
        startAmplifiedSynthesis();
'''
if java.count(request_anchor) != 1:
    raise SystemExit("v209.38 request reset anchor mismatch: " + str(java.count(request_anchor)))
java = java.replace(request_anchor, request_new, 1)

# One clean synthesized retry for court-finish announcements before direct TTS.
# The second failure still ALWAYS speaks through the existing direct TTS path.
fallback_old = '''    private void fallbackToDirectTts() {
        currentAmplifiedSynthId = "";
        releaseAmplifiedVoice(true);
        if (activeRepeatRequest == null || tts == null) {
            speaking.set(false);
            activeRepeatRequest = null;
            restoreAudio();
            return;
        }
        // Direct TTS remains as a compatibility fallback. It is still stream-max/volume=1.0.
        remainingVoiceRepeats = VOICE_REPEAT_COUNT;
        speakNextRepeat();
    }
'''
fallback_new = '''    private void fallbackToDirectTts() {
        currentAmplifiedSynthId = "";
        releaseAmplifiedVoice(true);
        if (activeRepeatRequest == null || tts == null) {
            speaking.set(false);
            activeRepeatRequest = null;
            restoreAudio();
            return;
        }

        // v209.38: a transient synth/file failure should not immediately bypass
        // every final-WAV protection. Retry synthesis once for a court finish.
        if (isCourtFinishAnnouncement(activeRepeatRequest) &&
                courtSynthRetryCountV20938 < 1 && ttsReady.get()) {
            courtSynthRetryCountV20938++;
            startAmplifiedSynthesis();
            return;
        }

        // ALWAYS-SPEAK final fallback. Never block a critical announcement just
        // because offline loudness processing could not be used.
        remainingVoiceRepeats = VOICE_REPEAT_COUNT;
        speakNextRepeat();
    }
'''
if java.count(fallback_old) != 1:
    raise SystemExit("v209.38 fallback anchor mismatch: " + str(java.count(fallback_old)))
java = java.replace(fallback_old, fallback_new, 1)

# If synth file exists but DSP cannot validate it, preserve audibility by
# playing the raw synthesized voice instead of deleting it.
raw_dsp_old = '''        boolean maximizeFullCourtFinish = isCourtFinishAnnouncement(activeRepeatRequest);
        if (!normalizeAndLimitVoiceWav(
                amplifiedVoiceFile, maximizeFullCourtFinish)) {
            fallbackToDirectTts();
            return;
        }
        startAmplifiedRepeatPlayback();'''
raw_dsp_new = '''        boolean maximizeFullCourtFinish = isCourtFinishAnnouncement(activeRepeatRequest);
        if (!normalizeAndLimitVoiceWav(
                amplifiedVoiceFile, maximizeFullCourtFinish)) {
            if (maximizeFullCourtFinish && amplifiedVoiceFile != null &&
                    amplifiedVoiceFile.exists() && amplifiedVoiceFile.length() > 0) {
                // RAW_SYNTH_ALWAYS_AUDIBLE_V20938
                startAmplifiedRepeatPlayback();
                return;
            }
            fallbackToDirectTts();
            return;
        }
        startAmplifiedRepeatPlayback();'''
if java.count(raw_dsp_old) != 1:
    raise SystemExit("v209.38 raw DSP fallback anchor mismatch: " + str(java.count(raw_dsp_old)))
java = java.replace(raw_dsp_old, raw_dsp_new, 1)

# tts.speak() can return ERROR without any callback. Consume the remaining
# direct attempts, then rebuild Android TTS once with the same pending request.
direct_result_old = '''        if (result == TextToSpeech.ERROR) {
            remainingVoiceRepeats = 0;
            speaking.set(false);
            activeRepeatRequest = null;
            restoreAudio();
        }'''
direct_result_new = '''        if (result == TextToSpeech.ERROR) {
            if (remainingVoiceRepeats > 0) {
                speakNextRepeat();
            } else {
                recoverTtsEngineOnceV20938();
            }
        }'''
if java.count(direct_result_old) != 1:
    raise SystemExit("v209.38 direct result anchor mismatch: " + str(java.count(direct_result_old)))
java = java.replace(direct_result_old, direct_result_new, 1)


# ---------------------------------------------------------------------------
# Replace v209.37 opening analysis/protection with lower-floor adaptive analysis,
# absolute floor + relative balance, adaptive phrase-end detection, and fallback.
# Keep the v209.37 public helper names so lineage/build assertions remain valid.
# ---------------------------------------------------------------------------
start = java.find("    private int detectFinalVoicedOnsetV20937(")
end = java.find("    private void applyCourtOpeningFixedGain(", start)
if start < 0 or end < 0:
    raise SystemExit("v209.38 opening helper boundaries missing")

replacement = r'''    private double frameRmsV20938(
            byte[] wav, int dataOffset, int sampleCount, int start, int end) {
        if (wav == null || sampleCount <= 0 || end <= start) return 0.0;
        start = Math.max(0, Math.min(sampleCount, start));
        end = Math.max(start, Math.min(sampleCount, end));
        double sq = 0.0;
        int count = 0;
        for (int i = start; i < end; i++) {
            int off = dataOffset + i * 2;
            if (off < 0 || off + 1 >= wav.length) break;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            double v = sample / 32768.0;
            sq += v * v;
            count++;
        }
        return count > 0 ? Math.sqrt(sq / count) : 0.0;
    }

    private double activeRmsLowFloorV20938(
            byte[] wav, int dataOffset, int sampleCount, int start, int end) {
        if (wav == null || sampleCount <= 0 || end <= start) return 0.0;
        start = Math.max(0, Math.min(sampleCount, start));
        end = Math.max(start, Math.min(sampleCount, end));

        // Much lower than the old -46 dBFS gate. TTS WAV leading silence is
        // digital/near-digital silence, so -78 dBFS keeps genuinely tiny speech
        // while rejecting zero-padding and negligible quantization residue.
        final double floor = dbToLinear(-86.0);
        double sq = 0.0;
        long count = 0L;
        for (int i = start; i < end; i++) {
            int off = dataOffset + i * 2;
            if (off < 0 || off + 1 >= wav.length) break;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            double v = sample / 32768.0;
            if (Math.abs(v) < floor) continue;
            sq += v * v;
            count++;
        }
        return count > 0L ? Math.sqrt(sq / count) : 0.0;
    }

    private int detectFinalVoicedOnsetV20937(
            byte[] wav, int dataOffset, int sampleCount, int sampleRate, int channels) {
        if (wav == null || sampleCount <= 0 || sampleRate < 8000 || channels < 1) return -1;

        final int frameSamples = Math.max(
                channels, (int) Math.round(sampleRate * channels * 0.012));
        final int searchEnd = Math.min(
                sampleCount, (int) Math.round(sampleRate * channels * 2.00));

        double minNonZero = Double.POSITIVE_INFINITY;
        for (int pos = 0; pos < searchEnd; pos += frameSamples) {
            double rms = frameRmsV20938(
                    wav, dataOffset, sampleCount, pos, Math.min(searchEnd, pos + frameSamples));
            if (rms > 1.0e-10) minNonZero = Math.min(minNonZero, rms);
        }
        double absoluteFloor = dbToLinear(-82.0);
        double adaptive = Double.isFinite(minNonZero)
                ? Math.max(absoluteFloor, Math.min(dbToLinear(-72.0), minNonZero * 2.5))
                : absoluteFloor;

        // Find the first strong frame, but DO NOT return it immediately.
        // A very quiet N번 may exist before a much louder "코트".
        int strongOnset = -1;
        for (int pos = 0; pos < searchEnd; pos += frameSamples) {
            int limit = Math.min(searchEnd, pos + frameSamples);
            double rms = frameRmsV20938(wav, dataOffset, sampleCount, pos, limit);
            if (rms >= adaptive) {
                strongOnset = pos;
                break;
            }
        }

        final double sampleFloor = dbToLinear(-86.0);
        int earlySearchEnd = strongOnset >= 0
                ? Math.min(searchEnd, strongOnset + frameSamples)
                : searchEnd;
        for (int i = 0; i < earlySearchEnd; i++) {
            int off = dataOffset + i * 2;
            if (off < 0 || off + 1 >= wav.length) break;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            if (Math.abs(sample / 32768.0) >= sampleFloor) {
                return Math.max(0, (i / channels) * channels);
            }
        }
        return strongOnset;
    }

    private int detectOpeningPhraseEndV20938(
            byte[] wav, int dataOffset, int sampleCount,
            int onset, int sampleRate, int channels) {
        if (wav == null || onset < 0 || sampleRate < 8000 || channels < 1) return -1;
        final int samplesPerSecond = Math.max(channels, sampleRate * channels);
        final int frameSamples = Math.max(
                channels, (int) Math.round(samplesPerSecond * 0.020));
        final int minEnd = Math.min(
                sampleCount, onset + (int) Math.round(samplesPerSecond * 0.75));
        final int maxEnd = Math.min(
                sampleCount, onset + (int) Math.round(samplesPerSecond * 2.80));
        if (maxEnd <= minEnd) return maxEnd;

        // Relative quiet threshold derived from the opening's own active energy,
        // with a low absolute floor so a quiet "N번" never disappears.
        double openingProbe = activeRmsLowFloorV20938(
                wav, dataOffset, sampleCount, onset, maxEnd);
        double quiet = Math.max(
                dbToLinear(-74.0),
                openingProbe > 1.0e-9 ? openingProbe * 0.10 : dbToLinear(-60.0));
        int quietFramesNeeded = Math.max(
                3, (int) Math.ceil(0.12 / 0.020));
        int quietFrames = 0;
        for (int pos = minEnd; pos < maxEnd; pos += frameSamples) {
            int limit = Math.min(maxEnd, pos + frameSamples);
            double rms = frameRmsV20938(wav, dataOffset, sampleCount, pos, limit);
            if (rms <= quiet) {
                quietFrames++;
                if (quietFrames >= quietFramesNeeded) {
                    return Math.max(
                            minEnd, pos - (quietFrames - 1) * frameSamples);
                }
            } else {
                quietFrames = 0;
            }
        }
        return maxEnd;
    }

    private void liftOpeningFrameFloorV20938(
            byte[] wav, int dataOffset, int sampleCount,
            int start, int end, int sampleRate, int channels) {
        if (wav == null || sampleCount <= 0 || end <= start ||
                sampleRate < 8000 || channels < 1) return;

        start = Math.max(0, Math.min(sampleCount, start));
        end = Math.max(start, Math.min(sampleCount, end));
        final int frameSamples = Math.max(
                channels, (int) Math.round(sampleRate * channels * 0.024));
        final double activityFloor = dbToLinear(-86.0);
        final double targetFrameRms = dbToLinear(-14.0);
        final double maxFrameGain = dbToLinear(36.0);
        final double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);

        // Deterministic OFFLINE frame floor, never runtime AGC: no detector
        // attack/release state and every frame gain is >= 1.0.
        for (int pos = start; pos < end; pos += frameSamples) {
            int limit = Math.min(end, pos + frameSamples);
            double rms = activeRmsLowFloorV20938(
                    wav, dataOffset, sampleCount, pos, limit);
            if (rms < activityFloor || rms >= targetFrameRms) continue;
            double gain = Math.max(
                    1.0, Math.min(maxFrameGain, targetFrameRms / rms));
            liftFinalRegionOnlyUpV20937(
                    wav, dataOffset, sampleCount, pos, limit, gain, ceiling);
        }
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
            writeFinalSampleV20935(
                    wav, dataOffset, i, original * gain, ceiling);
        }
    }

    private boolean protectOpeningRegionV20937(
            byte[] wav, int dataOffset, int sampleCount,
            int protectedStart, int protectedEnd,
            int referenceStart, int referenceEnd,
            int sampleRate, int channels) {
        if (wav == null || sampleCount <= 0 ||
                protectedEnd <= protectedStart) return false;

        protectedStart = Math.max(0, Math.min(sampleCount, protectedStart));
        protectedEnd = Math.max(protectedStart, Math.min(sampleCount, protectedEnd));
        referenceStart = Math.max(protectedEnd, Math.min(sampleCount, referenceStart));
        referenceEnd = Math.max(referenceStart, Math.min(sampleCount, referenceEnd));
        if (protectedEnd <= protectedStart) return false;

        final double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
        final double absoluteFloorRms = dbToLinear(-10.5);
        final double maxPassGain = dbToLinear(8.0);

        boolean measured = false;
        for (int pass = 0; pass < 3; pass++) {
            double protectedRms = activeRmsLowFloorV20938(
                    wav, dataOffset, sampleCount, protectedStart, protectedEnd);
            if (protectedRms <= 1.0e-10) return false;
            measured = true;

            double referenceRms = referenceEnd > referenceStart
                    ? activeRmsLowFloorV20938(
                            wav, dataOffset, sampleCount, referenceStart, referenceEnd)
                    : 0.0;

            // Relative target + absolute floor. Uniformly quiet speech can no
            // longer bypass correction merely because the dB gap is small.
            double targetRms = Math.max(absoluteFloorRms, referenceRms);
            if (protectedRms >= targetRms / dbToLinear(1.5)) break;

            double desiredGain = targetRms / protectedRms;
            double gain = Math.max(1.0, Math.min(maxPassGain, desiredGain));
            if (!Double.isFinite(gain) || gain <= 1.0001) break;
            liftFinalRegionOnlyUpV20937(
                    wav, dataOffset, sampleCount,
                    protectedStart, protectedEnd, gain, ceiling);
        }

        // Post-condition is diagnostic only. NEVER block playback.
        double afterProtected = activeRmsLowFloorV20938(
                wav, dataOffset, sampleCount, protectedStart, protectedEnd);
        boolean openingFloorReachedV20938 =
                afterProtected > 1.0e-10 &&
                afterProtected >= absoluteFloorRms / dbToLinear(2.0);
        if (!openingFloorReachedV20938) {
            // NEVER_SUPPRESS_PLAYBACK_V20938
            // Peak ceiling may make the floor mathematically unreachable. Keep
            // and play the strongest safe final WAV produced above.
        }
        return measured;
    }

    private void balanceExactCourtNumberFinalWavV20935(
            byte[] wav, int dataOffset, int dataSize, int sampleRate, int channels,
            int numberStartFrame, int numberEndFrame, int phraseEndFrame) {
        if (wav == null || dataSize < 4 || sampleRate < 8000 || channels < 1) return;

        final int sampleCount = dataSize / 2;
        final int onset = detectFinalVoicedOnsetV20937(
                wav, dataOffset, sampleCount, sampleRate, channels);
        if (onset < 0) return;

        int adaptivePhraseEnd = detectOpeningPhraseEndV20938(
                wav, dataOffset, sampleCount, onset, sampleRate, channels);
        if (adaptivePhraseEnd <= onset) adaptivePhraseEnd = sampleCount;

        // Exact N번 boundary is preferred whenever Android supplies it, even if
        // there is no later callback marking the end of "나왔습니다".
        boolean exactNumberBoundary =
                numberStartFrame >= 0 && numberEndFrame > numberStartFrame;
        boolean exactApplied = false;
        if (exactNumberBoundary) {
            int numberStart = Math.max(onset, numberStartFrame * channels);
            int numberEnd = Math.min(sampleCount, numberEndFrame * channels);
            int phraseEnd = phraseEndFrame > numberEndFrame
                    ? Math.min(sampleCount, phraseEndFrame * channels)
                    : adaptivePhraseEnd;
            if (numberEnd > numberStart && phraseEnd > numberEnd) {
                exactApplied = protectOpeningRegionV20937(
                        wav, dataOffset, sampleCount,
                        numberStart, numberEnd,
                        numberEnd, phraseEnd,
                        sampleRate, channels);
            }
        }

        // Always protect the COMPLETE opening phrase as well. This catches:
        // - engines with no lexical frame boundary,
        // - exact-range measurements that were too tiny to measure,
        // - the whole "N번 코트 나왔습니다" region being uniformly quiet.
        int phraseEnd = adaptivePhraseEnd;
        if (phraseEndFrame > 0) {
            int reported = phraseEndFrame * channels;
            if (reported > onset && reported <= sampleCount) {
                phraseEnd = Math.max(phraseEnd, reported);
            }
        }
        phraseEnd = Math.min(sampleCount, phraseEnd);
        if (phraseEnd <= onset) return;

        int referenceStart = phraseEnd;
        int samplesPerSecond = Math.max(channels, sampleRate * channels);
        int referenceEnd = Math.min(
                sampleCount,
                phraseEnd + (int) Math.round(samplesPerSecond * 1.40));
        protectOpeningRegionV20937(
                wav, dataOffset, sampleCount,
                onset, phraseEnd,
                referenceStart, referenceEnd,
                sampleRate, channels);

        // Final local floor catches a tiny N번 even if adjacent "코트" is loud.
        liftOpeningFrameFloorV20938(
                wav, dataOffset, sampleCount,
                onset, phraseEnd, sampleRate, channels);

        // Keep literal use so build-time verification proves exact-path fallback
        // is present rather than an unconditional return after exact mode.
        if (!exactApplied) {
            // ADAPTIVE_FINAL_WAV_FALLBACK_V20938 already applied above.
        }
    }

'''
java = java[:start] + replacement + java[end:]

# Extend diagnostics marker chain.
status_old = '+ ":" + EXACT_COURT_NUMBER_RANGE + ":" + GUARANTEED_COURT_OPENING_FLOOR + ":ready="'
status_new = '+ ":" + EXACT_COURT_NUMBER_RANGE + ":" + GUARANTEED_COURT_OPENING_FLOOR + ":" + COURT_OPENING_GAP_CLOSURE + ":ready="'
if status_old not in java:
    raise SystemExit("v209.38 status anchor missing")
java = java.replace(status_old, status_new, 1)

for required in (
    MARKER,
    "activeRmsLowFloorV20938(",
    "liftOpeningFrameFloorV20938(",
    "RAW_SYNTH_ALWAYS_AUDIBLE_V20938",
    "courtVoiceQueueV20938",
    "enqueueCourtVoiceV20938(",
    "startNextQueuedCourtVoiceV20938(",
    "finishVoiceCycleV20938(",
    "recoverTtsEngineOnceV20938(",
    "ttsEngineRecoveryBudgetV20938",
    "strongOnset",
    "isActiveDirectUtteranceV20938(",
    "voiceGenerationV20938",
    "targetFrameRms = dbToLinear(-14.0)",
    "detectOpeningPhraseEndV20938(",
    "dbToLinear(-86.0)",
    "dbToLinear(-10.5)",
    "ADAPTIVE_FINAL_WAV_FALLBACK_V20938",
    "NEVER_SUPPRESS_PLAYBACK_V20938",
    "prepareCompletedAmplifiedPlaybackV20938(",
    "amplifiedVoiceFile = null;",
    "normalizingNumberStartFrameV20938",
    "courtSynthRetryCountV20938 < 1",
    "ALWAYS-SPEAK final fallback",
):
    if required not in java:
        raise SystemExit("v209.38 output missing: " + required)

# Safety contracts.
for forbidden in (
    "if (!openingFloorReachedV20938) return false",
    "openingFloorReachedV20938) return false",
    "validation failure => silence",
):
    if forbidden in java:
        raise SystemExit("v209.38 forbidden playback suppression found: " + forbidden)

java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20938_COURT_OPENING_GAP_CLOSURE_OK")
