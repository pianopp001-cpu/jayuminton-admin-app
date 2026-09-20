#!/usr/bin/env python3
"""v209.30: remove login raw newline tokens and rebuild the one-PNG report for real final-pixel readability."""

from pathlib import Path
import re
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_TOP_SUMMARY_CRISP_REPORT_V20930"
LOGIN_MARKER = "JAYUMINTON_ADMIN_LOGIN_RAW_NEWLINE_FIX_V20930"

if MARKER in java and LOGIN_MARKER in html:
    print("ADMIN_V20930_TOP_SUMMARY_CRISP_REPORT_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_NATIVE_REPORT_COMPLETE_SMOOTH_V20929",
    "window.jmV20927SaveNativeCanvasReport",
):
    if token not in html:
        raise SystemExit("v209.30 HTML prerequisite missing: " + token)

for token in (
    "JAYUMINTON_NATIVE_CANVAS_REPORT_V20927",
    "JAYUMINTON_NATIVE_CANVAS_POLISH_V20928",
    "JAYUMINTON_NATIVE_REPORT_COMPLETE_SMOOTH_V20929",
    "private static final int NATIVE_REPORT_WIDTH = 3800;",
    "private static final int NATIVE_REPORT_COLUMNS = 3;",
    "private Bitmap jmRenderNativeReport(JSONObject payload)",
):
    if token not in java:
        raise SystemExit("v209.30 Java prerequisite missing: " + token)

# ---------------------------------------------------------------------------
# Login: remove the visible raw /n or \\n token from actual text nodes.
# Also remove any already-baked standalone token between tags before runtime.
# ---------------------------------------------------------------------------
html = re.sub(r'(?<=>)\s*(?:/n|\\\\n)\s*(?=<)', '', html)

login_script = r'''
<script id="jmAdminLoginRawNewlineFixV20930">
/* JAYUMINTON_ADMIN_LOGIN_RAW_NEWLINE_FIX_V20930 */
(function(){
  function cleanText(v){
    return String(v == null ? '' : v)
      .replace(/\/n/g, ' ')
      .replace(/\\n/g, ' ');
  }
  function cleanLogin(){
    var box=document.getElementById('adminLoginBox');
    if(!box)return;
    try{
      var walker=document.createTreeWalker(box,NodeFilter.SHOW_TEXT);
      var node;
      while((node=walker.nextNode())){
        var old=String(node.nodeValue||'');
        var next=cleanText(old);
        if(next!==old)node.nodeValue=next;
      }
      box.querySelectorAll('*').forEach(function(el){
        ['placeholder','title','aria-label'].forEach(function(name){
          if(!el.hasAttribute||!el.hasAttribute(name))return;
          var old=String(el.getAttribute(name)||''),next=cleanText(old);
          if(next!==old)el.setAttribute(name,next);
        });
      });
      if(!box.__jmV20930NewlineObserver){
        box.__jmV20930NewlineObserver=new MutationObserver(function(){cleanLogin();});
        box.__jmV20930NewlineObserver.observe(box,{subtree:true,childList:true,characterData:true});
      }
    }catch(_){}
  }
  window.jmV20930CleanAdminLogin=cleanLogin;
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',cleanLogin,{once:true});
  cleanLogin();
  setTimeout(cleanLogin,50);
  setTimeout(cleanLogin,300);
  setTimeout(cleanLogin,1200);
})();
</script>
'''
if LOGIN_MARKER not in html:
    if "</body>" not in html:
        raise SystemExit("v209.30 HTML body close missing")
    html = html.replace("</body>", login_script + "\n</body>", 1)

# ---------------------------------------------------------------------------
# Native text rendering: final pixels only. No card supersample->downsample pass.
# Use a real medium family without synthetic bold and keep Android hinting.
# ---------------------------------------------------------------------------
if "import android.graphics.PaintFlagsDrawFilter;\n" not in java:
    anchor = "import android.graphics.Paint;\n"
    if anchor not in java:
        raise SystemExit("v209.30 Paint import anchor missing")
    java = java.replace(anchor, anchor + "import android.graphics.PaintFlagsDrawFilter;\n", 1)

java = java.replace(
    "    private static final int NATIVE_REPORT_WIDTH = 3800;\n"
    "    private static final int NATIVE_REPORT_COLUMNS = 3;\n"
    "    private static final int NATIVE_REPORT_MARGIN = 64;\n"
    "    private static final int NATIVE_REPORT_GAP = 30;",
    "    // " + MARKER + "\n"
    "    private static final int NATIVE_REPORT_WIDTH = 4200;\n"
    "    private static final int NATIVE_REPORT_COLUMNS = 4;\n"
    "    private static final int NATIVE_REPORT_MARGIN = 72;\n"
    "    private static final int NATIVE_REPORT_GAP = 28;",
    1,
)

