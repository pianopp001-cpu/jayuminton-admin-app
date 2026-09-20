#!/usr/bin/env python3
"""v209.33: keep the game-statistics export to ONE file, but make that one
file resist a chat app's forced resize on its own.

User feedback on v209.32: "몇장으로 저장하라는 거야. 한장이면 좋은데" -- the
multi-panel "_당근용_" export from v209.32 technically worked around Carrot
Market's own image-resize step, but the user does not want extra files.
Requirement #2 was explicit about this from the very first request too:
a single PNG. This patch removes the v20932 split entirely (one saved file
again) and instead fixes the one file's own *shape* so a "fit this image
inside my own size limit" resize -- which is what any chat upload step
does, and which we cannot turn off -- shrinks it as little as possible.

Why shape matters here: whatever pixel budget the receiving app resizes
down to, that resize is a single uniform scale factor driven by whichever
of the image's two dimensions is larger. For fixed content (a fixed number
of member cards at a fixed, unchanged per-card pixel size/font size -- we
are not shrinking text, and every member's full history still renders,
nothing is cropped or dropped), the arrangement that minimizes that larger
dimension is the one closest to a square. The previous layout always used
a fixed 4 columns, so a big roster produced an image far taller than it
was wide (extreme portrait) -- exactly the shape a resize step punishes
hardest. This patch tries a small range of column counts (holding the
per-card pixel width, and therefore the exact same on-canvas font size,
completely fixed) and keeps whichever is most square, i.e. minimizes
max(width, height). That is the best a single exported file can do against
a downstream resize we do not control.
"""
from pathlib import Path
import sys

MARKER = "JAYUMINTON_REPORT_SQUARE_LAYOUT_V20933"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v209.33 {label} anchor mismatch: {count}")
    return text.replace(old, new, 1)


