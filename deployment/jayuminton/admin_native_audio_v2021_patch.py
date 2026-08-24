#!/usr/bin/env python3
"""Harden announcement ducking without muting or raising background music."""
from pathlib import Path

path = Path('app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')

old = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int duckedMusic = Math.max(0, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);
'''
new = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int levelSix = Math.max(1, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));
                // Announcement ducking is not music mute. Keep audible music at
                // level <= 6 and never raise a user's already quieter setting.
                int duckedMusic = originalMediaVolume > 0
                        ? Math.min(originalMediaVolume, levelSix)
                        : 0;
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);
'''
if text.count(old) != 1:
    raise SystemExit('native music duck anchor mismatch')
text = text.replace(old, new, 1)

required = [
    'MEDIA_DUCK_VOLUME_STEP = 6',
    'int levelSix = Math.max(1, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));',
    'Math.min(originalMediaVolume, levelSix)',
    'setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0)',
    'setStreamVolume(AudioManager.STREAM_MUSIC, originalMediaVolume, 0)',
]
for marker in required:
    if marker not in text:
        raise SystemExit('native audio contract missing: ' + marker)

path.write_text(text, encoding='utf-8')
print('NATIVE_AUDIO_V2021_OK music=audible<=6 voice=max restore=original')
