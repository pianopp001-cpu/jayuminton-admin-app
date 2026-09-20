#!/usr/bin/env python3
"""v209.32: split the saved game-statistics PNG into chat-upload-safe panels.

User-reported symptom (still present after v209.31's save-race fix):
"저장된 이미지를 확대하는 것은 해상도가 좋아. 그런데 당근이라는 채팅에 업로드를
하면 저렇게 되는 거라고" -- the saved file itself is sharp at full resolution;
the text only turns rough/blocky *after* the file is uploaded inside the
당근마켓 (Carrot Market) chat.

Root cause: the native-Canvas renderer (v20927-v20931) always saves exactly
ONE very tall PNG -- 4200px wide, and easily 10000px+ tall once every
member's full expanded history is included (that height is exactly what
requirement #2/#5 demanded, so it must stay). Third-party chat upload
pipelines (Carrot's included) resize an image to fit within a fairly small
max dimension before sending it over the wire. For a normal-shaped photo
that costs little detail, but for an unusually TALL image the longest side
is enormous, so the resize ratio applied is brutal -- e.g. a 4200x12000
image squeezed to fit inside a 2048px max side is shrunk to ~17% of its
original size, and 76px-tall Korean glyphs collapse to ~13px and fall
apart. This has nothing to do with our own PNG encoding (still lossless,
still 4200px, unchanged) -- it is Carrot's own resize step, which we cannot
turn off, only work around.

Mitigation (same idea v20914 already used for the old PixelCopy capture,
but that helper was dead code by v20915 and was never reattached to the
v20927+ native-Canvas save path -- this patch reintroduces it correctly):
alongside the single full-history PNG, also save the same image cut into
several panels close to a normal portrait-photo aspect ratio (~4:5). Each
panel is a lossless crop of the exact same high-resolution pixels -- no
re-render, no re-encode of existing pixels, no quality loss -- so when the
admin instead uploads one *panel* into the Carrot chat, its longest side is
much shorter and survives Carrot's own resize far more readably. Panels are
only ever cut at a card-row boundary (or right above the participant grid),
recorded while the report is laid out, so a member's card or a line of text
is never sliced across two images.
"""
from pathlib import Path
import sys

MARKER = "JAYUMINTON_REPORT_CARROT_CHAT_SPLIT_V20932"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v209.32 {label} anchor mismatch: {count}")
    return text.replace(old, new, 1)


