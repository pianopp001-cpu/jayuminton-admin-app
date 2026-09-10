#!/usr/bin/env python3
from pathlib import Path
import re, sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
html = html_path.read_text(encoding='utf-8')
java = java_path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_NATIVE_FULL_REPORT_CAPTURE_V20905'

if MARKER in html and MARKER in java:
    print('V20905_ALREADY_OK')
    raise SystemExit(0)

for token in ('JAYUMINTON_GAME_REPORT_EXPAND_EXPORT_V20901','JAYUMINTON_GAME_REPORT_ACTIONS_ATTACH_QUICKMENU_V20904','window.jmSaveGameReportImage=saveFullImage'):
    if token not in html:
        raise SystemExit('v209.05 HTML prerequisite missing: ' + token)
if 'public void saveStatisticsPng(String dataUrl, String requestedName)' not in java:
    raise SystemExit('v209.05 Java prerequisite missing: saveStatisticsPng')

# Native full-page WebView capture avoids Android WebView's fragile
# HTML -> SVG foreignObject -> Image -> Canvas conversion path.
for imp in (
    'import android.graphics.Bitmap;\n',
    'import android.graphics.Canvas;\n',
    'import android.graphics.Picture;\n',
):
    if imp not in java:
        anchor = 'import android.graphics.Color;\n'
        if anchor not in java:
            raise SystemExit('graphics import anchor missing')
        java = java.replace(anchor, anchor + imp, 1)

# Keep this bridge independent from BrowserBridge. Several historical build
# patches modify BrowserBridge, so injecting into that class is unnecessarily
# fragile. A separate JavascriptInterface has a stable registration point.
register_anchor = '        webView.addJavascriptInterface(new BrowserBridge(), "NativeBrowser");\n'
if register_anchor not in java:
    raise SystemExit('NativeBrowser registration anchor missing')
java = java.replace(
    register_anchor,
    register_anchor + '        webView.addJavascriptInterface(new ReportCaptureBridge(), "NativeReportCapture");\n',
    1,
)

report_class = r'''    // JAYUMINTON_NATIVE_FULL_REPORT_CAPTURE_V20905
    public final class ReportCaptureBridge {
        @SuppressWarnings("deprecation")
        @JavascriptInterface
        public void saveFullReportPng(String requestedName) {
            final String requested = requestedName == null || requestedName.trim().isEmpty()
                    ? "자유민턴_게임통계.png" : requestedName.trim();
            runOnUiThread(() -> {
                if (webView == null) return;
                webView.requestLayout();
                webView.invalidate();
                webView.postDelayed(() -> {
                    Bitmap bitmap = null;
                    try {
                        Picture picture = webView.capturePicture();
                        if (picture == null) throw new IllegalStateException("capturePicture returned null");
                        int sourceW = picture.getWidth();
                        int sourceH = picture.getHeight();
                        if (sourceW <= 0 || sourceH <= 0) {
                            throw new IllegalStateException("invalid report size " + sourceW + "x" + sourceH);
                        }

                        // A fully expanded report can be very tall. Downscale only
                        // when required so the complete report still fits one PNG
                        // without exhausting the device heap.
                        final long maxPixels = 10000000L;
                        long sourcePixels = (long) sourceW * (long) sourceH;
                        float scale = sourcePixels > maxPixels
                                ? (float) Math.sqrt((double) maxPixels / (double) sourcePixels)
                                : 1.0f;
                        int outW = Math.max(1, Math.round(sourceW * scale));
                        int outH = Math.max(1, Math.round(sourceH * scale));
                        bitmap = Bitmap.createBitmap(outW, outH, Bitmap.Config.ARGB_8888);
                        Canvas canvas = new Canvas(bitmap);
                        canvas.drawColor(Color.rgb(216, 247, 232));
                        if (scale != 1.0f) canvas.scale(scale, scale);
                        picture.draw(canvas);

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

                        Toast.makeText(MainActivity.this, "전체 이미지 저장 완료", Toast.LENGTH_SHORT).show();
                        webView.evaluateJavascript(
                                "window.jmNativeFullImageDone&&window.jmNativeFullImageDone(true)", null);
                    } catch (Throwable error) {
                        Toast.makeText(MainActivity.this, "전체 이미지 저장 실패", Toast.LENGTH_LONG).show();
                        webView.evaluateJavascript(
                                "window.jmNativeFullImageDone&&window.jmNativeFullImageDone(false)", null);
                    } finally {
                        if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
                    }
                }, 320L);
            });
        }
    }

'''
class_anchor = '    public final class BrowserBridge {\n'
if class_anchor not in java:
    raise SystemExit('BrowserBridge class anchor missing')
java = java.replace(class_anchor, report_class + class_anchor, 1)

destroy_anchor = '            webView.removeJavascriptInterface("NativeBrowser");\n'
if destroy_anchor in java:
    java = java.replace(
        destroy_anchor,
        destroy_anchor + '            webView.removeJavascriptInterface("NativeReportCapture");\n',
        1,
    )

