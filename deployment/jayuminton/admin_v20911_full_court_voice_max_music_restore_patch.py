#!/usr/bin/env python3
"""Maximize the complete 경기종료 announcement and guarantee page-music restore.

v209.10 intentionally maximized only the first ``N번 코트`` text range.  The
confirmed product requirement is broader: from ``N번 코트 나왔습니다`` through
all called names and ``N번 코트로 들어가 주세요`` the complete announcement
must stay at maximum safe loudness.  This patch therefore removes range-based
partial processing and selects an aggressive full-utterance compressor/target
only for verified ``court_finish_`` requests. Other TTS remains unchanged.

On Galaxy Tab the announcement and WebView music share STREAM_MUSIC, so lowering
the Android stream would lower both. The page's existing per-element ducking is
explicitly invoked instead, then restored on completion, stop, error, or process
recovery; external players continue to use Android transient ducking.
"""

from pathlib import Path
import sys


java_path = Path(sys.argv[1] if len(sys.argv) > 1 else
                 "app/src/main/java/com/jayuminton/admin/MainActivity.java")
text = java_path.read_text(encoding="utf-8")

MARKER = "JAYUMINTON_FULL_COURT_VOICE_MAX_MUSIC_RESTORE_V20911"
if MARKER in text:
    print("ADMIN_FULL_COURT_VOICE_MAX_MUSIC_RESTORE_V20911_ALREADY_OK")
    raise SystemExit(0)

for required in (
    "JAYUMINTON_COURT_OPENING_MAX_OUTPUT_V20910",
    "JAYUMINTON_AUDIBLE_MUSIC_DUCK_V20889",
    "maximizeCourtOpeningPcm(",
    "courtOpeningTextEndIndex",
    "private void restoreAudio()",
):
    if required not in text:
        raise SystemExit("v209.11 prerequisite missing: " + required)

old_constants = '''    private static final String COURT_OPENING_MAX_OUTPUT = "JAYUMINTON_COURT_OPENING_MAX_OUTPUT_V20910";
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
new_constants = '''    private static final String COURT_OPENING_MAX_OUTPUT = "JAYUMINTON_COURT_OPENING_MAX_OUTPUT_V20910";
    private static final String FULL_COURT_VOICE_MAX_MUSIC_RESTORE = "''' + MARKER + '''";
    // Entire verified court-finish announcement: strong crest reduction plus
    // the loudest safe full-file target. Other messages keep the old profile.
    private static final double COURT_FINISH_TARGET_RMS_DBFS = -9.0;
    private static final double COURT_FINISH_COMP_RATIO = 6.0;
'''
if text.count(old_constants) != 1:
    raise SystemExit("v209.11 constants anchor mismatch: " + str(text.count(old_constants)))
text = text.replace(old_constants, new_constants, 1)

old_fields = '''    private volatile String currentAmplifiedSynthId = "";
    private volatile int courtOpeningTextEndIndex = -1;
    private volatile int courtOpeningStartFrame = -1;
    private volatile int courtOpeningEndFrame = -1;
    private int ttsInitAttempts = 0;
'''
new_fields = '''    private volatile String currentAmplifiedSynthId = "";
    private int ttsInitAttempts = 0;
'''
if text.count(old_fields) != 1:
    raise SystemExit("v209.11 range fields anchor mismatch: " + str(text.count(old_fields)))
text = text.replace(old_fields, new_fields, 1)

range_listener = '''            @Override
            public void onRangeStart(String utteranceId, int start, int end, int frame) {
                if (utteranceId == null || !utteranceId.equals(currentAmplifiedSynthId) ||
                        courtOpeningTextEndIndex <= 0 || frame < 0) return;
                if (courtOpeningStartFrame < 0) courtOpeningStartFrame = frame;
                // The first range beginning after "N번 코트" is its exact end frame.
                if (courtOpeningEndFrame < 0 && start >= courtOpeningTextEndIndex) {
                    courtOpeningEndFrame = frame;
                }
            }

'''
if text.count(range_listener) != 1:
    raise SystemExit("v209.11 range listener anchor mismatch: " + str(text.count(range_listener)))
text = text.replace(range_listener, "", 1)

old_synth = '''            currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();
            courtOpeningTextEndIndex = firstCourtOpeningTextEnd(activeRepeatRequest);
            courtOpeningStartFrame = -1;
            courtOpeningEndFrame = -1;
            Bundle synthParams = new Bundle();
