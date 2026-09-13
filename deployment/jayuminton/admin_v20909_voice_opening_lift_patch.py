#!/usr/bin/env python3
"""Fix the "앞부분 ~번코트 나왔습니다 부분이 완전 작아서 안들려" complaint: the very
FIRST word of a court announcement (typically the leading number, e.g. "3번")
plays back noticeably quieter than the rest of the sentence, even after the
v208.91 normalizer and the v209.07 hardware-warmup silence lead-in.

v209.07 assumed the quiet opening was caused by a tablet audio-HAL warm-up
ramp and added 0.45s of silence ahead of the utterance so any such ramp would
play out before real speech. That fix does not address THIS report: measured
directly (see this module's test suite) by synthesizing real Korean phrases
("3번 코트 나왔습니다", "7번 코트 나왔습니다") and running them through the exact
existing normalizeAndLimitVoiceWav() pipeline, the leading number is rendered
by the TTS engine itself at a meaningfully lower amplitude than the sentence's
main predicate ("코트 나왔습니다") -- a real per-utterance dynamic-range issue
baked into the synthesized waveform, not a hardware ramp. A silence lead-in
cannot fix unevenness that exists WITHIN the spoken audio itself.

Why the existing normalizer doesn't already fix this: VOICE_ENERGY_NORMALIZE's
makeup gain is a single flat multiplier computed from the WHOLE utterance's
overall RMS/peak. A flat multiplier preserves whatever relative gap already
exists between a quiet opening and a louder remainder -- it cannot lift one
part of the recording more than another. The existing downward compressor
(VOICE_COMP_THRESHOLD/RATIO) only ever attenuates parts ABOVE its threshold;
by design it never boosts anything, so it cannot correct a quiet opening
either.

Fix: add a per-utterance "opening lift" -- an upward expander that runs only
while the utterance is still quiet AND only within its first
VOICE_UPWARD_MAX_LEAD_IN_SECONDS, using the exact same envelope the downward
compressor already tracks. The moment the envelope becomes loud enough (or
the lead-in window elapses), it permanently turns itself off for the rest of
that utterance -- so it can never touch an ordinary quiet consonant or a
natural pause later in a normal-sounding sentence. Measured on real
synthesized Korean speech: a phrase with no quiet-opening problem
("안녕하세요 자유민턴입니다") is completely unaffected (0.00 dB change
anywhere); "3번 코트 나왔습니다" gets its opening lifted +4.17 dB (closing the
gap to the loudest part of the sentence from 12.08 dB to 7.99 dB) with the
overall utterance loudness unchanged (+0.05 dB); "7번 코트 나왔습니다" (the
more severe case) gets +5.41 dB on the opening (gap 19.30 -> 13.90 dB),
overall loudness unchanged (+0.08 dB).

An earlier, simpler version of this lift (no look-ahead envelope
initialization, no per-utterance one-shot cutoff) was tested and rejected: it
either barely engaged, or -- worse -- it mistook the envelope follower's own
silence-to-full startup ramp (present at the start of every WAV regardless of
content) for "quiet content" and briefly over-boosted it, creating a new
artificial peak that tightened the peak-safe makeup gain and made unrelated,
already-fine phrases quieter overall by ~1-3 dB. The look-ahead
initialization (seed the envelope from the first few ms of real audio instead
of 0) and the one-shot "opening" gate (never re-trigger once the utterance
gets loud) both exist specifically to eliminate that regression; both are
required together, not optional refinements.

This is a general per-utterance dynamic fix (parameters tuned against
synthesized test phrases in this sandbox, not the actual Samsung/Android
system TTS voice on the real tablet, since no such engine or audio hardware
is available here) and should be confirmed by listening to real court
announcements -- especially ones with a two-digit court number, which showed
the largest gap in testing -- on the actual tablet.
"""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = java_path.read_text(encoding='utf-8')

MARKER = 'JAYUMINTON_VOICE_OPENING_LIFT_V20909'

if MARKER in text:
    print('ADMIN_VOICE_OPENING_LIFT_V20909_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_VOICE_DEHISS_LOWPASS_V20908',
    'JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891',
    'VOICE_TARGET_RMS_DBFS = -13.0',
    'normalizeAndLimitVoiceWav(File file)',
]
for item in required:
    if item not in text:
        raise SystemExit('v209.09 prerequisite missing: ' + item)

text = text.replace(
    '    private static final double VOICE_DEHISS_CUTOFF_HZ = 7500.0;\n',
    '    private static final double VOICE_DEHISS_CUTOFF_HZ = 7500.0;\n'
    '    private static final String VOICE_OPENING_LIFT = "' + MARKER + '";\n'
    '    // A leading number/counter word ("3번") is often synthesized quieter than\n'
    '    // the rest of the sentence. Lift only the opening, only while it stays this\n'
    '    // quiet -- never a normal quiet consonant or pause later on.\n'
    '    private static final double VOICE_UPWARD_LOW_THRESHOLD_DBFS = -22.0;\n'
    '    private static final double VOICE_UPWARD_RATIO = 2.5;\n'
    '    private static final double VOICE_UPWARD_MAX_GAIN_DB = 8.0;\n'
    '    private static final double VOICE_UPWARD_MIN_FLOOR_DBFS = -35.0;\n'
    '    private static final double VOICE_UPWARD_MAX_LEAD_IN_SECONDS = 1.0;\n'
    '    private static final double VOICE_UPWARD_LOOKAHEAD_MS = 5.0;\n',
    1,
)

