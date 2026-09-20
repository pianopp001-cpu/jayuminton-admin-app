#!/usr/bin/env python3
"""Polish the native Canvas report for sharper, larger, cleaner marketplace readability."""

from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
java = java_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_NATIVE_CANVAS_POLISH_V20928"

if MARKER in java:
    print("ADMIN_V20928_NATIVE_CANVAS_POLISH_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_NATIVE_CANVAS_REPORT_V20927",
    "private static final int NATIVE_REPORT_WIDTH = 2800;",
    "private static final int NATIVE_REPORT_COLUMNS = 4;",
    "private Bitmap jmRenderNativeReport(JSONObject payload)",
):
    if token not in java:
        raise SystemExit("v209.28 prerequisite missing: " + token)

replacements = {
    "    private static final int NATIVE_REPORT_WIDTH = 2800;\n"
    "    private static final int NATIVE_REPORT_COLUMNS = 4;\n"
    "    private static final int NATIVE_REPORT_MARGIN = 44;\n"
    "    private static final int NATIVE_REPORT_GAP = 20;":
    "    // " + MARKER + "\n"
    "    private static final int NATIVE_REPORT_WIDTH = 3800;\n"
    "    private static final int NATIVE_REPORT_COLUMNS = 3;\n"
    "    private static final int NATIVE_REPORT_MARGIN = 64;\n"
    "    private static final int NATIVE_REPORT_GAP = 30;",

    "        paint.setColor(color);\n"
    "        paint.setTextSize(size);\n"
    "        paint.setTypeface(Typeface.create(\"sans-serif\", bold ? Typeface.BOLD : Typeface.NORMAL));":
    "        paint.setColor(color);\n"
    "        paint.setTextSize(size);\n"
    "        paint.setDither(true);\n"
    "        paint.setHinting(Paint.HINTING_ON);\n"
    "        paint.setTypeface(Typeface.create(\"sans-serif\", bold ? Typeface.BOLD : Typeface.NORMAL));",

    "        final int inner = cardWidth - 44;\n"
    "        TextPaint namePaint = jmReportTextPaint(40f, Color.rgb(10, 39, 52), true);\n"
    "        TextPaint partnerPaint = jmReportTextPaint(32f, Color.rgb(10, 54, 76), false);\n"
    "        StaticLayout name = jmReportLayout(jmReportSafe(member, \"name\", \"-\"), namePaint, Math.max(120, inner - 150), 1.0f);\n"
    "        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.05f);\n"
    "        int nameHeight = Math.max(48, name.getHeight());\n"
    "        return 24 + nameHeight + 42 + 40 + partners.getHeight() + 30;":
    "        final int inner = cardWidth - 72;\n"
    "        TextPaint namePaint = jmReportTextPaint(58f, Color.rgb(7, 31, 43), true);\n"
    "        TextPaint partnerPaint = jmReportTextPaint(44f, Color.rgb(8, 49, 70), true);\n"
    "        StaticLayout name = jmReportLayout(jmReportSafe(member, \"name\", \"-\"), namePaint, Math.max(180, inner - 250), 1.0f);\n"
    "        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.12f);\n"
    "        int nameHeight = Math.max(72, name.getHeight());\n"
    "        return 36 + nameHeight + 66 + 58 + partners.getHeight() + 44;",

    "        stroke.setStrokeWidth(2f);\n"
    "        RectF box = new RectF(x, y, x + cardWidth, y + cardHeight);\n"
    "        canvas.drawRoundRect(box, 18f, 18f, fill);\n"
    "        canvas.drawRoundRect(box, 18f, 18f, stroke);":
    "        stroke.setStrokeWidth(3f);\n"
    "        RectF box = new RectF(x, y, x + cardWidth, y + cardHeight);\n"
    "        canvas.drawRoundRect(box, 26f, 26f, fill);\n"
    "        canvas.drawRoundRect(box, 26f, 26f, stroke);",

    "        final float left = x + 22f;\n"
    "        final int inner = cardWidth - 44;\n"
    "        TextPaint namePaint = jmReportTextPaint(40f, Color.rgb(10, 39, 52), true);\n"
    "        TextPaint gamesPaint = jmReportTextPaint(34f, Color.rgb(0, 143, 99), true);\n"
    "        TextPaint metaPaint = jmReportTextPaint(27f, Color.rgb(50, 81, 92), true);\n"
    "        TextPaint labelPaint = jmReportTextPaint(26f, Color.rgb(47, 91, 105), true);\n"
    "        TextPaint partnerPaint = jmReportTextPaint(32f, Color.rgb(10, 54, 76), false);":
    "        final float left = x + 36f;\n"
    "        final int inner = cardWidth - 72;\n"
    "        TextPaint namePaint = jmReportTextPaint(58f, Color.rgb(7, 31, 43), true);\n"
    "        TextPaint gamesPaint = jmReportTextPaint(48f, Color.rgb(0, 139, 96), true);\n"
    "        TextPaint metaPaint = jmReportTextPaint(38f, Color.rgb(43, 71, 82), true);\n"
    "        TextPaint labelPaint = jmReportTextPaint(35f, Color.rgb(39, 82, 95), true);\n"
    "        TextPaint partnerPaint = jmReportTextPaint(44f, Color.rgb(8, 49, 70), true);",

    "        StaticLayout name = jmReportLayout(jmReportSafe(member, \"name\", \"-\"), namePaint, Math.max(120, inner - 150), 1.0f);\n"
    "        int nameHeight = Math.max(48, name.getHeight());\n"
    "        jmDrawStaticLayout(canvas, name, left, y + 20f);":
    "        StaticLayout name = jmReportLayout(jmReportSafe(member, \"name\", \"-\"), namePaint, Math.max(180, inner - 250), 1.0f);\n"
    "        int nameHeight = Math.max(72, name.getHeight());\n"
    "        jmDrawStaticLayout(canvas, name, left, y + 28f);",

    "        float gamesWidth = gamesPaint.measureText(games);\n"
    "        canvas.drawText(games, x + cardWidth - 22f - gamesWidth, y + 20f - gamesPaint.ascent(), gamesPaint);":
    "        float gamesWidth = gamesPaint.measureText(games);\n"
    "        Paint gameBadge = jmReportPaint(Color.rgb(231, 249, 243), Paint.Style.FILL);\n"
    "        float badgeRight = x + cardWidth - 30f;\n"
    "        RectF gameBox = new RectF(badgeRight - gamesWidth - 42f, y + 24f, badgeRight, y + 88f);\n"
    "        canvas.drawRoundRect(gameBox, 18f, 18f, gameBadge);\n"
    "        canvas.drawText(games, badgeRight - gamesWidth - 21f, y + 24f - gamesPaint.ascent(), gamesPaint);",

    "        float metaY = y + 24f + nameHeight + 28f;":
    "        float metaY = y + 36f + nameHeight + 38f;",

    "        float dividerY = metaY + 18f;":
    "        float dividerY = metaY + 26f;",

    "        divider.setStrokeWidth(2f);\n"
    "        canvas.drawLine(left, dividerY, x + cardWidth - 22f, dividerY, divider);":
    "        divider.setStrokeWidth(3f);\n"
    "        canvas.drawLine(left, dividerY, x + cardWidth - 36f, dividerY, divider);",

    "        float labelY = dividerY + 35f;":
    "        float labelY = dividerY + 48f;",

    "        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.05f);\n"
    "        jmDrawStaticLayout(canvas, partners, left, labelY + 12f);":
    "        StaticLayout partners = jmReportLayout(jmReportPartners(member), partnerPaint, inner, 1.12f);\n"
    "        jmDrawStaticLayout(canvas, partners, left, labelY + 18f);",

    "        final int top = 300;":
    "        final int top = 410;",

    "        Paint headerBg = jmReportPaint(Color.rgb(232, 251, 247), Paint.Style.FILL);\n"
    "        canvas.drawRect(0, 0, width, 220, headerBg);\n"
    "        Paint band = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);\n"
    "        canvas.drawRect(0, 220, width, 72, band);\n"
    "\n"
    "        TextPaint title = jmReportTextPaint(56f, Color.rgb(8, 47, 60), true);\n"
    "        TextPaint subtitle = jmReportTextPaint(34f, Color.rgb(10, 83, 96), true);\n"
    "        TextPaint summary = jmReportTextPaint(29f, Color.rgb(66, 103, 115), true);\n"
    "        TextPaint section = jmReportTextPaint(34f, Color.WHITE, true);":
    "        Paint headerBg = jmReportPaint(Color.rgb(236, 252, 248), Paint.Style.FILL);\n"
    "        canvas.drawRect(0, 0, width, 305, headerBg);\n"
    "        Paint band = jmReportPaint(Color.rgb(0, 126, 104), Paint.Style.FILL);\n"
    "        canvas.drawRect(0, 305, width, 92, band);\n"
    "\n"
    "        TextPaint title = jmReportTextPaint(84f, Color.rgb(7, 42, 55), true);\n"
    "        TextPaint subtitle = jmReportTextPaint(52f, Color.rgb(9, 83, 96), true);\n"
    "        TextPaint summary = jmReportTextPaint(40f, Color.rgb(57, 91, 103), true);\n"
    "        TextPaint section = jmReportTextPaint(48f, Color.WHITE, true);",

    "        canvas.drawText(titleText, (width - titleW) / 2f, 72f, title);\n"
    "        canvas.drawText(subText, (width - subW) / 2f, 120f, subtitle);":
    "        canvas.drawText(titleText, (width - titleW) / 2f, 106f, title);\n"
    "        canvas.drawText(subText, (width - subW) / 2f, 176f, subtitle);",

    "        canvas.drawText(summaryText, Math.max(30f, (width - sumW) / 2f), 174f, summary);\n"
    "        canvas.drawText(\"참여자 통계\", 34f, 267f, section);":
    "        canvas.drawText(summaryText, Math.max(48f, (width - sumW) / 2f), 244f, summary);\n"
    "        canvas.drawText(\"참여자 통계\", 54f, 366f, section);",

    "        canvas.drawRect(0, height - 88, width, height, footerBg);\n"
    "        TextPaint footer = jmReportTextPaint(23f, Color.rgb(75, 104, 113), true);":
    "        canvas.drawRect(0, height - 112, width, height, footerBg);\n"
    "        TextPaint footer = jmReportTextPaint(30f, Color.rgb(67, 96, 107), true);",

    "        canvas.drawText(footerText, (width - footerW) / 2f, height - 38f, footer);":
    "        canvas.drawText(footerText, (width - footerW) / 2f, height - 48f, footer);",
}

for old, new in replacements.items():
    if old not in java:
        raise SystemExit("v209.28 anchor missing:\n" + old[:160])
    java = java.replace(old, new, 1)

for token in (
    MARKER,
    "NATIVE_REPORT_WIDTH = 3800",
    "NATIVE_REPORT_COLUMNS = 3",
    "jmReportTextPaint(58f",
    "jmReportTextPaint(44f",
    "gameBadge",
    "paint.setHinting(Paint.HINTING_ON)",
    "final int top = 410",
):
    if token not in java:
        raise SystemExit("v209.28 output missing: " + token)

java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20928_NATIVE_CANVAS_POLISH_OK")
