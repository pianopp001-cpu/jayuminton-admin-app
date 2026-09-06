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

old_attrs = """        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            try {
                tts.setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build());
            } catch (Exception ignored) {}
        }
        selectBestKoreanFemaleVoice();
"""
new_attrs = """        applyVoiceAudioRoute();
        selectBestKoreanFemaleVoice();
"""
if text.count(old_attrs) != 1:
    raise SystemExit('v208.88 TTS attributes anchor mismatch: ' + str(text.count(old_attrs)))
text = text.replace(old_attrs, new_attrs, 1)

helper_anchor = '    private void speakNative(SpeakRequest request) {\n'
helpers = """    private boolean useMediaVoiceRoute() {
        try {
            if (getResources().getConfiguration().smallestScreenWidthDp >= 600) return true;
        } catch (Exception ignored) {}
        String model = Build.MODEL == null ? "" : Build.MODEL.toUpperCase(Locale.ROOT);
        String product = Build.PRODUCT == null ? "" : Build.PRODUCT.toLowerCase(Locale.ROOT);
        return model.startsWith("SM-X") || model.startsWith("SM-T") || product.contains("gts");
    }

    private int voiceStreamType() {
        return useMediaVoiceRoute() ? AudioManager.STREAM_MUSIC : AudioManager.STREAM_ALARM;
    }

    private int voiceUsage() {
        return useMediaVoiceRoute() ? AudioAttributes.USAGE_MEDIA : AudioAttributes.USAGE_ALARM;
    }

    private void applyVoiceAudioRoute() {
        if (tts == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return;
        try {
            tts.setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(voiceUsage())
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build());
        } catch (Exception ignored) {}
    }

"""
if text.count(helper_anchor) != 1:
    raise SystemExit('v208.88 speakNative anchor mismatch')
text = text.replace(helper_anchor, helpers + helper_anchor, 1)

text = text.replace(
    '        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_MUSIC);',
    '        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, voiceStreamType());',
    1,
)

old_profile = """        // Follow Android TTS settings so the app preview and actual announcements match.
        tts.setSpeechRate(systemSpeechRate());
        tts.setPitch(systemSpeechPitch());
        selectBestKoreanFemaleVoice();
"""
new_profile = """        // Follow Android TTS settings so the app preview and actual announcements match.
        tts.setSpeechRate(systemSpeechRate());
        tts.setPitch(systemSpeechPitch());
        applyVoiceAudioRoute();
        selectBestKoreanFemaleVoice();
"""
if text.count(old_profile) != 1:
    raise SystemExit('v208.88 speech profile anchor mismatch')
text = text.replace(old_profile, new_profile, 1)

def replace_between(src: str, start_sig: str, next_sig: str, replacement: str) -> str:
    start = src.find(start_sig)
    if start < 0:
        raise SystemExit('method start not found: ' + start_sig)
    end = src.find(next_sig, start + len(start_sig))
    if end < 0:
        raise SystemExit('next method not found: ' + next_sig)
    return src[:start] + replacement.rstrip() + '\n\n' + src[end:]

