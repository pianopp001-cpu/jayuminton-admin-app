#!/usr/bin/env python3
"""Fix the ~3-second quiet start on real announcements.

Bug report: "음성 클리핑 안되게 하고 normalization까지 적용이 되었는데. 초반에
갑자기 음성이 확 줄어들어서 3초동안 말소리가 잘 안들리게 나오거든." -- clipping
prevention (v208.91 energy-normalize-limiter / v208.91b fast-peak-guard) and
loudness normalization are already applied and were independently verified
(see this module's test suite) to NOT introduce any location-dependent gain
error: a real Korean TTS waveform was run through a byte-for-byte Python port
of normalizeAndLimitVoiceWav() and its 100ms-window loudness contour showed no
systematic dip confined to the first few seconds -- the compressor/makeup-gain
math is not the cause.

What both v208.91 and v208.92 changed, though, is that native voice playback
now ALWAYS starts a brand new MediaPlayer right after the app has just quietly
synthesized+normalized a file with no audio output at all (the old +7dB
LoudnessEnhancer path was removed; nothing else plays sound during that
window). On many tablets (this pipeline forces the "media" audio route on
Galaxy Tab-class devices -- see JAYUMINTON_GALAXY_TAB_TTS and
useMediaVoiceRoute()) the amplifier/audio HAL applies a short ramp-up when a
stream that has been fully silent starts producing audio again, to avoid a
speaker pop. Real speech placed at sample 0 of that first MediaPlayer.start()
call lands squarely inside that ramp and plays back muffled for roughly its
duration; once the hardware is warmed up (by the second/third VOICE_REPEAT_COUNT
replay, which never goes idle in between) it plays at full, correct volume --
matching "초반에" + "3초동안" (about the length of one repeat) exactly.

A previous attempt at a *separate* silent priming clip on the browser side
(v208.92, JAYUMINTON_MUSIC55_NO_WARMUP_V20892) was removed because starting
and then abruptly stopping a zero-amplitude utterance created its own
click/pop on some Samsung devices. This fix avoids that failure mode by never
creating a second playback event at all: the lead-in silence is prepended
directly into the SAME already-normalized WAV buffer, inside the single
continuous MediaPlayer session that plays the real announcement, so the ramp
plays out during silence instead of during the first spoken word, and there
is no extra start/stop boundary that could itself click.

This cannot be verified against real device audio output from this sandbox
(no physical Galaxy Tab / no audio hardware here) -- it is shipped as the
best-evidenced, lowest-risk fix (it only ever adds a short leading silence; it
never changes any spoken sample, gain, or ducking/focus logic) and should be
confirmed by listening to a real announcement on the actual tablet.
"""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = java_path.read_text(encoding='utf-8')

MARKER = 'JAYUMINTON_NATIVE_AUDIO_WARMUP_LEAD_IN_V20907'

