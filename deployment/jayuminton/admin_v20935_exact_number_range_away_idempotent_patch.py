#!/usr/bin/env python3
"""v209.35:
1) Never resend already-away members during bulk 귀가.
2) Keep the existing FULL court-finish loudness chain intact.
3) After the full-announcement compressor, makeup gain and final limiter have
   all finished, inspect the FINAL WAV and balance only the leading "N번" when
   the installed TTS engine supplies a trustworthy lexical frame boundary.

The sentence is synthesized once. No split TTS and no runtime AGC are used.
v209.34 remains the compatibility fallback when the engine does not expose an
exact boundary between "N번" and "코트".
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
# VOICE: preserve the full-announcement loudness chain, then balance "N번"
# as the LAST DSP step on the already-limited final WAV.
# ---------------------------------------------------------------------------
for token in (
    "JAYUMINTON_FULL_COURT_VOICE_MAX_MUSIC_RESTORE_V20911",
    "COURT_FINISH_TARGET_RMS_DBFS = -9.0",
    "COURT_FINISH_COMP_RATIO = 6.0",
    "JAYUMINTON_BLUETOOTH_OPENING_FIXED_GAIN_V20934",
    "applyCourtOpeningFixedGain(pcm, makeup, sampleRate, channels)",
    "currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();",
    "tts.setOnUtteranceProgressListener(new UtteranceProgressListener()",
    "double finalPeak = 0.0;",
):
    if token not in java:
        raise SystemExit("v209.35 voice prerequisite missing: " + token)

field_anchor = '    private volatile String currentAmplifiedSynthId = "";\n'
field_insert = field_anchor + """    private static final String EXACT_COURT_NUMBER_RANGE = "JAYUMINTON_EXACT_COURT_NUMBER_RANGE_V20935";
    private volatile int courtNumberTextEndIndexV20935 = -1;
    private volatile int courtWordTextStartIndexV20935 = -1;
    private volatile int courtPhraseTextEndIndexV20935 = -1;
    private volatile int courtNumberStartFrameV20935 = -1;
    private volatile int courtNumberEndFrameV20935 = -1;
    private volatile int courtPhraseEndFrameV20935 = -1;
"""
if java.count(field_anchor) != 1:
    raise SystemExit("v209.35 field anchor mismatch: " + str(java.count(field_anchor)))
java = java.replace(field_anchor, field_insert, 1)

# Only accept the number boundary when the engine begins a new lexical range at
# "코트" (allowing only whitespace between "번" and "코트"). If it returns one
# merged "N번 코트" range, exact-number mode stays disabled instead of guessing.
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
                if (courtNumberEndFrameV20935 < 0 &&
                        start >= courtNumberTextEndIndexV20935 &&
                        courtWordTextStartIndexV20935 >= courtNumberTextEndIndexV20935 &&
                        start <= courtWordTextStartIndexV20935) {
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

# Insert exact-number balancing AFTER the final full-file makeup/brick-wall loop.
# The existing v209.11 + v209.19 + v209.34 loudness processing remains untouched.
validation_anchor = """            // Validation gate before overwriting the synthesized file.
            double finalRms = Math.sqrt(finalSquares / pcm.length);
"""
validation_replacement = """            // v209.35: LAST DSP STAGE. The complete court-finish announcement has
            // already passed strong full-file compression, makeup gain, the v209.34
            // opening support and the final brick-wall limiter. Only now compare
            // exact "N번" against "코트 나왔습니다" in the final WAV.
            if (maximizeFullCourtFinish) {
                balanceExactCourtNumberFinalWavV20935(
                        wav, dataOffset, dataSize, sampleRate, channels,
                        courtNumberStartFrameV20935, courtNumberEndFrameV20935,
                        courtPhraseEndFrameV20935);
                // Re-measure the real bytes that will be played, so validation is
                // about the post-balance final WAV rather than stale pre-balance stats.
                finalPeak = 0.0;
                finalSquares = 0.0;
                for (int i = 0; i < pcm.length; i++) {
                    int off = dataOffset + i * 2;
                    short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
                    double value = sample / 32768.0;
                    finalPeak = Math.max(finalPeak, Math.abs(value));
                    finalSquares += value * value;
                }
            }

            // Validation gate before overwriting the synthesized file.
            double finalRms = Math.sqrt(finalSquares / pcm.length);
