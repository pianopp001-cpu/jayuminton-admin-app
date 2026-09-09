#!/usr/bin/env python3
from pathlib import Path

p = Path('app/src/main/assets/admin/index.html')
s = p.read_text(encoding='utf-8')
# JAYUMINTON_GAME_REPORT_POLISH_V20899
p.write_text(s, encoding='utf-8')
