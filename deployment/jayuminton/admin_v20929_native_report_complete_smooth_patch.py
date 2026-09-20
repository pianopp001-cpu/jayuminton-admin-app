#!/usr/bin/env python3
"""Restore summary/highlights and supersample native Canvas cards for smoother text."""

from pathlib import Path
import re
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_NATIVE_REPORT_COMPLETE_SMOOTH_V20929"

if MARKER in html and MARKER in java:
    print("ADMIN_V20929_NATIVE_REPORT_COMPLETE_SMOOTH_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_NATIVE_CANVAS_REPORT_V20927",
    "window.jmV20927SaveNativeCanvasReport",
):
    if token not in html:
        raise SystemExit("v209.29 HTML prerequisite missing: " + token)

for token in (
    "JAYUMINTON_NATIVE_CANVAS_REPORT_V20927",
    "JAYUMINTON_NATIVE_CANVAS_POLISH_V20928",
    "NATIVE_REPORT_WIDTH = 3800",
    "NATIVE_REPORT_COLUMNS = 3",
    "private void jmDrawNativeReportCard",
    "private Bitmap jmRenderNativeReport(JSONObject payload)",
):
    if token not in java:
        raise SystemExit("v209.29 Java prerequisite missing: " + token)

# Stronger text flags / Korean-friendly medium face.
old_paint = '''        TextPaint paint = new TextPaint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
        paint.setColor(color);
        paint.setTextSize(size);
        paint.setDither(true);
        paint.setHinting(Paint.HINTING_ON);
        paint.setTypeface(Typeface.create("sans-serif", bold ? Typeface.BOLD : Typeface.NORMAL));
        return paint;'''
new_paint = '''        TextPaint paint = new TextPaint(
                Paint.ANTI_ALIAS_FLAG |
                Paint.SUBPIXEL_TEXT_FLAG |
                Paint.LINEAR_TEXT_FLAG |
                Paint.DITHER_FLAG
        );
        paint.setColor(color);
        paint.setTextSize(size);
        paint.setDither(true);
        paint.setSubpixelText(true);
        paint.setLinearText(true);
        paint.setHinting(Paint.HINTING_ON);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) paint.setElegantTextHeight(true);
        paint.setTypeface(Typeface.create(bold ? "sans-serif-medium" : "sans-serif", bold ? Typeface.BOLD : Typeface.NORMAL));
        return paint;'''
if java.count(old_paint) != 1:
    raise SystemExit("v209.29 text paint anchor mismatch: " + str(java.count(old_paint)))
java = java.replace(old_paint, new_paint, 1)

