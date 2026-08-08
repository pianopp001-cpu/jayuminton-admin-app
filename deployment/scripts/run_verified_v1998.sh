#!/usr/bin/env bash
set -euo pipefail

BASE="deployment/scripts/run_verified_v1997.sh"
TEMP="$RUNNER_TEMP/run_verified_v1998_generated.sh"
test -s "$BASE"

python3 - "$BASE" "$TEMP" <<'PY'
from pathlib import Path
import re
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')

src = src.replace('199.7', '199.8').replace('1997', '1998')

# TTS uses STREAM_ALARM. Keep music at level 6, but force the announcement
# stream to the device maximum. Match the source defensively across whitespace.
pattern = re.compile(
    r'int maxAlarm\s*=\s*audioManager\.getStreamMaxVolume\(AudioManager\.STREAM_ALARM\);\s*'
    r'int voiceStep\s*=\s*Math\.max\(1,\s*Math\.min\(VOICE_VOLUME_STEP,\s*maxAlarm\)\);\s*'
    r'audioManager\.setStreamVolume\(AudioManager\.STREAM_ALARM,\s*voiceStep,\s*0\);'
)
src, n = pattern.subn(
    'int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);\n'
    '                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0);',
    src,
    count=1,
)
if n != 1:
    raise SystemExit('alarm-volume patch target count=' + str(n))

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

    // Keep the original dog/racket artwork, remove the tall title/outer area,
    // and make the dog fill the actual square launcher tile.
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
p = Path(sys.argv[1])
data = p.read_bytes()
if data[:8] != b'\x89PNG\r\n\x1a\n': raise SystemExit('cropped launcher is not PNG')
w, h = struct.unpack('>II', data[16:24])
if (w, h) != (128, 128): raise SystemExit(f'cropped launcher must be 128x128, got {w}x{h}')
print('Cropped launcher dimensions verified: 128x128')
PYICONCHECK

rm -f "$SOURCE_B64"'''
src = src.replace(anchor, icon_transform, 1)

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