export_style = r'''
<style id="jmNativeFullReportCaptureV20905Style">
/* JAYUMINTON_NATIVE_FULL_REPORT_CAPTURE_V20905 */
html.jm-native-report-export-v20905,
html.jm-native-report-export-v20905 body{
  margin:0!important;padding:0!important;width:100%!important;max-width:none!important;
  height:auto!important;min-height:0!important;overflow:visible!important;background:#d8f7e8!important;
}
html.jm-native-report-export-v20905 body > :not(#jmNativeReportExportV20905){display:none!important}
#jmNativeReportExportV20905{
  display:block!important;position:relative!important;left:auto!important;top:auto!important;
  margin:0!important;padding:0!important;max-width:none!important;overflow:visible!important;
  background:#d8f7e8!important;z-index:1!important;
}
#jmNativeReportExportV20905 .j95-poster{
  display:block!important;margin:0!important;max-width:none!important;max-height:none!important;
  height:auto!important;overflow:visible!important;
}
</style>
'''
if '</head>' not in html:
    raise SystemExit('HTML head anchor missing')
html = html.replace('</head>', export_style + '\n</head>', 1)

new_save = r'''function saveFullImage(){
  var p=poster();if(!p){alert('저장할 통계 화면이 없습니다.');return;}if(busy)return;
  if(!(window.NativeReportCapture&&typeof window.NativeReportCapture.saveFullReportPng==='function')){
    alert('이 APK에서는 전체 이미지 저장 기능을 사용할 수 없습니다.');return;
  }
  setBusy(true,'이미지 만드는 중…');
  var old=document.getElementById('jmNativeReportExportV20905');if(old)old.remove();
  var rect=p.getBoundingClientRect(),w=Math.max(320,Math.ceil(rect.width||p.offsetWidth||941));
  var c=p.cloneNode(true);cleanClone(c);c.style.width=w+'px';
  var host=document.createElement('div');host.id='jmNativeReportExportV20905';host.style.width=w+'px';host.appendChild(c);
  var sx=window.scrollX||0,sy=window.scrollY||0;
  document.body.appendChild(host);
  document.documentElement.classList.add('jm-native-report-export-v20905');
  var finished=false;
  function restore(ok){
    if(finished)return;finished=true;
    document.documentElement.classList.remove('jm-native-report-export-v20905');
    if(host&&host.parentNode)host.parentNode.removeChild(host);
    try{window.scrollTo(sx,sy);}catch(_){}
    setBusy(false);
    if(!ok)alert('전체 이미지 저장에 실패했습니다. 다시 시도해 주세요.');
  }
  window.jmNativeFullImageDone=restore;
  requestAnimationFrame(function(){requestAnimationFrame(function(){
    setTimeout(function(){
      try{
        var now=new Date(),yy=now.getFullYear(),mm=String(now.getMonth()+1).padStart(2,'0'),dd=String(now.getDate()).padStart(2,'0');
        window.NativeReportCapture.saveFullReportPng('자유민턴_게임통계_'+yy+'-'+mm+'-'+dd+'.png');
      }catch(err){restore(false);}
    },120);
  });});
  setTimeout(function(){if(!finished)restore(false);},12000);
}'''

# Replace the actual active v209.01 exporter in place. This prevents its
# delayed install hooks from restoring the old SVG/foreignObject path.
pat = re.compile(r'function saveFullImage\(\)\{.*?\n\}\nfunction install\(\)\{', re.S)
m = pat.search(html)
if not m:
    raise SystemExit('v209.01 saveFullImage anchor missing')
html = html[:m.start()] + new_save + '\nfunction install(){' + html[m.end():]

for token in (
    MARKER,
    'NativeReportCapture',
    'saveFullReportPng',
    'webView.capturePicture()',
    'jm-native-report-export-v20905',
    'window.NativeReportCapture.saveFullReportPng',
    'window.jmNativeFullImageDone=restore',
    'window.jmSaveGameReportImage=saveFullImage',
    '전체 펼침',
    '전체 접힘',
):
    if token not in html + java:
        raise SystemExit('v209.05 contract missing: ' + token)

# The failing SVG/Image/Canvas exporter must not remain in the active v209.01
# save function after this patch.
active = re.search(r'function saveFullImage\(\)\{.*?\n\}\nfunction install\(\)\{', html, re.S)
if not active:
    raise SystemExit('patched saveFullImage not found')
if 'createObjectURL' in active.group(0) or 'foreignObject' in active.group(0) or 'new Image()' in active.group(0):
    raise SystemExit('old SVG export path still active')

html_path.write_text(html, encoding='utf-8')
java_path.write_text(java, encoding='utf-8')
print('V20905_NATIVE_FULL_REPORT_CAPTURE_OK')
