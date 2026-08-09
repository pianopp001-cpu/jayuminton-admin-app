#!/usr/bin/env python3
from pathlib import Path
import sys


path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

old = """function shouldCheckStatePush_(actionName) {
  return /(배정|이동|교환|종료|대기|코트)/.test(String(actionName || ''));
}"""
new = """function shouldCheckStatePush_(actionName) {
  // Every locked mutation is inspected. Notification emission still occurs
  // only when a member actually enters wait1 or a court. Filtering by the
  // Korean action label missed real wait-group operations whose labels did
  // not contain '대기/이동/배정'.
  return true;
}"""

if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("state transition predicate not found")

if "function shouldCheckStatePush_(actionName)" not in s or "return true;" not in s:
    raise SystemExit("unconditional state transition inspection missing")

path.write_text(s, encoding="utf-8")
print("Enabled wait1/court transition inspection for every locked mutation.")
