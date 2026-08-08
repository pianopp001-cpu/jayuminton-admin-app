#!/usr/bin/env bash
set -euo pipefail

SOURCE="deployment/scripts/build_verified_v1996.sh"
FIXED="$RUNNER_TEMP/build_verified_v1996_fixed.sh"
test -s "$SOURCE"

python3 - "$SOURCE" "$FIXED" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1]).read_text(encoding='utf-8')

decode_needle = 'base64 --decode "$SOURCE_B64" > "$TARGET_ICON"\n'
decode_replacement = r'''python3 - "$SOURCE_B64" "$TARGET_ICON" <<'PYICON'
import base64
import hashlib
import re
import struct
import sys
import zlib
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
raw = source.read_text(encoding='utf-8').strip()
if raw.startswith('data:') and ',' in raw:
    raw = raw.split(',', 1)[1]

compact = re.sub(r'\s+', '', raw)
alphabet = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
invalid_count = sum(1 for ch in compact if ch not in alphabet)
cleaned = ''.join(ch for ch in compact if ch in alphabet)
core = cleaned.rstrip('=')
core += '=' * ((4 - len(core) % 4) % 4)

try:
    png = base64.b64decode(core, validate=True)
except Exception as exc:
    raise SystemExit(f'Pinned launcher base64 cannot be decoded safely: {exc}')

signature = b'\x89PNG\r\n\x1a\n'
if not png.startswith(signature):
    raise SystemExit('Decoded launcher icon does not have a PNG signature')

pos = len(signature)
width = height = None
saw_iend = False
chunk_count = 0
while pos < len(png):
    if pos + 12 > len(png):
        raise SystemExit('Decoded launcher PNG is truncated before a complete chunk')
    length = struct.unpack('>I', png[pos:pos + 4])[0]
    chunk_type = png[pos + 4:pos + 8]
    data_start = pos + 8
    data_end = data_start + length
    crc_end = data_end + 4
    if crc_end > len(png):
        raise SystemExit('Decoded launcher PNG has a truncated chunk')
    chunk_data = png[data_start:data_end]
    expected_crc = struct.unpack('>I', png[data_end:crc_end])[0]
    actual_crc = zlib.crc32(chunk_type)
    actual_crc = zlib.crc32(chunk_data, actual_crc) & 0xffffffff
    if actual_crc != expected_crc:
        label = chunk_type.decode('latin1', errors='replace')
        raise SystemExit(f'Decoded launcher PNG CRC mismatch in {label}')
    chunk_count += 1
    if chunk_type == b'IHDR':
        if length != 13:
            raise SystemExit('Decoded launcher PNG has an invalid IHDR')
        width, height = struct.unpack('>II', chunk_data[:8])
    if chunk_type == b'IEND':
        if length != 0:
            raise SystemExit('Decoded launcher PNG has an invalid IEND')
        saw_iend = True
        pos = crc_end
        break
    pos = crc_end

if not saw_iend or pos != len(png):
    raise SystemExit('Decoded launcher PNG is incomplete or has trailing data')
if (width, height) != (128, 152):
    raise SystemExit(f'Decoded launcher PNG dimensions are invalid: {width}x{height}')
sha256 = hashlib.sha256(png).hexdigest()
expected_sha256 = 'a64eaa06107cd20478fe49ab7c10b5b2afd2347533b95c383a439f8705d4a58e'
if sha256 != expected_sha256:
    raise SystemExit(f'Decoded launcher PNG SHA-256 mismatch: {sha256}')

target.write_bytes(png)
print(
    f'Pinned launcher base64 validated: {width}x{height}, '
    f'{len(png)} bytes, sha256={sha256}, {chunk_count} chunks, ignored_non_base64={invalid_count}'
)
PYICON
'''
if decode_needle not in src:
    raise SystemExit('base64 decode insertion point missing')
src = src.replace(decode_needle, decode_replacement, 1)

file_needle = "file \"$TARGET_ICON\" | grep -F 'PNG image data' >/dev/null\n"
file_replacement = (
    file_needle
    + "# Do not let Android treat the base64 keeper as a drawable resource.\n"
    + "rm -f \"$SOURCE_B64\"\n"
)
if file_needle not in src:
    raise SystemExit('icon validation insertion point missing')
src = src.replace(file_needle, file_replacement, 1)

square_needle = "if w != h or w < 128:\n    raise SystemExit(f'launcher icon must be square and >=128px, got {w}x{h}')\n"
square_replacement = "if (w, h) != (128, 152):\n    raise SystemExit(f'launcher icon dimensions changed unexpectedly: {w}x{h}')\n"
if square_needle not in src:
    raise SystemExit('legacy square icon validation block missing')
src = src.replace(square_needle, square_replacement, 1)

packaged_icon_needle = 'unzip -p "$APK" res/drawable/icon.png > "$RUNNER_TEMP/final-icon.png"\n'
packaged_icon_replacement = r'''ICON_PATH="$(sed -n "s/^application-icon-160:'\([^']*\)'.*/\1/p" "$RUNNER_TEMP/badging.txt" | head -1)"
if [ -z "$ICON_PATH" ]; then
  ICON_PATH="$(sed -n "s/^application:.* icon='\([^']*\)'.*/\1/p" "$RUNNER_TEMP/badging.txt" | head -1)"
fi
test -n "$ICON_PATH"
echo "Packaged launcher icon path: $ICON_PATH"
unzip -p "$APK" "$ICON_PATH" > "$RUNNER_TEMP/final-icon.png"
'''
if packaged_icon_needle not in src:
    raise SystemExit('legacy packaged icon extraction line missing')
src = src.replace(packaged_icon_needle, packaged_icon_replacement, 1)

signer_needle = '''SIGNER_SHA="$(awk -F': ' '/Signer #1 certificate SHA-256 digest:/ {gsub(":", "", $2); print toupper($2); exit}' "$RUNNER_TEMP/apksigner.txt")"\n'''
signer_replacement = r'''SIGNER_SHA="$(sed -n -E 's/^.*certificate SHA-256 digest: ([0-9A-Fa-f:]+).*$/\1/p' "$RUNNER_TEMP/apksigner.txt" | head -1 | tr -d ':' | tr '[:lower:]' '[:upper:]')"
'''
if signer_needle not in src:
    raise SystemExit('legacy apksigner digest parser missing')
src = src.replace(signer_needle, signer_replacement, 1)

if 'rm -f "$SOURCE_B64"' not in src:
    raise SystemExit('resource cleanup patch missing')
if 'a64eaa06107cd20478fe49ab7c10b5b2afd2347533b95c383a439f8705d4a58e' not in src:
    raise SystemExit('pinned icon hash validation missing')
if "launcher icon dimensions changed unexpectedly" not in src:
    raise SystemExit('rectangular icon validation patch missing')
if 'Packaged launcher icon path:' not in src:
    raise SystemExit('dynamic packaged icon verification patch missing')
if "certificate SHA-256 digest: ([0-9A-Fa-f:]+)" not in src:
    raise SystemExit('current apksigner digest parser patch missing')

Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY

chmod +x "$FIXED"
echo 'Verified build wrapper: icon source/package pixels and current apksigner certificate digest are verified.'
bash "$FIXED"