def patch_java(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    for prereq in (
        "JAYUMINTON_REPORT_CARROT_CHAT_SPLIT_V20932",
        "private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {",
        "private void jmReportSaveMarketplaceParts(",
        "jmReportSaveMarketplaceParts(bitmap, name, jmLastReportCutLines);",
    ):
        if prereq not in text:
            raise SystemExit("v209.33 prerequisite missing: " + prereq)

    # 1) Undo v20932: back to exactly one saved file, one confirmation toast.
    save_old = (
        "                jmReportSaveBitmap(bitmap, name);\n"
        "                jmReportSaveMarketplaceParts(bitmap, name, jmLastReportCutLines);\n"
        "                runOnUiThread(() -> Toast.makeText(\n"
        "                        MainActivity.this,\n"
        "                        \"고해상도 게임 통계 저장 완료 (당근 채팅용 분할 이미지 함께 저장)\",\n"
        "                        Toast.LENGTH_SHORT\n"
        "                ).show());\n"
    )
    save_new = (
        "                jmReportSaveBitmap(bitmap, name);\n"
        "                runOnUiThread(() -> Toast.makeText(\n"
        "                        MainActivity.this,\n"
        "                        \"고해상도 게임 통계 저장 완료\",\n"
        "                        Toast.LENGTH_SHORT\n"
        "                ).show());\n"
    )
    text = replace_once(text, save_old, save_new, "saveReportJson revert to single save")

    # 2) Remove the now-unused v20932 helper method entirely.
    helper_start_marker = "    private void jmReportSaveMarketplaceParts(\n"
    helper_end_marker = "    public final class NativeCanvasReportBridge {"
    start = text.find(helper_start_marker)
    end = text.find(helper_end_marker)
    if start < 0 or end < 0 or end <= start:
        raise SystemExit("v209.33 jmReportSaveMarketplaceParts removal anchors not found")
    text = text[:start] + text[end:]

    # 3) Remove the v20932 field/constant and the cut-line bookkeeping, and
    #    replace the fixed-4-column layout header with the square-picking one.
    header_old = (
        "    private static final String REPORT_CARROT_CHAT_SPLIT = \"JAYUMINTON_REPORT_CARROT_CHAT_SPLIT_V20932\";\n"
        "    // JAYUMINTON_REPORT_CARROT_CHAT_SPLIT_V20932: safe horizontal cut lines for the last rendered\n"
        "    // report (section-top + every participant-card-row boundary), used\n"
        "    // to split the saved PNG into Carrot-chat-friendly panels without\n"
        "    // ever slicing a card or a line of text.\n"
        "    private int[] jmLastReportCutLines;\n"
        "\n"
        "    private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {\n"
        "        JSONArray members = payload.optJSONArray(\"members\");\n"
        "        if (members == null) members = new JSONArray();\n"
        "\n"
        "        final int width = NATIVE_REPORT_WIDTH;\n"
        "        final int margin = NATIVE_REPORT_MARGIN;\n"
        "        final int gap = NATIVE_REPORT_GAP;\n"
        "        final int columns = NATIVE_REPORT_COLUMNS;\n"
        "        final int cardWidth = (width - margin * 2 - gap * (columns - 1)) / columns;\n"
        "        final int top = 1140;\n"
        "\n"
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
        "        // JAYUMINTON_REPORT_CARROT_CHAT_SPLIT_V20932: 1022 is the fixed top of the green \"참여자 통계\"\n"
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
    header_new = (
        "    private static final String REPORT_SQUARE_LAYOUT = \"" + MARKER + "\";\n"
        "\n"
        "    private Bitmap jmRenderNativeReport(JSONObject payload) throws Exception {\n"
        "        JSONArray members = payload.optJSONArray(\"members\");\n"
        "        if (members == null) members = new JSONArray();\n"
        "\n"
        "        final int margin = NATIVE_REPORT_MARGIN;\n"
        "        final int gap = NATIVE_REPORT_GAP;\n"
        "        final int cardWidth = (NATIVE_REPORT_WIDTH - margin * 2 - gap * (NATIVE_REPORT_COLUMNS - 1)) / NATIVE_REPORT_COLUMNS;\n"
        "        final int top = 1140;\n"
        "        final int memberCount = members.length();\n"
        "\n"
        "        int[] memberCardHeight = new int[memberCount];\n"
        "        for (int i = 0; i < memberCount; i++) {\n"
        "            JSONObject member = members.optJSONObject(i);\n"
        "            if (member == null) member = new JSONObject();\n"
        "            memberCardHeight[i] = jmMeasureNativeReportCard(member, cardWidth);\n"
        "        }\n"
        "\n"
        "        // " + MARKER + ": a chat app's own upload step resizes whatever we\n"
        "        // save to fit its own limit, and that resize is one uniform scale\n"
        "        // driven by the LARGER of the image's width/height. For the exact\n"
        "        // same content at the exact same per-card pixel size (no text is\n"
        "        // shrunk, no member is dropped), the layout closest to a square\n"
        "        // minimizes that larger side, so it survives the resize best. Try a\n"
        "        // small range of column counts and keep whichever is most square.\n"
        "        int columns = NATIVE_REPORT_COLUMNS;\n"
        "        int width = NATIVE_REPORT_WIDTH;\n"
        "        if (memberCount > 0) {\n"
        "            int bestMax = Integer.MAX_VALUE;\n"
        "            for (int candidate = 2; candidate <= 8; candidate++) {\n"
        "                int candidateWidth = margin * 2 + gap * (candidate - 1) + candidate * cardWidth;\n"
        "                int candidateY = top;\n"
        "                for (int rowStart = 0; rowStart < memberCount; rowStart += candidate) {\n"
        "                    int rowEnd = Math.min(memberCount, rowStart + candidate);\n"
        "                    int rowHeight = 0;\n"
        "                    for (int i = rowStart; i < rowEnd; i++) {\n"
        "                        rowHeight = Math.max(rowHeight, memberCardHeight[i]);\n"
        "                    }\n"
        "                    candidateY += rowHeight + gap;\n"
        "                }\n"
        "                int candidateHeight = Math.max(1600, Math.max(top, candidateY) + 150);\n"
        "                int candidateMax = Math.max(candidateWidth, candidateHeight);\n"
        "                if (candidateMax < bestMax) {\n"
        "                    bestMax = candidateMax;\n"
        "                    columns = candidate;\n"
        "                    width = candidateWidth;\n"
        "                }\n"
        "            }\n"
        "        }\n"
        "\n"
        "        int[] cardHeights = new int[memberCount];\n"
        "        int[] cardColumns = new int[memberCount];\n"
        "        int[] cardTops = new int[memberCount];\n"
        "        int y = top;\n"
        "        for (int rowStart = 0; rowStart < memberCount; rowStart += columns) {\n"
        "            int rowEnd = Math.min(memberCount, rowStart + columns);\n"
        "            int rowHeight = 0;\n"
        "            for (int i = rowStart; i < rowEnd; i++) {\n"
        "                rowHeight = Math.max(rowHeight, memberCardHeight[i]);\n"
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
    text = replace_once(text, header_old, header_new, "square-layout header")

    forbidden = [
        "jmReportSaveMarketplaceParts",
        "REPORT_CARROT_CHAT_SPLIT",
        "jmLastReportCutLines",
        "당근용",
    ]
    for needle in forbidden:
        if needle in text:
            raise SystemExit("v209.33 stale v20932 code still present: " + needle)

    required = [
        MARKER,
        "REPORT_SQUARE_LAYOUT",
        "int columns = NATIVE_REPORT_COLUMNS;",
        "int width = NATIVE_REPORT_WIDTH;",
        "candidateMax < bestMax",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit("v209.33 marker missing: " + needle)

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    java_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
    patch_java(java_path)
    print("ADMIN_V20933_REPORT_SQUARE_LAYOUT_SINGLE_FILE_OK")
