#!/usr/bin/env bash
set -euo pipefail

BASE="deployment/scripts/run_verified_v1997.sh"
TEMP="$RUNNER_TEMP/run_verified_v1998_generated.sh"
test -s "$BASE"

python3 - "$BASE" "$TEMP" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')

# Keep the proven v199.7 pipeline and only alter its temporary build recipe.
src = src.replace('199.7', '199.8').replace('1997', '1998')

# The v199.7 recipe patches MainActivity during the build. Add the voice-volume
# change inside that same Java-patching Python block: MUSIC=6, TTS/ALARM=MAX.
needle = """text = text.replace(old, new, 1)
java_path.write_text(text, encoding='utf-8')"""
if needle not in src:
    raise SystemExit('Java patch insertion point missing')
injected = """text = text.replace(old, new, 1)

alarm_old = '''                int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);
                int voiceStep = Math.max(1, Math.min(VOICE_VOLUME_STEP, maxAlarm));
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, voiceStep, 0);'''
alarm_new = '''                int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);'''
if alarm_old not in text:
    raise SystemExit('MainActivity alarm-volume block missing')
text = text.replace(alarm_old, alarm_new, 1)
text = text.replace('    private static final int VOICE_VOLUME_STEP = 6;\\n', '')

java_path.write_text(text, encoding='utf-8')"""
src = src.replace(needle, injected, 1)

# Update hard checks to prove the final Java source uses max alarm volume.
src = src.replace(
    "grep -F 'private static final int VOICE_VOLUME_STEP = 6;' \"$JAVA_FILE\" >/dev/null\n",
    "",
)
src = src.replace(
    "grep -F 'setStreamVolume(AudioManager.STREAM_ALARM, voiceStep, 0);' \"$JAVA_FILE\" >/dev/null",
    "grep -F 'setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);' \"$JAVA_FILE\" >/dev/null",
)
src = src.replace('voice_volume_step=6', 'voice_volume=max-device-level')
src = src.replace(
    '# Music remains audible at level 6 while TTS/ALARM is also explicitly level 6.',
    '# Music remains audible at level 6 while TTS/ALARM is forced to the device maximum.',
)

# Convert the original 128x152 artwork to a real square icon. Keep the dog and
# racket, remove the tall title/outer area, and scale the dog crop to the tile.
anchor = '''PYICON
rm -f "$SOURCE_B64"'''
if anchor not in src:
    raise SystemExit('icon transform anchor not found')
icon_transform = r'''PYICON

cat > "$RUNNER_TEMP/CropDogIcon.java" <<'JAVAICON'
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;

public final class CropDogIcon {
  public static void main(String[] args) throws Exception {
    File file = new File(args[0]);
    BufferedImage source = ImageIO.read(file);
    if (source == null) throw new RuntimeException("launcher PNG decode failed");
    if (source.getWidth() != 128 || source.getHeight() != 152)
      throw new RuntimeException("unexpected source launcher size");

    BufferedImage crop = source.getSubimage(16, 56, 96, 96);
    BufferedImage square = new BufferedImage(128, 128, BufferedImage.TYPE_INT_ARGB);
    Graphics2D g = square.createGraphics();
    g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
    g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
    g.drawImage(crop, 0, 0, 128, 128, null);
    g.dispose();
    if (!ImageIO.write(square, "png", file)) throw new RuntimeException("launcher PNG write failed");
    System.out.println("Full-tile dog launcher generated: 128x128");
  }
}
JAVAICON
javac "$RUNNER_TEMP/CropDogIcon.java"
java -cp "$RUNNER_TEMP" CropDogIcon "$TARGET_ICON"

python3 - "$TARGET_ICON" <<'PYICONCHECK'
from pathlib import Path
import struct, sys
data = Path(sys.argv[1]).read_bytes()
if data[:8] != b'\x89PNG\r\n\x1a\n': raise SystemExit('cropped launcher is not PNG')
w, h = struct.unpack('>II', data[16:24])
if (w, h) != (128, 128): raise SystemExit(f'cropped launcher must be 128x128, got {w}x{h}')
print('Cropped launcher dimensions verified: 128x128')
PYICONCHECK

rm -f "$SOURCE_B64"'''
src = src.replace(anchor, icon_transform, 1)

# Record exactly what was verified in the final APK.
src = src.replace(
    'media_duck_volume_step=6\nmedia_restore=original-value',
    'media_duck_volume_step=6\nvoice_stream=alarm-max\nmedia_restore=original-value',
)
src = src.replace(
    'launcher_label=자유민턴 관리자\nlauncher_icon_sha256=',
    'launcher_label=자유민턴 관리자\nlauncher_icon_layout=dog-full-square-128x128\nlauncher_icon_sha256=',
)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY

chmod +x "$TEMP"
bash "$TEMP"