paint_pat = re.compile(
    r"    private TextPaint jmReportTextPaint\(float size, int color, boolean bold\) \{.*?\n    \}\n\n    private Paint jmReportPaint",
    re.S,
)
paint_new = r'''    private TextPaint jmReportTextPaint(float size, int color, boolean bold) {
        TextPaint paint = new TextPaint(
                Paint.ANTI_ALIAS_FLAG |
                Paint.SUBPIXEL_TEXT_FLAG |
                Paint.DITHER_FLAG
        );
        paint.setColor(color);
        paint.setTextSize(size);
        paint.setDither(true);
        paint.setSubpixelText(true);
        paint.setLinearText(false);
        paint.setHinting(Paint.HINTING_ON);
        paint.setFakeBoldText(false);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) paint.setElegantTextHeight(true);
        paint.setTypeface(Typeface.create(bold ? "sans-serif-medium" : "sans-serif", Typeface.NORMAL));
        return paint;
    }

    private Paint jmReportPaint'''
java, n = paint_pat.subn(paint_new, java, count=1)
if n != 1:
    raise SystemExit("v209.30 text paint replacement mismatch: " + str(n))

measure_pat = re.compile(
    r"    private int jmMeasureNativeReportCard\(JSONObject member, int cardWidth\) \{.*?\n    \}\n\n    private void jmDrawStaticLayout",
    re.S,
)
measure_new = r'''    private int jmMeasureNativeReportCard(JSONObject member, int cardWidth) {
        final int inner = cardWidth - 76;
        TextPaint namePaint = jmReportTextPaint(76f, Color.rgb(7, 31, 43), true);
        TextPaint partnerPaint = jmReportTextPaint(58f, Color.rgb(8, 49, 70), false);
        StaticLayout name = jmReportLayout(
                jmReportSafe(member, "name", "-"),
                namePaint,
                Math.max(220, inner - 280),
                1.0f
        );
        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.12f);
        int nameHeight = Math.max(90, name.getHeight());
        return 44 + nameHeight + 76 + 66 + partners.getHeight() + 54;
    }

    private void jmDrawStaticLayout'''
java, n = measure_pat.subn(measure_new, java, count=1)
if n != 1:
    raise SystemExit("v209.30 card measure replacement mismatch: " + str(n))

draw_pat = re.compile(
    r"    private void jmDrawNativeReportCard\(Canvas canvas, JSONObject member, float x, float y, int cardWidth, int cardHeight\) \{.*?\n    \}\n\n    private void jmDrawNativeReportCardSmooth",
    re.S,
)
draw_new = r'''    private void jmDrawNativeReportCard(Canvas canvas, JSONObject member, float x, float y, int cardWidth, int cardHeight) {
        Paint fill = jmReportPaint(Color.WHITE, Paint.Style.FILL);
        Paint stroke = jmReportPaint(Color.rgb(194, 218, 224), Paint.Style.STROKE);
        stroke.setStrokeWidth(3f);
        RectF box = new RectF(x, y, x + cardWidth, y + cardHeight);
        canvas.drawRoundRect(box, 26f, 26f, fill);
        canvas.drawRoundRect(box, 26f, 26f, stroke);

        final float left = x + 38f;
        final int inner = cardWidth - 76;
        TextPaint namePaint = jmReportTextPaint(76f, Color.rgb(7, 31, 43), true);
        TextPaint gamesPaint = jmReportTextPaint(64f, Color.rgb(0, 139, 96), true);
        TextPaint metaPaint = jmReportTextPaint(50f, Color.rgb(42, 69, 80), false);
        TextPaint labelPaint = jmReportTextPaint(46f, Color.rgb(35, 78, 92), true);
        TextPaint partnerPaint = jmReportTextPaint(58f, Color.rgb(8, 49, 70), false);

        StaticLayout name = jmReportLayout(
                jmReportSafe(member, "name", "-"),
                namePaint,
                Math.max(220, inner - 280),
                1.0f
        );
        int nameHeight = Math.max(90, name.getHeight());
        jmDrawStaticLayout(canvas, name, left, y + 30f);

        String games = Math.max(0, member.optInt("games", 0)) + "회";
        float gamesWidth = gamesPaint.measureText(games);
        Paint gameBadge = jmReportPaint(Color.rgb(231, 249, 243), Paint.Style.FILL);
        float badgeRight = x + cardWidth - 34f;
        RectF gameBox = new RectF(badgeRight - gamesWidth - 52f, y + 28f, badgeRight, y + 116f);
        canvas.drawRoundRect(gameBox, 20f, 20f, gameBadge);
        canvas.drawText(games, badgeRight - gamesWidth - 26f, y + 28f - gamesPaint.ascent(), gamesPaint);

        float metaY = y + 44f + nameHeight + 44f;
        String arrived = jmReportSafe(member, "arrived", "-");
        String departed = jmReportSafe(member, "departed", "-");
        canvas.drawText("도착 " + arrived + "   ·   귀가 " + departed, left, metaY, metaPaint);

        float dividerY = metaY + 30f;
        Paint divider = jmReportPaint(Color.rgb(220, 233, 237), Paint.Style.STROKE);
        divider.setStrokeWidth(3f);
        canvas.drawLine(left, dividerY, x + cardWidth - 38f, dividerY, divider);

        float labelY = dividerY + 54f;
        canvas.drawText("함께 경기한 사람 전체 " + jmReportPartnerCount(member) + "명", left, labelY, labelPaint);

        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.12f);
        jmDrawStaticLayout(canvas, partners, left, labelY + 22f);
    }

    private void jmDrawNativeReportCardSmooth'''
