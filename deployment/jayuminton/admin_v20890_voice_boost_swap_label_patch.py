#!/usr/bin/env python3
from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
html_path = Path(sys.argv[2] if len(sys.argv) > 2 else 'app/src/main/assets/admin/index.html')
text = java_path.read_text(encoding='utf-8')
html = html_path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_VOICE_BOOST_V20890'

if MARKER in text:
    print('ADMIN_VOICE_BOOST_V20890_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_AUDIBLE_MUSIC_DUCK_V20889',
    'private static final float MUSIC_DUCK_RATIO = 0.30f;',
    'private void speakNative(SpeakRequest request)',
    'private void speakNextRepeat()',
    'params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);',
    'audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.90 prerequisite missing: ' + item)

# Keep background music clearly audible. The user reported 30% was already hard to hear,
# so do NOT lower it further; raise the target slightly to 35% while boosting voice separately.
text = text.replace(
    '    private static final float MUSIC_DUCK_RATIO = 0.30f;\n',
    '    private static final float MUSIC_DUCK_RATIO = 0.35f;\n'
    '    private static final String VOICE_BOOST = "JAYUMINTON_VOICE_BOOST_V20890";\n'
    '    private static final int VOICE_BOOST_MILLIBELS = 700; // +7 dB software gain\n'
    '    private static final String AMP_SYNTH_PREFIX = "jayuminton_amp_synth_";\n',
    1,
)

# Native amplified playback needs its own audio session so LoudnessEnhancer affects voice only.
if 'import android.media.MediaPlayer;' not in text:
    text = text.replace('import android.media.AudioFocusRequest;\n', 'import android.media.AudioFocusRequest;\nimport android.media.MediaPlayer;\nimport android.media.audiofx.LoudnessEnhancer;\n', 1)
if 'import java.io.File;' not in text:
    text = text.replace('import java.util.ArrayList;\n', 'import java.io.File;\nimport java.util.ArrayList;\n', 1)

text = text.replace(
    '    private int remainingVoiceRepeats = 0;\n',
    '    private int remainingVoiceRepeats = 0;\n'
    '    private MediaPlayer amplifiedVoicePlayer;\n'
    '    private LoudnessEnhancer amplifiedVoiceEnhancer;\n'
    '    private File amplifiedVoiceFile;\n'
    '    private volatile String currentAmplifiedSynthId = "";\n',
    1,
)

old_listener = '''            @Override\n            public void onDone(String utteranceId) {\n                runOnUiThread(() -> {\n                    if (activeRepeatRequest != null && remainingVoiceRepeats > 0) {\n                        speakNextRepeat();\n                    } else {\n                        speaking.set(false);\n                        activeRepeatRequest = null;\n                        restoreAudio();\n                    }\n                });\n            }\n\n            @Override\n            public void onError(String utteranceId) {\n                speaking.set(false);\n                runOnUiThread(MainActivity.this::restoreAudio);\n            }\n\n            @Override\n            public void onStop(String utteranceId, boolean interrupted) {\n                speaking.set(false);\n                runOnUiThread(MainActivity.this::restoreAudio);\n            }\n'''
new_listener = '''            @Override\n            public void onDone(String utteranceId) {\n                if (utteranceId != null && utteranceId.equals(currentAmplifiedSynthId)) {\n                    currentAmplifiedSynthId = "";\n                    runOnUiThread(MainActivity.this::startAmplifiedRepeatPlayback);\n                    return;\n                }\n                runOnUiThread(() -> {\n                    if (activeRepeatRequest != null && remainingVoiceRepeats > 0) {\n                        speakNextRepeat();\n                    } else {\n                        speaking.set(false);\n                        activeRepeatRequest = null;\n                        releaseAmplifiedVoice(true);\n                        restoreAudio();\n                    }\n                });\n            }\n\n            @Override\n            public void onError(String utteranceId) {\n                if (utteranceId != null && utteranceId.equals(currentAmplifiedSynthId)) {\n                    currentAmplifiedSynthId = "";\n                    runOnUiThread(MainActivity.this::fallbackToDirectTts);\n                    return;\n                }\n                speaking.set(false);\n                runOnUiThread(() -> {\n                    releaseAmplifiedVoice(true);\n                    restoreAudio();\n                });\n            }\n\n            @Override\n            public void onStop(String utteranceId, boolean interrupted) {\n                if (utteranceId != null && utteranceId.startsWith(AMP_SYNTH_PREFIX)) {\n                    // Old synth callbacks are intentionally ignored after a new message/stop.\n                    if (utteranceId.equals(currentAmplifiedSynthId)) {\n                        currentAmplifiedSynthId = "";\n                        runOnUiThread(MainActivity.this::fallbackToDirectTts);\n                    }\n                    return;\n                }\n                speaking.set(false);\n                runOnUiThread(() -> {\n                    releaseAmplifiedVoice(true);\n                    restoreAudio();\n                });\n            }\n'''
if text.count(old_listener) != 1:
    raise SystemExit('v208.90 listener anchor mismatch: ' + str(text.count(old_listener)))
