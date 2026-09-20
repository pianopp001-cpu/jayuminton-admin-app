#!/usr/bin/env python3
"""Remove blank green capture tiles and restore readable two-column export."""

from pathlib import Path
import re
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923"

if MARKER in html and MARKER in java:
    print("ADMIN_V20923_REPORT_NO_GREEN_TILE_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_MARKETPLACE_READABLE_FULL_REPORT_V20922",
    "jm-marketplace-onepage-v20918",
    "w=Math.max(2400",
):
    if token not in html:
        raise SystemExit("v209.23 HTML prerequisite missing: " + token)
for token in (
    "JAYUMINTON_HIGH_RES_SINGLE_REPORT_V20920",
    "private void jmReportCaptureTile(final int targetLeft, final int targetTop)",
    "android.view.PixelCopy.request",
):
    if token not in java:
        raise SystemExit("v209.23 Java prerequisite missing: " + token)

style = r'''
<style id="jmNoGreenTileReadableReportV20923">
/* JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923
   Two columns preserve legible glyph size after marketplace resizing. */
#jmNativeReportExportV20905,
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918{
  width:1600px!important;
  min-width:1600px!important;
  max-width:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:16px!important;
  padding:0 16px 16px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row{
  padding:18px 20px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-name{
  font-size:28px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-games{
  font-size:27px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time{
  font-size:23px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-title{
  font-size:20px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list,
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list .j95-chip{
  font-size:20px!important;
}
</style>
'''
if "</head>" not in html:
    raise SystemExit("v209.23 head close missing")
html = html.replace("</head>", style + "\n</head>", 1)
html = html.replace(
    "w=Math.max(2400,Math.ceil(rect.width||p.offsetWidth||941))",
    "w=Math.max(1600,Math.ceil(rect.width||p.offsetWidth||941))",
    1,
)

capture_method = r'''    // JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923
    private void jmReportCaptureTile(final int targetLeft, final int targetTop) {
        if (!jmReportCaptureRunning || webView == null) return;
        final int maxScrollX = Math.max(0, jmReportSourceWidth - jmReportViewportWidth);
        final int maxScrollY = Math.max(0, jmReportSourceHeight - jmReportViewportHeight);
        final int actualScrollLeft = Math.min(Math.max(0, targetLeft), maxScrollX);
        final int actualScrollTop = Math.min(Math.max(0, targetTop), maxScrollY);
        webView.scrollTo(actualScrollLeft, actualScrollTop);
        webView.postOnAnimation(() -> webView.postOnAnimation(() -> webView.postDelayed(() -> {
            if (!jmReportCaptureRunning || webView == null) return;
            int width = Math.min(jmReportViewportWidth, webView.getWidth());
            int height = Math.min(jmReportViewportHeight, webView.getHeight());
            if (width <= 0 || height <= 0) {
                jmReportFinishCapture(false);
                return;
            }
            Bitmap tile = null;
            try {
                tile = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
                Canvas canvas = new Canvas(tile);
                canvas.drawColor(Color.WHITE);
                webView.draw(canvas);
                if (!jmReportTileHasContent(tile)) {
                    tile.recycle();
                    jmReportFinishCapture(false);
                    return;
                }
                jmReportDrawTile(tile, targetLeft, targetTop,
                        actualScrollLeft, actualScrollTop);
            } catch (Throwable error) {
                if (tile != null && !tile.isRecycled()) tile.recycle();
                jmReportFinishCapture(false);
            }
        }, 220L)));
    }

'''
pat = re.compile(
    r"    private void jmReportCaptureTile\(final int targetLeft, final int targetTop\) \{.*?\n    private void jmReportStartCapture\(",
    re.S,
)
m = pat.search(java)
if not m:
    raise SystemExit("v209.23 capture method boundaries missing")
java = java[:m.start()] + capture_method + "    private void jmReportStartCapture(" + java[m.end():]

for token in (
    MARKER,
    "w=Math.max(1600",
    "grid-template-columns:repeat(2,minmax(0,1fr))",
    "canvas.drawColor(Color.WHITE)",
    "webView.draw(canvas)",
    "220L",
):
    if token not in html + java:
        raise SystemExit("v209.23 output missing: " + token)

active = re.search(
    r"// JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923.*?private void jmReportStartCapture\(",
    java,
    re.S,
)
if not active or "PixelCopy.request" in active.group(0) or "Color.rgb(216, 247, 232)" in active.group(0):
    raise SystemExit("v209.23 unsafe capture path remains active")

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20923_REPORT_NO_GREEN_TILE_READABLE_OK")
