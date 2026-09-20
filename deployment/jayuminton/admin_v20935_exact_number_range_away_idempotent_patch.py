#!/usr/bin/env python3
"""v209.35:
1) Never resend already-away members during bulk 귀가.
2) Reintroduce TTS engine text->PCM range timing for the exact leading "N번"
   inside the ORIGINAL one-piece utterance, then match only that token's active
   RMS to the following "코트 나왔습니다" range before playback.

This does not split/re-synthesize the sentence. When the installed TTS engine
provides UtteranceProgressListener.onRangeStart timing, the correction uses the
engine's own lexical frame boundaries. If timing is unavailable, v209.34's
whole-opening fixed-gain path remains as compatibility fallback.
"""

from pathlib import Path
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")

HTML_MARKER = "JAYUMINTON_AWAY_IDEMPOTENT_V20935"
VOICE_MARKER = "JAYUMINTON_EXACT_COURT_NUMBER_RANGE_V20935"

if HTML_MARKER in html and VOICE_MARKER in java:
    print("ADMIN_V20935_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_CARD_STACK_BULK_STATUS_V20934",
    "selectedIdsCompleteV20934",
    "applyStatusV20934",
):
    if token not in html:
        raise SystemExit("v209.35 HTML prerequisite missing: " + token)

# ---------------------------------------------------------------------------
# BULK AWAY: already-away members are not sent to the server at all.
# ---------------------------------------------------------------------------
old_ids = """  async function applyStatusV20934(status,label){
    var ids=selectedIdsCompleteV20934();
    if(!ids.length){alert('멤버를 선택하세요.');return;}
    var before=null;
"""
new_ids = """  async function applyStatusV20934(status,label){
    var ids=selectedIdsCompleteV20934();
    if(!ids.length){alert('멤버를 선택하세요.');return;}
    /* JAYUMINTON_AWAY_IDEMPOTENT_V20935
       전체선택 -> 귀가에서 이미 귀가 완료된 멤버는 절대 서버 변경대상에
       다시 넣지 않는다. 기존 departedAt/귀가시간을 그대로 보존한다. */
    if(String(status)==='away'){
      var live=currentState(), statusById={};
      try{(live&&Array.isArray(live.members)?live.members:[]).forEach(function(m){
        statusById[String(m&&m.id!=null?m.id:'')]=String(m&&m.status||'');
      });}catch(_){}
      ids=ids.filter(function(id){return statusById[String(id)]!=='away';});
      if(!ids.length){
        clearBoth();
        try{renderState();}catch(_){}
        return;
      }
    }
    var before=null;
"""
if html.count(old_ids) != 1:
    raise SystemExit("v209.35 bulk-away anchor mismatch: " + str(html.count(old_ids)))
html = html.replace(old_ids, new_ids, 1)

# ---------------------------------------------------------------------------
# VOICE: exact TTS lexical range timing for "N번" in the original utterance.
# ---------------------------------------------------------------------------
for token in (
    "JAYUMINTON_BLUETOOTH_OPENING_FIXED_GAIN_V20934",
    "applyCourtOpeningFixedGain(pcm, makeup, sampleRate, channels)",
    "currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();",
    "tts.setOnUtteranceProgressListener(new UtteranceProgressListener()",
):
    if token not in java:
        raise SystemExit("v209.35 voice prerequisite missing: " + token)

# Fields used only during synthToFile. Volatile because TTS callbacks are not UI-thread bound.
field_anchor = '    private volatile String currentAmplifiedSynthId = "";\n'
field_insert = field_anchor + """    private static final String EXACT_COURT_NUMBER_RANGE = "JAYUMINTON_EXACT_COURT_NUMBER_RANGE_V20935";
    private volatile int courtNumberTextEndIndexV20935 = -1;
    private volatile int courtPhraseTextEndIndexV20935 = -1;
    private volatile int courtNumberStartFrameV20935 = -1;
    private volatile int courtNumberEndFrameV20935 = -1;
    private volatile int courtPhraseEndFrameV20935 = -1;
"""
if java.count(field_anchor) != 1:
    raise SystemExit("v209.35 field anchor mismatch: " + str(java.count(field_anchor)))
java = java.replace(field_anchor, field_insert, 1)

