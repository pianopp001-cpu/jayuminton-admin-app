#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
marker='JAYUMINTON_MEMBER_STALE_WAIT_ID_V1'
if marker in s:
    print('already patched')
    raise SystemExit(0)
needle="""              const member =\n                memberById(id);\n\n              if (!IS_ADMIN) {\n                if (isSelfMember(member)) {"""
replacement="""              const member =\n                memberById(id);\n\n              /* JAYUMINTON_MEMBER_STALE_WAIT_ID_V1: stale wait ids must not abort the whole member render. */\n              if (!member) {\n                return memberWaitEmptySlotCard(groupIndex, slotIndex);\n              }\n\n              if (!IS_ADMIN) {\n                if (isSelfMember(member)) {"""
if needle not in s:
    raise SystemExit('stale wait member render anchor missing')
s=s.replace(needle,replacement,1)
p.write_text(s,encoding='utf-8')
print('MEMBER_STALE_WAIT_ID_V1_OK')