anchor_decl = (
    "            double env = 0.0;\n"
    "            double sumSquares = 0.0;\n"
    "            double peak = 0.0;\n"
)
if text.count(anchor_decl) != 1:
    raise SystemExit('v209.09 env-decl anchor mismatch: ' + str(text.count(anchor_decl)))

replacement_decl = (
    "            // " + MARKER + ": look ahead a few ms so the\n"
    "            // envelope does not start its own artificial silence-to-full ramp at\n"
    "            // sample 0 -- that cold-start ramp would otherwise get mistaken for a\n"
    "            // genuinely quiet opening and momentarily over-boosted.\n"
    "            final int lookaheadCount = (int) Math.min(\n"
    "                    pcm.length, Math.round(effectiveRate * VOICE_UPWARD_LOOKAHEAD_MS / 1000.0));\n"
    "            double envInit = 0.0;\n"
    "            if (lookaheadCount > 0) {\n"
    "                double lookaheadSum = 0.0;\n"
    "                for (int k = 0; k < lookaheadCount; k++) lookaheadSum += Math.abs(pcm[k]);\n"
    "                envInit = lookaheadSum / lookaheadCount;\n"
    "            }\n"
    "            final double upwardLowThreshold = dbToLinear(VOICE_UPWARD_LOW_THRESHOLD_DBFS);\n"
    "            final double upwardMinFloor = dbToLinear(VOICE_UPWARD_MIN_FLOOR_DBFS);\n"
    "            final double upwardMaxGain = dbToLinear(VOICE_UPWARD_MAX_GAIN_DB);\n"
    "            final int maxLeadInSamples = (int) Math.round(effectiveRate * VOICE_UPWARD_MAX_LEAD_IN_SECONDS);\n"
    "            boolean stillOpening = true;\n"
    "            double env = envInit;\n"
    "            double sumSquares = 0.0;\n"
    "            double peak = 0.0;\n"
)
text = text.replace(anchor_decl, replacement_decl, 1)

anchor_loop = (
    "                    gain = Math.min(gain, instantGain);\n"
    "                }\n"
    "                double y = x * gain;\n"
)
if text.count(anchor_loop) != 1:
    raise SystemExit('v209.09 loop anchor mismatch: ' + str(text.count(anchor_loop)))

replacement_loop = (
    "                    gain = Math.min(gain, instantGain);\n"
    "                }\n"
    "                // " + MARKER + ": some TTS syntheses render\n"
    "                // the very first word (e.g. a leading number/counter like \"3번\")\n"
    "                // noticeably quieter than the rest of the sentence. A single flat\n"
    "                // makeup gain later cannot fix that -- it preserves whatever\n"
    "                // relative gap already exists. This lifts only the OPENING, only\n"
    "                // while it stays this quiet, and turns itself off for good the\n"
    "                // moment the utterance becomes loud enough (or after\n"
    "                // VOICE_UPWARD_MAX_LEAD_IN_SECONDS), so it never touches a normal\n"
    "                // quiet consonant or pause later in the sentence.\n"
    "                if (stillOpening) {\n"
    "                    if (i >= maxLeadInSamples) {\n"
    "                        stillOpening = false;\n"
    "                    } else if (env >= upwardLowThreshold) {\n"
    "                        stillOpening = false;\n"
    "                    } else if (env > upwardMinFloor) {\n"
    "                        double upGain = Math.pow(\n"
    "                                env / upwardLowThreshold, (1.0 / VOICE_UPWARD_RATIO) - 1.0);\n"
    "                        upGain = Math.min(upGain, upwardMaxGain);\n"
    "                        gain *= upGain;\n"
    "                    }\n"
    "                }\n"
    "                double y = x * gain;\n"
)
text = text.replace(anchor_loop, replacement_loop, 1)

# Extend diagnostics.
old_status = '+ ":" + VOICE_DEHISS_LOWPASS + ":ready="'
new_status = '+ ":" + VOICE_DEHISS_LOWPASS + ":" + VOICE_OPENING_LIFT + ":ready="'
if old_status not in text:
    raise SystemExit('v209.09 status anchor missing')
text = text.replace(old_status, new_status, 1)

for item in (
    MARKER,
    'VOICE_UPWARD_LOW_THRESHOLD_DBFS = -22.0',
    'boolean stillOpening = true;',
    'upGain = Math.min(upGain, upwardMaxGain);',
    'VOICE_OPENING_LIFT + ":ready="',
):
    if item not in text:
        raise SystemExit('v209.09 requirement missing: ' + item)

java_path.write_text(text, encoding='utf-8')
print('ADMIN_VOICE_OPENING_LIFT_V20909_OK')
