#!/usr/bin/env python3
from pathlib import Path
import re, sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
html = html_path.read_text(encoding='utf-8')
java = java_path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_REPORT_PIXELCOPY_CAPTURE_V20906'

if MARKER in html and MARKER in java:
    print('V20906_ALREADY_OK')
    raise SystemExit(0)

for token in ('JAYUMINTON_NATIVE_FULL_REPORT_CAPTURE_V20905','NativeReportCapture','jm-native-report-export-v20905'):
    if token not in html + java:
        raise SystemExit('v209.06 prerequisite missing: ' + token)

if 'import android.graphics.Rect;\n' not in java:
    anchor = 'import android.graphics.Picture;\n'
    if anchor not in java:
        anchor = 'import android.graphics.Canvas;\n'
    if anchor not in java:
        raise SystemExit('graphics import anchor missing')
    java = java.replace(anchor, anchor + 'import android.graphics.Rect;\n', 1)

new_native = r'''    // JAYUMINTON_REPORT_PIXELCOPY_CAPTURE_V20906
    private Bitmap jmReportBitmap;
    private int jmReportOriginalScrollY;
    private int jmReportSourceWidth;
    private int jmReportSourceHeight;
    private int jmReportViewportHeight;
    private int jmReportOutputWidth;
    private int jmReportOutputHeight;
    private float jmReportOutputScale = 1.0f;
    private String jmReportRequestedName = "";
    private boolean jmReportCaptureRunning = false;

    private void jmReportNotifyJavascript(boolean ok) {
        if (webView == null) return;
        webView.evaluateJavascript(
                "window.jmNativeFullImageDone&&window.jmNativeFullImageDone(" + (ok ? "true" : "false") + ")",
                null
        );
    }

    private boolean jmReportTileHasContent(Bitmap bitmap) {
        if (bitmap == null || bitmap.getWidth() < 2 || bitmap.getHeight() < 2) return false;
        int first = bitmap.getPixel(bitmap.getWidth() / 2, bitmap.getHeight() / 2);
        int different = 0;
        for (int gy = 1; gy <= 7; gy++) {
            int y = Math.min(bitmap.getHeight() - 1, Math.max(0, gy * bitmap.getHeight() / 8));
            for (int gx = 1; gx <= 7; gx++) {
                int x = Math.min(bitmap.getWidth() - 1, Math.max(0, gx * bitmap.getWidth() / 8));
                int c = bitmap.getPixel(x, y);
                int dr = Math.abs(Color.red(c) - Color.red(first));
                int dg = Math.abs(Color.green(c) - Color.green(first));
                int db = Math.abs(Color.blue(c) - Color.blue(first));
                if (dr + dg + db > 18) {
                    different++;
                    if (different >= 3) return true;
                }
            }
        }
        return false;
    }

    private void jmReportSaveBitmap(Bitmap bitmap, String requested) throws Exception {
        String safeName = requested.replaceAll("[^0-9A-Za-z가-힣._-]", "_");
        if (!safeName.toLowerCase(Locale.ROOT).endsWith(".png")) safeName += ".png";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.Images.Media.DISPLAY_NAME, safeName);
            values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
            values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/자유민턴");
            values.put(MediaStore.Images.Media.IS_PENDING, 1);
            Uri uri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
            if (uri == null) throw new IllegalStateException("MediaStore insert failed");
            try (OutputStream out = getContentResolver().openOutputStream(uri)) {
                if (out == null || !bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) {
                    throw new IllegalStateException("PNG write failed");
                }
            }
            values.clear();
            values.put(MediaStore.Images.Media.IS_PENDING, 0);
            getContentResolver().update(uri, values, null, null);
        } else {
            java.io.File dir = new java.io.File(
                    Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES),
                    "자유민턴"
            );
            if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("Pictures directory create failed");
            java.io.File outFile = new java.io.File(dir, safeName);
            try (FileOutputStream out = new FileOutputStream(outFile)) {
                if (!bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)) {
                    throw new IllegalStateException("PNG write failed");
                }
            }
            sendBroadcast(new Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE, Uri.fromFile(outFile)));
        }
    }

    private void jmReportFinishCapture(boolean success) {
        if (!jmReportCaptureRunning) return;
        jmReportCaptureRunning = false;
        if (webView != null) webView.scrollTo(0, jmReportOriginalScrollY);
        boolean ok = success;
        try {
            if (ok) {
                if (jmReportBitmap == null || !jmReportTileHasContent(jmReportBitmap)) {
                    throw new IllegalStateException("captured report is blank");
                }
                jmReportSaveBitmap(jmReportBitmap, jmReportRequestedName);
            }
        } catch (Throwable error) {
            ok = false;
        } finally {
            if (jmReportBitmap != null && !jmReportBitmap.isRecycled()) jmReportBitmap.recycle();
            jmReportBitmap = null;
        }
        Toast.makeText(
                MainActivity.this,
                ok ? "전체 이미지 저장 완료" : "전체 이미지 저장 실패",
                ok ? Toast.LENGTH_SHORT : Toast.LENGTH_LONG
        ).show();
        jmReportNotifyJavascript(ok);
    }

    private void jmReportDrawTile(Bitmap tile, int targetTop, int actualScrollTop) {
        if (tile == null || jmReportBitmap == null) {
            jmReportFinishCapture(false);
            return;
        }
        int sourceOffset = Math.max(0, targetTop - actualScrollTop);
        if (sourceOffset >= tile.getHeight()) {
            tile.recycle();
            jmReportFinishCapture(false);
            return;
        }
        int copyHeight = Math.min(jmReportSourceHeight - targetTop, tile.getHeight() - sourceOffset);
        if (copyHeight <= 0) {
            tile.recycle();
            jmReportFinishCapture(true);
            return;
        }
        Canvas out = new Canvas(jmReportBitmap);
        Rect src = new Rect(0, sourceOffset, tile.getWidth(), sourceOffset + copyHeight);
        int dstTop = Math.max(0, Math.round(targetTop * jmReportOutputScale));
        int dstBottom = Math.min(jmReportOutputHeight, Math.max(dstTop + 1, Math.round((targetTop + copyHeight) * jmReportOutputScale)));
        Rect dst = new Rect(0, dstTop, jmReportOutputWidth, dstBottom);
        out.drawBitmap(tile, src, dst, null);
        tile.recycle();
        int nextTop = targetTop + copyHeight;
        if (nextTop >= jmReportSourceHeight) jmReportFinishCapture(true);
        else jmReportCaptureTile(nextTop);
    }

    private void jmReportCaptureTile(final int targetTop) {
        if (!jmReportCaptureRunning || webView == null) return;
        final int maxScroll = Math.max(0, jmReportSourceHeight - jmReportViewportHeight);
        final int actualScrollTop = Math.min(Math.max(0, targetTop), maxScroll);
        webView.scrollTo(0, actualScrollTop);
        webView.postOnAnimation(() -> webView.postOnAnimation(() -> webView.postDelayed(() -> {
            if (!jmReportCaptureRunning || webView == null) return;
            final int[] loc = new int[2];
            webView.getLocationInWindow(loc);
            int width = Math.min(jmReportSourceWidth, webView.getWidth());
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
                                if (result == android.view.PixelCopy.SUCCESS && jmReportTileHasContent(tile)) {
                                    jmReportDrawTile(tile, targetTop, actualScrollTop);
                                    return;
                                }
                                try {
                                    Canvas canvas = new Canvas(tile);
                                    canvas.drawColor(Color.rgb(216, 247, 232));
                                    webView.draw(canvas);
                                    jmReportDrawTile(tile, targetTop, actualScrollTop);
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
                    jmReportDrawTile(tile, targetTop, actualScrollTop);
                } catch (Throwable error) {
                    if (!tile.isRecycled()) tile.recycle();
                    jmReportFinishCapture(false);
                }
            }
        }, 70L)));
    }

    private void jmReportStartCapture(String requestedName, int cssWidth, int cssHeight) {
        runOnUiThread(() -> {
            if (jmReportCaptureRunning || webView == null) {
                jmReportNotifyJavascript(false);
                return;
            }
            webView.postDelayed(() -> {
                try {
                    float pageScale = Math.max(0.1f, webView.getScale());
                    jmReportSourceWidth = Math.min(webView.getWidth(), Math.max(1, Math.round(Math.max(1, cssWidth) * pageScale)));
                    jmReportSourceHeight = Math.max(1, Math.round(Math.max(1, cssHeight) * pageScale));
                    jmReportViewportHeight = Math.max(1, webView.getHeight());
                    jmReportOriginalScrollY = webView.getScrollY();
                    jmReportRequestedName = requestedName == null || requestedName.trim().isEmpty()
                            ? "자유민턴_게임통계.png" : requestedName.trim();
                    long sourcePixels = (long) jmReportSourceWidth * (long) jmReportSourceHeight;
                    final long maxPixels = 12000000L;
                    jmReportOutputScale = sourcePixels > maxPixels
                            ? (float) Math.sqrt((double) maxPixels / (double) sourcePixels)
                            : 1.0f;
                    jmReportOutputWidth = Math.max(1, Math.round(jmReportSourceWidth * jmReportOutputScale));
                    jmReportOutputHeight = Math.max(1, Math.round(jmReportSourceHeight * jmReportOutputScale));
                    jmReportBitmap = Bitmap.createBitmap(jmReportOutputWidth, jmReportOutputHeight, Bitmap.Config.ARGB_8888);
                    Canvas background = new Canvas(jmReportBitmap);
                    background.drawColor(Color.rgb(216, 247, 232));
                    jmReportCaptureRunning = true;
                    jmReportCaptureTile(0);
                } catch (Throwable error) {
                    jmReportCaptureRunning = true;
                    jmReportFinishCapture(false);
                }
            }, 180L);
        });
    }

    public final class ReportCaptureBridge {
        @JavascriptInterface
        public void saveFullReportPng(String requestedName, int cssWidth, int cssHeight) {
            jmReportStartCapture(requestedName, cssWidth, cssHeight);
        }
    }

    public final class BrowserBridge {'''

