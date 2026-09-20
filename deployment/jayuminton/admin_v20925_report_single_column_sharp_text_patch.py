#!/usr/bin/env python3
"""Render the full one-image report as a high-contrast single column."""

from pathlib import Path
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
html = html_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_REPORT_SINGLE_COLUMN_SHARP_TEXT_V20925"

if MARKER in html:
    print("ADMIN_V20925_SINGLE_COLUMN_SHARP_TEXT_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_REPORT_TILE_RETRY_V20924",
    "JAYUMINTON_REPORT_NO_GREEN_TILE_READABLE_V20923",
    "w=Math.max(1600",
):
    if token not in html:
        raise SystemExit("v209.25 prerequisite missing: " + token)

style = r'''
<style id="jmSingleColumnSharpTextV20925">
/* JAYUMINTON_REPORT_SINGLE_COLUMN_SHARP_TEXT_V20925
   One PNG and every expanded history remain, but text gets enough real pixels
   to survive gallery/marketplace resizing. */
#jmNativeReportExportV20905,
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918{
  width:1080px!important;
  min-width:1080px!important;
  max-width:none!important;
  background:#fff!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child{
  display:grid!important;
  grid-template-columns:minmax(0,1fr)!important;
  gap:12px!important;
  padding:0 16px 16px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-head{
  grid-column:1!important;
  margin:0 -16px!important;
  font-size:34px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row{
  grid-template-columns:minmax(360px,1fr) 110px 145px 145px!important;
  column-gap:16px!important;
  row-gap:12px!important;
  padding:20px 22px!important;
  background:#fff!important;
  border:2px solid #d5e3e7!important;
  box-shadow:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-name{
  font-size:34px!important;
  line-height:1.25!important;
  font-weight:1000!important;
  color:#071f2a!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-av{
  width:48px!important;
  height:48px!important;
  flex:0 0 48px!important;
  font-size:21px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-games{
  font-size:32px!important;
  line-height:1.15!important;
  font-weight:1000!important;
  color:#008a63!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time{
  font-size:27px!important;
  line-height:1.2!important;
  font-weight:1000!important;
  color:#153745!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time::before{
  font-size:19px!important;
  color:#355563!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-full-history{
  padding:12px 0 0!important;
  background:#fff!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-title{
  margin:0 0 9px!important;
  font-size:25px!important;
  line-height:1.25!important;
  font-weight:1000!important;
  color:#173b49!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list{
  gap:8px!important;
  font-size:25px!important;
  line-height:1.45!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list .j95-chip{
  margin:0!important;
  padding:6px 9px!important;
  font-size:25px!important;
  line-height:1.25!important;
  font-weight:900!important;
  color:#073652!important;
  background:#edf7fb!important;
  border:1px solid #c7dde6!important;
  text-shadow:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-card,
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-panel{
  box-shadow:none!important;
}
</style>
'''

html = html.replace("</head>", style + "\n</head>", 1)
html = html.replace(
    "w=Math.max(1600,Math.ceil(rect.width||p.offsetWidth||941))",
    "w=Math.max(1080,Math.ceil(rect.width||p.offsetWidth||941))",
    1,
)

for token in (
    MARKER,
    "w=Math.max(1080",
    "grid-template-columns:minmax(0,1fr)",
    "font-size:34px!important",
    "font-size:25px!important",
    "color:#073652!important",
):
    if token not in html:
        raise SystemExit("v209.25 output missing: " + token)

html_path.write_text(html, encoding="utf-8")
print("ADMIN_V20925_SINGLE_COLUMN_SHARP_TEXT_OK")
