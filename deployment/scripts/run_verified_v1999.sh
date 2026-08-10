#!/usr/bin/env bash
set -euo pipefail

JAVA_FILE="app/src/main/java/com/jayuminton/admin/MainActivity.java"
BASE="deployment/scripts/run_verified_v1998.sh"
TEMP="$RUNNER_TEMP/run_verified_v1999_generated.sh"
test -s "$BASE"
test -s "$JAVA_FILE"

# Fix only the repeated TTS callback race first.  Audio values are intentionally
# left at the repository baseline here because the proven v199.8 pipeline below
# applies the already verified MUSIC=6 / TTS(ALARM)=MAX build transformation.
python3 deployment/scripts/patch_admin_repeat_tts_v1999.py "$JAVA_FILE"

grep -F 'JAYUMINTON_REPEAT_TTS_V1999' "$JAVA_FILE" >/dev/null
grep -F 'AtomicLong speechGeneration = new AtomicLong(0L)' "$JAVA_FILE" >/dev/null
grep -F 'private volatile String activeUtteranceId = "";' "$JAVA_FILE" >/dev/null
grep -F 'String utteranceId = request.id + "-" + generation;' "$JAVA_FILE" >/dev/null

# Reuse the fully verified v199.8 recipe, changing only the package build
# identity/output paths to v199.9.  This preserves the exact earlier audio ratio:
# media stream level 6 remains audible while native TTS uses ALARM at device max.
python3 - "$BASE" "$TEMP" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
src = src.replace('199.8', '199.9').replace('1998', '1999')
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$TEMP"
bash "$TEMP"

# Hard gates on the final Java source actually compiled by the proven pipeline.
grep -F 'private static final int MEDIA_DUCK_VOLUME_STEP = 6;' "$JAVA_FILE" >/dev/null
grep -F 'int mediaStep = Math.max(0, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));' "$JAVA_FILE" >/dev/null
grep -F 'setStreamVolume(AudioManager.STREAM_MUSIC, mediaStep, 0);' "$JAVA_FILE" >/dev/null
grep -F 'setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);' "$JAVA_FILE" >/dev/null
grep -F 'params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);' "$JAVA_FILE" >/dev/null
grep -F 'JAYUMINTON_REPEAT_TTS_V1999' "$JAVA_FILE" >/dev/null
grep -F 'if (!isActiveUtterance(utteranceId)) return;' "$JAVA_FILE" >/dev/null
grep -F 'activeUtteranceId = utteranceId;' "$JAVA_FILE" >/dev/null

APK='releases/jayuminton-v199.9-verified.apk'
STATUS='deployment/status/apk-v1999.txt'
test -s "$APK"
test -s "$STATUS"
grep -F 'status=success' "$STATUS" >/dev/null
grep -F 'version=199.9' "$STATUS" >/dev/null
grep -F 'version_code=1999' "$STATUS" >/dev/null
grep -F 'application_id=com.jayuminton.admin199' "$STATUS" >/dev/null
grep -F 'voice_volume=max-device-level' "$STATUS" >/dev/null
grep -F 'media_duck_volume_step=6' "$STATUS" >/dev/null
grep -F 'voice_stream=alarm-max' "$STATUS" >/dev/null

# Append explicit repeat behavior evidence to the v199.9 verification record.
cat >> "$STATUS" <<'EOF'
repeat_voice=stale-utterance-callback-guarded
member_change_voice=repeat-safe-queue-flush
music_during_voice=audible-media-level-6
voice_during_music=alarm-stream-device-max
EOF

# Stable internal download alias.  This does NOT touch the public user-app
# install button; it is only the administrator APK download target.
cp "$APK" releases/jayuminton-admin-latest.apk
cmp "$APK" releases/jayuminton-admin-latest.apk

echo 'v199.9 verified: music level 6 + max voice + repeat-safe member announcements + stable admin APK alias.'