pat = re.compile(
    r'    // JAYUMINTON_NATIVE_FULL_REPORT_CAPTURE_V20905\n.*?    public final class BrowserBridge \{',
    re.S,
)
m = pat.search(java)
if not m:
    raise SystemExit('v209.05 native bridge block anchor missing')
java = java[:m.start()] + new_native + java[m.end():]

# Update the active JS call so native code receives the exact export clone size.
call_pat = re.compile(
    r"window\.NativeReportCapture\.saveFullReportPng\('자유민턴_게임통계_'\+yy\+'-'\+mm\+'-'\+dd\+'\\.png'\);"
)
# The filename expression may not contain an escaped dot in generated HTML, so
# use a direct literal fallback as well.
old_call = "window.NativeReportCapture.saveFullReportPng('자유민턴_게임통계_'+yy+'-'+mm+'-'+dd+'.png');"
new_call = "var hh=Math.max(host.scrollHeight,c.scrollHeight,Math.ceil(c.getBoundingClientRect().height));window.NativeReportCapture.saveFullReportPng('자유민턴_게임통계_'+yy+'-'+mm+'-'+dd+'.png',w,hh);"
if old_call not in html:
    raise SystemExit('v209.05 native save call anchor missing')
html = html.replace(old_call, new_call, 1)
html = html.replace('setTimeout(function(){if(!finished)restore(false);},12000);', 'setTimeout(function(){if(!finished)restore(false);},30000);', 1)

