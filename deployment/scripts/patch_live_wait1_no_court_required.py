#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
path = root / "Code.js"
s = path.read_text(encoding="utf-8")
marker = "JAYUMINTON_WAIT1_NO_COURT_REQUIRED_V1"

if marker not in s:
    old = """  const expectedCourtNo = Number(body.expectedCourtNo);
  if ([1, 2, 3, 4].indexOf(expectedCourtNo) === -1 ||
      members.length < 1 || members.length > 4) {
    throw new Error('Wait-1 notification requires one expected court and one to four members.');
  }
  return {
    type: type,
    assignmentId: assignmentId,
    courtNo: 0,
    expectedCourtNo: expectedCourtNo,
    members: members
  };"""
    new = """  /* JAYUMINTON_WAIT1_NO_COURT_REQUIRED_V1
   * Entering wait group 1 means prepare now; it does not yet have a court.
   * The main assignment app deliberately sends an empty expectedCourtNo.
   */
  const expectedCourtNo = Number(body.expectedCourtNo) || 0;
  if (members.length < 1 || members.length > 4) {
    throw new Error('Wait-1 notification requires one to four members.');
  }
  return {
    type: type,
    assignmentId: assignmentId,
    courtNo: 0,
    expectedCourtNo: expectedCourtNo,
    members: members
  };"""
    if s.count(old) != 1:
        raise SystemExit("wait1 strict court validation block not found once")
    s = s.replace(old, new, 1)

for required in (marker, "const expectedCourtNo = Number(body.expectedCourtNo) || 0", "Wait-1 notification requires one to four members"):
    if required not in s:
        raise SystemExit("missing wait1 validation marker: " + required)

path.write_text(s, encoding="utf-8")
print("Allowed wait1-ready push without a court number.")