# Supersample each participant card independently (bounded memory), then filtered downsample.
anchor = '''    private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {'''
smooth_method = r'''
    // JAYUMINTON_NATIVE_REPORT_COMPLETE_SMOOTH_V20929
    private void jmDrawNativeReportCardSmooth(
            Canvas target,
            JSONObject member,
            float x,
            float y,
            int cardWidth,
            int cardHeight
    ) {
        final float scale = 2.0f;
        Bitmap hi = null;
        try {
            hi = Bitmap.createBitmap(
                    Math.max(1, Math.round(cardWidth * scale)),
                    Math.max(1, Math.round(cardHeight * scale)),
                    Bitmap.Config.ARGB_8888
            );
            Canvas hc = new Canvas(hi);
            hc.scale(scale, scale);
            jmDrawNativeReportCard(hc, member, 0f, 0f, cardWidth, cardHeight);
            Paint down = new Paint(
                    Paint.ANTI_ALIAS_FLAG |
                    Paint.FILTER_BITMAP_FLAG |
                    Paint.DITHER_FLAG
            );
            target.drawBitmap(
                    hi,
                    null,
                    new RectF(x, y, x + cardWidth, y + cardHeight),
                    down
            );
        } finally {
            if (hi != null && !hi.isRecycled()) hi.recycle();
        }
    }

    private void jmDrawReportMetricCard(
            Canvas canvas,
            float left,
            float top,
            float width,
            String label,
            String value,
            int accent
    ) {
        Paint bg = jmReportPaint(Color.WHITE, Paint.Style.FILL);
        Paint border = jmReportPaint(Color.rgb(207, 228, 224), Paint.Style.STROKE);
        border.setStrokeWidth(3f);
        RectF box = new RectF(left, top, left + width, top + 150f);
        canvas.drawRoundRect(box, 24f, 24f, bg);
        canvas.drawRoundRect(box, 24f, 24f, border);
        TextPaint lp = jmReportTextPaint(31f, Color.rgb(74, 100, 109), true);
        TextPaint vp = jmReportTextPaint(52f, accent, true);
        canvas.drawText(label, left + 28f, top + 46f, lp);
        canvas.drawText(value, left + 28f, top + 112f, vp);
    }

    private void jmDrawReportHighlightCard(
            Canvas canvas,
            float left,
            float top,
            float width,
            String label,
            String main,
            String sub
    ) {
        Paint bg = jmReportPaint(Color.rgb(249, 255, 252), Paint.Style.FILL);
        Paint border = jmReportPaint(Color.rgb(211, 235, 224), Paint.Style.STROKE);
        border.setStrokeWidth(3f);
        RectF box = new RectF(left, top, left + width, top + 190f);
        canvas.drawRoundRect(box, 26f, 26f, bg);
        canvas.drawRoundRect(box, 26f, 26f, border);
        TextPaint lp = jmReportTextPaint(31f, Color.rgb(22, 137, 165), true);
        TextPaint mp = jmReportTextPaint(45f, Color.rgb(15, 53, 72), true);
        TextPaint sp = jmReportTextPaint(29f, Color.rgb(18, 145, 99), true);
        canvas.drawText(label, left + 30f, top + 48f, lp);
        StaticLayout mainLayout = jmReportLayout(main, mp, Math.max(1, (int) width - 60), 1.0f);
        jmDrawStaticLayout(canvas, mainLayout, left + 30f, top + 64f);
        canvas.drawText(sub, left + 30f, top + 166f, sp);
    }

'''
if java.count(anchor) != 1:
    raise SystemExit("v209.29 render anchor mismatch: " + str(java.count(anchor)))
java = java.replace(anchor, smooth_method + anchor, 1)

# Shift participants down to make room for explicit summary report cards.
if "        final int top = 410;" not in java:
    raise SystemExit("v209.29 top anchor missing")
java = java.replace("        final int top = 410;", "        final int top = 650;", 1)

# Reserve bottom room for highlights.
old_bottom = '''        int height = Math.max(900, contentBottom + 120);'''
new_bottom = '''        int height = Math.max(1200, contentBottom + 430);'''
if java.count(old_bottom) != 1:
    raise SystemExit("v209.29 height anchor mismatch: " + str(java.count(old_bottom)))
java = java.replace(old_bottom, new_bottom, 1)

# Header height/band, explicit summary section title + metric cards.
old_header = '''        Paint headerBg = jmReportPaint(Color.rgb(236, 252, 248), Paint.Style.FILL);
        canvas.drawRect(0, 0, width, 305, headerBg);
        Paint band = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);
        canvas.drawRect(0, 305, width, 92, band);'''
new_header = '''        Paint headerBg = jmReportPaint(Color.rgb(236, 252, 248), Paint.Style.FILL);
        canvas.drawRect(0, 0, width, 305, headerBg);
        Paint band = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);
        canvas.drawRect(0, 305, width, 92, band);'''
# structurally unchanged; marker comes from helper.
if java.count(old_header) != 1:
    raise SystemExit("v209.29 header anchor mismatch")

old_section_line = '''        canvas.drawText(summaryText, Math.max(48f, (width - sumW) / 2f), 244f, summary);
        canvas.drawText("참여자 통계", 54f, 366f, section);'''