text = text.replace(old_listener, new_listener, 1)

old_native = '''        beginStrongDucking();\n        speaking.set(true);\n        tts.stop();\n        // Follow Android TTS settings so the app preview and actual announcements match.\n        tts.setSpeechRate(systemSpeechRate());\n        tts.setPitch(systemSpeechPitch());\n        applyVoiceAudioRoute();\n        selectBestKoreanFemaleVoice();\n\n        activeRepeatRequest = request;\n        remainingVoiceRepeats = VOICE_REPEAT_COUNT;\n        speakNextRepeat();\n'''
new_native = '''        beginStrongDucking();\n        speaking.set(true);\n        // Cancel any previous synthesis/playback without restoring the ducked music yet.\n        currentAmplifiedSynthId = "";\n        try { tts.stop(); } catch (Exception ignored) {}\n        releaseAmplifiedVoice(true);\n        // Follow Android TTS settings so the app preview and actual announcements match.\n        tts.setSpeechRate(systemSpeechRate());\n        tts.setPitch(systemSpeechPitch());\n        applyVoiceAudioRoute();\n        selectBestKoreanFemaleVoice();\n\n        activeRepeatRequest = request;\n        remainingVoiceRepeats = VOICE_REPEAT_COUNT;\n        startAmplifiedSynthesis();\n'''
if text.count(old_native) != 1:
    raise SystemExit('v208.90 speakNative anchor mismatch: ' + str(text.count(old_native)))
text = text.replace(old_native, new_native, 1)

# Insert amplified synthesis/playback helpers before the existing direct-TTS repeat method.
anchor = '    private void speakNextRepeat() {\n'
helpers = '''    private void startAmplifiedSynthesis() {\n        if (tts == null || activeRepeatRequest == null) {\n            fallbackToDirectTts();\n            return;\n        }\n        try {\n            releaseAmplifiedVoice(true);\n            amplifiedVoiceFile = new File(\n                    getCacheDir(), "jayuminton_voice_" + System.nanoTime() + ".wav");\n            currentAmplifiedSynthId = AMP_SYNTH_PREFIX + System.nanoTime();\n            Bundle synthParams = new Bundle();\n            int result = tts.synthesizeToFile(\n                    activeRepeatRequest.text, synthParams, amplifiedVoiceFile, currentAmplifiedSynthId);\n            if (result == TextToSpeech.ERROR) {\n                currentAmplifiedSynthId = "";\n                fallbackToDirectTts();\n            }\n        } catch (Exception error) {\n            currentAmplifiedSynthId = "";\n            fallbackToDirectTts();\n        }\n    }\n\n    private void startAmplifiedRepeatPlayback() {\n        if (activeRepeatRequest == null || amplifiedVoiceFile == null ||\n                !amplifiedVoiceFile.exists() || amplifiedVoiceFile.length() <= 0) {\n            fallbackToDirectTts();\n            return;\n        }\n        if (remainingVoiceRepeats <= 0) {\n            finishAmplifiedSpeech();\n            return;\n        }\n\n        remainingVoiceRepeats--;\n        releaseAmplifiedPlayerOnly();\n        try {\n            MediaPlayer player = new MediaPlayer();\n            amplifiedVoicePlayer = player;\n            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {\n                player.setAudioAttributes(new AudioAttributes.Builder()\n                        .setUsage(voiceUsage())\n                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)\n                        .build());\n            } else {\n                player.setAudioStreamType(voiceStreamType());\n            }\n            player.setDataSource(amplifiedVoiceFile.getAbsolutePath());\n            player.setVolume(1.0f, 1.0f);\n            player.setOnPreparedListener(mp -> {\n                try {\n                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {\n                        LoudnessEnhancer enhancer = new LoudnessEnhancer(mp.getAudioSessionId());\n                        enhancer.setTargetGain(VOICE_BOOST_MILLIBELS);\n                        enhancer.setEnabled(true);\n                        amplifiedVoiceEnhancer = enhancer;\n                    }\n                } catch (Exception ignored) {\n                    amplifiedVoiceEnhancer = null;\n                }\n                try { mp.start(); } catch (Exception error) { fallbackToDirectTts(); }\n            });\n            player.setOnCompletionListener(mp -> runOnUiThread(() -> {\n                releaseAmplifiedPlayerOnly();\n                if (remainingVoiceRepeats > 0) {\n                    startAmplifiedRepeatPlayback();\n                } else {\n                    finishAmplifiedSpeech();\n                }\n            }));\n            player.setOnErrorListener((mp, what, extra) -> {\n                runOnUiThread(MainActivity.this::fallbackToDirectTts);\n                return true;\n            });\n            player.prepareAsync();\n        } catch (Exception error) {\n            fallbackToDirectTts();\n        }\n    }\n\n    private void fallbackToDirectTts() {\n        currentAmplifiedSynthId = "";\n        releaseAmplifiedVoice(true);\n        if (activeRepeatRequest == null || tts == null) {\n            speaking.set(false);\n            activeRepeatRequest = null;\n            restoreAudio();\n            return;\n        }\n        // Direct TTS remains as a compatibility fallback. It is still stream-max/volume=1.0.\n        remainingVoiceRepeats = VOICE_REPEAT_COUNT;\n        speakNextRepeat();\n    }\n\n    private void finishAmplifiedSpeech() {\n        currentAmplifiedSynthId = "";\n        releaseAmplifiedVoice(true);\n        remainingVoiceRepeats = 0;\n        speaking.set(false);\n        activeRepeatRequest = null;\n        restoreAudio();\n    }\n\n    private void releaseAmplifiedPlayerOnly() {\n        if (amplifiedVoiceEnhancer != null) {\n            try { amplifiedVoiceEnhancer.setEnabled(false); } catch (Exception ignored) {}\n            try { amplifiedVoiceEnhancer.release(); } catch (Exception ignored) {}\n            amplifiedVoiceEnhancer = null;\n        }\n        if (amplifiedVoicePlayer != null) {\n            try { amplifiedVoicePlayer.stop(); } catch (Exception ignored) {}\n            try { amplifiedVoicePlayer.release(); } catch (Exception ignored) {}\n            amplifiedVoicePlayer = null;\n        }\n    }\n\n    private void releaseAmplifiedVoice(boolean deleteFile) {\n        releaseAmplifiedPlayerOnly();\n        if (deleteFile && amplifiedVoiceFile != null) {\n            try { amplifiedVoiceFile.delete(); } catch (Exception ignored) {}\n            amplifiedVoiceFile = null;\n        }\n    }\n\n'''
if text.count(anchor) != 1:
    raise SystemExit('v208.90 speakNextRepeat anchor mismatch')