def patch_java(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    for prereq in (
        "JAYUMINTON_NATIVE_CANVAS_REPORT_V20927",
        "NATIVE_REPORT_RENDERER_MARKER_V20930",
        "private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {",
        "public final class NativeCanvasReportBridge",
        "private void jmReportSaveBitmap(Bitmap bitmap, String requested) throws Exception {",
    ):
        if prereq not in text:
            raise SystemExit("v209.32 prerequisite missing: " + prereq)
    if "jmReportSaveMarketplaceParts" in text:
        raise SystemExit("v209.32 unexpected pre-existing jmReportSaveMarketplaceParts")

    # 1) Remember a field for the safe horizontal cut lines computed while the
    #    report is laid out (row boundaries -- never through a card).
    field_anchor = (
        "    private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {"
    )
    field_new = (
        "    private static final String REPORT_CARROT_CHAT_SPLIT = \"" + MARKER + "\";\n"
        "    // " + MARKER + ": safe horizontal cut lines for the last rendered\n"
        "    // report (section-top + every participant-card-row boundary), used\n"
        "    // to split the saved PNG into Carrot-chat-friendly panels without\n"
        "    // ever slicing a card or a line of text.\n"
        "    private int[] jmLastReportCutLines;\n\n"
        + field_anchor
    )
    text = replace_once(text, field_anchor, field_new, "jmRenderNativeReport signature")

    # 2) Collect row-bottom boundaries while the grid is laid out, then stash
    #    them (plus the fixed top of the participant-grid header band) into
    #    jmLastReportCutLines just before the bitmap is returned.
    layout_old = (
        "        int[] cardHeights = new int[members.length()];\n"
        "        int[] cardColumns = new int[members.length()];\n"
        "        int[] cardTops = new int[members.length()];\n"
        "        int y = top;\n"
        "        for (int rowStart = 0; rowStart < members.length(); rowStart += columns) {\n"
        "            int rowHeight = 0;\n"
        "            int rowEnd = Math.min(members.length(), rowStart + columns);\n"
        "            for (int i = rowStart; i < rowEnd; i++) {\n"
        "                JSONObject member = members.optJSONObject(i);\n"
        "                if (member == null) member = new JSONObject();\n"
        "                rowHeight = Math.max(rowHeight, jmMeasureNativeReportCard(member, cardWidth));\n"
        "            }\n"
        "            for (int i = rowStart; i < rowEnd; i++) {\n"
        "                cardHeights[i] = rowHeight;\n"
        "                cardColumns[i] = i - rowStart;\n"
        "                cardTops[i] = y;\n"
        "            }\n"
        "            y += rowHeight + gap;\n"
        "        }\n"
        "\n"
        "        int contentBottom = Math.max(top, y);\n"
        "        int height = Math.max(1600, contentBottom + 150);\n"
    )
    layout_new = (
        "        int[] cardHeights = new int[members.length()];\n"
        "        int[] cardColumns = new int[members.length()];\n"
        "        int[] cardTops = new int[members.length()];\n"
        "        java.util.List<Integer> jmRowBottoms = new java.util.ArrayList<>();\n"
        "        int y = top;\n"
        "        for (int rowStart = 0; rowStart < members.length(); rowStart += columns) {\n"
        "            int rowHeight = 0;\n"
        "            int rowEnd = Math.min(members.length(), rowStart + columns);\n"
        "            for (int i = rowStart; i < rowEnd; i++) {\n"
        "                JSONObject member = members.optJSONObject(i);\n"
        "                if (member == null) member = new JSONObject();\n"
        "                rowHeight = Math.max(rowHeight, jmMeasureNativeReportCard(member, cardWidth));\n"
        "            }\n"
        "            for (int i = rowStart; i < rowEnd; i++) {\n"
        "                cardHeights[i] = rowHeight;\n"
        "                cardColumns[i] = i - rowStart;\n"
        "                cardTops[i] = y;\n"
        "            }\n"
        "            y += rowHeight + gap;\n"
        "            jmRowBottoms.add(y - gap);\n"
        "        }\n"
        "\n"
        "        int contentBottom = Math.max(top, y);\n"
        "        int height = Math.max(1600, contentBottom + 150);\n"
        "        // " + MARKER + ": 1022 is the fixed top of the green \"참여자 통계\"\n"
        "        // band drawn below, i.e. the boundary right before the card grid\n"
        "        // starts; every other entry is a row bottom, so no cut ever lands\n"
        "        // inside a card or a line of text.\n"
        "        int[] jmCutLines = new int[jmRowBottoms.size() + 1];\n"
        "        jmCutLines[0] = 1022;\n"
        "        for (int jmCutI = 0; jmCutI < jmRowBottoms.size(); jmCutI++) {\n"
        "            jmCutLines[jmCutI + 1] = jmRowBottoms.get(jmCutI);\n"
        "        }\n"
        "        jmLastReportCutLines = jmCutLines;\n"
    )
    text = replace_once(text, layout_old, layout_new, "card layout loop")

    # 3) New helper: crop the already-rendered, already-lossless bitmap into
    #    ~4:5 panels, cutting only at the safe lines recorded above.
    helper_anchor = "    public final class NativeCanvasReportBridge {"
    helper = (
        "    private void jmReportSaveMarketplaceParts(\n"
        "            Bitmap full,\n"
        "            String requestedName,\n"
        "            int[] safeCuts\n"
        "    ) throws Exception {\n"
        "        if (full == null || full.isRecycled()) return;\n"
        "        final int w = full.getWidth();\n"
        "        final int totalH = full.getHeight();\n"
        "        final int targetPanelHeight = Math.max(1, Math.round(w * 1.25f));\n"
        "        if (totalH <= targetPanelHeight) return;\n"
        "\n"
        "        java.util.TreeSet<Integer> boundarySet = new java.util.TreeSet<>();\n"
        "        boundarySet.add(0);\n"
        "        boundarySet.add(totalH);\n"
        "        if (safeCuts != null) {\n"
        "            for (int c : safeCuts) {\n"
        "                if (c > 0 && c < totalH) boundarySet.add(c);\n"
        "            }\n"
        "        }\n"
        "        Integer[] bounds = boundarySet.toArray(new Integer[0]);\n"
        "\n"
        "        java.util.List<int[]> panels = new java.util.ArrayList<>();\n"
        "        int panelStart = 0;\n"
        "        int lastFit = 0;\n"
        "        for (int i = 1; i < bounds.length; i++) {\n"
        "            int b = bounds[i];\n"
        "            if (b - panelStart <= targetPanelHeight) {\n"
        "                lastFit = b;\n"
        "                continue;\n"
        "            }\n"
        "            int cut = lastFit > panelStart ? lastFit : b;\n"
        "            panels.add(new int[]{panelStart, cut});\n"
        "            panelStart = cut;\n"
        "            lastFit = cut;\n"
        "            if (b - panelStart <= targetPanelHeight) lastFit = b;\n"
        "        }\n"
        "        panels.add(new int[]{panelStart, totalH});\n"
        "        if (panels.size() <= 1) return;\n"
        "\n"
        "        String base = requestedName == null ? \"자유민턴_게임통계\" : requestedName;\n"
        "        if (base.toLowerCase(Locale.ROOT).endsWith(\".png\")) {\n"
        "            base = base.substring(0, base.length() - 4);\n"
        "        }\n"
        "        int count = panels.size();\n"
        "        for (int p = 0; p < count; p++) {\n"
        "            int panelTop = panels.get(p)[0];\n"
        "            int panelBottom = panels.get(p)[1];\n"
        "            if (panelBottom <= panelTop) continue;\n"
        "            Bitmap panel = Bitmap.createBitmap(full, 0, panelTop, w, panelBottom - panelTop);\n"
        "            try {\n"
        "                jmReportSaveBitmap(panel, base + \"_당근용_\" + (p + 1) + \"-\" + count + \".png\");\n"
        "            } finally {\n"
        "                if (!panel.isRecycled()) panel.recycle();\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "\n"
        + helper_anchor
    )
    text = replace_once(text, helper_anchor, helper, "NativeCanvasReportBridge anchor")

    # 4) Call the new helper right after the existing full-image save, and
    #    make the confirmation toast mention it. bitmap is not recycled until
    #    saveReportJson's own finally block, so it is safe to still read here.
    save_old = (
        "                jmReportSaveBitmap(bitmap, name);\n"
        "                runOnUiThread(() -> Toast.makeText(\n"
        "                        MainActivity.this,\n"
        "                        \"고해상도 게임 통계 저장 완료\",\n"
        "                        Toast.LENGTH_SHORT\n"
        "                ).show());\n"
    )
    save_new = (
        "                jmReportSaveBitmap(bitmap, name);\n"
        "                jmReportSaveMarketplaceParts(bitmap, name, jmLastReportCutLines);\n"
        "                runOnUiThread(() -> Toast.makeText(\n"
        "                        MainActivity.this,\n"
        "                        \"고해상도 게임 통계 저장 완료 (당근 채팅용 분할 이미지 함께 저장)\",\n"
        "                        Toast.LENGTH_SHORT\n"
        "                ).show());\n"
    )
    text = replace_once(text, save_old, save_new, "saveReportJson toast")

    required = [
        MARKER,
        "REPORT_CARROT_CHAT_SPLIT",
        "jmLastReportCutLines",
        "jmReportSaveMarketplaceParts(bitmap, name, jmLastReportCutLines);",
        '"_당근용_"',
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit("v209.32 marker missing: " + needle)

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    java_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
    patch_java(java_path)
    print("ADMIN_V20932_REPORT_CARROT_CHAT_SPLIT_OK")