java, n = draw_pat.subn(draw_new, java, count=1)
if n != 1:
    raise SystemExit("v209.30 card draw replacement mismatch: " + str(n))

metric_pat = re.compile(
    r"    private void jmDrawReportMetricCard\(.*?\n    \}\n\n    private void jmDrawReportHighlightCard",
    re.S,
)
metric_new = r'''    private void jmDrawReportMetricCard(
            Canvas canvas,
            float left,
            float top,
            float width,
            String label,
            String value,
            int accent
    ) {
        Paint bg = jmReportPaint(Color.WHITE, Paint.Style.FILL);
        Paint border = jmReportPaint(Color.rgb(203, 226, 221), Paint.Style.STROKE);
        border.setStrokeWidth(3f);
        RectF box = new RectF(left, top, left + width, top + 188f);
        canvas.drawRoundRect(box, 28f, 28f, bg);
        canvas.drawRoundRect(box, 28f, 28f, border);
        TextPaint lp = jmReportTextPaint(44f, Color.rgb(65, 91, 101), true);
        TextPaint vp = jmReportTextPaint(74f, accent, true);
        canvas.drawText(label, left + 34f, top + 58f, lp);
        canvas.drawText(value, left + 34f, top + 145f, vp);
    }

    private void jmDrawReportHighlightCard'''
java, n = metric_pat.subn(metric_new, java, count=1)
if n != 1:
    raise SystemExit("v209.30 metric replacement mismatch: " + str(n))

highlight_pat = re.compile(
    r"    private void jmDrawReportHighlightCard\(.*?\n    \}\n\n    private Bitmap jmRenderNativeReport",
    re.S,
)
highlight_new = r'''    private void jmDrawReportHighlightCard(
            Canvas canvas,
            float left,
            float top,
            float width,
            String label,
            String main,
            String sub
    ) {
        Paint bg = jmReportPaint(Color.rgb(249, 255, 252), Paint.Style.FILL);
        Paint border = jmReportPaint(Color.rgb(205, 232, 220), Paint.Style.STROKE);
        border.setStrokeWidth(3f);
        RectF box = new RectF(left, top, left + width, top + 236f);
        canvas.drawRoundRect(box, 28f, 28f, bg);
        canvas.drawRoundRect(box, 28f, 28f, border);
        TextPaint lp = jmReportTextPaint(44f, Color.rgb(20, 132, 158), true);
        TextPaint mp = jmReportTextPaint(68f, Color.rgb(12, 47, 65), true);
        TextPaint sp = jmReportTextPaint(40f, Color.rgb(15, 137, 94), true);
        canvas.drawText(label, left + 34f, top + 60f, lp);
        StaticLayout mainLayout = jmReportLayout(main, mp, Math.max(1, (int) width - 68), 1.0f);
        jmDrawStaticLayout(canvas, mainLayout, left + 34f, top + 76f);
        canvas.drawText(sub, left + 34f, top + 205f, sp);
    }

    private Bitmap jmRenderNativeReport'''
java, n = highlight_pat.subn(highlight_new, java, count=1)
if n != 1:
    raise SystemExit("v209.30 highlight replacement mismatch: " + str(n))

