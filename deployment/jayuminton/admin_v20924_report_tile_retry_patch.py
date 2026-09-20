#!/usr/bin/env python3
"""Retry native report tiles instead of saving green blanks or failing immediately."""

from pathlib import Path
import re
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_REPORT_TILE_RETRY_V20924"

if MARKER in html and MARKER in java:
    print("ADMIN_V20924_REPORT_TILE_RETRY_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923",
    "w=Math.max(1600",
):
    if token not in html:
        raise SystemExit("v209.24 HTML prerequisite missing: " + token)
for token in (
    "JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923",
    "private void jmReportCaptureTile(final int targetLeft, final int targetTop)",
    "canvas.drawColor(Color.WHITE)",
):
    if token not in java:
        raise SystemExit("v209.24 Java prerequisite missing: " + token)

style = r'''
<style id="jmReportTileRetryV20924">
/* JAYUMINTON_REPORT_TILE_RETRY_V20924 */
</style>
'''
html = html.replace("</head>", style + "\n</head>", 1)

capture = r'''    // JAYUMINTON_REPORT_TILE_RETRY_V20924
    private void jmReportCaptureTile(final int targetLeft, final int targetTop) {
        jmReportCaptureTileAttempt(targetLeft, targetTop, 0);
    }

    private void jmReportCaptureTileAttempt(final int targetLeft, final int targetTop,
                                            final int attempt) {
        if (!jmReportCaptureRunning || webView == null) return;
        final int maxScrollX = Math.max(0, jmReportSourceWidth - jmReportViewportWidth);
        final int maxScrollY = Math.max(0, jmReportSourceHeight - jmReportViewportHeight);
        final int requestedScrollLeft = Math.min(Math.max(0, targetLeft), maxScrollX);
        final int requestedScrollTop = Math.min(Math.max(0, targetTop), maxScrollY);
        webView.scrollTo(requestedScrollLeft, requestedScrollTop);
        webView.postOnAnimation(() -> webView.postOnAnimation(() -> webView.postDelayed(() -> {
            if (!jmReportCaptureRunning || webView == null) return;
            final int actualScrollLeft = webView.getScrollX();
            final int actualScrollTop = webView.getScrollY();
            if ((Math.abs(actualScrollLeft - requestedScrollLeft) > 2
                    || Math.abs(actualScrollTop - requestedScrollTop) > 2) && attempt < 3) {
                jmReportCaptureTileAttempt(targetLeft, targetTop, attempt + 1);
                return;
            }

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

            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
                try {
                    Canvas canvas = new Canvas(tile);
                    canvas.drawColor(Color.WHITE);
                    webView.draw(canvas);
                    if (!jmReportTileHasContent(tile)) throw new IllegalStateException("blank tile");
                    jmReportDrawTile(tile, targetLeft, targetTop,
                            actualScrollLeft, actualScrollTop);
                } catch (Throwable error) {
                    if (!tile.isRecycled()) tile.recycle();
                    if (attempt < 3) jmReportCaptureTileAttempt(targetLeft, targetTop, attempt + 1);
                    else jmReportFinishCapture(false);
                }
                return;
            }

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
                            if (!tile.isRecycled()) tile.recycle();
                            if (attempt < 3) {
                                webView.postDelayed(() -> jmReportCaptureTileAttempt(
                                        targetLeft, targetTop, attempt + 1), 180L);
                            } else {
                                jmReportFinishCapture(false);
                            }
                        },
                        new android.os.Handler(android.os.Looper.getMainLooper())
                );
            } catch (Throwable error) {
                if (!tile.isRecycled()) tile.recycle();
                if (attempt < 3) {
                    webView.postDelayed(() -> jmReportCaptureTileAttempt(
                            targetLeft, targetTop, attempt + 1), 180L);
                } else {
                    jmReportFinishCapture(false);
                }
            }
        }, 280L)));
    }

'''
pat = re.compile(
    r"    // JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923\n"
    r"    private void jmReportCaptureTile\(final int targetLeft, final int targetTop\) \{.*?\n"
    r"    private void jmReportStartCapture\(",
    re.S,
)
m = pat.search(java)
if not m:
    raise SystemExit("v209.24 capture method boundaries missing")
java = java[:m.start()] + capture + "    private void jmReportStartCapture(" + java[m.end():]

for token in (
    MARKER,
    "jmReportCaptureTileAttempt(targetLeft, targetTop, 0)",
    "attempt < 3",
    "android.view.PixelCopy.request",
    "actualScrollLeft = webView.getScrollX()",
    "280L",
):
    if token not in html + java:
        raise SystemExit("v209.24 output missing: " + token)

active = re.search(
    r"// JAYUMINTON_REPORT_TILE_RETRY_V20924.*?private void jmReportStartCapture\(",
    java,
    re.S,
)
if not active or "Color.rgb(216, 247, 232)" in active.group(0):
    raise SystemExit("v209.24 green fallback remains active")

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20924_REPORT_TILE_RETRY_OK")