new_section_line = '''        canvas.drawText(summaryText, Math.max(48f, (width - sumW) / 2f), 244f, summary);

        TextPaint summaryTitle = jmReportTextPaint(38f, Color.rgb(23, 71, 84), true);
        canvas.drawText("요약 리포트", 64f, 445f, summaryTitle);
        float metricGap = 26f;
        float metricWidth = (width - 128f - metricGap * 3f) / 4f;
        int attendeeCount = Math.max(0, payload.optInt("attendees", totalMembers));
        float avgGames = (float) payload.optDouble("avgGames", attendeeCount > 0 ? ((double) totalGames / attendeeCount) : 0.0);
        String usedCourts = jmReportSafe(payload, "usedCourts", "-");
        jmDrawReportMetricCard(canvas, 64f, 468f, metricWidth, "총 참석", attendeeCount + "명", Color.rgb(12, 116, 154));
        jmDrawReportMetricCard(canvas, 64f + (metricWidth + metricGap), 468f, metricWidth, "총 경기", totalMatches + "게임", Color.rgb(0, 143, 99));
        jmDrawReportMetricCard(canvas, 64f + (metricWidth + metricGap) * 2f, 468f, metricWidth, "사용 코트", usedCourts + "면", Color.rgb(43, 97, 160));
        jmDrawReportMetricCard(canvas, 64f + (metricWidth + metricGap) * 3f, 468f, metricWidth, "평균 게임", String.format(Locale.KOREA, "%.1f회", avgGames), Color.rgb(135, 92, 20));

        canvas.drawText("참여자 통계", 54f, 626f, section);'''
if java.count(old_section_line) != 1:
    raise SystemExit("v209.29 section insertion anchor mismatch: " + str(java.count(old_section_line)))
java = java.replace(old_section_line, new_section_line, 1)

# Use smooth supersampled card path.
old_draw = '''            jmDrawNativeReportCard(canvas, member, x, cardTops[i], cardWidth, cardHeights[i]);'''
new_draw = '''            jmDrawNativeReportCardSmooth(canvas, member, x, cardTops[i], cardWidth, cardHeights[i]);'''
if java.count(old_draw) != 1:
    raise SystemExit("v209.29 participant draw anchor mismatch: " + str(java.count(old_draw)))
java = java.replace(old_draw, new_draw, 1)

# Insert highlights immediately after participant cards and before footer.
old_footer_anchor = '''        Paint footerBg = jmReportPaint(Color.rgb(232, 251, 247), Paint.Style.FILL);'''
highlight_block = r'''        float hiTop = contentBottom + 42f;
        Paint hiBand = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);
        canvas.drawRoundRect(new RectF(64f, hiTop, width - 64f, hiTop + 76f), 20f, 20f, hiBand);
        TextPaint hiTitle = jmReportTextPaint(42f, Color.WHITE, true);
        canvas.drawText("오늘의 하이라이트", 94f, hiTop + 52f, hiTitle);

        float hiGap = 28f;
        float hiWidth = (width - 128f - hiGap * 2f) / 3f;
        String maxName = jmReportSafe(payload, "maxName", "-");
        int maxGames = Math.max(0, payload.optInt("maxGames", 0));
        String longestName = jmReportSafe(payload, "longestName", "-");
        String longestDuration = jmReportSafe(payload, "longestDuration", "-");
        String pairMain = jmReportSafe(payload, "bestPair", "-");
        int pairCount = Math.max(0, payload.optInt("bestPairCount", 0));
        jmDrawReportHighlightCard(canvas, 64f, hiTop + 96f, hiWidth, "최다 경기", maxName, maxGames > 0 ? maxGames + "회" : "-");
        jmDrawReportHighlightCard(canvas, 64f + hiWidth + hiGap, hiTop + 96f, hiWidth, "최장 참여", longestName, longestDuration);
        jmDrawReportHighlightCard(canvas, 64f + (hiWidth + hiGap) * 2f, hiTop + 96f, hiWidth, "인기 파트너", pairMain, pairCount > 0 ? pairCount + "회" : "-");

'''
if java.count(old_footer_anchor) != 1:
    raise SystemExit("v209.29 footer anchor mismatch: " + str(java.count(old_footer_anchor)))
