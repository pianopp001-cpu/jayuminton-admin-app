#!/usr/bin/env python3
"""Render the full statistics report directly with Android Canvas at native resolution."""

from pathlib import Path
import re
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_NATIVE_CANVAS_REPORT_V20927"

if MARKER in html and MARKER in java:
    print("ADMIN_V20927_NATIVE_CANVAS_REPORT_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_DIRECT_VECTOR_REPORT_V20926",
    "window.jmV20926SaveVectorReport",
):
    if token not in html:
        raise SystemExit("v209.27 HTML prerequisite missing: " + token)

for token in (
    "JAYUMINTON_REPORT_PIXELCOPY_CAPTURE_V20906",
    "private void jmReportSaveBitmap",
    'webView.addJavascriptInterface(new ReportCaptureBridge(), "NativeReportCapture");',
):
    if token not in java:
        raise SystemExit("v209.27 Java prerequisite missing: " + token)

# Imports for true native text rendering.
imports = [
    "import android.graphics.Paint;\n",
    "import android.graphics.RectF;\n",
    "import android.graphics.Typeface;\n",
    "import android.text.Layout;\n",
    "import android.text.StaticLayout;\n",
    "import android.text.TextPaint;\n",
    "import org.json.JSONArray;\n",
    "import org.json.JSONObject;\n",
]
anchor = "import android.graphics.Color;\n"
if anchor not in java:
    raise SystemExit("v209.27 import anchor missing")
for imp in imports:
    if imp not in java:
        java = java.replace(anchor, anchor + imp, 1)

# Register a dedicated bridge; the old WebView screenshot bridge remains installed
# for compatibility but is no longer called by the active report save path.
reg = '        webView.addJavascriptInterface(new ReportCaptureBridge(), "NativeReportCapture");\n'
if java.count(reg) != 1:
    raise SystemExit("v209.27 report bridge registration anchor mismatch: " + str(java.count(reg)))
java = java.replace(
    reg,
    reg + '        webView.addJavascriptInterface(new NativeCanvasReportBridge(), "NativeCanvasReport"); // ' + MARKER + '\n',
    1,
)