render_pat = re.compile(
    r"    private Bitmap jmRenderNativeReport\(JSONObject payload\) throws Exception \{.*?\n    \}\n\n    public final class NativeCanvasReportBridge",
    re.S,
)
render_new = r'''    private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {
        JSONArray members = payload.optJSONArray("members");
        if (members == null) members = new JSONArray();

        final int width = NATIVE_REPORT_WIDTH;
        final int margin = NATIVE_REPORT_MARGIN;
        final int gap = NATIVE_REPORT_GAP;
        final int columns = NATIVE_REPORT_COLUMNS;
        final int cardWidth = (width - margin * 2 - gap * (columns - 1)) / columns;
        final int top = 1140;

        int[] cardHeights = new int[members.length()];
        int[] cardColumns = new int[members.length()];
        int[] cardTops = new int[members.length()];
        int y = top;
        for (int rowStart = 0; rowStart < members.length(); rowStart += columns) {
            int rowHeight = 0;
            int rowEnd = Math.min(members.length(), rowStart + columns);
            for (int i = rowStart; i < rowEnd; i++) {
                JSONObject member = members.optJSONObject(i);
                if (member == null) member = new JSONObject();
                rowHeight = Math.max(rowHeight, jmMeasureNativeReportCard(member, cardWidth));
            }
            for (int i = rowStart; i < rowEnd; i++) {
                cardHeights[i] = rowHeight;
                cardColumns[i] = i - rowStart;
                cardTops[i] = y;
            }
            y += rowHeight + gap;
        }

        int contentBottom = Math.max(top, y);
        int height = Math.max(1600, contentBottom + 150);

        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        bitmap.setHasAlpha(false);
        Canvas canvas = new Canvas(bitmap);
        canvas.setDrawFilter(new PaintFlagsDrawFilter(
                0,
                Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG
        ));
        canvas.drawColor(Color.WHITE);

        Paint headerBg = jmReportPaint(Color.rgb(236, 252, 248), Paint.Style.FILL);
        canvas.drawRect(0, 0, width, 326, headerBg);

        TextPaint title = jmReportTextPaint(112f, Color.rgb(7, 42, 55), true);
        TextPaint subtitle = jmReportTextPaint(70f, Color.rgb(9, 83, 96), true);
        TextPaint summary = jmReportTextPaint(50f, Color.rgb(55, 88, 100), false);
        TextPaint topSection = jmReportTextPaint(62f, Color.rgb(18, 64, 78), true);
        TextPaint whiteSection = jmReportTextPaint(58f, Color.WHITE, true);

        String titleText = jmReportSafe(payload, "title", "자유민턴");
        String subText = jmReportSafe(payload, "subtitle", "오늘의 게임 통계");
        float titleW = title.measureText(titleText);
        float subW = subtitle.measureText(subText);
        canvas.drawText(titleText, (width - titleW) / 2f, 122f, title);
        canvas.drawText(subText, (width - subW) / 2f, 205f, subtitle);

        int totalGames = Math.max(0, payload.optInt("totalGames", 0));
        int totalMembers = members.length();
        int totalMatches = Math.max(0, payload.optInt("totalMatches", Math.round(totalGames / 4f)));
        String summaryText = "참여 " + totalMembers + "명   ·   총 게임수 " + totalGames + "회   ·   경기 " + totalMatches + "게임   ·   모든 함께 경기 이력 포함";
        float sumW = summary.measureText(summaryText);
        canvas.drawText(summaryText, Math.max(48f, (width - sumW) / 2f), 278f, summary);

        // Summary report: large and immediately visible at the very top.
        canvas.drawText("요약 리포트", 72f, 382f, topSection);
        float metricGap = 30f;
        float metricWidth = (width - 144f - metricGap * 3f) / 4f;
        int attendeeCount = Math.max(0, payload.optInt("attendees", totalMembers));
        float avgGames = (float) payload.optDouble(
                "avgGames",
                attendeeCount > 0 ? ((double) totalGames / attendeeCount) : 0.0
        );
        String usedCourts = jmReportSafe(payload, "usedCourts", "-");
        jmDrawReportMetricCard(canvas, 72f, 408f, metricWidth, "총 참석", attendeeCount + "명", Color.rgb(12, 116, 154));
        jmDrawReportMetricCard(canvas, 72f + (metricWidth + metricGap), 408f, metricWidth, "총 경기", totalMatches + "게임", Color.rgb(0, 143, 99));
        jmDrawReportMetricCard(canvas, 72f + (metricWidth + metricGap) * 2f, 408f, metricWidth, "사용 코트", usedCourts + "면", Color.rgb(43, 97, 160));
        jmDrawReportMetricCard(canvas, 72f + (metricWidth + metricGap) * 3f, 408f, metricWidth, "평균 게임", String.format(Locale.KOREA, "%.1f회", avgGames), Color.rgb(135, 92, 20));

        // Highlights are also at the top, directly below the summary.
        float hiBandTop = 632f;
        Paint hiBand = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);
        canvas.drawRoundRect(new RectF(72f, hiBandTop, width - 72f, hiBandTop + 92f), 22f, 22f, hiBand);
        canvas.drawText("오늘의 하이라이트", 108f, hiBandTop + 64f, whiteSection);

        float hiGap = 30f;
        float hiWidth = (width - 144f - hiGap * 2f) / 3f;
        String maxName = jmReportSafe(payload, "maxName", "-");
        int maxGames = Math.max(0, payload.optInt("maxGames", 0));
        String longestName = jmReportSafe(payload, "longestName", "-");
        String longestDuration = jmReportSafe(payload, "longestDuration", "-");
        String pairMain = jmReportSafe(payload, "bestPair", "-");
        int pairCount = Math.max(0, payload.optInt("bestPairCount", 0));
        jmDrawReportHighlightCard(canvas, 72f, 752f, hiWidth, "최다 경기", maxName, maxGames > 0 ? maxGames + "회" : "-");
        jmDrawReportHighlightCard(canvas, 72f + hiWidth + hiGap, 752f, hiWidth, "최장 참여", longestName, longestDuration);
        jmDrawReportHighlightCard(canvas, 72f + (hiWidth + hiGap) * 2f, 752f, hiWidth, "인기 파트너", pairMain, pairCount > 0 ? pairCount + "회" : "-");

        Paint participantBand = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);
        canvas.drawRect(0, 1022f, width, 96f + 1022f, participantBand);
        canvas.drawText("참여자 통계", 72f, 1088f, whiteSection);

        // Draw once at final output pixels. No 2x card render and no downsample.
        for (int i = 0; i < members.length(); i++) {
            JSONObject member = members.optJSONObject(i);
            if (member == null) member = new JSONObject();
            int col = cardColumns[i];
            float x = margin + col * (cardWidth + gap);
            jmDrawNativeReportCard(canvas, member, x, cardTops[i], cardWidth, cardHeights[i]);
        }

        Paint footerBg = jmReportPaint(Color.rgb(236, 252, 248), Paint.Style.FILL);
        canvas.drawRect(0, height - 118, width, height, footerBg);
        TextPaint footer = jmReportTextPaint(34f, Color.rgb(67, 96, 107), false);
        String footerText = "자유민턴 게임 통계 · 최종 픽셀 직접 렌더 " + width + "×" + height;
        float footerW = footer.measureText(footerText);
        canvas.drawText(footerText, (width - footerW) / 2f, height - 48f, footer);
        return bitmap;
    }

    public final class NativeCanvasReportBridge'''
