#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_AUDIBLE_MUSIC_DUCK_V20889'

if MARKER in text:
    print('ADMIN_AUDIBLE_MUSIC_DUCK_V20889_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_SAFE_AUDIO_BALANCE_V20888',
    'private boolean useMediaVoiceRoute()',
    'private int voiceStreamType()',
    'private void beginStrongDucking()',
    'private void restoreAudio()',
    'private void recoverAudioIfNeeded()',
    'params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, voiceStreamType());',
    'params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.89 prerequisite missing: ' + item)

text = text.replace(
    '    private static final String SAFE_AUDIO_BALANCE = "JAYUMINTON_SAFE_AUDIO_BALANCE_V20888";\n',
    '    private static final String SAFE_AUDIO_BALANCE = "JAYUMINTON_SAFE_AUDIO_BALANCE_V20888";\n'
    '    private static final String AUDIBLE_MUSIC_DUCK = "JAYUMINTON_AUDIBLE_MUSIC_DUCK_V20889";\n'
    '    private static final float MUSIC_DUCK_RATIO = 0.30f;\n',
    1,
)

# Insert a deterministic non-zero duck level helper before beginStrongDucking.
anchor = '    private void beginStrongDucking() {\n'
helper = '''    private int audibleDuckedMusicVolume(int originalVolume) {\n        if (audioManager == null || originalVolume <= 0) return originalVolume;\n        int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);\n        int target = Math.round(originalVolume * MUSIC_DUCK_RATIO);\n        // Keep music clearly present: never turn a playing stream to zero.\n        target = Math.max(1, target);\n        if (originalVolume >= 5 && maxMedia >= 5) target = Math.max(2, target);\n        return Math.min(originalVolume, Math.min(target, maxMedia));\n    }\n\n'''
if text.count(anchor) != 1:
    raise SystemExit('v208.89 beginStrongDucking anchor mismatch')
text = text.replace(anchor, helper + anchor, 1)


def replace_between(src: str, start_sig: str, next_sig: str, replacement: str) -> str:
    start = src.find(start_sig)
    if start < 0:
        raise SystemExit('method not found: ' + start_sig)
    end = src.find(next_sig, start + len(start_sig))
    if end < 0:
        raise SystemExit('next method not found: ' + next_sig)
    return src[:start] + replacement.rstrip() + '\n\n' + src[end:]

begin_method = '''    private void beginStrongDucking() {\n        synchronized (audioLock) {\n            if (ducking || audioManager == null) return;\n\n            final boolean mediaVoiceRoute = useMediaVoiceRoute();\n            originalMediaVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC);\n            originalAlarmVolume = audioManager.getStreamVolume(AudioManager.STREAM_ALARM);\n\n            // Save the exact pre-announcement levels before touching either stream.\n            // If the process is interrupted, recoverAudioIfNeeded() restores these.\n            getSharedPreferences(PREFS, MODE_PRIVATE).edit()\n                    .putBoolean(KEY_WAS_DUCKING, true)\n                    .putInt(KEY_MEDIA_VOLUME, originalMediaVolume)\n                    .putInt(KEY_ALARM_VOLUME, originalAlarmVolume)\n                    .apply();\n\n            try {\n                if (mediaVoiceRoute) {\n                    // Galaxy Tab TTS must stay on the media route for compatibility.\n                    // Do NOT lower the media stream index here because that would also\n                    // lower TTS. Instead request transient ducking: other music becomes\n                    // quieter while the TTS utterance stays at KEY_PARAM_VOLUME=1.0.\n                    try {\n                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {\n                            AudioAttributes attrs = new AudioAttributes.Builder()\n                                    .setUsage(AudioAttributes.USAGE_MEDIA)\n                                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)\n                                    .build();\n                            voiceFocusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)\n                                    .setAudioAttributes(attrs)\n                                    .setAcceptsDelayedFocusGain(false)\n                                    .setWillPauseWhenDucked(false)\n                                    .build();\n                            audioManager.requestAudioFocus(voiceFocusRequest);\n                        } else {\n                            audioManager.requestAudioFocus(\n                                    null, AudioManager.STREAM_MUSIC,\n                                    AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK);\n                        }\n                    } catch (Exception ignored) {}\n                } else {\n                    // Phone: voice is on the independent alarm stream. Reduce music\n                    // to about 30% of the user's PREVIOUS level, never to zero, and\n                    // do not request a second system duck (which could make it inaudible).\n                    int duckedMusic = audibleDuckedMusicVolume(originalMediaVolume);\n                    if (duckedMusic >= 0 && duckedMusic != originalMediaVolume) {\n                        audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);\n                    }\n\n                    // The announcement itself is deliberately maximum volume on phone.\n                    int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);\n                    audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);\n                }\n                ducking = true;\n            } catch (SecurityException error) {\n                try {\n                    if (originalMediaVolume >= 0) {\n                        audioManager.setStreamVolume(\n                                AudioManager.STREAM_MUSIC, originalMediaVolume, 0);\n                    }\n                    if (originalAlarmVolume >= 0) {\n                        audioManager.setStreamVolume(\n                                AudioManager.STREAM_ALARM, originalAlarmVolume, 0);\n                    }\n                } catch (Exception ignored) {}\n                ducking = false;\n                originalMediaVolume = -1;\n                originalAlarmVolume = -1;\n                getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();\n            }\n        }\n    }\n'''

