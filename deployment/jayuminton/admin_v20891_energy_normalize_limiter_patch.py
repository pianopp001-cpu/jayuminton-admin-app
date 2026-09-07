#!/usr/bin/env python3
from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = java_path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891'

if MARKER in text:
    print('ADMIN_ENERGY_NORMALIZE_LIMITER_V20891_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_VOICE_BOOST_V20890',
    'VOICE_BOOST_MILLIBELS = 700',
    'tts.synthesizeToFile(',
    'startAmplifiedRepeatPlayback()',
    'new LoudnessEnhancer(mp.getAudioSessionId())',
    'private static final float MUSIC_DUCK_RATIO = 0.35f;',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.91 prerequisite missing: ' + item)

# Keep the old marker for lineage, but replace blind +7 dB playback with deterministic
# offline energy normalization + compression + a hard sample-peak ceiling.
text = text.replace(
    '    private static final String VOICE_BOOST = "JAYUMINTON_VOICE_BOOST_V20890";\n',
    '    private static final String VOICE_BOOST = "JAYUMINTON_VOICE_BOOST_V20890";\n'
    '    private static final String ENERGY_NORMALIZE_LIMITER = "JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891";\n'
    '    private static final double VOICE_TARGET_RMS_DBFS = -13.0;\n'
    '    private static final double VOICE_PEAK_CEILING_DBFS = -2.0;\n'
    '    private static final double VOICE_COMP_THRESHOLD_DBFS = -18.0;\n'
    '    private static final double VOICE_COMP_RATIO = 3.0;\n',
    1,
)

if 'import java.io.RandomAccessFile;' not in text:
    text = text.replace('import java.io.File;\n', 'import java.io.File;\nimport java.io.RandomAccessFile;\n', 1)

# Run normalization once, after TTS has finished writing the WAV and before playback starts.
old_done = '''                if (utteranceId != null && utteranceId.equals(currentAmplifiedSynthId)) {\n                    currentAmplifiedSynthId = "";\n                    runOnUiThread(MainActivity.this::startAmplifiedRepeatPlayback);\n                    return;\n                }'''
new_done = '''                if (utteranceId != null && utteranceId.equals(currentAmplifiedSynthId)) {\n                    currentAmplifiedSynthId = "";\n                    runOnUiThread(MainActivity.this::prepareNormalizedAmplifiedPlayback);\n                    return;\n                }'''
if text.count(old_done) != 1:
    raise SystemExit('v208.91 synth-done anchor mismatch: ' + str(text.count(old_done)))
text = text.replace(old_done, new_done, 1)

# Remove blind LoudnessEnhancer gain from the prepared MediaPlayer. The file itself is
# already normalized/limited, so player volume=1.0 cannot create digital clipping here.
old_prepared = '''            player.setOnPreparedListener(mp -> {\n                try {\n                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {\n                        LoudnessEnhancer enhancer = new LoudnessEnhancer(mp.getAudioSessionId());\n                        enhancer.setTargetGain(VOICE_BOOST_MILLIBELS);\n                        enhancer.setEnabled(true);\n                        amplifiedVoiceEnhancer = enhancer;\n                    }\n                } catch (Exception ignored) {\n                    amplifiedVoiceEnhancer = null;\n                }\n                try { mp.start(); } catch (Exception error) { fallbackToDirectTts(); }\n            });'''
new_prepared = '''            player.setOnPreparedListener(mp -> {\n                // v208.91: no blind post-normalization gain. The processed WAV is\n                // already energy-normalized and peak-limited with 2 dB headroom.\n                amplifiedVoiceEnhancer = null;\n                try { mp.start(); } catch (Exception error) { fallbackToDirectTts(); }\n            });'''
if text.count(old_prepared) != 1:
    raise SystemExit('v208.91 LoudnessEnhancer anchor mismatch: ' + str(text.count(old_prepared)))
text = text.replace(old_prepared, new_prepared, 1)

anchor = '    private void startAmplifiedRepeatPlayback() {\n'
helpers = r'''    private void prepareNormalizedAmplifiedPlayback() {
        if (activeRepeatRequest == null || amplifiedVoiceFile == null ||
                !amplifiedVoiceFile.exists() || amplifiedVoiceFile.length() <= 0) {
            fallbackToDirectTts();
            return;
        }
        // Only play the boosted path when we can prove the synthesized PCM has been
        // normalized and limited. Unsupported WAV formats fall back to direct TTS
        // instead of applying an unchecked gain.
        if (!normalizeAndLimitVoiceWav(amplifiedVoiceFile)) {
            fallbackToDirectTts();
            return;
        }
        startAmplifiedRepeatPlayback();
    }

    private boolean normalizeAndLimitVoiceWav(File file) {
        if (file == null || !file.exists()) return false;
        RandomAccessFile raf = null;
        try {
            long length = file.length();
            if (length < 44 || length > 16L * 1024L * 1024L) return false;
            byte[] wav = new byte[(int) length];
            raf = new RandomAccessFile(file, "rw");
            raf.readFully(wav);
            if (!isFourCc(wav, 0, 'R', 'I', 'F', 'F') ||
                    !isFourCc(wav, 8, 'W', 'A', 'V', 'E')) return false;

            int pos = 12;
            int audioFormat = -1;
            int channels = 0;
            int sampleRate = 0;
            int bitsPerSample = 0;
            int dataOffset = -1;
            int dataSize = -1;
            while (pos + 8 <= wav.length) {
                int chunkSize = leInt(wav, pos + 4);
                if (chunkSize < 0 || pos + 8L + chunkSize > wav.length) return false;
                if (isFourCc(wav, pos, 'f', 'm', 't', ' ') && chunkSize >= 16) {
                    audioFormat = leU16(wav, pos + 8);
                    channels = leU16(wav, pos + 10);
                    sampleRate = leInt(wav, pos + 12);
                    bitsPerSample = leU16(wav, pos + 22);
                } else if (isFourCc(wav, pos, 'd', 'a', 't', 'a')) {
                    dataOffset = pos + 8;
                    dataSize = chunkSize;
                    break;
                }
                pos += 8 + chunkSize + (chunkSize & 1);
            }
            // Deterministic DSP only for uncompressed signed 16-bit PCM.
            if (audioFormat != 1 || channels < 1 || channels > 2 ||
                    sampleRate < 8000 || bitsPerSample != 16 ||
                    dataOffset < 0 || dataSize < 4 || dataOffset + dataSize > wav.length) return false;

            int samples = dataSize / 2;
            float[] pcm = new float[samples];
            for (int i = 0; i < samples; i++) {
                int off = dataOffset + i * 2;
                short s = (short) ((wav[off] & 0xff) | (wav[off + 1] << 8));
                pcm[i] = s / 32768.0f;
            }

            // Envelope compressor: reduce short peaks first so the average speech
            // energy can be raised without crushing consonant transients into 0 dBFS.
            final double threshold = dbToLinear(VOICE_COMP_THRESHOLD_DBFS);
            final double attackSeconds = 0.004;
            final double releaseSeconds = 0.120;
            final double effectiveRate = Math.max(8000.0, sampleRate * (double) channels);
            final double attack = Math.exp(-1.0 / (attackSeconds * effectiveRate));
            final double release = Math.exp(-1.0 / (releaseSeconds * effectiveRate));
            double env = 0.0;
            double sumSquares = 0.0;
            double peak = 0.0;
            for (int i = 0; i < pcm.length; i++) {
                double x = pcm[i];
                double ax = Math.abs(x);
                double coeff = ax > env ? attack : release;
                env = coeff * env + (1.0 - coeff) * ax;
                double gain = 1.0;
                if (env > threshold && env > 1.0e-9) {
                    // output/input ratio in the log domain, equivalent to a 3:1
                    // compressor above the threshold.
                    gain = Math.pow(env / threshold, (1.0 / VOICE_COMP_RATIO) - 1.0);
                }
                double y = x * gain;
                pcm[i] = (float) y;
                sumSquares += y * y;
                peak = Math.max(peak, Math.abs(y));
            }
            if (peak <= 1.0e-9 || sumSquares <= 1.0e-12) return false;

            double rms = Math.sqrt(sumSquares / pcm.length);
            double targetRms = dbToLinear(VOICE_TARGET_RMS_DBFS);
            double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
            double rmsGain = targetRms / rms;
            double peakSafeGain = ceiling / peak;
            // Never use an unchecked gain: the peak constraint always wins.
            double makeup = Math.min(rmsGain, peakSafeGain);
            if (!Double.isFinite(makeup) || makeup <= 0.0) return false;

            double finalPeak = 0.0;
            double finalSquares = 0.0;
            for (int i = 0; i < pcm.length; i++) {
                double y = pcm[i] * makeup;
                // Final brick-wall sample limiter at -2 dBFS. Normally the peak-safe
                // makeup gain means this clamp does nothing; it is a last numerical
                // safety net and guarantees no PCM sample reaches 0 dBFS.
                if (y > ceiling) y = ceiling;
                if (y < -ceiling) y = -ceiling;
                finalPeak = Math.max(finalPeak, Math.abs(y));
                finalSquares += y * y;
                int out = (int) Math.round(y * 32767.0);
                if (out > 32767) out = 32767;
                if (out < -32768) out = -32768;
                int off = dataOffset + i * 2;
                wav[off] = (byte) (out & 0xff);
                wav[off + 1] = (byte) ((out >>> 8) & 0xff);
            }

            // Validation gate before overwriting the synthesized file.
            double finalRms = Math.sqrt(finalSquares / pcm.length);
            if (!Double.isFinite(finalRms) || finalRms <= 0.0 ||
                    finalPeak > ceiling + 1.0e-6 || finalPeak >= 1.0) return false;

            raf.seek(0);
            raf.write(wav);
            raf.setLength(wav.length);
            return true;
        } catch (Exception ignored) {
            return false;
        } finally {
            if (raf != null) {
                try { raf.close(); } catch (Exception ignored) {}
            }
        }
    }

    private double dbToLinear(double db) {
        return Math.pow(10.0, db / 20.0);
    }

    private boolean isFourCc(byte[] data, int off, char a, char b, char c, char d) {
        return data != null && off >= 0 && off + 4 <= data.length &&
                data[off] == (byte) a && data[off + 1] == (byte) b &&
                data[off + 2] == (byte) c && data[off + 3] == (byte) d;
    }

    private int leInt(byte[] data, int off) {
        return (data[off] & 0xff) |
                ((data[off + 1] & 0xff) << 8) |
                ((data[off + 2] & 0xff) << 16) |
                ((data[off + 3] & 0xff) << 24);
    }

    private int leU16(byte[] data, int off) {
        return (data[off] & 0xff) | ((data[off + 1] & 0xff) << 8);
    }

'''
if text.count(anchor) != 1:
    raise SystemExit('v208.91 playback anchor mismatch')
text = text.replace(anchor, helpers + anchor, 1)

# Extend diagnostics.
old_status = '+ ":" + AUDIBLE_MUSIC_DUCK + ":" + VOICE_BOOST + ":ready="'
new_status = '+ ":" + AUDIBLE_MUSIC_DUCK + ":" + VOICE_BOOST + ":" + ENERGY_NORMALIZE_LIMITER + ":ready="'
if old_status not in text:
    raise SystemExit('v208.91 status anchor missing')
text = text.replace(old_status, new_status, 1)

for item in (
    MARKER,
    'VOICE_TARGET_RMS_DBFS = -13.0',
    'VOICE_PEAK_CEILING_DBFS = -2.0',
    'VOICE_COMP_THRESHOLD_DBFS = -18.0',
    'VOICE_COMP_RATIO = 3.0',
    'prepareNormalizedAmplifiedPlayback()',
    'normalizeAndLimitVoiceWav(File file)',
    'finalPeak > ceiling + 1.0e-6',
    'runOnUiThread(MainActivity.this::prepareNormalizedAmplifiedPlayback)',
):
    if item not in text:
        raise SystemExit('v208.91 requirement missing: ' + item)

# No blind +7 dB enhancer may remain in the actual playback setup.
if 'new LoudnessEnhancer(mp.getAudioSessionId())' in text:
    raise SystemExit('blind LoudnessEnhancer playback survived')

java_path.write_text(text, encoding='utf-8')
print('ADMIN_ENERGY_NORMALIZE_LIMITER_V20891_OK')
