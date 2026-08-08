from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = root / "Script.html"
s = p.read_text(encoding="utf-8")

# Repeated patch runs used to leave the preceding `async` token behind because
# the function replacer starts at the word `function`. Collapse every such
# prefix to exactly one valid async function declaration.
s = re.sub(
    r"(?<![A-Za-z0-9_$])(?:async\s+)+function\s+applyMemberEdit\s*\(",
    "async function applyMemberEdit(",
    s,
)

# A plain declaration is also normalized to the intended async declaration.
s = re.sub(
    r"(?<![A-Za-z0-9_$])function\s+applyMemberEdit\s*\(",
    "async function applyMemberEdit(",
    s,
)

# The second substitution can see the `function` portion inside the line just
# produced above only if the negative lookbehind allows it; normalize once more
# defensively and reject any duplicate async prefix.
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
print("member edit JavaScript declaration normalized")