java = java.replace(old_footer_anchor, highlight_block + old_footer_anchor, 1)

# Footer must sit at true bottom after highlights.
# Existing footer already uses height-112.

# Extend JS payload with summary/highlight fields from original data.
old_payload_start = '''  function payload(){
    var a=rows(),total=a.reduce(function(n,r){return n+Math.max(0,Number(r.games||0));},0);
    return {
      title:'자유민턴',
      subtitle:'오늘의 게임 통계',
      totalGames:total,
      totalMatches:Math.max(0,Math.round(total/4)),
      members:a.map(function(r){'''
new_payload_start = r'''  function payload(){
    var a=rows(),total=a.reduce(function(n,r){return n+Math.max(0,Number(r.games||0));},0);
    var attendees=a.filter(function(r){return r.arrivedAt||Number(r.games||0)>0;});
    var max=a.slice().sort(function(x,y){return Number(y.games||0)-Number(x.games||0);})[0]||null;
    var now=Date.now(),longest=null,longestMs=-1;
    a.forEach(function(r){
      var s=r.arrivedAt?new Date(r.arrivedAt):null;
      if(!s||Number.isNaN(s.getTime()))return;
      var e=r.departedAt?new Date(r.departedAt):new Date(now);
      if(Number.isNaN(e.getTime()))return;
      var ms=e.getTime()-s.getTime();
      if(ms>longestMs){longest=r;longestMs=ms;}
    });
    var seen={},best=null;
    a.forEach(function(r){
      (Array.isArray(r.partners)?r.partners:[]).forEach(function(p){
        var x=String(r.id||r.name||''),y=String(p.id||p.name||'');
        var key=[x,y].sort().join('::');
        if(seen[key])return;seen[key]=1;
        var n=Math.max(0,Number(p.count||0));
        if(!best||n>best.count)best={a:String(r.name||''),b:String(p.name||''),count:n};
      });
    });
    function duration(ms){
      if(!(ms>=0))return '-';
      var m=Math.round(ms/60000),h=Math.floor(m/60),mm=m%60;
      return h>0?(h+'시간 '+mm+'분'):(mm+'분');
    }
    var oldStats=null;
    try{
      if(window.__JAYUMINTON_GAME_REPORT_V20895__&&typeof window.__JAYUMINTON_GAME_REPORT_V20895__.stats==='function'){
        oldStats=window.__JAYUMINTON_GAME_REPORT_V20895__.stats(a);
      }
    }catch(_){}
    return {
      title:'자유민턴',
      subtitle:'오늘의 게임 통계',
      totalGames:total,
      totalMatches:Math.max(0,Math.round(total/4)),
      attendees:attendees.length,
      avgGames:attendees.length?total/attendees.length:0,
      usedCourts:oldStats&&oldStats.courts!=null?String(oldStats.courts):'-',
      maxName:max?String(max.name||''):'-',
      maxGames:max?Math.max(0,Number(max.games||0)):0,
      longestName:longest?String(longest.name||''):'-',
      longestDuration:duration(longestMs),
      bestPair:best?(best.a+' · '+best.b):'-',
      bestPairCount:best?best.count:0,
      members:a.map(function(r){'''
if html.count(old_payload_start) != 1:
    raise SystemExit("v209.29 payload anchor mismatch: " + str(html.count(old_payload_start)))
html = html.replace(old_payload_start, new_payload_start, 1)

for token in (
    MARKER,
    "jmDrawNativeReportCardSmooth",
    "Paint.FILTER_BITMAP_FLAG",
    '"요약 리포트"',
    '"오늘의 하이라이트"',
    "attendees:attendees.length",
    "bestPairCount",
    "paint.setLinearText(true)",
):
    if token not in java + html:
        raise SystemExit("v209.29 output missing: " + token)

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20929_NATIVE_REPORT_COMPLETE_SMOOTH_OK")
