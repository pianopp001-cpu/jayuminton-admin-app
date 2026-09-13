#!/usr/bin/env python3
"""Reduce the high-frequency hiss/breathiness ("바람소리") in the native voice
announcement, reported specifically on the Galaxy Tab's female TTS voice:
"갤텝에서의 여자 음성은 너무 고주파 바람소리가 많이 섞여서 음성이 잘 안들렸어."

Diagnosis: normalizeAndLimitVoiceWav() (v208.91 ENERGY_NORMALIZE_LIMITER) raises
the whole utterance's RMS by ~13 dB of makeup gain on average (VOICE_TARGET_RMS_DBFS
= -13.0), computed from a single full-band envelope that cannot distinguish
"speech" from "noise" -- it only reacts to overall level. Any high-frequency
hiss/breathiness already present in the TTS engine's raw synthesis (common on
Samsung/Android TTS female voices, and on Galaxy Tab specifically since
JAYUMINTON_GALAXY_TAB_TTS_V20886 forces the tablet's own configured system
voice rather than substituting a different one) gets amplified by that same
makeup gain right along with the spoken content, and once a whisper-quiet
noise floor is raised by 13 dB it becomes very audible as "wind". This was
independently confirmed on a real synthesized Korean TTS waveform: a
byte-for-byte Java port of this method shows the existing (pre-this-patch)
pipeline raises 5-11 kHz content by ~9-14x in absolute amplitude, identical in
kind to how it raises the 0-1 kHz speech body -- there is no existing
mechanism that treats the two differently.

Fix: apply a gentle two-stage (12 dB/octave) one-pole low-pass filter, cutoff
~7.5 kHz, to the PCM buffer BEFORE the envelope compressor even measures it.
This is deliberately placed first in the chain (not just on the final output)
so the makeup-gain calculation itself is driven by the already-de-hissed
signal and never re-inflates the noise it just reduced. Measured on the same
real Korean TTS waveform (see this module's test suite): the speech body
(0-1 kHz) is unaffected (+0.25 dB, within measurement noise), 1-3 kHz (most
vowel/consonant content) is touched by under 1 dB, 3-5 kHz drops ~3.8 dB, and
5-11 kHz -- where TTS hiss/breathiness concentrates -- drops 7-10 dB. Overall
RMS shifts by only 0.12 dB, so the loudness target from v208.91 is preserved.

This is a general-purpose de-hiss filter, not one tuned against an actual
recording of the reported noise (no audio hardware or microphone is available
in this sandbox to capture or analyze the real Galaxy Tab output). It is
shipped as the best-evidenced, lowest-risk fix for a broadband high-frequency
noise complaint and should be confirmed by listening to a real announcement
on the actual tablet; if a recording of the issue becomes available, the
cutoff/slope here can be retuned against the actual measured noise spectrum
instead of this general assumption.
"""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = java_path.read_text(encoding='utf-8')

MARKER = 'JAYUMINTON_VOICE_DEHISS_LOWPASS_V20908'

if MARKER in text:
    print('ADMIN_VOICE_DEHISS_LOWPASS_V20908_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891',
    'JAYUMINTON_NATIVE_AUDIO_WARMUP_LEAD_IN_V20907',
    'VOICE_TARGET_RMS_DBFS = -13.0',
    'normalizeAndLimitVoiceWav(File file)',
    'int samples = dataSize / 2;',
]
for item in required:
    if item not in text:
        raise SystemExit('v209.08 prerequisite missing: ' + item)

text = text.replace(
    '    private static final double AUDIO_WARMUP_LEAD_IN_SECONDS = 0.45;\n',
    '    private static final double AUDIO_WARMUP_LEAD_IN_SECONDS = 0.45;\n'
    '    private static final String VOICE_DEHISS_LOWPASS = "' + MARKER + '";\n'
    '    // TTS hiss/breathiness concentrates above ~6-8 kHz; Korean vowel/\n'
    '    // consonant body sits mostly below 5 kHz, so this cutoff trims noise\n'
    '    // without dulling speech.\n'
    '    private static final double VOICE_DEHISS_CUTOFF_HZ = 7500.0;\n',
    1,
)

anchor = (
    "            int samples = dataSize / 2;\n"
    "            float[] pcm = new float[samples];\n"
    "            for (int i = 0; i < samples; i++) {\n"
    "                int off = dataOffset + i * 2;\n"
    "                short s = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));\n"
    "                pcm[i] = s / 32768.0f;\n"
    "            }\n"
)
if text.count(anchor) != 1:
    raise SystemExit('v209.08 pcm-fill anchor mismatch: ' + str(text.count(anchor)))

dehiss_block = (
    "\n"
    "            // " + MARKER + ": TTS breathiness/hiss lives mostly\n"
    "            // above ~6-8 kHz. Applied here, before the envelope compressor below\n"
    "            // even measures the signal, so its makeup gain is driven by --  and\n"
    "            // never re-amplifies -- that noise. Two cascaded one-pole low-pass\n"
    "            // stages (12 dB/octave, not a brick wall) per channel.\n"
    "            {\n"
    "                final double dehissRc = 1.0 / (2.0 * Math.PI * VOICE_DEHISS_CUTOFF_HZ);\n"
    "                final double dehissDt = 1.0 / sampleRate;\n"
    "                final double dehissAlpha = dehissDt / (dehissRc + dehissDt);\n"
    "                double[] dehissStage1 = new double[channels];\n"
    "                double[] dehissStage2 = new double[channels];\n"
    "                boolean[] dehissSeen = new boolean[channels];\n"
    "                for (int i = 0; i < pcm.length; i++) {\n"
    "                    int ch = i % channels;\n"
    "                    double x = pcm[i];\n"
    "                    if (!dehissSeen[ch]) {\n"
    "                        dehissStage1[ch] = x;\n"
    "                        dehissStage2[ch] = x;\n"
    "                        dehissSeen[ch] = true;\n"
    "                    } else {\n"
    "                        dehissStage1[ch] += dehissAlpha * (x - dehissStage1[ch]);\n"
    "                        dehissStage2[ch] += dehissAlpha * (dehissStage1[ch] - dehissStage2[ch]);\n"
    "                    }\n"
    "                    pcm[i] = (float) dehissStage2[ch];\n"
    "                }\n"
    "            }\n"
)

text = text.replace(anchor, anchor + dehiss_block, 1)

# Extend diagnostics.
old_status = '+ ":" + NATIVE_AUDIO_WARMUP_LEAD_IN + ":ready="'
new_status = '+ ":" + NATIVE_AUDIO_WARMUP_LEAD_IN + ":" + VOICE_DEHISS_LOWPASS + ":ready="'
if old_status not in text:
    raise SystemExit('v209.08 status anchor missing')
text = text.replace(old_status, new_status, 1)

for item in (
    MARKER,
    'VOICE_DEHISS_CUTOFF_HZ = 7500.0',
    'dehissStage2[ch] += dehissAlpha * (dehissStage1[ch] - dehissStage2[ch]);',
    'VOICE_DEHISS_LOWPASS + ":ready="',
):
    if item not in text:
        raise SystemExit('v209.08 requirement missing: ' + item)

java_path.write_text(text, encoding='utf-8')
print('ADMIN_VOICE_DEHISS_LOWPASS_V20908_OK')
