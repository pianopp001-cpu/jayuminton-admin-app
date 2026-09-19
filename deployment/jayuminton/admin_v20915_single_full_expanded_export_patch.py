#!/usr/bin/env python3
"""Keep one fully-expanded report image and improve its raster quality."""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else
                 "app/src/main/java/com/jayuminton/admin/MainActivity.java")
text = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_SINGLE_FULL_EXPANDED_EXPORT_V20915"

if MARKER in text:
    print("ADMIN_V20915_ALREADY_OK")
    raise SystemExit(0)

for required in (
    "JAYUMINTON_BLUETOOTH_OPENING_CARROT_EXPORT_V20914",
    "jmReportSaveMarketplaceParts(jmReportBitmap, jmReportRequestedName);",
    "final long maxPixels = 12000000L;",
):
    if required not in text:
        raise SystemExit("v209.15 prerequisite missing: " + required)

# Keep a runtime marker so the packaged APK can be verified from classes.dex.
constant_anchor = '    private static final String BLUETOOTH_OPENING_CARROT_EXPORT = "JAYUMINTON_BLUETOOTH_OPENING_CARROT_EXPORT_V20914";\n'
constant_new = constant_anchor + '    private static final String SINGLE_FULL_EXPANDED_EXPORT = "' + MARKER + '";\n'
if text.count(constant_anchor) != 1:
    raise SystemExit("v209.15 runtime marker anchor mismatch")
text = text.replace(constant_anchor, constant_new, 1)

# User requirement: exactly one image, containing the complete expanded report.
+text = text.replace(
    "                jmReportSaveMarketplaceParts(jmReportBitmap, jmReportRequestedName);\n",
    "",
    1,
)
helper_start = text.find("    private void jmReportSaveMarketplaceParts(")
helper_end = text.find("    private void jmReportFinishCapture(boolean success) {", helper_start)
if helper_start < 0 or helper_end < 0:
    raise SystemExit("v209.15 split helper boundaries missing")
text = text[:helper_start] + text[helper_end:]

text = text.replace(
    'ok ? "전체 이미지와 당근용 분할 이미지 저장 완료" : "전체 이미지 저장 실패",',
    'ok ? "펼침 통계 전체 이미지 저장 완료" : "전체 이미지 저장 실패",',
    1,
)

# The old 12 MP ceiling silently shrank long reports before they even reached
# the marketplace uploader. 24 MP retains substantially more glyph detail while
# remaining bounded to avoid an unbounded bitmap allocation.
text = text.replace(
    "                    final long maxPixels = 12000000L;",
    "                    final long maxPixels = 24000000L; // " + MARKER,
    1,
)

# Bilinear filtering matters whenever the safety ceiling still requires a
# downscale. Drawing with a null Paint produced visibly broken/jagged Hangul.
if "import android.graphics.Paint;" not in text:
    text = text.replace("import android.graphics.Canvas;\n",
                        "import android.graphics.Canvas;\nimport android.graphics.Paint;\n", 1)
text = text.replace(
    "        out.drawBitmap(tile, src, dst, null);",
    "        Paint exportPaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);\n"
    "        out.drawBitmap(tile, src, dst, exportPaint);",
    1,
)

for forbidden in (
    "jmReportSaveMarketplaceParts(",
    '"_당근용_"',
    "maxPixels = 12000000L",
):
    if forbidden in text:
        raise SystemExit("v209.15 obsolete split/low-resolution behavior remains: " + forbidden)

for required in (
    MARKER,
    "maxPixels = 24000000L",
    "Paint.FILTER_BITMAP_FLAG",
    "펼침 통계 전체 이미지 저장 완료",
):
    if required not in text:
        raise SystemExit("v209.15 output missing: " + required)

java_path.write_text(text, encoding="utf-8")
print("ADMIN_V20915_SINGLE_FULL_EXPANDED_EXPORT_OK")
