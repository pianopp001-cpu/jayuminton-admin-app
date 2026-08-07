from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
path = root / "bootstrap" / "v199-assets.zip.b64"
text = path.read_text(encoding="utf-8-sig")
clean = re.sub(r"[^A-Za-z0-9+/=]", "", text)
if not clean:
    raise SystemExit("v199 archive data is empty")
path.write_text(clean, encoding="ascii")
print(f"cleaned v199 archive data: {len(clean)} characters")
