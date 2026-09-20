#!/usr/bin/env python3
"""Force every member history fully expanded in export and prevent time/count overlap."""

from pathlib import Path
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
html = html_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_FULL_HISTORY_EXPORT_LAYOUT_V20921"

if MARKER in html:
    print("ADMIN_V20921_FULL_HISTORY_EXPORT_LAYOUT_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_HIGH_RES_SINGLE_REPORT_V20920",
    "JAYUMINTON_SINGLE_REPORT_READABLE_REFLOW_V20918",
    "function cleanClone(c){",
    "function saveFullImage(){",
    "window.NativeReportCapture.saveFullReportPng",
):
    if token not in html:
        raise SystemExit("v209.21 prerequisite missing: " + token)

style = r'''
<style id="jmFullHistoryExportLayoutV20921">
/* JAYUMINTON_FULL_HISTORY_EXPORT_LAYOUT_V20921
   Export only: explicit grid areas keep name/game/arrival/departure separate,
   and every partner-history block spans the complete card width. */
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row{
  display:grid!important;
  grid-template-columns:minmax(260px,1fr) 90px 126px 126px!important;
  grid-template-areas:
    "name games arrived departed"
    "partners partners partners partners"!important;
  column-gap:14px!important;
  row-gap:10px!important;
  align-items:center!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-name{
  grid-area:name!important;
  grid-column:auto!important;
  min-width:0!important;
  overflow:visible!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-games{
  grid-area:games!important;
  grid-column:auto!important;
  min-width:0!important;
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
  min-width:0!important;
  width:auto!important;
  display:flex!important;
  flex-direction:column!important;
  justify-content:center!important;
  align-items:center!important;
  text-align:center!important;
  white-space:nowrap!important;
  overflow:visible!important;
  font-size:21px!important;
  font-weight:900!important;
  line-height:1.18!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(3)::before,
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-time:nth-child(4)::before{
  display:block!important;
  margin:0 0 4px!important;
  font-size:15px!important;
  line-height:1!important;
  font-weight:950!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .j95-row>.j95-partners{
  grid-area:partners!important;
  grid-column:1/-1!important;
  width:100%!important;
  min-width:0!important;
  overflow:visible!important;
  white-space:normal!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-full-history{
  display:block!important;
  width:100%!important;
  margin-top:2px!important;
  padding:14px!important;
  border-top:1px dashed #d7e7eb!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-summary{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:8px!important;
  margin-bottom:10px!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-stat{
  min-width:0!important;
  padding:8px 7px!important;
  border-radius:9px!important;
  background:#f4fafb!important;
  text-align:center!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-stat small{
  display:block!important;
  margin-bottom:3px!important;
  font-size:14px!important;
  line-height:1.1!important;
  font-weight:900!important;
  color:#607b86!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-stat b{
  display:block!important;
  font-size:20px!important;
  line-height:1.2!important;
  font-weight:1000!important;
  color:#123f52!important;
  white-space:nowrap!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-title{
  margin:4px 0 7px!important;
  font-size:17px!important;
  font-weight:1000!important;
  color:#355f6c!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list{
  display:flex!important;
  flex-wrap:wrap!important;
  gap:6px!important;
  min-width:0!important;
  font-size:18px!important;
  line-height:1.45!important;
}
#jmNativeReportExportV20905 .jm-marketplace-onepage-v20918 .jm-v20921-history-list .j95-chip{
  display:inline-flex!important;
  align-items:center!important;
  margin:0!important;
  padding:5px 8px!important;
  font-size:18px!important;
  line-height:1.25!important;
  white-space:nowrap!important;
}
</style>
'''

if "</head>" not in html:
    raise SystemExit("v209.21 head close missing")
html = html.replace("</head>", style + "\n</head>", 1)