text = text.replace(anchor, helpers + anchor, 1)

old_stop = '''                remainingVoiceRepeats = 0;\n                activeRepeatRequest = null;\n                if (tts != null) tts.stop();\n                speaking.set(false);\n                restoreAudio();\n'''
new_stop = '''                remainingVoiceRepeats = 0;\n                activeRepeatRequest = null;\n                currentAmplifiedSynthId = "";\n                releaseAmplifiedVoice(true);\n                if (tts != null) tts.stop();\n                speaking.set(false);\n                restoreAudio();\n'''
if text.count(old_stop) != 1:
    raise SystemExit('v208.90 VoiceBridge.stop anchor mismatch: ' + str(text.count(old_stop)))
text = text.replace(old_stop, new_stop, 1)

old_destroy = '''    protected void onDestroy() {\n        if (tts != null) {\n            tts.stop();\n            tts.shutdown();\n        }\n        restoreAudio();\n'''
new_destroy = '''    protected void onDestroy() {\n        currentAmplifiedSynthId = "";\n        releaseAmplifiedVoice(true);\n        if (tts != null) {\n            tts.stop();\n            tts.shutdown();\n        }\n        restoreAudio();\n'''
if text.count(old_destroy) != 1:
    raise SystemExit('v208.90 onDestroy anchor mismatch: ' + str(text.count(old_destroy)))
text = text.replace(old_destroy, new_destroy, 1)

# Visible label only. Keep the same button ID, click handler, target action and error handling.
old_label = "make('jmQuickMultiSwap','다중교환'"
new_label = "make('jmQuickMultiSwap','교환'"
if html.count(old_label) != 1:
    raise SystemExit('v208.90 quick swap label anchor mismatch: ' + str(html.count(old_label)))
html = html.replace(old_label, new_label, 1)

# Extend diagnostics without changing the JS interface.
old_status_part = '+ ":" + AUDIBLE_MUSIC_DUCK + ":ready="'
new_status_part = '+ ":" + AUDIBLE_MUSIC_DUCK + ":" + VOICE_BOOST + ":ready="'
if old_status_part not in text:
    raise SystemExit('v208.90 diagnostic anchor missing')
text = text.replace(old_status_part, new_status_part, 1)

for item in (
    MARKER,
    'private static final float MUSIC_DUCK_RATIO = 0.35f;',
    'VOICE_BOOST_MILLIBELS = 700',
    'new LoudnessEnhancer(mp.getAudioSessionId())',
    'tts.synthesizeToFile(',
    'startAmplifiedRepeatPlayback()',
    "make('jmQuickMultiSwap','교환'",
):
    haystack = text if item != "make('jmQuickMultiSwap','교환'" else html
    if item not in haystack:
        raise SystemExit('v208.90 requirement missing: ' + item)

if "make('jmQuickMultiSwap','다중교환'" in html:
    raise SystemExit('old visible multi-swap label survived')
if 'setStreamVolume(AudioManager.STREAM_MUSIC, 0,' in text:
    raise SystemExit('unsafe music mute exists')
if 'setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia' in text:
    raise SystemExit('unsafe music max write exists')

java_path.write_text(text, encoding='utf-8')
html_path.write_text(html, encoding='utf-8')
print('ADMIN_VOICE_BOOST_V20890_OK')