DOCK_STYLE = r'''
<style id="jmReportDockAndCaptureV20906Style">
/* JAYUMINTON_REPORT_PIXELCOPY_CAPTURE_V20906 */
#pairStatisticsModal .j95-actions{
  bottom:var(--jm-quick-menu-h)!important;
  padding:3px 5px 0!important;
  border-radius:10px 10px 0 0!important;
  box-shadow:0 -2px 7px rgba(15,70,55,.08)!important;
}
#pairStatisticsModal .j95-actions .j101-tool,
#pairStatisticsModal .j95-actions .j95-save,
#pairStatisticsModal .j95-actions .j95-close{margin-bottom:0!important}
@media(max-width:720px){#pairStatisticsModal .j95-actions{padding:2px 4px 0!important}}
</style>
'''
if '</head>' not in html:
    raise SystemExit('head anchor missing')
html = html.replace('</head>', DOCK_STYLE + '\n</head>', 1)

for token in (
    MARKER,
    'android.view.PixelCopy.request',
    'saveFullReportPng(String requestedName, int cssWidth, int cssHeight)',
    'jmReportCaptureTile',
    'captured report is blank',
    "saveFullReportPng('자유민턴_게임통계_'",
    'padding:3px 5px 0!important',
    'bottom:var(--jm-quick-menu-h)!important',
):
    if token not in html + java:
        raise SystemExit('v209.06 contract missing: ' + token)

if 'Picture picture = webView.capturePicture()' in java:
    raise SystemExit('old capturePicture path still active')

html_path.write_text(html, encoding='utf-8')
java_path.write_text(java, encoding='utf-8')
print('V20906_PIXELCOPY_CAPTURE_DOCK_OK')