java, n = render_pat.subn(render_new, java, count=1)
if n != 1:
    raise SystemExit("v209.30 native report replacement mismatch: " + str(n))

# ---------------------------------------------------------------------------
# Verification inside the patch itself.
# ---------------------------------------------------------------------------
active_render = re.search(
    r"private Bitmap jmRenderNativeReport\(JSONObject payload\).*?public final class NativeCanvasReportBridge",
    java,
    re.S,
)
if not active_render:
    raise SystemExit("v209.30 active renderer missing")

for forbidden in (
    "jmDrawNativeReportCardSmooth(canvas",
    "hiTop = contentBottom",
):
    if forbidden in active_render.group(0):
        raise SystemExit("v209.30 old resample/bottom-highlight path still active: " + forbidden)

for token in (
    MARKER,
    "NATIVE_REPORT_WIDTH = 4200",
    "NATIVE_REPORT_COLUMNS = 4",
    'canvas.drawText("요약 리포트"',
    'canvas.drawText("오늘의 하이라이트"',
    "jmDrawNativeReportCard(canvas, member",
    "paint.setLinearText(false)",
    'Typeface.create(bold ? "sans-serif-medium" : "sans-serif", Typeface.NORMAL)',
    LOGIN_MARKER,
    "window.jmV20930CleanAdminLogin",
):
    if token not in java + html:
        raise SystemExit("v209.30 output missing: " + token)

# Static visible standalone raw newline tokens must be gone.
if re.search(r'>\s*(?:/n|\\n)\s*<', html):
    raise SystemExit("v209.30 visible raw newline token remains in HTML")

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20930_TOP_SUMMARY_CRISP_REPORT_OK")
