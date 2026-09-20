#!/usr/bin/env python3
"""Make the single full report image shorter and more marketplace-readable without splitting it."""

from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
text = path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_SINGLE_REPORT_READABLE_REFLOW_V20918"

if MARKER in text:
    print("ADMIN_V20918_SINGLE_REPORT_REFLOW_ALREADY_OK")
    raise SystemExit(0)

for required in (
    "JAYUMINTON_NATIVE_FULL_REPORT_CAPTURE_V20905",
    "JAYUMINTON_REPORT_PIXELCOPY_CAPTURE_V20906",
    "window.jmSaveGameReportImage=saveFullImage",
    "var c=p.cloneNode(true);cleanClone(c);c.style.width=w+'px';",
):
    if required not in text:
        raise SystemExit("v209.18 prerequisite missing: " + required)

style = r'''
<style id="jmSingleReportReadableReflowV20918">
/* JAYUMINTON_SINGLE_REPORT_READABLE_REFLOW_V20918
   Keep exactly one fully-expanded image. For export only, reflow participant
   rows into two columns so marketplace resizing does not destroy text detail. */
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-hero{
  padding-top:14px!important;
  padding-bottom:14px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-brand{
  margin-top:4px!important;
  font-size:72px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-sub{
  margin-top:10px!important;
  font-size:38px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-cap{
  margin-top:3px!important;
  font-size:15px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-date{
  margin:9px auto 12px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-sum{
  gap:8px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-card{
  min-height:92px!important;
  padding:11px 10px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-card strong{
  margin-top:7px!important;
  font-size:34px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body{
  padding-bottom:12px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:8px!important;
  padding:0 8px 8px!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-head{
  grid-column:1/-1!important;
  margin:0 -8px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-th{
  display:none!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-body>.j95-panel:first-child>.j95-row{
  display:grid!important;
  grid-template-columns:minmax(0,1fr) auto auto!important;
  gap:5px 8px!important;
  align-items:center!important;
  min-width:0!important;
  min-height:0!important;
  margin:0!important;
  padding:9px 10px!important;
  border:1px solid #d8e9ed!important;
  border-radius:13px!important;
  background:#fff!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-name{
  grid-column:1/3!important;
  min-width:0!important;
  gap:6px!important;
  font-size:15px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-av{
  width:30px!important;
  height:30px!important;
  font-size:13px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-games{
  grid-column:3!important;
  font-size:16px!important;
  white-space:nowrap!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time{
  font-size:12px!important;
  text-align:left!important;
  white-space:nowrap!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(3)::before{
  content:"도착 "!important;
  color:#718096!important;
  font-size:10px!important;
  font-weight:900!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(4)::before{
  content:"귀가 "!important;
  color:#718096!important;
  font-size:10px!important;
  font-weight:900!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-partners{
  grid-column:1/-1!important;
  min-width:0!important;
  font-size:11px!important;
  line-height:1.45!important;
  padding-top:3px!important;
  border-top:1px dashed #e1eaee!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-card{
  margin:4px 0 0!important;
  padding:8px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-summary{
  gap:4px!important;
  margin-bottom:6px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-stat{
  padding:5px 4px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-stat small{
  font-size:8px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-stat b{
  font-size:11px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-title{
  font-size:10px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-expand-list{
  line-height:1.5!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-chip{
  margin:1px 2px 1px 0!important;
  padding:2px 4px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-hi{
  padding:10px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-hc{
  min-height:104px!important;
  padding:10px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-footer{
  min-height:84px!important;
}
</style>
'''

if "</head>" not in text:
    raise SystemExit("head close missing")
text = text.replace("</head>", style + "\n</head>", 1)

old = "var c=p.cloneNode(true);cleanClone(c);c.style.width=w+'px';"
new = "var c=p.cloneNode(true);cleanClone(c);c.classList.add('jm-marketplace-onepage-v20918');c.style.width=w+'px';"
if text.count(old) != 1:
    raise SystemExit("active export clone anchor mismatch: " + str(text.count(old)))
text = text.replace(old, new, 1)

for required in (
    MARKER,
    "jm-marketplace-onepage-v20918",
    "grid-template-columns:repeat(2,minmax(0,1fr))",
    'content:"도착 "',
    'content:"귀가 "',
):
    if required not in text:
        raise SystemExit("v209.18 output missing: " + required)

path.write_text(text, encoding="utf-8")
print("ADMIN_V20918_SINGLE_REPORT_REFLOW_OK")