# Inject helpers immediately before cleanClone so the active v209.05/v209.20
# saveFullImage path can expand the clone directly from the statistics source,
# regardless of whether the on-screen cards are currently expanded.
anchor = "function cleanClone(c){"
helper = r'''function jmV20921Escape(v){return String(v==null?'':v).replace(/[&<>"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch];});}
function jmV20921Date(v){var d=v?new Date(String(v)):null;return d&&!Number.isNaN(d.getTime())?d:null;}
function jmV20921Hm(v){var d=jmV20921Date(v);if(!d)return '-';try{var p=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(d),h=(p.find(function(x){return x.type==='hour';})||{}).value,m=(p.find(function(x){return x.type==='minute';})||{}).value;return h&&m?h+':'+m:'-';}catch(_){return '-';}}
function jmV20921Rows(){var a=Array.isArray(window.ADMIN_PAIR_STATISTICS)?window.ADMIN_PAIR_STATISTICS:(Array.isArray(window.MD_PAIR_STATISTICS)?window.MD_PAIR_STATISTICS:[]);return a.slice().sort(function(x,y){return Number(y.games||0)-Number(x.games||0)||String(x.name||'').localeCompare(String(y.name||''),'ko');});}
function jmV20921ForceFullHistory(c){
  var data=jmV20921Rows(),cards=Array.prototype.slice.call(c.querySelectorAll('.j95-body>.j95-panel:first-child>.j95-row'));
  cards.forEach(function(card,i){
    var r=data[i];if(!r)return;
    var games=Number(r.games||0),arr=jmV20921Hm(r.arrivedAt),dep=jmV20921Hm(r.departedAt),partners=Array.isArray(r.partners)?r.partners:[];
    var list=partners.map(function(p){return '<span class="j95-chip">'+jmV20921Escape(p.name)+(Number(p.count||0)>1?' <b>'+Number(p.count||0)+'회</b>':'')+'</span>';}).join('')||'<span class="j95-empty">기록 없음</span>';
    var box=card.querySelector('.j95-partners');
    if(box){
      box.innerHTML='<div class="jm-v20921-full-history"><div class="jm-v20921-history-summary"><span class="jm-v20921-history-stat"><small>게임횟수</small><b>'+games+'회</b></span><span class="jm-v20921-history-stat"><small>도착시간</small><b>'+arr+'</b></span><span class="jm-v20921-history-stat"><small>귀가시간</small><b>'+dep+'</b></span></div><div class="jm-v20921-history-title">함께 경기한 사람 전체 '+partners.length+'명</div><div class="jm-v20921-history-list">'+list+'</div></div>';
    }
    var times=card.querySelectorAll('.j95-time');
    if(times[0])times[0].textContent=arr;
    if(times[1])times[1].textContent=dep;
    var game=card.querySelector('.j95-games');if(game)game.textContent=games+'회';
  });
}
'''
if html.count(anchor) != 1:
    raise SystemExit("v209.21 cleanClone anchor mismatch: " + str(html.count(anchor)))
html = html.replace(anchor, helper + "\n" + anchor, 1)

# Make every export clone fully expanded before cleanClone strips control buttons.
old_clone = "var c=p.cloneNode(true);cleanClone(c);c.classList.add('jm-marketplace-onepage-v20918');c.style.width=w+'px';"
new_clone = "var c=p.cloneNode(true);jmV20921ForceFullHistory(c);cleanClone(c);c.classList.add('jm-marketplace-onepage-v20918');c.style.width=w+'px';"
if html.count(old_clone) != 1:
    raise SystemExit("v209.21 active clone anchor mismatch: " + str(html.count(old_clone)))
html = html.replace(old_clone, new_clone, 1)

for token in (
    MARKER,
    "jmV20921ForceFullHistory(c)",
    "jm-v20921-full-history",
    'grid-template-areas:',
    '"name games arrived departed"',
    "함께 경기한 사람 전체",
    "도착시간",
    "귀가시간",
):
    if token not in html:
        raise SystemExit("v209.21 output missing: " + token)

html_path.write_text(html, encoding="utf-8")
print("ADMIN_V20921_FULL_HISTORY_EXPORT_LAYOUT_OK")
