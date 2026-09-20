#!/usr/bin/env python3
"""Export one readable, fully-expanded statistics image at a wide native resolution."""

from pathlib import Path
import re
import sys


html_path = Path(sys.argv[1] if len(sys.argv) > 1 else
                 "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else
                 "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_HIGH_RES_SINGLE_REPORT_V20920"

if MARKER in html and MARKER in java:
    print("ADMIN_V20920_HIGH_RES_SINGLE_REPORT_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_SINGLE_REPORT_READABLE_REFLOW_V20918",
    "jm-marketplace-onepage-v20918",
    "window.NativeReportCapture.saveFullReportPng",
):
    if token not in html:
        raise SystemExit("v209.20 HTML prerequisite missing: " + token)

for token in (
    "JAYUMINTON_REPORT_PIXELCOPY_CAPTURE_V20906",
    "JAYUMINTON_SINGLE_FULL_EXPANDED_EXPORT_V20915",
    "private void jmReportDrawTile(",
    "private void jmReportCaptureTile(",
    "maxPixels = 24000000L",
):
    if token not in java:
        raise SystemExit("v209.20 Java prerequisite missing: " + token)

# The old exporter could only capture the visible WebView width. Increasing the
# report width therefore stretched a screen-sized tile and blurred every glyph.
# Capture both axes so a 1600 px report is assembled from native-resolution
# viewport tiles without interpolation.
field_anchor = "    private int jmReportViewportHeight;\n"
if java.count(field_anchor) != 1:
    raise SystemExit("v209.20 viewport field anchor mismatch")
java = java.replace(
    field_anchor,
    "    private int jmReportViewportWidth;\n" + field_anchor,
    1,
)

draw_method = r'''    // JAYUMINTON_HIGH_RES_SINGLE_REPORT_V20920
    private void jmReportDrawTile(Bitmap tile, int targetLeft, int targetTop,
                                  int actualScrollLeft, int actualScrollTop) {
        if (tile == null || jmReportBitmap == null) {
            jmReportFinishCapture(false);
            return;
        }
        int sourceOffsetX = Math.max(0, targetLeft - actualScrollLeft);
        int sourceOffsetY = Math.max(0, targetTop - actualScrollTop);
        if (sourceOffsetX >= tile.getWidth() || sourceOffsetY >= tile.getHeight()) {
            tile.recycle();
            jmReportFinishCapture(false);
            return;
        }
        int copyWidth = Math.min(jmReportSourceWidth - targetLeft,
                tile.getWidth() - sourceOffsetX);
        int copyHeight = Math.min(jmReportSourceHeight - targetTop,
                tile.getHeight() - sourceOffsetY);
        if (copyWidth <= 0 || copyHeight <= 0) {
            tile.recycle();
            jmReportFinishCapture(false);
            return;
        }

        Canvas out = new Canvas(jmReportBitmap);
        Rect src = new Rect(sourceOffsetX, sourceOffsetY,
                sourceOffsetX + copyWidth, sourceOffsetY + copyHeight);
        int dstLeft = Math.max(0, Math.round(targetLeft * jmReportOutputScale));
        int dstTop = Math.max(0, Math.round(targetTop * jmReportOutputScale));
        int dstRight = Math.min(jmReportOutputWidth,
                Math.max(dstLeft + 1, Math.round((targetLeft + copyWidth) * jmReportOutputScale)));
        int dstBottom = Math.min(jmReportOutputHeight,
                Math.max(dstTop + 1, Math.round((targetTop + copyHeight) * jmReportOutputScale)));
        Rect dst = new Rect(dstLeft, dstTop, dstRight, dstBottom);
        Paint exportPaint = new Paint(Paint.ANTI_ALIAS_FLAG
                | Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);
        out.drawBitmap(tile, src, dst, exportPaint);
        tile.recycle();

        int nextLeft = targetLeft + copyWidth;
        if (nextLeft < jmReportSourceWidth) {
            jmReportCaptureTile(nextLeft, targetTop);
            return;
        }
        int nextTop = targetTop + copyHeight;
        if (nextTop >= jmReportSourceHeight) jmReportFinishCapture(true);
        else jmReportCaptureTile(0, nextTop);
    }

'''

draw_pattern = re.compile(
    r"    private void jmReportDrawTile\(.*?\n    private void jmReportCaptureTile\(",
    re.S,
)
draw_match = draw_pattern.search(java)
if not draw_match:
    raise SystemExit("v209.20 draw method boundaries missing")
java = java[:draw_match.start()] + draw_method + "    private void jmReportCaptureTile(" + java[draw_match.end():]

capture_method = r'''    private void jmReportCaptureTile(final int targetLeft, final int targetTop) {
        if (!jmReportCaptureRunning || webView == null) return;
        final int maxScrollX = Math.max(0, jmReportSourceWidth - jmReportViewportWidth);
        final int maxScrollY = Math.max(0, jmReportSourceHeight - jmReportViewportHeight);
        final int actualScrollLeft = Math.min(Math.max(0, targetLeft), maxScrollX);
        final int actualScrollTop = Math.min(Math.max(0, targetTop), maxScrollY);
        webView.scrollTo(actualScrollLeft, actualScrollTop);
        webView.postOnAnimation(() -> webView.postOnAnimation(() -> webView.postDelayed(() -> {
            if (!jmReportCaptureRunning || webView == null) return;
            final int[] loc = new int[2];
            webView.getLocationInWindow(loc);
            int width = Math.min(jmReportViewportWidth, webView.getWidth());
            int height = Math.min(jmReportViewportHeight, webView.getHeight());
            if (width <= 0 || height <= 0) {
                jmReportFinishCapture(false);
                return;
            }
            final Bitmap tile;
            try {
                tile = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            } catch (Throwable error) {
                jmReportFinishCapture(false);
                return;
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Rect windowRect = new Rect(loc[0], loc[1], loc[0] + width, loc[1] + height);
                try {
                    android.view.PixelCopy.request(
                            getWindow(),
                            windowRect,
                            tile,
                            result -> {
                                if (!jmReportCaptureRunning) {
                                    if (!tile.isRecycled()) tile.recycle();
                                    return;
                                }
                                if (result == android.view.PixelCopy.SUCCESS
                                        && jmReportTileHasContent(tile)) {
                                    jmReportDrawTile(tile, targetLeft, targetTop,
                                            actualScrollLeft, actualScrollTop);
                                    return;
                                }
                                try {
                                    Canvas canvas = new Canvas(tile);
                                    canvas.drawColor(Color.rgb(216, 247, 232));
                                    webView.draw(canvas);
                                    jmReportDrawTile(tile, targetLeft, targetTop,
                                            actualScrollLeft, actualScrollTop);
                                } catch (Throwable error) {
                                    if (!tile.isRecycled()) tile.recycle();
                                    jmReportFinishCapture(false);
                                }
                            },
                            new android.os.Handler(android.os.Looper.getMainLooper())
                    );
                } catch (Throwable error) {
                    if (!tile.isRecycled()) tile.recycle();
                    jmReportFinishCapture(false);
                }
            } else {
                try {
                    Canvas canvas = new Canvas(tile);
                    canvas.drawColor(Color.rgb(216, 247, 232));
                    webView.draw(canvas);
                    jmReportDrawTile(tile, targetLeft, targetTop,
                            actualScrollLeft, actualScrollTop);
                } catch (Throwable error) {
                    if (!tile.isRecycled()) tile.recycle();
                    jmReportFinishCapture(false);
                }
            }
        }, 90L)));
    }

'''

capture_pattern = re.compile(
    r"    private void jmReportCaptureTile\(.*?\n    private void jmReportStartCapture\(",
    re.S,
)
capture_match = capture_pattern.search(java)
if not capture_match:
    raise SystemExit("v209.20 capture method boundaries missing")
java = (java[:capture_match.start()] + capture_method
        + "    private void jmReportStartCapture(" + java[capture_match.end():])

old_width = ("                    jmReportSourceWidth = Math.min(webView.getWidth(), "
             "Math.max(1, Math.round(Math.max(1, cssWidth) * pageScale)));\n")
new_width = ("                    jmReportSourceWidth = Math.max(1, "
             "Math.round(Math.max(1, cssWidth) * pageScale));\n"
             "                    jmReportViewportWidth = Math.max(1, webView.getWidth());\n")
if java.count(old_width) != 1:
    raise SystemExit("v209.20 source width anchor mismatch")
java = java.replace(old_width, new_width, 1)

if java.count("                    jmReportCaptureTile(0);\n") != 1:
    raise SystemExit("v209.20 first tile anchor mismatch")
java = java.replace(
    "                    jmReportCaptureTile(0);\n",
    "                    jmReportCaptureTile(0, 0);\n",
    1,
)

style = r'''
<style id="jmHighResolutionSingleReportV20920">
/* JAYUMINTON_HIGH_RES_SINGLE_REPORT_V20920
   This style is active only on the temporary export clone. The on-screen
   statistics modal remains unchanged. */
#jmNativeReportExportV20905{width:1600px!important;min-width:1600px!important}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918{
  width:1600px!important;min-width:1600px!important;max-width:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child{
  gap:16px!important;padding:0 16px 16px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-head{
  margin:0 -16px!important;font-size:30px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-row{
  gap:10px 14px!important;padding:18px 20px!important;border-radius:18px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-name{
  gap:10px!important;font-size:24px!important;line-height:1.35!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-av{
  width:44px!important;height:44px!important;font-size:19px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-games{
  font-size:26px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time{
  font-size:20px!important;line-height:1.35!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time::before{
  font-size:16px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-partners{
  font-size:20px!important;line-height:1.55!important;padding-top:8px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-card{
  padding:14px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-summary{
  gap:8px!important;margin-bottom:10px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-stat{
  padding:9px 7px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-stat small{
  font-size:15px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-stat b{
  font-size:20px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-title{
  font-size:19px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-list{
  font-size:19px!important;line-height:1.6!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-chip{
  margin:2px 4px 2px 0!important;padding:4px 7px!important;font-size:18px!important;
}
</style>
'''

if "</head>" not in html:
    raise SystemExit("v209.20 head close missing")
html = html.replace("</head>", style + "\n</head>", 1)

old_js = "var rect=p.getBoundingClientRect(),w=Math.max(320,Math.ceil(rect.width||p.offsetWidth||941));"
new_js = "var rect=p.getBoundingClientRect(),w=Math.max(1600,Math.ceil(rect.width||p.offsetWidth||941));"
if html.count(old_js) != 1:
    raise SystemExit("v209.20 export width anchor mismatch: " + str(html.count(old_js)))
html = html.replace(old_js, new_js, 1)

for token in (
    MARKER,
    "jmReportViewportWidth",
    "jmReportCaptureTile(nextLeft, targetTop)",
    "jmReportCaptureTile(0, nextTop)",
    "jmReportCaptureTile(0, 0)",
    "w=Math.max(1600",
    "font-size:24px!important",
    "font-size:20px!important",
):
    if token not in html + java:
        raise SystemExit("v209.20 output missing: " + token)

if "Math.min(webView.getWidth(), Math.max(1, Math.round(Math.max(1, cssWidth)" in java:
    raise SystemExit("v209.20 old screen-width clamp remains")

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20920_HIGH_RES_SINGLE_REPORT_OK")
