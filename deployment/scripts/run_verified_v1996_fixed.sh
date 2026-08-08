#!/usr/bin/env bash
set -euo pipefail

SOURCE="deployment/scripts/build_verified_v1996.sh"
FIXED="$RUNNER_TEMP/build_verified_v1996_fixed.sh"
test -s "$SOURCE"

python3 - "$SOURCE" "$FIXED" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
needle = "file \"$TARGET_ICON\" | grep -F 'PNG image data' >/dev/null\n"
replacement = needle + "# Do not let Android treat the base64 keeper as a drawable resource.\nrm -f \"$SOURCE_B64\"\n"
if needle not in src:
    raise SystemExit('icon validation insertion point missing')
fixed = src.replace(needle, replacement, 1)
if 'rm -f "$SOURCE_B64"' not in fixed:
    raise SystemExit('resource cleanup patch missing')
Path(sys.argv[2]).write_text(fixed, encoding='utf-8')
PY

chmod +x "$FIXED"
echo 'Verified build wrapper: invalid .b64 drawable is removed only in the runner checkout.'
bash "$FIXED"