begin_method = """    private void beginStrongDucking() {
        synchronized (audioLock) {
            if (ducking || audioManager == null) return;

            final boolean mediaVoiceRoute = useMediaVoiceRoute();
            originalMediaVolume = -1;
            originalAlarmVolume = -1;

            if (!mediaVoiceRoute) {
                originalAlarmVolume = audioManager.getStreamVolume(AudioManager.STREAM_ALARM);
                getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                        .putBoolean(KEY_WAS_DUCKING, true)
                        .putInt(KEY_MEDIA_VOLUME, -1)
                        .putInt(KEY_ALARM_VOLUME, originalAlarmVolume)
                        .apply();
            } else {
                getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
            }

            try {
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        AudioAttributes attrs = new AudioAttributes.Builder()
                                .setUsage(voiceUsage())
                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                                .build();
                        voiceFocusRequest = new AudioFocusRequest.Builder(
                                AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                                .setAudioAttributes(attrs)
                                .setAcceptsDelayedFocusGain(false)
                                .setWillPauseWhenDucked(false)
                                .build();
                        audioManager.requestAudioFocus(voiceFocusRequest);
                    } else {
                        audioManager.requestAudioFocus(
                                null, voiceStreamType(),
                                AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK);
                    }
                } catch (Exception ignored) {}

                // v208.88 safety rule: normal announcements never change STREAM_MUSIC.
                // Android audio focus alone performs temporary music ducking.
                if (!mediaVoiceRoute) {
                    int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);
                    audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);
                }
                ducking = true;
            } catch (SecurityException error) {
                if (originalAlarmVolume >= 0) {
                    try {
                        audioManager.setStreamVolume(
                                AudioManager.STREAM_ALARM, originalAlarmVolume, 0);
                    } catch (Exception ignored) {}
                }
                ducking = false;
                originalMediaVolume = -1;
                originalAlarmVolume = -1;
                getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
            }
        }
    }
"""

restore_method = """    private void restoreAudio() {
        synchronized (audioLock) {
            if (audioManager == null) return;
            try {
                // STREAM_MUSIC is deliberately untouched. Releasing audio focus
                // makes the external music player return to its own existing volume.
                if (originalAlarmVolume >= 0) {
                    audioManager.setStreamVolume(
                            AudioManager.STREAM_ALARM, originalAlarmVolume, 0);
                }
            } catch (SecurityException ignored) {
            }
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                        && voiceFocusRequest != null) {
                    audioManager.abandonAudioFocusRequest(voiceFocusRequest);
                    voiceFocusRequest = null;
                } else {
                    audioManager.abandonAudioFocus(null);
                }
            } catch (Exception ignored) {}
            ducking = false;
            originalMediaVolume = -1;
            originalAlarmVolume = -1;
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
        }
    }
"""

recover_method = """    private void recoverAudioIfNeeded() {
        boolean wasDucking = getSharedPreferences(PREFS, MODE_PRIVATE)
                .getBoolean(KEY_WAS_DUCKING, false);
        if (!wasDucking || audioManager == null) return;
        int media = getSharedPreferences(PREFS, MODE_PRIVATE)
                .getInt(KEY_MEDIA_VOLUME, -1);
        int alarm = getSharedPreferences(PREFS, MODE_PRIVATE)
                .getInt(KEY_ALARM_VOLUME, -1);
        try {
            // Migration safety for an interrupted v208.86/v208.87 announcement:
            // restore the old saved media value once. v208.88 itself stores -1.
            if (media >= 0) {
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, media, 0);
            }
            if (alarm >= 0) {
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, alarm, 0);
            }
        } catch (SecurityException ignored) {
        }
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
    }
"""

text = replace_between(text, '    private void beginStrongDucking()', '    private void restoreAudio()', begin_method)
text = replace_between(text, '    private void restoreAudio()', '    private void recoverAudioIfNeeded()', restore_method)
text = replace_between(text, '    private void recoverAudioIfNeeded()', '    @Override\n    public void onBackPressed()', recover_method)

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
    'normal announcements never change STREAM_MUSIC',
    'audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);',
    '.putInt(KEY_MEDIA_VOLUME, -1)',
):
    if item not in text:
        raise SystemExit('v208.88 requirement missing: ' + item)

if 'audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia, 0);' in text:
    raise SystemExit('dangerous max media-volume write survived')

begin_start = text.index('    private void beginStrongDucking()')
begin_end = text.index('    private void restoreAudio()', begin_start)
if 'setStreamVolume(AudioManager.STREAM_MUSIC' in text[begin_start:begin_end]:
    raise SystemExit('normal announcement path still writes media volume')

path.write_text(text, encoding='utf-8')
print('ADMIN_SAFE_AUDIO_BALANCE_V20888_OK')