restore_method = '''    private void restoreAudio() {\n        synchronized (audioLock) {\n            if (audioManager == null) return;\n            try {\n                // Restore EXACTLY what the user had before the announcement.\n                // Never restore to max or to a guessed value.\n                if (originalMediaVolume >= 0) {\n                    audioManager.setStreamVolume(\n                            AudioManager.STREAM_MUSIC, originalMediaVolume, 0);\n                }\n                if (originalAlarmVolume >= 0) {\n                    audioManager.setStreamVolume(\n                            AudioManager.STREAM_ALARM, originalAlarmVolume, 0);\n                }\n            } catch (SecurityException ignored) {\n            }\n            try {\n                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && voiceFocusRequest != null) {\n                    audioManager.abandonAudioFocusRequest(voiceFocusRequest);\n                    voiceFocusRequest = null;\n                } else if (useMediaVoiceRoute()) {\n                    audioManager.abandonAudioFocus(null);\n                }\n            } catch (Exception ignored) {}\n            ducking = false;\n            originalMediaVolume = -1;\n            originalAlarmVolume = -1;\n            getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();\n        }\n    }\n'''

recover_method = '''    private void recoverAudioIfNeeded() {\n        boolean wasDucking = getSharedPreferences(PREFS, MODE_PRIVATE)\n                .getBoolean(KEY_WAS_DUCKING, false);\n        if (!wasDucking || audioManager == null) return;\n        int media = getSharedPreferences(PREFS, MODE_PRIVATE).getInt(KEY_MEDIA_VOLUME, -1);\n        int alarm = getSharedPreferences(PREFS, MODE_PRIVATE).getInt(KEY_ALARM_VOLUME, -1);\n        try {\n            if (media >= 0) audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, media, 0);\n            if (alarm >= 0) audioManager.setStreamVolume(AudioManager.STREAM_ALARM, alarm, 0);\n        } catch (SecurityException ignored) {\n        }\n        getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();\n    }\n'''

text = replace_between(text, '    private void beginStrongDucking()', '    private void restoreAudio()', begin_method)
text = replace_between(text, '    private void restoreAudio()', '    private void recoverAudioIfNeeded()', restore_method)
text = replace_between(text, '    private void recoverAudioIfNeeded()', '    @Override\n    public void onBackPressed()', recover_method)

old_status = 'return NATIVE_TTS_FIX + ":" + SYSTEM_TTS_PROFILE + ":" + SAFE_AUDIO_BALANCE + ":ready=" + ttsReady.get() + ":attempts=" + ttsInitAttempts + ":rate=" + systemSpeechRate() + ":stream=" + voiceStreamType();'
new_status = 'return NATIVE_TTS_FIX + ":" + SYSTEM_TTS_PROFILE + ":" + SAFE_AUDIO_BALANCE + ":" + AUDIBLE_MUSIC_DUCK + ":ready=" + ttsReady.get() + ":attempts=" + ttsInitAttempts + ":rate=" + systemSpeechRate() + ":stream=" + voiceStreamType();'
if text.count(old_status) != 1:
    raise SystemExit('v208.89 diagnostic anchor mismatch: ' + str(text.count(old_status)))
text = text.replace(old_status, new_status, 1)

for item in (
    MARKER,
    'private static final float MUSIC_DUCK_RATIO = 0.30f;',
    'private int audibleDuckedMusicVolume(int originalVolume)',
    'target = Math.max(1, target);',
    'audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);',
    'audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);',
    'AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK',
    'params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);',
):
    if item not in text:
        raise SystemExit('v208.89 requirement missing: ' + item)

# Safety: no normal path may ever set music to max or zero.
if 'setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia' in text:
    raise SystemExit('unsafe max music write survived')
if 'setStreamVolume(AudioManager.STREAM_MUSIC, 0,' in text:
    raise SystemExit('unsafe mute music write survived')

path.write_text(text, encoding='utf-8')
print('ADMIN_AUDIBLE_MUSIC_DUCK_V20889_OK')
