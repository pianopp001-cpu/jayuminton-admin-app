#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding='utf-8')

marker = 'JAYUMINTON_REPEAT_TTS_V1999'
if marker in s:
    print('Repeat-safe TTS patch already present.')
    raise SystemExit(0)

# Track each native TTS request independently.  QUEUE_FLUSH causes Android to
# report onStop for the previous utterance; without an id guard that stale
# callback can restore the music/alarm volumes while the next member's voice is
# already speaking.
import_anchor = 'import java.util.concurrent.atomic.AtomicBoolean;\n'
if s.count(import_anchor) != 1:
    raise SystemExit('AtomicBoolean import anchor missing')
s = s.replace(import_anchor, import_anchor + 'import java.util.concurrent.atomic.AtomicLong;\n', 1)

field_anchor = '''    private final AtomicBoolean ttsReady = new AtomicBoolean(false);
    private final AtomicBoolean speaking = new AtomicBoolean(false);
    private final Object audioLock = new Object();'''
field_replacement = '''    private final AtomicBoolean ttsReady = new AtomicBoolean(false);
    private final AtomicBoolean speaking = new AtomicBoolean(false);
    private final AtomicLong speechGeneration = new AtomicLong(0L);
    private volatile String activeUtteranceId = "";
    private final Object audioLock = new Object();
    // JAYUMINTON_REPEAT_TTS_V1999'''
if s.count(field_anchor) != 1:
    raise SystemExit('TTS field anchor missing')
s = s.replace(field_anchor, field_replacement, 1)

listener_old = '''        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override
            public void onStart(String utteranceId) {
                speaking.set(true);
            }

            @Override
            public void onDone(String utteranceId) {
                speaking.set(false);
                runOnUiThread(MainActivity.this::restoreAudio);
            }

            @Override
            public void onError(String utteranceId) {
                speaking.set(false);
                runOnUiThread(MainActivity.this::restoreAudio);
            }

            @Override
            public void onStop(String utteranceId, boolean interrupted) {
                speaking.set(false);
                runOnUiThread(MainActivity.this::restoreAudio);
            }
        });'''
listener_new = '''        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override
            public void onStart(String utteranceId) {
                if (isActiveUtterance(utteranceId)) speaking.set(true);
            }

            @Override
            public void onDone(String utteranceId) {
                finishUtterance(utteranceId);
            }

            @Override
            public void onError(String utteranceId) {
                finishUtterance(utteranceId);
            }

            @Override
            public void onStop(String utteranceId, boolean interrupted) {
                finishUtterance(utteranceId);
            }
        });'''
if s.count(listener_old) != 1:
    raise SystemExit('TTS listener anchor missing')
s = s.replace(listener_old, listener_new, 1)

speak_old = '''    private void speakNative(SpeakRequest request) {
        if (tts == null || !ttsReady.get()) {
            pendingRequest = request;
            return;
        }

        beginStrongDucking();
        speaking.set(true);
        tts.stop();
        tts.setSpeechRate(clamp(request.rate, 0.75f, 1.15f));
        tts.setPitch(clamp(request.pitch, 0.90f, 1.15f));
        selectBestKoreanFemaleVoice();

        Bundle params = new Bundle();
        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM);
        params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);
        int result = tts.speak(request.text, TextToSpeech.QUEUE_FLUSH, params, request.id);
        if (result == TextToSpeech.ERROR) {
            speaking.set(false);
            restoreAudio();
        }
    }
'''
speak_new = '''    private void speakNative(SpeakRequest request) {
        if (tts == null || !ttsReady.get()) {
            pendingRequest = request;
            return;
        }

        long generation = speechGeneration.incrementAndGet();
        String utteranceId = request.id + "-" + generation;
        // Publish the next id BEFORE stopping the previous voice.  A delayed
        // onStop from the previous member is therefore ignored and cannot undo
        // the ducking for this member's announcement.
        activeUtteranceId = utteranceId;
        speaking.set(true);
        tts.stop();
        beginStrongDucking();
        tts.setSpeechRate(clamp(request.rate, 0.75f, 1.15f));
        tts.setPitch(clamp(request.pitch, 0.90f, 1.15f));
        selectBestKoreanFemaleVoice();

        Bundle params = new Bundle();
        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM);
        params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);
        int result = tts.speak(request.text, TextToSpeech.QUEUE_FLUSH, params, utteranceId);
        if (result == TextToSpeech.ERROR && isActiveUtterance(utteranceId)) {
            activeUtteranceId = "";
            speaking.set(false);
            restoreAudio();
        }
    }

    private boolean isActiveUtterance(String utteranceId) {
        return utteranceId != null && utteranceId.equals(activeUtteranceId);
    }

    private void finishUtterance(String utteranceId) {
        if (!isActiveUtterance(utteranceId)) return;
        activeUtteranceId = "";
        speaking.set(false);
        runOnUiThread(MainActivity.this::restoreAudio);
    }
'''
if s.count(speak_old) != 1:
    raise SystemExit('speakNative anchor missing')
s = s.replace(speak_old, speak_new, 1)

stop_old = '''        public void stop() {
            runOnUiThread(() -> {
                if (tts != null) tts.stop();
                speaking.set(false);
                restoreAudio();
            });
        }'''
stop_new = '''        public void stop() {
            runOnUiThread(() -> {
                speechGeneration.incrementAndGet();
                activeUtteranceId = "";
                if (tts != null) tts.stop();
                speaking.set(false);
                restoreAudio();
            });
        }'''
if s.count(stop_old) != 1:
    raise SystemExit('VoiceBridge.stop anchor missing')
s = s.replace(stop_old, stop_new, 1)

# Invalidate callbacks before shutdown for the same reason.
destroy_old = '''    protected void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }'''
destroy_new = '''    protected void onDestroy() {
        speechGeneration.incrementAndGet();
        activeUtteranceId = "";
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }'''
if s.count(destroy_old) != 1:
    raise SystemExit('onDestroy TTS anchor missing')
s = s.replace(destroy_old, destroy_new, 1)

for required in (
    marker,
    'AtomicLong speechGeneration = new AtomicLong(0L)',
    'private volatile String activeUtteranceId = ""',
    'String utteranceId = request.id + "-" + generation',
    'if (isActiveUtterance(utteranceId)) speaking.set(true)',
    'finishUtterance(utteranceId)',
    'speechGeneration.incrementAndGet();',
):
    if required not in s:
        raise SystemExit('missing repeat-safe TTS marker: ' + required)

path.write_text(s, encoding='utf-8')
print('Patched admin TTS so repeated member announcements keep the correct audio ducking until the current voice finishes.')