# Capture exact text-range frame timing supplied by the installed TTS engine.
listener_anchor = """            @Override
            public void onDone(String utteranceId) {
"""
listener_insert = """            @Override
            public void onRangeStart(String utteranceId, int start, int end, int frame) {
                if (utteranceId == null || !utteranceId.equals(currentAmplifiedSynthId) || frame < 0 ||
                        courtNumberTextEndIndexV20935 <= 0) return;
                if (courtNumberStartFrameV20935 < 0 && start < courtNumberTextEndIndexV20935) {
                    courtNumberStartFrameV20935 = frame;
                }
                if (courtNumberEndFrameV20935 < 0 && start >= courtNumberTextEndIndexV20935) {
                    courtNumberEndFrameV20935 = frame;
                }
                if (courtPhraseTextEndIndexV20935 > courtNumberTextEndIndexV20935 &&
                        courtPhraseEndFrameV20935 < 0 && start >= courtPhraseTextEndIndexV20935) {
                    courtPhraseEndFrameV20935 = frame;
                }
            }

            @Override
            public void onDone(String utteranceId) {
"""
if java.count(listener_anchor) != 1:
    raise SystemExit("v209.35 listener anchor mismatch: " + str(java.count(listener_anchor)))
java = java.replace(listener_anchor, listener_insert, 1)

# Arm lexical indices before asynchronous file synthesis begins.
synth_anchor = """            currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();
            Bundle synthParams = new Bundle();
"""
synth_replacement = """            currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();
            armExactCourtNumberRangeV20935(activeRepeatRequest);
            Bundle synthParams = new Bundle();
"""
if java.count(synth_anchor) != 1:
    raise SystemExit("v209.35 synth anchor mismatch: " + str(java.count(synth_anchor)))
java = java.replace(synth_anchor, synth_replacement, 1)

# Prefer exact token correction; retain v209.34 only when engine timing is unavailable.
old_call = """            if (maximizeFullCourtFinish) {
                applyCourtOpeningFixedGain(pcm, makeup, sampleRate, channels);
            }
"""
new_call = """            if (maximizeFullCourtFinish) {
                boolean exactNumberBalanced = applyExactCourtNumberGainV20935(
                        pcm, makeup, sampleRate, channels,
                        courtNumberStartFrameV20935, courtNumberEndFrameV20935,
                        courtPhraseEndFrameV20935);
                if (!exactNumberBalanced) {
                    applyCourtOpeningFixedGain(pcm, makeup, sampleRate, channels);
                }
            }
"""
if java.count(old_call) != 1:
    raise SystemExit("v209.35 normalize-call anchor mismatch: " + str(java.count(old_call)))
java = java.replace(old_call, new_call, 1)

helper_anchor = "    private void applyCourtOpeningFixedGain(\n"
if java.count(helper_anchor) != 1:
    raise SystemExit("v209.35 helper anchor mismatch: " + str(java.count(helper_anchor)))