native = r'''
    // JAYUMINTON_NATIVE_CANVAS_REPORT_V20927
    private static final int NATIVE_REPORT_WIDTH = 2800;
    private static final int NATIVE_REPORT_COLUMNS = 4;
    private static final int NATIVE_REPORT_MARGIN = 44;
    private static final int NATIVE_REPORT_GAP = 20;

    private TextPaint jmReportTextPaint(float size, int color, boolean bold) {
        TextPaint paint = new TextPaint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        paint.setColor(color);
        paint.setTextSize(size);
        paint.setTypeface(Typeface.create("sans-serif", bold ? Typeface.BOLD : Typeface.NORMAL));
        return paint;
    }

    private Paint jmReportPaint(int color, Paint.Style style) {
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setColor(color);
        paint.setStyle(style);
        return paint;
    }

    @SuppressWarnings("deprecation")
    private StaticLayout jmReportLayout(String text, TextPaint paint, int width, float spacing) {
        return new StaticLayout(
                text == null ? "" : text,
                paint,
                Math.max(1, width),
                Layout.Alignment.ALIGN_NORMAL,
                spacing,
                0.0f,
                false
        );
    }

    private String jmReportSafe(JSONObject object, String key, String fallback) {
        if (object == null) return fallback;
        String value = object.optString(key, fallback);
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }

    private String jmReportPartners(JSONObject member) {
        JSONArray partners = member == null ? null : member.optJSONArray("partners");
        if (partners == null || partners.length() == 0) return "기록 없음";
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < partners.length(); i++) {
            JSONObject p = partners.optJSONObject(i);
            if (p == null) continue;
            String name = jmReportSafe(p, "name", "-");
            int count = Math.max(0, p.optInt("count", 0));
            if (out.length() > 0) out.append("   ·   ");
            out.append(name);
            if (count > 1) out.append(" ").append(count).append("회");
        }
        return out.length() == 0 ? "기록 없음" : out.toString();
    }

    private int jmReportPartnerCount(JSONObject member) {
        JSONArray partners = member == null ? null : member.optJSONArray("partners");
        return partners == null ? 0 : partners.length();
    }

    private int jmMeasureNativeReportCard(JSONObject member, int cardWidth) {
        final int inner = cardWidth - 44;
        TextPaint namePaint = jmReportTextPaint(40f, Color.rgb(10, 39, 52), true);
        TextPaint partnerPaint = jmReportTextPaint(32f, Color.rgb(10, 54, 76), false);
        StaticLayout name = jmReportLayout(jmReportSafe(member, "name", "-"), namePaint, Math.max(120, inner - 150), 1.0f);
        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.05f);
        int nameHeight = Math.max(48, name.getHeight());
        return 24 + nameHeight + 42 + 40 + partners.getHeight() + 30;
    }

    private void jmDrawStaticLayout(Canvas canvas, StaticLayout layout, float x, float y) {
        canvas.save();
        canvas.translate(x, y);
        layout.draw(canvas);
        canvas.restore();
    }

    private void jmDrawNativeReportCard(Canvas canvas, JSONObject member, float x, float y, int cardWidth, int cardHeight) {
        Paint fill = jmReportPaint(Color.WHITE, Paint.Style.FILL);
        Paint stroke = jmReportPaint(Color.rgb(194, 218, 224), Paint.Style.STROKE);
        stroke.setStrokeWidth(2f);
        RectF box = new RectF(x, y, x + cardWidth, y + cardHeight);
        canvas.drawRoundRect(box, 18f, 18f, fill);
        canvas.drawRoundRect(box, 18f, 18f, stroke);

        final float left = x + 22f;
        final int inner = cardWidth - 44;
        TextPaint namePaint = jmReportTextPaint(40f, Color.rgb(10, 39, 52), true);
        TextPaint gamesPaint = jmReportTextPaint(34f, Color.rgb(0, 143, 99), true);
        TextPaint metaPaint = jmReportTextPaint(27f, Color.rgb(50, 81, 92), true);
        TextPaint labelPaint = jmReportTextPaint(26f, Color.rgb(47, 91, 105), true);
        TextPaint partnerPaint = jmReportTextPaint(32f, Color.rgb(10, 54, 76), false);

        StaticLayout name = jmReportLayout(jmReportSafe(member, "name", "-"), namePaint, Math.max(120, inner - 150), 1.0f);
        int nameHeight = Math.max(48, name.getHeight());
        jmDrawStaticLayout(canvas, name, left, y + 20f);

        String games = Math.max(0, member.optInt("games", 0)) + "회";
        float gamesWidth = gamesPaint.measureText(games);
        canvas.drawText(games, x + cardWidth - 22f - gamesWidth, y + 20f - gamesPaint.ascent(), gamesPaint);

        float metaY = y + 24f + nameHeight + 28f;
        String arrived = jmReportSafe(member, "arrived", "-");
        String departed = jmReportSafe(member, "departed", "-");
        canvas.drawText("도착 " + arrived + "    ·    귀가 " + departed, left, metaY, metaPaint);

        float dividerY = metaY + 18f;
        Paint divider = jmReportPaint(Color.rgb(220, 233, 237), Paint.Style.STROKE);
        divider.setStrokeWidth(2f);
        canvas.drawLine(left, dividerY, x + cardWidth - 22f, dividerY, divider);

        float labelY = dividerY + 35f;
        canvas.drawText("함께 경기한 사람 전체 " + jmReportPartnerCount(member) + "명", left, labelY, labelPaint);

        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.05f);
        jmDrawStaticLayout(canvas, partners, left, labelY + 12f);
    }

    private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {
        JSONArray members = payload.optJSONArray("members");
        if (members == null) members = new JSONArray();

        final int width = NATIVE_REPORT_WIDTH;
        final int margin = NATIVE_REPORT_MARGIN;
        final int gap = NATIVE_REPORT_GAP;
        final int columns = NATIVE_REPORT_COLUMNS;
        final int cardWidth = (width - margin * 2 - gap * (columns - 1)) / columns;
        final int top = 300;
        int[] columnY = new int[columns];
        for (int i = 0; i < columns; i++) columnY[i] = top;

        int[] cardHeights = new int[members.length()];
        int[] cardColumns = new int[members.length()];
        int[] cardTops = new int[members.length()];

        for (int i = 0; i < members.length(); i++) {
            JSONObject member = members.optJSONObject(i);
            if (member == null) member = new JSONObject();
            int height = jmMeasureNativeReportCard(member, cardWidth);
            int col = 0;
            for (int c = 1; c < columns; c++) {
                if (columnY[c] < columnY[col]) col = c;
            }
            cardHeights[i] = height;
            cardColumns[i] = col;
            cardTops[i] = columnY[col];
            columnY[col] += height + gap;
        }

        int contentBottom = top;
        for (int c = 0; c < columns; c++) contentBottom = Math.max(contentBottom, columnY[c]);
        int height = Math.max(900, contentBottom + 120);

        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bitmap);
        canvas.drawColor(Color.WHITE);

        Paint headerBg = jmReportPaint(Color.rgb(232, 251, 247), Paint.Style.FILL);
        canvas.drawRect(0, 0, width, 220, headerBg);
        Paint band = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);
        canvas.drawRect(0, 220, width, 72, band);

        TextPaint title = jmReportTextPaint(56f, Color.rgb(8, 47, 60), true);
        TextPaint subtitle = jmReportTextPaint(34f, Color.rgb(10, 83, 96), true);
        TextPaint summary = jmReportTextPaint(29f, Color.rgb(66, 103, 115), true);
        TextPaint section = jmReportTextPaint(34f, Color.WHITE, true);

        String titleText = jmReportSafe(payload, "title", "자유민턴");
        String subText = jmReportSafe(payload, "subtitle", "오늘의 게임 통계");
        float titleW = title.measureText(titleText);
        float subW = subtitle.measureText(subText);
        canvas.drawText(titleText, (width - titleW) / 2f, 72f, title);
        canvas.drawText(subText, (width - subW) / 2f, 120f, subtitle);

        int totalGames = Math.max(0, payload.optInt("totalGames", 0));
        int totalMembers = members.length();
        int totalMatches = Math.max(0, payload.optInt("totalMatches", Math.round(totalGames / 4f)));
        String summaryText = "참여 " + totalMembers + "명    ·    총 게임수 " + totalGames + "회    ·    경기 " + totalMatches + "게임    ·    모든 함께 경기 이력 포함";
        float sumW = summary.measureText(summaryText);
        canvas.drawText(summaryText, Math.max(30f, (width - sumW) / 2f), 174f, summary);
        canvas.drawText("참여자 통계", 34f, 267f, section);

        for (int i = 0; i < members.length(); i++) {
            JSONObject member = members.optJSONObject(i);
            if (member == null) member = new JSONObject();
            int col = cardColumns[i];
            float x = margin + col * (cardWidth + gap);
            jmDrawNativeReportCard(canvas, member, x, cardTops[i], cardWidth, cardHeights[i]);
        }

        Paint footerBg = jmReportPaint(Color.rgb(232, 251, 247), Paint.Style.FILL);
        canvas.drawRect(0, height - 88, width, height, footerBg);
        TextPaint footer = jmReportTextPaint(23f, Color.rgb(75, 104, 113), true);
        String footerText = "자유민턴 게임 통계 · Android Canvas 원본 렌더 " + width + "×" + height;
        float footerW = footer.measureText(footerText);
        canvas.drawText(footerText, (width - footerW) / 2f, height - 38f, footer);
        return bitmap;
    }

    public final class NativeCanvasReportBridge {
        @JavascriptInterface
        public boolean saveReportJson(String json, String requestedName) {
            Bitmap bitmap = null;
            try {
                JSONObject payload = new JSONObject(json == null ? "{}" : json);
                bitmap = jmRenderNativeReport(payload);
                String name = requestedName == null || requestedName.trim().isEmpty()
                        ? "자유민턴_게임통계.png" : requestedName.trim();
                jmReportSaveBitmap(bitmap, name);
                runOnUiThread(() -> Toast.makeText(
                        MainActivity.this,
                        "고해상도 게임 통계 저장 완료",
                        Toast.LENGTH_SHORT
                ).show());
                return true;
            } catch (Throwable error) {
                runOnUiThread(() -> Toast.makeText(
                        MainActivity.this,
                        "통계 이미지 저장 실패: " + error.getMessage(),
                        Toast.LENGTH_LONG
                ).show());
                return false;
            } finally {
                if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
            }
        }
    }

'''
class_anchor = "    public final class BrowserBridge {\n"
if java.count(class_anchor) != 1:
    raise SystemExit("v209.27 BrowserBridge anchor mismatch: " + str(java.count(class_anchor)))
