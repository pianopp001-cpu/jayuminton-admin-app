#!/usr/bin/env python3
"""Make the one-image fully-expanded report survive marketplace downscaling."""

from pathlib import Path
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
html = html_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_MARKETPLACE_READABLE_FULL_REPORT_V20922"

if MARKER in html:
    print("ADMIN_V20922_MARKETPLACE_READABLE_FULL_REPORT_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_HIGH_RES_SINGLE_REPORT_V20920",
    "JAYUMINTON_FULL_HISTORY_EXPORT_LAYOUT_V20921",
    "jmV20921ForceFullHistory(c)",
    "w=Math.max(1600",
):
    if token not in html:
        raise SystemExit("v209.22 prerequisite missing: " + token)

style = r'''
<style id="jmMarketplaceReadableFullReportV20922">
/* JAYUMINTON_MARKETPLACE_READABLE_FULL_REPORT_V20922
   One PNG, all member histories. Use a much wider 3-column export so the
   platform's long-image resize leaves substantially more pixels per glyph. */
#jmNativeReportExportV20905{
  width:2400px!important;
  min-width:2400px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918{
  width:2400px!important;
  min-width:2400px!important;
  max-width:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:18px!important;
  padding:0 18px 18px!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-head{
  grid-column:1/-1!important;
  margin:0 -18px!important;
  font-size:32px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-th{
  display:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row{
  display:grid!important;
  grid-template-columns:minmax(250px,1fr) 96px 132px 132px!important;
  grid-template-areas:
    "name games arrived departed"
    "partners partners partners partners"!important;
  column-gap:12px!important;
  row-gap:10px!important;
  align-items:center!important;
  min-width:0!important;
  min-height:0!important;
  margin:0!important;
  padding:18px 18px!important;
  border-radius:16px!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-name{
  grid-area:name!important;
  grid-column:auto!important;
  min-width:0!important;
  gap:10px!important;
  font-size:30px!important;
  line-height:1.2!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-av{
  width:46px!important;
  height:46px!important;
  flex:0 0 46px!important;
  font-size:20px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-games{
  grid-area:games!important;
  grid-column:auto!important;
  min-width:0!important;
  font-size:29px!important;
  line-height:1.1!important;
  text-align:center!important;
  white-space:nowrap!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(3){
  grid-area:arrived!important;
  grid-column:auto!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(4){
  grid-area:departed!important;
  grid-column:auto!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time{
  width:auto!important;
  min-width:0!important;
  display:flex!important;
  flex-direction:column!important;
  align-items:center!important;
  justify-content:center!important;
  font-size:25px!important;
  line-height:1.12!important;
  font-weight:950!important;
  text-align:center!important;
  white-space:nowrap!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(3)::before,
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(4)::before{
  display:block!important;
  margin:0 0 4px!important;
  font-size:17px!important;
  line-height:1!important;
  font-weight:1000!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-partners{
  grid-area:partners!important;
  grid-column:1/-1!important;
  width:100%!important;
  min-width:0!important;
  padding-top:8px!important;
  overflow:visible!important;
  white-space:normal!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-full-history{
  width:100%!important;
  margin:0!important;
  padding:10px 0 0!important;
  border-top:1px dashed #d7e7eb!important;
}
/* Game/arrival/departure already exist in large dedicated columns above.
   Hiding this duplicated summary shortens the one-image report without
   removing any information. */
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-summary{
  display:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-title{
  margin:0 0 7px!important;
  font-size:20px!important;
  line-height:1.25!important;
  font-weight:1000!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  min-width:0!important;
  font-size:21px!important;
  line-height:1.4!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list .j95-chip{
  margin:0!important;
  padding:5px 8px!important;
  font-size:21px!important;
  line-height:1.2!important;
  font-weight:850!important;
  white-space:nowrap!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-hero{
  padding-top:16px!important;
  padding-bottom:16px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-card{
  min-height:100px!important;
}
</style>
'''

if "</head>" not in html:
    raise SystemExit("v209.22 head close missing")
html = html.replace("</head>", style + "\n</head>", 1)

old = "w=Math.max(1600,Math.ceil(rect.width||p.offsetWidth||941))"
new = "w=Math.max(2400,Math.ceil(rect.width||p.offsetWidth||941))"
if html.count(old) != 1:
    raise SystemExit("v209.22 export width anchor mismatch: " + str(html.count(old)))
html = html.replace(old, new, 1)

for token in (
    MARKER,
    "width:2400px!important",
    "grid-template-columns:repeat(3,minmax(0,1fr))",
    "font-size:30px!important",
    "font-size:25px!important",
    "font-size:21px!important",
    "jm-v20921-history-summary",
    "display:none!important",
    "w=Math.max(2400",
):
    if token not in html:
        raise SystemExit("v209.22 output missing: " + token)

html_path.write_text(html, encoding="utf-8")
print("ADMIN_V20922_MARKETPLACE_READABLE_FULL_REPORT_OK")
