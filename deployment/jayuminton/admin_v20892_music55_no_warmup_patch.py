#!/usr/bin/env python3
from pathlib import Path
import re
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
html_path = Path(sys.argv[2] if len(sys.argv) > 2 else 'app/src/main/assets/admin/index.html')
java = java_path.read_text(encoding='utf-8')
html = html_path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_MUSIC55_NO_WARMUP_V20892'

if MARKER in java:
    print('ADMIN_MUSIC55_NO_WARMUP_V20892_ALREADY_OK')
    raise SystemExit(0)

required_java = [
    'JAYUMINTON_FAST_PEAK_GUARD_V20891B',
    'JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891',
    'private static final float MUSIC_DUCK_RATIO = 0.35f;',
    'private int audibleDuckedMusicVolume(int originalVolume)',
    'audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);',
    'VOICE_TARGET_RMS_DBFS = -13.0',
    'VOICE_PEAK_CEILING_DBFS = -2.0',
]
for item in required_java:
    if item not in java:
        raise SystemExit('v208.92 java prerequisite missing: ' + item)

# 35% of Android's discrete stream index sounded almost muted in field use.
# Keep the announcement clearly dominant, but leave music audibly present at ~55%
# of the user's exact pre-announcement media volume.
java = java.replace(
    '    private static final float MUSIC_DUCK_RATIO = 0.35f;\n',
    '    private static final float MUSIC_DUCK_RATIO = 0.55f;\n'
    '    private static final String MUSIC55_NO_WARMUP = "JAYUMINTON_MUSIC55_NO_WARMUP_V20892";\n',
    1,
)

# The legacy browser-side warmup synthesizes a zero-width utterance at volume 0.
# Some Samsung devices still open/close the audio route and produce a click/static pop.
# Native TTS already initializes independently, so mark the web voice path warmed without
# synthesizing any audio. Real announcements are untouched.
warmup_re = re.compile(
    r"if\s*\(!VOICE_WARMED\)\s*\{\s*"
    r"const\s+utterance\s*=\s*new\s+SpeechSynthesisUtterance\('\\u200b'\);\s*"
    r"utterance\.lang\s*=\s*'ko-KR';\s*"
    r"utterance\.volume\s*=\s*0;\s*"
    r"utterance\.onstart\s*=\s*utterance\.onend\s*=\s*function\(\)\s*\{\s*"
    r"VOICE_WARMED\s*=\s*true;\s*"
    r"updateSoundUnlockButton\(\);\s*"
    r"\};\s*"
    r"window\.speechSynthesis\.speak\(utterance\);\s*"
    r"\}",
    re.S,
)
html, count = warmup_re.subn(
    "if (!VOICE_WARMED) {\n"
    "      // v208.92: no silent TTS warmup; Samsung audio-route clicks are avoided.\n"
    "      VOICE_WARMED = true;\n"
    "      updateSoundUnlockButton();\n"
    "    }",
    html,
    count=1,
)
if count != 1:
    # Formatting-safe fallback: bound replacement by the warmup's unique statements.
    start = html.find('if (!VOICE_WARMED) {')
    synth = html.find("new SpeechSynthesisUtterance('\\u200b')", start if start >= 0 else 0)
    speak = html.find('window.speechSynthesis.speak(utterance);', synth if synth >= 0 else 0)
    if start < 0 or synth < start or speak < synth or synth - start > 500:
        raise SystemExit('v208.92 silent warmup anchor mismatch: ' + str(count))
    end = html.find('}', speak)
    if end < 0 or end - start > 1200:
        raise SystemExit('v208.92 silent warmup closing brace missing')
    replacement = (
        "if (!VOICE_WARMED) {\n"
        "      // v208.92: no silent TTS warmup; Samsung audio-route clicks are avoided.\n"
        "      VOICE_WARMED = true;\n"
        "      updateSoundUnlockButton();\n"
        "    }"
    )
    html = html[:start] + replacement + html[end + 1:]

# Extend native diagnostics while keeping the existing bridge contract.
status_old = '+ ":" + FAST_PEAK_GUARD + ":ready="'
status_new = '+ ":" + FAST_PEAK_GUARD + ":" + MUSIC55_NO_WARMUP + ":ready="'
if status_old not in java:
    raise SystemExit('v208.92 status anchor missing')
java = java.replace(status_old, status_new, 1)

for item in (
    MARKER,
    'private static final float MUSIC_DUCK_RATIO = 0.55f;',
    'MUSIC55_NO_WARMUP + ":ready="',
):
    if item not in java:
        raise SystemExit('v208.92 java requirement missing: ' + item)

if "new SpeechSynthesisUtterance('\\u200b')" in html:
    raise SystemExit('legacy zero-width TTS warmup survived')
if 'v208.92: no silent TTS warmup' not in html:
    raise SystemExit('v208.92 no-warmup marker missing')
if 'setStreamVolume(AudioManager.STREAM_MUSIC, 0,' in java:
    raise SystemExit('unsafe music mute exists')
if 'setStreamVolume(AudioManager.STREAM_MUSIC, maxMedia' in java:
    raise SystemExit('unsafe music max write exists')

java_path.write_text(java, encoding='utf-8')
html_path.write_text(html, encoding='utf-8')
print('ADMIN_MUSIC55_NO_WARMUP_V20892_OK')