if MARKER in text:
    print('ADMIN_NATIVE_AUDIO_WARMUP_LEAD_IN_V20907_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891',
    'JAYUMINTON_FAST_PEAK_GUARD_V20891B',
    'VOICE_TARGET_RMS_DBFS = -13.0',
    'normalizeAndLimitVoiceWav(File file)',
    'finalPeak > ceiling + 1.0e-6',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.93 prerequisite missing: ' + item)

text = text.replace(
    '    private static final double VOICE_COMP_RATIO = 3.0;\n',
    '    private static final double VOICE_COMP_RATIO = 3.0;\n'
    '    private static final String NATIVE_AUDIO_WARMUP_LEAD_IN = "' + MARKER + '";\n'
    '    // Long enough to cover a slow-ramping tablet amplifier, short enough to be\n'
    '    // an unnoticeable pause rather than an audible gap.\n'
    '    private static final double AUDIO_WARMUP_LEAD_IN_SECONDS = 0.45;\n',
    1,
)

anchor = (
    "            // Validation gate before overwriting the synthesized file.\n"
    "            double finalRms = Math.sqrt(finalSquares / pcm.length);\n"
    "            if (!Double.isFinite(finalRms) || finalRms <= 0.0 ||\n"
    "                    finalPeak > ceiling + 1.0e-6 || finalPeak >= 1.0) return false;\n"
    "\n"
    "            raf.seek(0);\n"
    "            raf.write(wav);\n"
    "            raf.setLength(wav.length);\n"
    "            return true;"
)
if text.count(anchor) != 1:
    raise SystemExit('v208.93 write-back anchor mismatch: ' + str(text.count(anchor)))

replacement = (
    "            // Validation gate before overwriting the synthesized file.\n"
    "            double finalRms = Math.sqrt(finalSquares / pcm.length);\n"
    "            if (!Double.isFinite(finalRms) || finalRms <= 0.0 ||\n"
    "                    finalPeak > ceiling + 1.0e-6 || finalPeak >= 1.0) return false;\n"
    "\n"
    "            // " + MARKER + ": prepend a short true-silence lead-in so a\n"
    "            // slow-ramping speaker/audio-route warm-up (common on tablets right\n"
    "            // after fully idle output) plays out before real speech, not during\n"
    "            // it. This only ever adds silent samples ahead of the already-\n"
    "            // validated audio -- it never touches a single spoken sample.\n"
    "            int silenceFrames = (int) Math.round(sampleRate * AUDIO_WARMUP_LEAD_IN_SECONDS);\n"
    "            int silenceBytes = silenceFrames * channels * 2;\n"
    "            byte[] outWav = new byte[dataOffset + silenceBytes + dataSize];\n"
    "            System.arraycopy(wav, 0, outWav, 0, dataOffset);\n"
    "            // The silenceBytes region is already zero-filled by `new byte[]`.\n"
    "            System.arraycopy(wav, dataOffset, outWav, dataOffset + silenceBytes, dataSize);\n"
    "            writeLeInt(outWav, 4, outWav.length - 8);\n"
    "            writeLeInt(outWav, dataOffset - 4, dataSize + silenceBytes);\n"
    "\n"
    "            raf.seek(0);\n"
    "            raf.write(outWav);\n"
    "            raf.setLength(outWav.length);\n"
    "            return true;"
)
text = text.replace(anchor, replacement, 1)

helper_anchor = '    private int leU16(byte[] data, int off) {\n'
if text.count(helper_anchor) != 1:
    raise SystemExit('v208.93 leU16 anchor mismatch: ' + str(text.count(helper_anchor)))
helper = (
    "    private void writeLeInt(byte[] data, int off, int value) {\n"
    "        data[off] = (byte) (value & 0xff);\n"
    "        data[off + 1] = (byte) ((value >>> 8) & 0xff);\n"
    "        data[off + 2] = (byte) ((value >>> 16) & 0xff);\n"
    "        data[off + 3] = (byte) ((value >>> 24) & 0xff);\n"
    "    }\n\n"
)
text = text.replace(helper_anchor, helper + helper_anchor, 1)

# Extend diagnostics.
old_status = '+ ":" + FAST_PEAK_GUARD + ":" + MUSIC55_NO_WARMUP + ":ready="'
new_status = '+ ":" + FAST_PEAK_GUARD + ":" + MUSIC55_NO_WARMUP + ":" + NATIVE_AUDIO_WARMUP_LEAD_IN + ":ready="'
if old_status not in text:
    raise SystemExit('v208.93 status anchor missing')
text = text.replace(old_status, new_status, 1)

for item in (
    MARKER,
    'AUDIO_WARMUP_LEAD_IN_SECONDS = 0.45',
    'private void writeLeInt(byte[] data, int off, int value)',
    'System.arraycopy(wav, 0, outWav, 0, dataOffset);',
    'NATIVE_AUDIO_WARMUP_LEAD_IN + ":ready="',
):
    if item not in text:
        raise SystemExit('v208.93 requirement missing: ' + item)

java_path.write_text(text, encoding='utf-8')
print('ADMIN_NATIVE_AUDIO_WARMUP_LEAD_IN_V20907_OK')