java = java.replace(class_anchor, native + class_anchor, 1)

destroy_anchor = '            webView.removeJavascriptInterface("NativeBrowser");\n'
if destroy_anchor in java and 'removeJavascriptInterface("NativeCanvasReport")' not in java:
    java = java.replace(
        destroy_anchor,
        destroy_anchor + '            webView.removeJavascriptInterface("NativeCanvasReport");\n',
        1,
    )

# Build a compact JSON payload from the original statistics data and hand it to
# Android. No WebView rasterization, SVG rasterization, PixelCopy, or screenshot.
script = r'''
<script id="jmNativeCanvasReportV20927">
/* JAYUMINTON_NATIVE_CANVAS_REPORT_V20927 */
(function(){
  function rows(){
    var a=Array.isArray(window.ADMIN_PAIR_STATISTICS)?window.ADMIN_PAIR_STATISTICS:
      (Array.isArray(window.MD_PAIR_STATISTICS)?window.MD_PAIR_STATISTICS:[]);
    return a.slice().sort(function(x,y){return Number(y.games||0)-Number(x.games||0)||String(x.name||'').localeCompare(String(y.name||''),'ko');});
  }
  function hm(v){
    var d=v?new Date(String(v)):null;if(!d||Number.isNaN(d.getTime()))return '-';
    try{
      var p=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(d);
      var h=(p.find(function(x){return x.type==='hour';})||{}).value,m=(p.find(function(x){return x.type==='minute';})||{}).value;
      return h&&m?h+':'+m:'-';
    }catch(_){return '-';}
  }
  function payload(){
    var a=rows(),total=a.reduce(function(n,r){return n+Math.max(0,Number(r.games||0));},0);
    return {
      title:'자유민턴',
      subtitle:'오늘의 게임 통계',
      totalGames:total,
      totalMatches:Math.max(0,Math.round(total/4)),
      members:a.map(function(r){
        return {
          name:String(r.name||''),
          games:Math.max(0,Number(r.games||0)),
          arrived:hm(r.arrivedAt),
          departed:hm(r.departedAt),
          partners:(Array.isArray(r.partners)?r.partners:[]).map(function(p){
            return {name:String(p.name||''),count:Math.max(0,Number(p.count||0))};
          })
        };
      })
    };
  }
  window.jmV20927SaveNativeCanvasReport=function(){
    if(!window.NativeCanvasReport||typeof window.NativeCanvasReport.saveReportJson!=='function')return false;
    var d=new Date(),name='자유민턴_게임통계_'+d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')+'.png';
    return !!window.NativeCanvasReport.saveReportJson(JSON.stringify(payload()),name);
  };
})();
</script>
'''

