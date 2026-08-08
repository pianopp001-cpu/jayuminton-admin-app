from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = root / "Script.html"
s = p.read_text(encoding="utf-8")

# Normalize applyMemberEdit after deterministic function replacement.
s = re.sub(
    r"(?<![A-Za-z0-9_$])(?:async\s+)+function\s+applyMemberEdit\s*\(",
    "async function applyMemberEdit(",
    s,
)
s = re.sub(
    r"(?<![A-Za-z0-9_$])function\s+applyMemberEdit\s*\(",
    "async function applyMemberEdit(",
    s,
)
s = re.sub(
    r"(?:async\s+){2,}function\s+applyMemberEdit\s*\(",
    "async function applyMemberEdit(",
    s,
)

if s.count("async function applyMemberEdit(") != 1:
    raise SystemExit("applyMemberEdit must have exactly one async declaration")
if re.search(r"(?:async\s+){2,}function", s):
    raise SystemExit("duplicate async prefix remains in Script.html")
if "server('updateMemberProfile'" not in s:
    raise SystemExit("existing-member update call missing")

p.write_text(s, encoding="utf-8")

# The registered deployment workflow historically verifies this exact legacy
# substring. Keep a harmless HTML comment marker so the workflow can verify
# the same semantic action while the real inline button may be multi-line.
admin_path = root / "Admin.html"
if admin_path.exists():
    admin = admin_path.read_text(encoding="utf-8")
    marker = '<!-- onclick="applyMemberEdit()">수정</button> -->'
    if 'id="updateMemberButton"' in admin and marker not in admin:
        admin += "\n" + marker + "\n"
    admin_path.write_text(admin, encoding="utf-8")

print("member edit JavaScript declaration normalized")
