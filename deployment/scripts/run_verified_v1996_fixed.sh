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
expected_sha256 = 'fa8c7154f81f933f60b793d4f9b7bd50fe688be2eab12121f8fe3b0960981877'
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

if 'rm -f "$SOURCE_B64"' not in src:
    raise SystemExit('resource cleanup patch missing')
if 'fa8c7154f81f933f60b793d4f9b7bd50fe688be2eab12121f8fe3b0960981877' not in src:
    raise SystemExit('pinned icon hash validation missing')
if "launcher icon dimensions changed unexpectedly" not in src:
    raise SystemExit('rectangular icon validation patch missing')

Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY

chmod +x "$FIXED"
echo 'Verified build wrapper: pinned 128x152 icon is base64-normalized, PNG CRC/SHA-256 validated, then the .b64 keeper is removed from the runner drawable tree.'
bash "$FIXED"
