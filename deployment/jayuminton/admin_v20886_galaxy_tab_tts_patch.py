#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_GALAXY_TAB_TTS_V20886'

if MARKER in text:
    print('ADMIN_GALAXY_TAB_TTS_V20886_ALREADY_OK')
    raise SystemExit(0)

required = [
    'public final class MainActivity extends Activity implements TextToSpeech.OnInitListener',
    'private final AtomicBoolean ttsReady = new AtomicBoolean(false);',
    'tts = new TextToSpeech(this, this);',
    'public void onInit(int status)',
    'params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM);',
    '.setUsage(AudioAttributes.USAGE_ALARM)',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.86 prerequisite missing: ' + item)

text = text.replace(
    '    private static final int VOICE_REPEAT_COUNT = 3;\n',
    '    private static final int VOICE_REPEAT_COUNT = 3;\n'
    '    private static final int MAX_TTS_INIT_ATTEMPTS = 3;\n'
    '    private static final String NATIVE_TTS_FIX = "JAYUMINTON_GALAXY_TAB_TTS_V20886";\n',
    1,
)

text = text.replace(
    '    private int remainingVoiceRepeats = 0;\n',
    '    private int remainingVoiceRepeats = 0;\n'
    '    private int ttsInitAttempts = 0;\n'
    '    private boolean ttsInitializing = false;\n',
    1,
)

text = text.replace(
    '        tts = new TextToSpeech(this, this);\n        configureWebView();',
    '        initTts(false);\n        configureWebView();',
    1,
)

on_init_anchor = '''    @Override\n    public void onInit(int status) {\n        if (status != TextToSpeech.SUCCESS) {\n            ttsReady.set(false);\n            return;\n        }\n\n        int languageResult = tts.setLanguage(Locale.KOREA);\n        ttsReady.set(languageResult != TextToSpeech.LANG_MISSING_DATA &&\n                languageResult != TextToSpeech.LANG_NOT_SUPPORTED);\n        selectBestKoreanFemaleVoice();\n'''

on_init_new = '''    private void initTts(boolean force) {\n        runOnUiThread(() -> {\n            if (isFinishing() || (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1 && isDestroyed())) return;\n            if (ttsInitializing) return;\n            if (!force && tts != null && ttsReady.get()) return;\n            ttsInitializing = true;\n            ttsReady.set(false);\n            if (force && tts != null) {\n                try { tts.stop(); } catch (Exception ignored) {}\n                try { tts.shutdown(); } catch (Exception ignored) {}\n                tts = null;\n            }\n            ttsInitAttempts += 1;\n            tts = new TextToSpeech(getApplicationContext(), MainActivity.this);\n        });\n    }\n\n    private void scheduleTtsRetry() {\n        if (ttsInitAttempts >= MAX_TTS_INIT_ATTEMPTS) return;\n        View root = webView != null ? webView : getWindow().getDecorView();\n        root.postDelayed(() -> initTts(true), 900L);\n    }\n\n    @Override\n    protected void onResume() {\n        super.onResume();\n        if (!ttsReady.get() && !ttsInitializing) {\n            ttsInitAttempts = 0;\n            initTts(true);\n        }\n    }\n\n    @Override\n    public void onInit(int status) {\n        ttsInitializing = false;\n        if (status != TextToSpeech.SUCCESS || tts == null) {\n            ttsReady.set(false);\n            scheduleTtsRetry();\n            return;\n        }\n\n        int languageResult = tts.setLanguage(Locale.KOREA);\n        if (languageResult == TextToSpeech.LANG_MISSING_DATA || languageResult == TextToSpeech.LANG_NOT_SUPPORTED) {\n            Locale fallback = Locale.getDefault();\n            if (fallback != null && "ko".equalsIgnoreCase(fallback.getLanguage())) {\n                languageResult = tts.setLanguage(fallback);\n            }\n        }\n        boolean languageReady = languageResult != TextToSpeech.LANG_MISSING_DATA &&\n                languageResult != TextToSpeech.LANG_NOT_SUPPORTED;\n        ttsReady.set(languageReady);\n        if (!languageReady) {\n            scheduleTtsRetry();\n            return;\n        }\n        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {\n            try {\n                tts.setAudioAttributes(new AudioAttributes.Builder()\n                        .setUsage(AudioAttributes.USAGE_MEDIA)\n                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)\n                        .build());\n            } catch (Exception ignored) {}\n        }\n        selectBestKoreanFemaleVoice();\n'''

if text.count(on_init_anchor) != 1:
    raise SystemExit(f'onInit anchor mismatch: {text.count(on_init_anchor)}')
text = text.replace(on_init_anchor, on_init_new, 1)

text = text.replace(
    '''        if (tts == null || !ttsReady.get()) {\n            pendingRequest = request;\n            return;\n        }''',
    '''        if (tts == null || !ttsReady.get()) {\n            pendingRequest = request;\n            if (!ttsInitializing) {\n                ttsInitAttempts = 0;\n                initTts(true);\n            }\n            return;\n        }''',
    1,
)

text = text.replace(
    '        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM);',
    '        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_MUSIC);',
    1,
)

text = text.replace(
    '.setUsage(AudioAttributes.USAGE_ALARM)\n                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)',
    '.setUsage(AudioAttributes.USAGE_MEDIA)\n                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)',
    1,
)

text = text.replace(
    'audioManager.requestAudioFocus(null, AudioManager.STREAM_ALARM, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK);',
    'audioManager.requestAudioFocus(null, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK);',
    1,
)

text = text.replace(
    '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);\n                int duckedMusic = Math.max(0, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));\n                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);\n\n                int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);\n                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);''',
    '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);\n                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia, 0);\n\n                // Keep alarm volume untouched for tablet compatibility. Voice output now\n                // follows the same media route used by Android's successful TTS sample.''',
    1,
)

# If the app returned from TTS settings after the user installed a voice, onResume() reinitializes it.
# Add a tiny JS-readable status endpoint for diagnostics without adding any observer/timer work.
voice_anchor = '''        @JavascriptInterface\n        public boolean isSpeaking() {\n            return speaking.get() || (tts != null && tts.isSpeaking());\n        }\n'''
voice_new = voice_anchor + '''\n        @JavascriptInterface\n        public String status() {\n            return NATIVE_TTS_FIX + ":ready=" + ttsReady.get() + ":attempts=" + ttsInitAttempts;\n        }\n'''
if text.count(voice_anchor) != 1:
    raise SystemExit('VoiceBridge status anchor mismatch')
text = text.replace(voice_anchor, voice_new, 1)

for item in (
    MARKER,
    'private void initTts(boolean force)',
    'private void scheduleTtsRetry()',
    'protected void onResume()',
    'AudioAttributes.USAGE_MEDIA',
    'TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_MUSIC',
    'audioManager.requestAudioFocus(null, AudioManager.STREAM_MUSIC',
    'audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia, 0);',
    'public String status()',
):
    if item not in text:
        raise SystemExit('v208.86 requirement missing: ' + item)

if 'TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM' in text:
    raise SystemExit('old TTS alarm stream survived')

path.write_text(text, encoding='utf-8')
print('ADMIN_GALAXY_TAB_TTS_V20886_OK')
