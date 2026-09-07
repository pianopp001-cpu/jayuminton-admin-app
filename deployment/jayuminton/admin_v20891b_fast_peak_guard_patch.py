#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_FAST_PEAK_GUARD_V20891B'

if MARKER in text:
    print('ADMIN_FAST_PEAK_GUARD_V20891B_ALREADY_OK')
    raise SystemExit(0)

required = [
    'JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891',
    'VOICE_TARGET_RMS_DBFS = -13.0',
    'VOICE_PEAK_CEILING_DBFS = -2.0',
    'VOICE_COMP_RATIO = 3.0',
    'normalizeAndLimitVoiceWav(File file)',
]
for item in required:
    if item not in text:
        raise SystemExit('v208.91b prerequisite missing: ' + item)

text = text.replace(
    '    private static final String ENERGY_NORMALIZE_LIMITER = "JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891";\n',
    '    private static final String ENERGY_NORMALIZE_LIMITER = "JAYUMINTON_ENERGY_NORMALIZE_LIMITER_V20891";\n'
    '    private static final String FAST_PEAK_GUARD = "JAYUMINTON_FAST_PEAK_GUARD_V20891B";\n',
    1,
)

old = '''                double gain = 1.0;\n                if (env > threshold && env > 1.0e-9) {\n                    // output/input ratio in the log domain, equivalent to a 3:1\n                    // compressor above the threshold.\n                    gain = Math.pow(env / threshold, (1.0 / VOICE_COMP_RATIO) - 1.0);\n                }\n                double y = x * gain;'''
new = '''                double gain = 1.0;\n                if (env > threshold && env > 1.0e-9) {\n                    // Smooth envelope compressor for ordinary speech energy.\n                    gain = Math.pow(env / threshold, (1.0 / VOICE_COMP_RATIO) - 1.0);\n                }\n                if (ax > threshold && ax > 1.0e-9) {\n                    // Fast peak guard: one-sample/very short transients can outrun a\n                    // 4 ms envelope. Catch them immediately so they cannot dictate\n                    // the makeup gain for the entire utterance. This lowers crest\n                    // factor while preserving the slower envelope on normal speech.\n                    double instantGain = Math.pow(\n                            ax / threshold, (1.0 / VOICE_COMP_RATIO) - 1.0);\n                    gain = Math.min(gain, instantGain);\n                }\n                double y = x * gain;'''
if text.count(old) != 1:
    raise SystemExit('v208.91b compressor anchor mismatch: ' + str(text.count(old)))
text = text.replace(old, new, 1)

old_status = '+ ":" + ENERGY_NORMALIZE_LIMITER + ":ready="'
new_status = '+ ":" + ENERGY_NORMALIZE_LIMITER + ":" + FAST_PEAK_GUARD + ":ready="'
if old_status not in text:
    raise SystemExit('v208.91b status anchor missing')
text = text.replace(old_status, new_status, 1)

for item in (
    MARKER,
    'double instantGain = Math.pow(',
    'gain = Math.min(gain, instantGain);',
    'FAST_PEAK_GUARD + ":ready="',
):
    if item not in text:
        raise SystemExit('v208.91b requirement missing: ' + item)

path.write_text(text, encoding='utf-8')
print('ADMIN_FAST_PEAK_GUARD_V20891B_OK')