'''
new_synth = '''            currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();
            Bundle synthParams = new Bundle();
'''
if text.count(old_synth) != 1:
    raise SystemExit("v209.11 synth range anchor mismatch: " + str(text.count(old_synth)))
text = text.replace(old_synth, new_synth, 1)

old_prepare = '''        boolean maximizeCourtOpening = firstCourtOpeningTextEnd(activeRepeatRequest) > 0;
        if (!normalizeAndLimitVoiceWav(
                amplifiedVoiceFile, maximizeCourtOpening,
                courtOpeningStartFrame, courtOpeningEndFrame)) {
'''
new_prepare = '''        boolean maximizeFullCourtFinish = isCourtFinishAnnouncement(activeRepeatRequest);
        if (!normalizeAndLimitVoiceWav(
                amplifiedVoiceFile, maximizeFullCourtFinish)) {
'''
if text.count(old_prepare) != 1:
    raise SystemExit("v209.11 prepare anchor mismatch: " + str(text.count(old_prepare)))
text = text.replace(old_prepare, new_prepare, 1)

old_classifier = '''    private int firstCourtOpeningTextEnd(SpeakRequest request) {
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
new_classifier = '''    private boolean isCourtFinishAnnouncement(SpeakRequest request) {
        if (request == null || request.id == null || request.text == null ||
                !request.id.startsWith("court_finish_")) return false;
        return request.text.trim().matches("(?s)^[1-4]\\\\s*번\\\\s*코트.*");
    }

    private boolean normalizeAndLimitVoiceWav(
            File file, boolean maximizeFullCourtFinish) {
'''
if text.count(old_classifier) != 1:
    raise SystemExit("v209.11 classifier anchor mismatch: " + str(text.count(old_classifier)))
text = text.replace(old_classifier, new_classifier, 1)

# The same compressor processes the full PCM stream. Only court-finish requests
# select the strong 6:1 ratio; greetings and all other speech remain at 3:1.
rate_anchor = '''            final double effectiveRate = Math.max(8000.0, sampleRate * (double) channels);
            final double attack = Math.exp(-1.0 / (attackSeconds * effectiveRate));
'''
rate_replacement = '''            final double effectiveRate = Math.max(8000.0, sampleRate * (double) channels);
            final double compressionRatio = maximizeFullCourtFinish
                    ? COURT_FINISH_COMP_RATIO : VOICE_COMP_RATIO;
            final double attack = Math.exp(-1.0 / (attackSeconds * effectiveRate));
'''
if text.count(rate_anchor) != 1:
    raise SystemExit("v209.11 compression rate anchor mismatch: " + str(text.count(rate_anchor)))
text = text.replace(rate_anchor, rate_replacement, 1)

if text.count("(1.0 / VOICE_COMP_RATIO) - 1.0") != 2:
    raise SystemExit("v209.11 compressor ratio use mismatch: " +
                     str(text.count("(1.0 / VOICE_COMP_RATIO) - 1.0")))
text = text.replace("(1.0 / VOICE_COMP_RATIO) - 1.0",
                    "(1.0 / compressionRatio) - 1.0")

old_partial_stats = '''            if (maximizeCourtOpening) {
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
'''
if text.count(old_partial_stats) != 1:
    raise SystemExit("v209.11 partial max anchor mismatch: " + str(text.count(old_partial_stats)))
text = text.replace(old_partial_stats, "", 1)

old_target = "            double targetRms = dbToLinear(VOICE_TARGET_RMS_DBFS);\n"
new_target = '''            double targetRms = dbToLinear(maximizeFullCourtFinish
                    ? COURT_FINISH_TARGET_RMS_DBFS : VOICE_TARGET_RMS_DBFS);
'''
if text.count(old_target) != 1:
    raise SystemExit("v209.11 target anchor mismatch: " + str(text.count(old_target)))
text = text.replace(old_target, new_target, 1)

# Delete the now-obsolete partial-range maximizer wholesale.
helper_start = text.find("    private void maximizeCourtOpeningPcm(")
helper_end = text.find("    private double dbToLinear(double db) {", helper_start)
if helper_start < 0 or helper_end < 0:
    raise SystemExit("v209.11 partial helper boundaries missing")
text = text[:helper_start] + text[helper_end:]

# Explicit WebView media ducking is necessary on tablets where voice and page
# music share STREAM_MUSIC. It restores each media element's exact saved volume.
music_helper_anchor = '''    private int audibleDuckedMusicVolume(int originalVolume) {
'''
music_helpers = '''    private void duckPageMusicForNativeVoice() {
        if (webView == null) return;
        runOnUiThread(() -> {
            try {
                webView.evaluateJavascript(
                        "(function(){if(typeof duckPageMediaForVoice==='function')duckPageMediaForVoice();})()",
                        null);
            } catch (Exception ignored) {}
        });
    }

    private void restorePageMusicAfterNativeVoice() {
        if (webView == null) return;
        runOnUiThread(() -> {
            try {
                webView.evaluateJavascript(
                        "(function(){if(typeof restorePageMediaVolume==='function')restorePageMediaVolume();})()",
                        null);
            } catch (Exception ignored) {}
        });
    }

'''
if text.count(music_helper_anchor) != 1:
    raise SystemExit("v209.11 music helper anchor mismatch: " + str(text.count(music_helper_anchor)))
text = text.replace(music_helper_anchor, music_helpers + music_helper_anchor, 1)

media_route_anchor = '''                if (mediaVoiceRoute) {
                    // Galaxy Tab TTS must stay on the media route for compatibility.
'''
media_route_replacement = '''                if (mediaVoiceRoute) {
                    // Voice and WebView music share STREAM_MUSIC on Galaxy Tab.
                    // Duck only the page media elements, never the shared stream.
                    duckPageMusicForNativeVoice();
                    // Galaxy Tab TTS must stay on the media route for compatibility.
'''
if text.count(media_route_anchor) != 1:
    raise SystemExit("v209.11 media route anchor mismatch: " + str(text.count(media_route_anchor)))
text = text.replace(media_route_anchor, media_route_replacement, 1)

restore_anchor = '''    private void restoreAudio() {
        synchronized (audioLock) {
'''
restore_replacement = '''    private void restoreAudio() {
        // Always restore WebView media too, including error/stop paths where the
        // AudioManager may already be unavailable.
        restorePageMusicAfterNativeVoice();
        synchronized (audioLock) {
'''
if text.count(restore_anchor) != 1:
    raise SystemExit("v209.11 restore anchor mismatch: " + str(text.count(restore_anchor)))
text = text.replace(restore_anchor, restore_replacement, 1)

old_status = '+ ":" + COURT_OPENING_MAX_OUTPUT + ":ready="'
new_status = '+ ":" + COURT_OPENING_MAX_OUTPUT + ":" + FULL_COURT_VOICE_MAX_MUSIC_RESTORE + ":ready="'
if old_status not in text:
    raise SystemExit("v209.11 status anchor missing")
text = text.replace(old_status, new_status, 1)

for required in (
    MARKER,
    "COURT_FINISH_TARGET_RMS_DBFS = -9.0",
    "COURT_FINISH_COMP_RATIO = 6.0",
    "isCourtFinishAnnouncement(activeRepeatRequest)",
    "duckPageMusicForNativeVoice();",
    "restorePageMusicAfterNativeVoice();",
    "restorePageMediaVolume",
    "FULL_COURT_VOICE_MAX_MUSIC_RESTORE + \":ready=\"",
):
    if required not in text:
        raise SystemExit("v209.11 output requirement missing: " + required)

for forbidden in (
    "maximizeCourtOpeningPcm(",
    "courtOpeningTextEndIndex",
    "courtOpeningStartFrame",
    "courtOpeningEndFrame",
    "public void onRangeStart(String utteranceId, int start, int end, int frame)",
    "COURT_OPENING_FALLBACK_SECONDS",
):
    if forbidden in text:
        raise SystemExit("v209.11 obsolete partial behavior survived: " + forbidden)

java_path.write_text(text, encoding="utf-8")
print("ADMIN_FULL_COURT_VOICE_MAX_MUSIC_RESTORE_V20911_OK")
