#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_SAFE_AUDIO_BALANCE_V20888'

if MARKER in text:
    print('ADMIN_SAFE_AUDIO_BALANCE_V20888_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_GALAXY_TAB_TTS_V20886',
    'JAYUMINTON_SYSTEM_TTS_PROFILE_V20887',
    'private void beginStrongDucking()',
    'private void restoreAudio()',
    'private void recoverAudioIfNeeded()',
    'TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_MUSIC',
    'audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia, 0);',
    'tts.setSpeechRate(systemSpeechRate());',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.88 prerequisite missing: ' + item)

text = text.replace(
    '    private static final String SYSTEM_TTS_PROFILE = "JAYUMINTON_SYSTEM_TTS_PROFILE_V20887";\n',
    '    private static final String SYSTEM_TTS_PROFILE = "JAYUMINTON_SYSTEM_TTS_PROFILE_V20887";\n'
    '    private static final String SAFE_AUDIO_BALANCE = "JAYUMINTON_SAFE_AUDIO_BALANCE_V20888";\n',
    1,
)

# On v208.86 the tablet fix correctly moved Galaxy Tab speech to the media route,
# but it also raised STREAM_MUSIC to its maximum while speaking. That can leave
# background music painfully loud if focus/utterance callbacks race. v208.88
# never changes the media-volume index during a normal announcement.
old_tts_attrs = '''        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {\n            try {\n                tts.setAudioAttributes(new AudioAttributes.Builder()\n                        .setUsage(AudioAttributes.USAGE_MEDIA)\n                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)\n                        .build());\n            } catch (Exception ignored) {}\n        }\n        selectBestKoreanFemaleVoice();\n'''
new_tts_attrs = '''        applyVoiceAudioRoute();\n        selectBestKoreanFemaleVoice();\n'''
if text.count(old_tts_attrs) != 1:
    raise SystemExit('v208.88 TTS audio-attribute anchor mismatch: ' + str(text.count(old_tts_attrs)))
text = text.replace(old_tts_attrs, new_tts_attrs, 1)

# Tablet: keep the media route that fixed Galaxy Tab TTS.
# Phone: return speech to the independent alarm route used by the older working
# phone build so the announcement can be loud without raising music volume.
helper_anchor = '    private void speakNative(SpeakRequest request) {\n'
helpers = '''    private boolean useMediaVoiceRoute() {\n        try {\n            if (getResources().getConfiguration().smallestScreenWidthDp >= 600) return true;\n        } catch (Exception ignored) {}\n        String model = Build.MODEL == null ? "" : Build.MODEL.toUpperCase(Locale.ROOT);\n        String product = Build.PRODUCT == null ? "" : Build.PRODUCT.toLowerCase(Locale.ROOT);\n        // Samsung Galaxy Tab families. The width check above covers normal tablets;\n        // these prefixes are an extra guard for vendor configurations reporting an\n        // unusual smallest-width value.\n        return model.startsWith("SM-X") || model.startsWith("SM-T") || product.contains("gts");\n    }\n\n    private int voiceStreamType() {\n        return useMediaVoiceRoute() ? AudioManager.STREAM_MUSIC : AudioManager.STREAM_ALARM;\n    }\n\n    private int voiceUsage() {\n        return useMediaVoiceRoute() ? AudioAttributes.USAGE_MEDIA : AudioAttributes.USAGE_ALARM;\n    }\n\n    private void applyVoiceAudioRoute() {\n        if (tts == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return;\n        try {\n            tts.setAudioAttributes(new AudioAttributes.Builder()\n                    .setUsage(voiceUsage())\n                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)\n                    .build());\n        } catch (Exception ignored) {}\n    }\n\n'''
if text.count(helper_anchor) != 1:
    raise SystemExit('v208.88 speakNative anchor mismatch')
text = text.replace(helper_anchor, helpers + helper_anchor, 1)

text = text.replace(
    '        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_MUSIC);',
    '        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, voiceStreamType());',
    1,
)

# Ensure the currently selected route is re-applied immediately before speech.
old_speak_profile = '''        // Follow Android TTS settings so the app preview and actual announcements match.\n        tts.setSpeechRate(systemSpeechRate());\n        tts.setPitch(systemSpeechPitch());\n        selectBestKoreanFemaleVoice();\n'''
new_speak_profile = '''        // Follow Android TTS settings so the app preview and actual announcements match.\n        tts.setSpeechRate(systemSpeechRate());\n        tts.setPitch(systemSpeechPitch());\n        applyVoiceAudioRoute();\n        selectBestKoreanFemaleVoice();\n'''
if text.count(old_speak_profile) != 1:
    raise SystemExit('v208.88 speech profile anchor mismatch')
text = text.replace(old_speak_profile, new_speak_profile, 1)


def replace_method(src: str, signature: str, replacement: str) -> str:
    start = src.find(signature)
    if start < 0:
        raise SystemExit('method not found: ' + signature)
    brace = src.find('{', start)
    if brace < 0:
        raise SystemExit('method brace not found: ' + signature)
    depth = 0
    end = None
    in_string = False
    escaped = False
    quote = ''
    i = brace
    while i < len(src):
        ch = src[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == quote:
                in_string = False
        else:
            if ch in ('"', "'"):
                in_string = True
                quote = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        i += 1
    if end is None:
        raise SystemExit('method end not found: ' + signature)
    return src[:start] + replacement.rstrip() + src[end:]


begin_method = '''    private void beginStrongDucking() {\n        synchronized (audioLock) {\n            if (ducking || audioManager == null) return;\n\n            final boolean mediaVoiceRoute = useMediaVoiceRoute();\n            originalMediaVolume = -1; // v208.88 never modifies normal music volume.\n            originalAlarmVolume = -1;\n\n            // Only phones use the independent alarm stream for a stronger voice.\n            // Save that one value so it can be restored exactly after the message.\n            if (!mediaVoiceRoute) {\n                originalAlarmVolume = audioManager.getStreamVolume(AudioManager.STREAM_ALARM);\n                getSharedPreferences(PREFS, MODE_PRIVATE).edit()\n                        .putBoolean(KEY_WAS_DUCKING, true)\n                        .putInt(KEY_MEDIA_VOLUME, -1)\n                        .putInt(KEY_ALARM_VOLUME, originalAlarmVolume)\n                        .apply();\n            } else {\n                // Tablet speech does not alter any system volume index.\n                getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();\n            }\n\n            try {\n                try {\n                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {\n                        AudioAttributes attrs = new AudioAttributes.Builder()\n                                .setUsage(voiceUsage())\n                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)\n                                .build();\n                        voiceFocusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)\n                                .setAudioAttributes(attrs)\n                                .setAcceptsDelayedFocusGain(false)\n                                .setWillPauseWhenDucked(false)\n                                .build();\n                        audioManager.requestAudioFocus(voiceFocusRequest);\n                    } else {\n                        audioManager.requestAudioFocus(\n                                null, voiceStreamType(), AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK);\n                    }\n                } catch (Exception ignored) {}\n\n                // Critical v208.88 rule: NEVER raise/lower STREAM_MUSIC here.\n                // Android audio focus performs the temporary music ducking itself.\n                // This removes the path that could leave music at maximum volume.\n                if (!mediaVoiceRoute) {\n                    int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);\n                    // Match the older phone behavior: voice gets the independent\n                    // alarm stream at full level, while music stays on its own volume.\n                    audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);\n                }\n                ducking = true;\n            } catch (SecurityException error) {\n                if (originalAlarmVolume >= 0) {\n                    try {\n                        audioManager.setStreamVolume(\n                                AudioManager.STREAM_ALARM, originalAlarmVolume, 0);\n                    } catch (Exception ignored) {}\n                }\n                ducking = false;\n                originalMediaVolume = -1;\n                originalAlarmVolume = -1;\n                getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();\n            }\n        }\n    }\n'''

restore_method = '''    private void restoreAudio() {\n        synchronized (audioLock) {\n            if (audioManager == null) return;\n            try {\n                // Music volume is intentionally never written here. The external\n                // music player simply unducks when audio focus is abandoned.\n                if (originalAlarmVolume >= 0) {\n                    audioManager.setStreamVolume(\n                            AudioManager.STREAM_ALARM, originalAlarmVolume, 0);\n                }\n            } catch (SecurityException ignored) {\n            }\n            try {\n                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && voiceFocusRequest != null) {\n                    audioManager.abandonAudioFocusRequest(voiceFocusRequest);\n                    voiceFocusRequest = null;\n                } else {\n                    audioManager.abandonAudioFocus(null);\n                }\n            } catch (Exception ignored) {}\n            ducking = false;\n            originalMediaVolume = -1;\n            originalAlarmVolume = -1;\n            getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();\n        }\n    }\n'''

recover_method = '''    private void recoverAudioIfNeeded() {\n        boolean wasDucking = getSharedPreferences(PREFS, MODE_PRIVATE)\n                .getBoolean(KEY_WAS_DUCKING, false);\n        if (!wasDucking || audioManager == null) return;\n        int media = getSharedPreferences(PREFS, MODE_PRIVATE).getInt(KEY_MEDIA_VOLUME, -1);\n        int alarm = getSharedPreferences(PREFS, MODE_PRIVATE).getInt(KEY_ALARM_VOLUME, -1);\n        try {\n            // One-time migration safety: an interrupted v208.86/v208.87 session may\n            // have left STREAM_MUSIC at max. Restore the saved pre-announcement value\n            // once on startup. New v208.88 announcements store media=-1 and never\n            // modify the music-volume index.\n            if (media >= 0) audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, media, 0);\n            if (alarm >= 0) audioManager.setStreamVolume(AudioManager.STREAM_ALARM, alarm, 0);\n        } catch (SecurityException ignored) {\n        }\n        getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();\n    }\n'''

text = replace_method(text, '    private void beginStrongDucking()', begin_method)
text = replace_method(text, '    private void restoreAudio()', restore_method)
text = replace_method(text, '    private void recoverAudioIfNeeded()', recover_method)

# Extend diagnostics.
old_status = 'return NATIVE_TTS_FIX + ":" + SYSTEM_TTS_PROFILE + ":ready=" + ttsReady.get() + ":attempts=" + ttsInitAttempts + ":rate=" + systemSpeechRate();'
new_status = 'return NATIVE_TTS_FIX + ":" + SYSTEM_TTS_PROFILE + ":" + SAFE_AUDIO_BALANCE + ":ready=" + ttsReady.get() + ":attempts=" + ttsInitAttempts + ":rate=" + systemSpeechRate() + ":stream=" + voiceStreamType();'
if text.count(old_status) != 1:
    raise SystemExit('v208.88 status anchor mismatch')
text = text.replace(old_status, new_status, 1)

for item in (
    MARKER,
    'private boolean useMediaVoiceRoute()',
    'return useMediaVoiceRoute() ? AudioManager.STREAM_MUSIC : AudioManager.STREAM_ALARM;',
    'params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, voiceStreamType());',
    'applyVoiceAudioRoute();',
    'Critical v208.88 rule: NEVER raise/lower STREAM_MUSIC here.',
    'audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);',
    '.putInt(KEY_MEDIA_VOLUME, -1)',
):
    if item not in text:
        raise SystemExit('v208.88 requirement missing: ' + item)

# The dangerous v208.86 normal-path write must be gone.
if 'audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia, 0);' in text:
    raise SystemExit('dangerous max media-volume write survived')

# Only the startup migration/recovery method may write STREAM_MUSIC now.
begin_start = text.index('    private void beginStrongDucking()')
begin_end = text.index('    private void restoreAudio()', begin_start)
begin_block = text[begin_start:begin_end]
if 'setStreamVolume(AudioManager.STREAM_MUSIC' in begin_block:
    raise SystemExit('normal announcement path still writes media volume')

path.write_text(text, encoding='utf-8')
print('ADMIN_SAFE_AUDIO_BALANCE_V20888_OK')
