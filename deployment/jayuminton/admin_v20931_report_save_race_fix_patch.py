#!/usr/bin/env python3
"""v209.31: fix the real cause of the persistent blurry/broken game-statistics PNG.

Root-cause audit for "이미지 확대하면 한글 글씨가 거칠고 깨져 보인다" (previously
"fixed" across v209.20-v209.30 by repeatedly improving the *new* native Canvas
renderer's font quality and pixel width, without ever finding why the old,
low-resolution renderer kept winning):

Three different scripts assign the SAME global entry point,
window.jmSaveGameReportImage, that the "이미지로 저장" / "전체 이미지 저장"
button calls by reference (onclick="window.jmSaveGameReportImage()"), so
whichever assignment executes LAST wins at click time:

  1. v20893 (base): a one-time synchronous assignment to a 1080-wide SVG
     export. Harmless -- always overwritten below.
  2. v20895 (poster): assigns to a 941px-wide DOM-clone -> SVG
     <foreignObject> -> <canvas> export ("save" in this file), and does so
     not just once but via install() scheduled AGAIN at 0ms, 450ms and
     1200ms after load (jayumintonGameReportPosterV20895Script).
  3. v20901 (expand/export fix): assigns to saveFullImage(), which calls the
     real v209.27+ native-Canvas renderer through the NativeCanvasReport
     Android bridge (4200px, no supersample/downsample). Its own install()
     re-runs at 50ms, 500ms and 1300ms.

Because v20895's LAST re-assignment (1200ms) fires before v20901's LAST
re-assignment (1300ms), the 100ms window between them was the only reliably
"safe" instant for the high-resolution renderer to be in control from cold
boot -- and any earlier click (a normal admin opening the report right after
launching the app), or any later code path that re-invokes v20895's install()
(e.g. a stray click matched by its own delegated listeners), hands control
right back to the 941px low-resolution exporter. That -- not font rendering
quality -- is why zoomed-in PNGs kept looking soft/blocky no matter how many
times the native renderer itself was polished: a real fraction of saves were
never produced by the native renderer at all.

Fix: remove the ONE stale reassignment inside v20895's install() so the
941px path can never re-claim window.jmSaveGameReportImage. v20895's render()
DOM output, its own `save` helper's other bookkeeping (stats/expand-card
UI), and every other feature are left completely untouched -- only the
overwrite of the save entry point is deleted, so it deterministically stays
on v209.27's true 4200px native-Canvas exporter once v20901 has run.
"""
from pathlib import Path
import sys

MARKER = "JAYUMINTON_REPORT_SAVE_RACE_FIX_V20931"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v209.31 {label} anchor mismatch: {count}")
    return text.replace(old, new, 1)


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    for prereq in (
        "JAYUMINTON_GAME_REPORT_POSTER_V20895",
        "window.jmSaveGameReportImage=save;",
        "window.jmV20927SaveNativeCanvasReport",
        "function saveFullImage(){",
    ):
        if prereq not in text:
            raise SystemExit("v209.31 prerequisite missing: " + prereq)

    old = (
        "function install(){var api=window.__JAYUMINTON_GAME_REPORT_V20893__;"
        "if(!api)return;api.render=render;api.svg=function(){return'';};"
        "window.renderPairStatistics=render;window.renderMdPairStatistics=render;"
        "window.jmSaveGameReportImage=save;"
        "window.__JAYUMINTON_GAME_REPORT_V20895__={render:render,save:save,stats:stats};}"
    )
    new = (
        "function install(){var api=window.__JAYUMINTON_GAME_REPORT_V20893__;"
        "if(!api)return;api.render=render;api.svg=function(){return'';};"
        "window.renderPairStatistics=render;window.renderMdPairStatistics=render;"
        "/* " + MARKER + ": do NOT reassign window.jmSaveGameReportImage here. "
        "This 941px poster exporter (save(), above) used to keep re-winning the "
        "save button against the real 4200px native-Canvas exporter (v20901+) "
        "because this install() reran on a timer after page load. render()/"
        "stats() below are still used for the on-screen report UI. */"
        "window.__JAYUMINTON_GAME_REPORT_V20895__={render:render,save:save,stats:stats};}"
    )
    text = replace_once(text, old, new, "v20895 install()")

    required = [MARKER, "window.jmV20927SaveNativeCanvasReport"]
    for needle in required:
        if needle not in text:
            raise SystemExit("v209.31 marker missing: " + needle)
    if "window.jmSaveGameReportImage=save;" in text:
        raise SystemExit("v209.31 stale low-res save reassignment still present")

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
    patch_html(html_path)
    print("ADMIN_V20931_REPORT_SAVE_RACE_FIX_OK")
