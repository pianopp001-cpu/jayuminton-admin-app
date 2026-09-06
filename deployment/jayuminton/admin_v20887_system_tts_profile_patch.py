#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_SYSTEM_TTS_PROFILE_V20887'

if MARKER in text:
    print('ADMIN_SYSTEM_TTS_PROFILE_V20887_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_GALAXY_TAB_TTS_V20886',
    'private void initTts(boolean force)',
    'AudioAttributes.USAGE_MEDIA',
    'private void selectBestKoreanFemaleVoice()',
    'tts.setSpeechRate(clamp(request.rate, 0.75f, 1.15f));',
    'tts.setPitch(clamp(request.pitch, 0.90f, 1.15f));',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.87 prerequisite missing: ' + item)

if 'import android.provider.Settings;' not in text:
    text = text.replace('import android.os.Bundle;\n', 'import android.os.Bundle;\nimport android.provider.Settings;\n', 1)

text = text.replace(
    '    private static final String NATIVE_TTS_FIX = "JAYUMINTON_GALAXY_TAB_TTS_V20886";\n',
    '    private static final String NATIVE_TTS_FIX = "JAYUMINTON_GALAXY_TAB_TTS_V20886";\n'
    '    private static final String SYSTEM_TTS_PROFILE = "JAYUMINTON_SYSTEM_TTS_PROFILE_V20887";\n'
    '    private static final float FALLBACK_SPEECH_RATE = 0.82f;\n'
    '    private static final float FALLBACK_SPEECH_PITCH = 1.00f;\n',
    1,
)

old_selector = '''    private void selectBestKoreanFemaleVoice() {\n        if (tts == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return;\n        Set<Voice> available = tts.getVoices();\n        if (available == null || available.isEmpty()) return;\n\n        List<Voice> koreanVoices = new ArrayList<>();\n        for (Voice voice : available) {\n            Locale locale = voice.getLocale();\n            if (locale != null && "ko".equalsIgnoreCase(locale.getLanguage())) {\n                koreanVoices.add(voice);\n            }\n        }\n        if (koreanVoices.isEmpty()) return;\n\n        koreanVoices.sort((left, right) -> {\n            int scoreCompare = Integer.compare(femaleVoiceScore(right), femaleVoiceScore(left));\n            if (scoreCompare != 0) return scoreCompare;\n            int networkCompare = Boolean.compare(left.isNetworkConnectionRequired(), right.isNetworkConnectionRequired());\n            if (networkCompare != 0) return networkCompare;\n            return Integer.compare(right.getQuality(), left.getQuality());\n        });\n        tts.setVoice(koreanVoices.get(0));\n    }\n\n    private int femaleVoiceScore(Voice voice) {\n        String name = voice.getName() == null ? "" : voice.getName().toLowerCase(Locale.ROOT);\n        int score = 0;\n        String[] preferred = {"female", "woman", "여성", "suna", "seoyeon", "yuna", "ism", "kod"};\n        for (String token : preferred) {\n            if (name.contains(token)) score += 20;\n        }\n        if (!voice.isNetworkConnectionRequired()) score += 8;\n        score += Math.max(0, voice.getQuality());\n        return score;\n    }\n'''

new_selector = '''    private void selectBestKoreanFemaleVoice() {\n        // v208.87: Respect the voice selected in Android TTS settings first.\n        // The previous heuristic could silently replace the user's chosen female\n        // voice with another Korean voice, which made phone and Galaxy Tab sound\n        // different even when their TTS settings were intentionally matched.\n        if (tts == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return;\n        try {\n            Voice configured = tts.getDefaultVoice();\n            if (configured != null) {\n                Locale locale = configured.getLocale();\n                if (locale != null && "ko".equalsIgnoreCase(locale.getLanguage())) {\n                    tts.setVoice(configured);\n                    return;\n                }\n            }\n        } catch (Exception ignored) {}\n\n        // Fallback only when the engine exposes no configured Korean default.\n        Set<Voice> available = tts.getVoices();\n        if (available == null || available.isEmpty()) return;\n        List<Voice> koreanVoices = new ArrayList<>();\n        for (Voice voice : available) {\n            Locale locale = voice.getLocale();\n            if (locale != null && "ko".equalsIgnoreCase(locale.getLanguage())) koreanVoices.add(voice);\n        }\n        if (koreanVoices.isEmpty()) return;\n        koreanVoices.sort((left, right) -> {\n            int scoreCompare = Integer.compare(femaleVoiceScore(right), femaleVoiceScore(left));\n            if (scoreCompare != 0) return scoreCompare;\n            int networkCompare = Boolean.compare(left.isNetworkConnectionRequired(), right.isNetworkConnectionRequired());\n            if (networkCompare != 0) return networkCompare;\n            return Integer.compare(right.getQuality(), left.getQuality());\n        });\n        try { tts.setVoice(koreanVoices.get(0)); } catch (Exception ignored) {}\n    }\n\n    private int femaleVoiceScore(Voice voice) {\n        String name = voice.getName() == null ? "" : voice.getName().toLowerCase(Locale.ROOT);\n        int score = 0;\n        String[] preferred = {\n                "female", "woman", "여성", "seoyeon", "suna", "yuna",\n                "yoonjung", "yunjeong", "yunjung", "yuri", "hayoon", "arin", "jiwoo",\n                "ism", "kod"\n        };\n        String[] male = {"male", "man", "남성"};\n        for (String token : preferred) if (name.contains(token)) score += 80;\n        for (String token : male) if (name.contains(token)) score -= 200;\n        if (!voice.isNetworkConnectionRequired()) score += 8;\n        score += Math.max(0, voice.getQuality());\n        return score;\n    }\n\n    private float systemSpeechRate() {\n        try {\n            int value = Settings.Secure.getInt(\n                    getContentResolver(), Settings.Secure.TTS_DEFAULT_RATE, 100);\n            return clamp(value / 100.0f, 0.50f, 2.00f);\n        } catch (Exception ignored) {\n            return FALLBACK_SPEECH_RATE;\n        }\n    }\n\n    private float systemSpeechPitch() {\n        try {\n            int value = Settings.Secure.getInt(\n                    getContentResolver(), Settings.Secure.TTS_DEFAULT_PITCH, 100);\n            return clamp(value / 100.0f, 0.50f, 2.00f);\n        } catch (Exception ignored) {\n            return FALLBACK_SPEECH_PITCH;\n        }\n    }\n'''

if text.count(old_selector) != 1:
    raise SystemExit('v208.87 voice selector anchor mismatch: ' + str(text.count(old_selector)))
text = text.replace(old_selector, new_selector, 1)

text = text.replace(
    '        tts.setSpeechRate(clamp(request.rate, 0.75f, 1.15f));\n        tts.setPitch(clamp(request.pitch, 0.90f, 1.15f));',
    '        // Follow Android TTS settings so the app preview and actual announcements match.\n'
    '        tts.setSpeechRate(systemSpeechRate());\n'
    '        tts.setPitch(systemSpeechPitch());',
    1,
)

# Extend the diagnostic status string without changing the JS contract.
text = text.replace(
    'return NATIVE_TTS_FIX + ":ready=" + ttsReady.get() + ":attempts=" + ttsInitAttempts;',
    'return NATIVE_TTS_FIX + ":" + SYSTEM_TTS_PROFILE + ":ready=" + ttsReady.get() + ":attempts=" + ttsInitAttempts + ":rate=" + systemSpeechRate();',
    1,
)

for item in (
    MARKER,
    'Settings.Secure.TTS_DEFAULT_RATE',
    'Settings.Secure.TTS_DEFAULT_PITCH',
    'tts.setSpeechRate(systemSpeechRate());',
    'tts.setPitch(systemSpeechPitch());',
    'Voice configured = tts.getDefaultVoice();',
    '"female", "woman", "여성"',
):
    if item not in text:
        raise SystemExit('v208.87 requirement missing: ' + item)

if 'tts.setSpeechRate(clamp(request.rate' in text:
    raise SystemExit('per-message speech-rate override survived')

path.write_text(text, encoding='utf-8')
print('ADMIN_SYSTEM_TTS_PROFILE_V20887_OK')