helpers = r'''    private void armExactCourtNumberRangeV20935(SpeakRequest request) {
        courtNumberTextEndIndexV20935 = -1;
        courtPhraseTextEndIndexV20935 = -1;
        courtNumberStartFrameV20935 = -1;
        courtNumberEndFrameV20935 = -1;
        courtPhraseEndFrameV20935 = -1;
        if (request == null || request.id == null || request.text == null ||
                !request.id.startsWith("court_finish_")) return;

        String text = request.text;
        int beon = text.indexOf("번");
        if (beon < 0 || beon > 4) return;
        String prefix = text.substring(0, beon).trim();
        if (!prefix.matches("^[1-4]$")) return;
        courtNumberTextEndIndexV20935 = beon + "번".length();

        int phrase = text.indexOf("나왔습니다", courtNumberTextEndIndexV20935);
        if (phrase >= 0) {
            courtPhraseTextEndIndexV20935 = phrase + "나왔습니다".length();
        }
    }

    private double activeRmsV20935(
            float[] pcm, double makeup, int start, int end, double threshold) {
        if (pcm == null || end <= start) return 0.0;
        double squares = 0.0;
        long count = 0L;
        for (int i = Math.max(0, start); i < Math.min(pcm.length, end); i++) {
            double v = pcm[i] * makeup;
            if (Math.abs(v) < threshold) continue;
            squares += v * v;
            count++;
        }
        return count > 0L ? Math.sqrt(squares / count) : 0.0;
    }

    private boolean applyExactCourtNumberGainV20935(
            float[] pcm, double makeup, int sampleRate, int channels,
            int numberStartFrame, int numberEndFrame, int phraseEndFrame) {
        if (pcm == null || pcm.length == 0 || sampleRate < 8000 || channels < 1 ||
                !Double.isFinite(makeup) || makeup <= 0.0) return false;

        // Exact mode is used only when the TTS engine supplied all three lexical
        // boundaries. No guessed seconds/RMS onset is used to locate "N번".
        if (numberStartFrame < 0 || numberEndFrame <= numberStartFrame ||
                phraseEndFrame <= numberEndFrame) return false;

        int numberStart = numberStartFrame * channels;
        int numberEnd = numberEndFrame * channels;
        int phraseEnd = phraseEndFrame * channels;
        if (numberStart < 0 || numberEnd <= numberStart || phraseEnd <= numberEnd ||
                numberStart >= pcm.length) return false;
        numberEnd = Math.min(numberEnd, pcm.length);
        phraseEnd = Math.min(phraseEnd, pcm.length);

        double activeThreshold = dbToLinear(-46.0);
        double numberRms = activeRmsV20935(
                pcm, makeup, numberStart, numberEnd, activeThreshold);
        double referenceRms = activeRmsV20935(
                pcm, makeup, numberEnd, phraseEnd, activeThreshold);
        if (numberRms <= 1.0e-9 || referenceRms <= 1.0e-9) return false;

        // If "N번" is already within 1.5 dB of "코트 나왔습니다", leave it untouched.
        double gapDb = 20.0 * Math.log10(referenceRms / numberRms);
        if (!Double.isFinite(gapDb) || gapDb <= 1.5) return true;

        double desiredGain = referenceRms / numberRms;
        double maxGain = dbToLinear(18.0);
        double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
        double numberPeak = 0.0;
        for (int i = numberStart; i < numberEnd; i++) {
            numberPeak = Math.max(numberPeak, Math.abs(pcm[i] * makeup));
        }
        if (numberPeak <= 1.0e-9) return false;
        double gain = Math.max(
                1.0,
                Math.min(maxGain, Math.min(desiredGain, ceiling / numberPeak)));
        if (!Double.isFinite(gain) || gain <= 1.0001) return true;

        // No attack: the very first sample in the TTS-reported "N번" range gets
        // the full offline gain. A tiny post-boundary crossfade only prevents a
        // discontinuity when returning to unity.
        for (int i = numberStart; i < numberEnd; i++) {
            pcm[i] = (float) (pcm[i] * gain);
        }
        int fade = Math.max(channels, (int) Math.round(sampleRate * channels * 0.012));
        int fadeEnd = Math.min(phraseEnd, numberEnd + fade);
        for (int i = numberEnd; i < fadeEnd; i++) {
            double t = (i - numberEnd) / (double) Math.max(1, fadeEnd - numberEnd);
            double localGain = gain + (1.0 - gain) * t;
            pcm[i] = (float) (pcm[i] * localGain);
        }

        // Self-check after processing. Exact range mode succeeds when the number
        // is no more than 2 dB below the following phrase, or when peak headroom
        // physically prevents further safe gain.
        double afterNumber = activeRmsV20935(
                pcm, makeup, numberStart, numberEnd, activeThreshold);
        double afterReference = activeRmsV20935(
                pcm, makeup, numberEnd, phraseEnd, activeThreshold);
        if (afterNumber <= 1.0e-9 || afterReference <= 1.0e-9) return false;
        double afterGapDb = 20.0 * Math.log10(afterReference / afterNumber);
        return Double.isFinite(afterGapDb) && afterGapDb <= 2.0 + 1.0e-6;
    }

'''
java = java.replace(helper_anchor, helpers + helper_anchor, 1)

# Keep diagnostics visible in the native status string.
status_old = '+ ":" + BLUETOOTH_COURT_OPENING_PRIORITY + ":" + BLUETOOTH_COURT_OPENING_FIXED_GAIN + ":ready="'
status_new = '+ ":" + BLUETOOTH_COURT_OPENING_PRIORITY + ":" + BLUETOOTH_COURT_OPENING_FIXED_GAIN + ":" + EXACT_COURT_NUMBER_RANGE + ":ready="'
if status_old not in java:
    raise SystemExit("v209.35 status anchor missing")
java = java.replace(status_old, status_new, 1)

for required in (
    HTML_MARKER,
    "statusById[String(m&&m.id!=null?m.id:'')]",
    "statusById[String(id)]!=='away'",
    VOICE_MARKER,
    "public void onRangeStart(String utteranceId, int start, int end, int frame)",
    "armExactCourtNumberRangeV20935(activeRepeatRequest)",
    "applyExactCourtNumberGainV20935(",
    "gapDb <= 1.5",
    "afterGapDb <= 2.0",
):
    if required not in html + java:
        raise SystemExit("v209.35 output missing: " + required)

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20935_EXACT_NUMBER_RANGE_AWAY_IDEMPOTENT_OK")
