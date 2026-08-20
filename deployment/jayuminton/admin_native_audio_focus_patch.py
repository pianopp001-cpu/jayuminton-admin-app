#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
if 'import android.media.AudioAttributes;' not in s:
    s=s.replace('import android.media.AudioManager;','import android.media.AudioManager;\nimport android.media.AudioAttributes;\nimport android.media.AudioFocusRequest;',1)
if 'private AudioFocusRequest voiceFocusRequest;' not in s:
    s=s.replace('private AudioManager audioManager;','private AudioManager audioManager;\n    private AudioFocusRequest voiceFocusRequest;',1)
old='''            try {\n                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);'''
new='''            try {\n                try {\n                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {\n                        AudioAttributes attrs = new AudioAttributes.Builder()\n                                .setUsage(AudioAttributes.USAGE_ALARM)\n                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)\n                                .build();\n                        voiceFocusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE)\n                                .setAudioAttributes(attrs)\n                                .setAcceptsDelayedFocusGain(false)\n                                .setWillPauseWhenDucked(true)\n                                .build();\n                        audioManager.requestAudioFocus(voiceFocusRequest);\n                    } else {\n                        audioManager.requestAudioFocus(null, AudioManager.STREAM_ALARM, AudioManager.AUDIOFOCUS_GAIN_TRANSIENT);\n                    }\n                } catch (Exception ignored) {}\n                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);'''
if old in s:
    s=s.replace(old,new,1)
elif 'AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE' not in s:
    raise SystemExit('beginStrongDucking anchor missing')
restore='''            } catch (SecurityException ignored) {\n            }\n            ducking = false;'''
restore_new='''            } catch (SecurityException ignored) {\n            }\n            try {\n                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && voiceFocusRequest != null) {\n                    audioManager.abandonAudioFocusRequest(voiceFocusRequest);\n                    voiceFocusRequest = null;\n                } else {\n                    audioManager.abandonAudioFocus(null);\n                }\n            } catch (Exception ignored) {}\n            ducking = false;'''
if restore in s:
    s=s.replace(restore,restore_new,1)
elif 'abandonAudioFocusRequest' not in s:
    raise SystemExit('restoreAudio anchor missing')
for req in ['AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE','USAGE_ALARM','CONTENT_TYPE_SPEECH','abandonAudioFocusRequest','MEDIA_DUCK_VOLUME_STEP = 6']:
    if req not in s: raise SystemExit('missing '+req)
p.write_text(s,encoding='utf-8')
print('ADMIN_NATIVE_AUDIO_FOCUS_PATCH_OK')
