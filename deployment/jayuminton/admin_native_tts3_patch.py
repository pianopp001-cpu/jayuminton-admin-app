from pathlib import Path

path = Path('app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')

text = text.replace(
    'private static final int VOICE_VOLUME_STEP = 6;',
    'private static final int MEDIA_DUCK_VOLUME_STEP = 6;\n    private static final int VOICE_REPEAT_COUNT = 3;',
    1,
)

text = text.replace(
    '    private SpeakRequest pendingRequest;\n',
    '    private SpeakRequest pendingRequest;\n    private SpeakRequest activeRepeatRequest;\n    private int remainingVoiceRepeats = 0;\n',
    1,
)

old_done = '''            @Override
            public void onDone(String utteranceId) {
                speaking.set(false);
                runOnUiThread(MainActivity.this::restoreAudio);
            }
'''
new_done = '''            @Override
            public void onDone(String utteranceId) {
                runOnUiThread(() -> {
                    if (activeRepeatRequest != null && remainingVoiceRepeats > 0) {
                        speakNextRepeat();
                    } else {
                        speaking.set(false);
                        activeRepeatRequest = null;
                        restoreAudio();
                    }
                });
            }
'''
if old_done not in text:
    raise SystemExit('TTS onDone anchor missing')
text = text.replace(old_done, new_done, 1)

old_speak = '''        Bundle params = new Bundle();
        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM);
        params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);
        int result = tts.speak(request.text, TextToSpeech.QUEUE_FLUSH, params, request.id);
        if (result == TextToSpeech.ERROR) {
            speaking.set(false);
            restoreAudio();
        }
    }
'''
new_speak = '''        activeRepeatRequest = request;
        remainingVoiceRepeats = VOICE_REPEAT_COUNT;
        speakNextRepeat();
    }

    private void speakNextRepeat() {
        if (tts == null || activeRepeatRequest == null || remainingVoiceRepeats <= 0) {
            speaking.set(false);
            activeRepeatRequest = null;
            restoreAudio();
            return;
        }
        int repeatNumber = VOICE_REPEAT_COUNT - remainingVoiceRepeats + 1;
        remainingVoiceRepeats--;
        Bundle params = new Bundle();
        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM);
        params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);
        int result = tts.speak(
                activeRepeatRequest.text,
                TextToSpeech.QUEUE_FLUSH,
                params,
                activeRepeatRequest.id + "-repeat-" + repeatNumber
        );
        if (result == TextToSpeech.ERROR) {
            remainingVoiceRepeats = 0;
            speaking.set(false);
            activeRepeatRequest = null;
            restoreAudio();
        }
    }
'''
if old_speak not in text:
    raise SystemExit('single TTS speak anchor missing')
text = text.replace(old_speak, new_speak, 1)

old_volume = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int minimumMusic = maxMedia > 0 ? 1 : 0;
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, minimumMusic, 0);

                int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);
                int voiceStep = Math.max(1, Math.min(VOICE_VOLUME_STEP, maxAlarm));
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, voiceStep, 0);
'''
new_volume = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int duckedMusic = Math.max(0, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);

                int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);
'''
if old_volume not in text:
    raise SystemExit('native audio volume anchor missing')
text = text.replace(old_volume, new_volume, 1)

# A user-triggered stop must stop the remaining repeats too.
text = text.replace(
    '                if (tts != null) tts.stop();\n                speaking.set(false);\n                restoreAudio();',
    '                remainingVoiceRepeats = 0;\n                activeRepeatRequest = null;\n                if (tts != null) tts.stop();\n                speaking.set(false);\n                restoreAudio();',
    1,
)

required = [
    'VOICE_REPEAT_COUNT = 3',
    'remainingVoiceRepeats = VOICE_REPEAT_COUNT',
    'speakNextRepeat()',
    'MEDIA_DUCK_VOLUME_STEP = 6',
    'setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0)',
]
for marker in required:
    if marker not in text:
        raise SystemExit('native TTS3 contract missing: ' + marker)

path.write_text(text, encoding='utf-8')
print('native TTS3 contract applied: repeat=3, alarm=max, media<=6')
