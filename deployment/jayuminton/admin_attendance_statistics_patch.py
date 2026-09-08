#!/usr/bin/env python3
"""Show arrival/departure timestamps in the administrator game-statistics view."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_attendance_statistics_patch.py HTML_FILE')

path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = 'JAYUMINTON_ADMIN_ATTENDANCE_STATS_V1'
if marker in html:
    print('ADMIN_ATTENDANCE_STATS_V1_ALREADY_PRESENT')
    raise SystemExit(0)

addon = r'''
<style id="jayuminton-admin-attendance-stats-style-v1">
#adminApp .pair-statistics-head,#adminApp .md-pair-head{flex-wrap:wrap!important}
#adminApp .pair-statistics-attendance{display:block;flex:0 0 100%;margin-top:5px;color:#64748b;font-size:12px;font-weight:800;line-height:1.5}
#adminApp .pair-statistics-partner-label{display:inline-block;margin-right:6px;color:#475569;font-size:12px;font-weight:900}
</style>
<script id="jayuminton-admin-attendance-stats-v1">
/* JAYUMINTON_ADMIN_ATTENDANCE_STATS_V1 */
(function(){
  'use strict';
  function esc(value){
    try{if(typeof escapeMemberInfo==='function')return escapeMemberInfo(String(value||''));}catch(e){}
    return String(value||'').replace(/[&<>"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch];});
  }
  function hm(value){
    if(!value)return '-';
    var d=new Date(String(value));
    if(Number.isNaN(d.getTime()))return '-';
    try{
      var parts=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(d);
      var h=(parts.find(function(p){return p.type==='hour';})||{}).value||'';
      var m=(parts.find(function(p){return p.type==='minute';})||{}).value||'';
      return h&&m?(h+'시 '+m+'분'):'-';
    }catch(e){
      var h2=String(d.getHours()).padStart(2,'0'),m2=String(d.getMinutes()).padStart(2,'0');
      return h2+'시 '+m2+'분';
    }
  }
  function render(){
    var list=document.getElementById('pairStatisticsList')||document.getElementById('mdPairStatisticsList');
    if(!list)return;
    var search=document.getElementById('pairStatisticsSearch')||document.getElementById('mdPairStatisticsSearch');
    var query=String(search&&search.value||'').trim().toLowerCase();
    var source=Array.isArray(window.ADMIN_PAIR_STATISTICS)?window.ADMIN_PAIR_STATISTICS:(Array.isArray(window.MD_PAIR_STATISTICS)?window.MD_PAIR_STATISTICS:[]);
    var rows=source.filter(function(row){return !query||String(row&&row.name||'').toLowerCase().indexOf(query)>=0;});
    if(!rows.length){list.innerHTML='<div class="pair-statistics-empty">표시할 통계가 없습니다.</div>';return;}
    list.innerHTML=rows.map(function(row){
      var partners=(row.partners||[]).map(function(partner){
        return '<span class="pair-statistics-chip">'+esc(partner.name)+' <strong>'+Number(partner.count||0)+'회</strong></span>';
      }).join('');
      var attendance='<span class="pair-statistics-attendance">도착: '+esc(hm(row.arrivedAt))+' · 귀가: '+esc(hm(row.departedAt))+'</span>';
      return '<div class="pair-statistics-row"><div class="pair-statistics-head">'+
        '<span class="pair-statistics-name">'+esc(row.name)+'</span>'+
        '<span class="pair-statistics-games">총 게임 '+Number(row.games||0)+'회</span>'+attendance+'</div>'+
        '<div class="pair-statistics-partners"><span class="pair-statistics-partner-label">함께 경기:</span>'+
        (partners||'<span class="pair-statistics-empty">기록 없음</span>')+'</div></div>';
    }).join('');
    try{
      document.querySelectorAll('.pair-statistics-row').forEach(function(row){row.removeAttribute('data-jm-disclosure-ready');});
    }catch(e){}
  }
  window.renderPairStatistics=render;
  if(typeof window.renderMdPairStatistics==='function')window.renderMdPairStatistics=render;
  window.__JAYUMINTON_ADMIN_ATTENDANCE_STATS_V1__={formatTime:hm,render:render};
})();
</script>
'''

if '</body>' not in html:
    raise SystemExit('body closing tag missing')
html = html.replace('</body>', addon + '\n</body>', 1)
required = [
    marker,
    '도착: ',
    '귀가: ',
    '총 게임 ',
    '함께 경기:',
    "timeZone:'Asia/Seoul'",
]
for token in required:
    if token not in html:
        raise SystemExit('attendance statistics UI contract missing: ' + token)
path.write_text(html, encoding='utf-8')
print('ADMIN_ATTENDANCE_STATS_V1_PATCHED')