if "</body>" not in html:
    raise SystemExit("v209.27 body close missing")
html = html.replace("</body>", script + "\n</body>", 1)

new_save = r'''function saveFullImage(){
  if(busy)return;
  if(typeof window.jmV20927SaveNativeCanvasReport!=='function'){alert('고해상도 저장 기능을 불러오지 못했습니다.');return;}
  setBusy(true,'원본 해상도로 만드는 중…');
  try{
    var ok=window.jmV20927SaveNativeCanvasReport();
    setBusy(false);
    if(!ok)alert('전체 이미지 저장에 실패했습니다.');
  }catch(e){
    setBusy(false);
    alert('전체 이미지 저장 실패: '+((e&&e.message)||e));
  }
}'''

pat = re.compile(r"function saveFullImage\(\)\{.*?\n\}\nfunction install\(\)\{", re.S)
m = pat.search(html)
if not m:
    raise SystemExit("v209.27 active saveFullImage boundaries missing")
html = html[:m.start()] + new_save + "\nfunction install(){" + html[m.end():]

for token in (
    MARKER,
    "window.jmV20927SaveNativeCanvasReport",
    "NativeCanvasReport.saveReportJson",
    "NATIVE_REPORT_WIDTH = 2800",
    "NATIVE_REPORT_COLUMNS = 4",
    "Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG",
    "StaticLayout",
    "jmReportSaveBitmap(bitmap, name)",
):
    if token not in html + java:
        raise SystemExit("v209.27 output missing: " + token)

active = re.search(r"function saveFullImage\(\)\{.*?\n\}\nfunction install\(\)\{", html, re.S)
if not active:
    raise SystemExit("v209.27 active save block missing")
for forbidden in ("jmV20926SaveVectorReport", "NativeReportCapture", "PixelCopy"):
    if forbidden in active.group(0):
        raise SystemExit("v209.27 old exporter still active: " + forbidden)

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20927_NATIVE_CANVAS_REPORT_OK")