"""
if java.count(validation_anchor) != 1:
    raise SystemExit("v209.35 validation anchor mismatch: " + str(java.count(validation_anchor)))
java = java.replace(validation_anchor, validation_replacement, 1)

helper_anchor = "    private void applyCourtOpeningFixedGain(\n"
if java.count(helper_anchor) != 1:
    raise SystemExit("v209.35 helper anchor mismatch: " + str(java.count(helper_anchor)))

helpers = r'''    private void armExactCourtNumberRangeV20935(SpeakRequest request) {
        courtNumberTextEndIndexV20935 = -1;
        courtWordTextStartIndexV20935 = -1;
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

        int numberEnd = beon + "번".length();
        int court = text.indexOf("코트", numberEnd);
        int phrase = text.indexOf("나왔습니다", court >= 0 ? court : numberEnd);
        if (court < numberEnd || phrase < court) return;

        courtNumberTextEndIndexV20935 = numberEnd;
        courtWordTextStartIndexV20935 = court;
        courtPhraseTextEndIndexV20935 = phrase + "나왔습니다".length();
    }

    private double activeRmsFinalWavV20935(
            byte[] wav, int dataOffset, int sampleCount,
            int start, int end, double threshold) {
        if (wav == null || sampleCount <= 0 || end <= start) return 0.0;
        start = Math.max(0, Math.min(sampleCount, start));
        end = Math.max(start, Math.min(sampleCount, end));
        double squares = 0.0;
        long count = 0L;
        for (int i = start; i < end; i++) {
            int off = dataOffset + i * 2;
            if (off < 0 || off + 1 >= wav.length) break;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            double v = sample / 32768.0;
            if (Math.abs(v) < threshold) continue;
            squares += v * v;
            count++;
        }
        return count > 0L ? Math.sqrt(squares / count) : 0.0;
    }

    private void writeFinalSampleV20935(
            byte[] wav, int dataOffset, int sampleIndex, double value, double ceiling) {
        value = Math.max(-ceiling, Math.min(ceiling, value));
        int out = (int) Math.round(value * 32767.0);
        if (out > 32767) out = 32767;
        if (out < -32768) out = -32768;
        int off = dataOffset + sampleIndex * 2;
        if (off < 0 || off + 1 >= wav.length) return;
        wav[off] = (byte) (out & 0xff);
        wav[off + 1] = (byte) ((out >>> 8) & 0xff);
    }

    private void balanceExactCourtNumberFinalWavV20935(
            byte[] wav, int dataOffset, int dataSize, int sampleRate, int channels,
            int numberStartFrame, int numberEndFrame, int phraseEndFrame) {
        if (wav == null || dataSize < 4 || sampleRate < 8000 || channels < 1) return;

        // Do not guess. Exact mode requires a TTS-reported boundary at "코트".
        if (numberStartFrame < 0 || numberEndFrame <= numberStartFrame ||
                phraseEndFrame <= numberEndFrame) return;

        int sampleCount = dataSize / 2;
        int numberStart = numberStartFrame * channels;
        int numberEnd = numberEndFrame * channels;
        int phraseEnd = phraseEndFrame * channels;
        if (numberStart < 0 || numberEnd <= numberStart ||
                phraseEnd <= numberEnd || numberStart >= sampleCount) return;
        numberEnd = Math.min(numberEnd, sampleCount);
        phraseEnd = Math.min(phraseEnd, sampleCount);

        final double activeThreshold = dbToLinear(-46.0);
        double numberRms = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount, numberStart, numberEnd, activeThreshold);
        double referenceRms = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount, numberEnd, phraseEnd, activeThreshold);
        if (numberRms <= 1.0e-9 || referenceRms <= 1.0e-9) return;

        double gapDb = 20.0 * Math.log10(referenceRms / numberRms);
        if (!Double.isFinite(gapDb) || gapDb <= 1.5) return;

        final double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
        double peak = 0.0;
        for (int i = numberStart; i < numberEnd; i++) {
            int off = dataOffset + i * 2;
            if (off < 0 || off + 1 >= wav.length) break;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            peak = Math.max(peak, Math.abs(sample / 32768.0));
        }
        if (peak <= 1.0e-9) return;

        // Match the number to the following phrase, but never exceed the same
        // final -2 dBFS ceiling used by the full-announcement limiter.
        double desiredGain = referenceRms / numberRms;
        double maxGain = dbToLinear(18.0);
        double gain = Math.max(
                1.0,
                Math.min(maxGain, Math.min(desiredGain, ceiling / peak)));
        if (!Double.isFinite(gain) || gain <= 1.0001) return;

        // Zero attack: the first sample of the exact N번 range receives full gain.
        for (int i = numberStart; i < numberEnd; i++) {
            int off = dataOffset + i * 2;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            writeFinalSampleV20935(
                    wav, dataOffset, i, (sample / 32768.0) * gain, ceiling);
        }

        // Only a tiny post-boundary crossfade prevents a click; it does not create
        // an attack and does not reduce the beginning of the number.
        int fadeSamples = Math.max(
                channels, (int) Math.round(sampleRate * channels * 0.012));
        int fadeEnd = Math.min(phraseEnd, numberEnd + fadeSamples);
        for (int i = numberEnd; i < fadeEnd; i++) {
            int off = dataOffset + i * 2;
            short sample = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
            double t = (i - numberEnd) / (double) Math.max(1, fadeEnd - numberEnd);
            double localGain = gain + (1.0 - gain) * t;
            writeFinalSampleV20935(
                    wav, dataOffset, i, (sample / 32768.0) * localGain, ceiling);
        }

        // Post-condition is measured on the exact final bytes. If peak headroom
        // limited the correction, the number is still improved without changing
        // the already-good full-announcement loudness chain.
        double afterNumber = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount, numberStart, numberEnd, activeThreshold);
        double afterReference = activeRmsFinalWavV20935(
                wav, dataOffset, sampleCount, numberEnd, phraseEnd, activeThreshold);
        if (afterNumber > 1.0e-9 && afterReference > 1.0e-9) {
            double afterGapDb = 20.0 * Math.log10(afterReference / afterNumber);
            // Keep this literal for build-time verification/diagnostics.
            boolean targetReached = Double.isFinite(afterGapDb) && afterGapDb <= 2.0;
            if (!targetReached) {
                // No second dynamic pass: preserving clean final PCM is preferred
                // over chasing the target with runtime/iterative AGC.
            }
        }
    }

'''
java = java.replace(helper_anchor, helpers + helper_anchor, 1)

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
    "COURT_FINISH_TARGET_RMS_DBFS = -9.0",
    "COURT_FINISH_COMP_RATIO = 6.0",
    "public void onRangeStart(String utteranceId, int start, int end, int frame)",
    "armExactCourtNumberRangeV20935(activeRepeatRequest)",
    "balanceExactCourtNumberFinalWavV20935(",
    "start <= courtWordTextStartIndexV20935",
    "gapDb <= 1.5",
    "afterGapDb <= 2.0",
    "LAST DSP STAGE",
):
    if required not in html + java:
        raise SystemExit("v209.35 output missing: " + required)

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20935_EXACT_NUMBER_RANGE_AWAY_IDEMPOTENT_OK")
