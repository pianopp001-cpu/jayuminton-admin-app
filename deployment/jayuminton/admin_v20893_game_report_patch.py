#!/usr/bin/env python3
from pathlib import Path
import sys

java_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/java/com/jayuminton/admin/MainActivity.java')
html_path = Path(sys.argv[2] if len(sys.argv) > 2 else 'app/src/main/assets/admin/index.html')
java = java_path.read_text(encoding='utf-8')
html = html_path.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_GAME_REPORT_V20893'

if MARKER in html and MARKER in java:
    print('ADMIN_GAME_REPORT_V20893_ALREADY_OK')
    raise SystemExit(0)

for required in (
    'jmAdminRestoreKokTotalV20885',
    'id="pairStatisticsModal"',
    'id="pairStatisticsList"',
    'function openPairStatistics()',
    'JAYUMINTON_ADMIN_ATTENDANCE_STATS_V1',
):
    if required not in html:
        raise SystemExit('v208.93 HTML prerequisite missing: ' + required)

# Keep the same control/handler but give it the shorter user-facing name.
html = html.replace('📊 함께 경기 통계', '📊 게임 통계')

STYLE = r'''
<style id="jayumintonGameReportV20893Style">
/* JAYUMINTON_GAME_REPORT_V20893 */
#pairStatisticsModal{padding:10px!important;background:rgba(3,20,31,.72)!important;backdrop-filter:blur(4px)}
#pairStatisticsModal .pair-statistics-modal{width:min(980px,98vw)!important;max-width:980px!important;max-height:94vh!important;padding:0!important;overflow:auto!important;border:0!important;border-radius:24px!important;background:#eefaf4!important;box-shadow:0 24px 70px rgba(1,32,24,.35)!important}
#pairStatisticsModal .modal-head{position:sticky;top:0;z-index:8;margin:0!important;padding:13px 16px!important;background:rgba(255,255,255,.96)!important;border-bottom:1px solid #d6ebe0!important;backdrop-filter:blur(8px)}
#pairStatisticsModal .modal-head h2{font-size:19px!important;color:#0c3b32!important;margin:0!important}
#pairStatisticsModal .modal-help,#pairStatisticsSearch{display:none!important}
#pairStatisticsList{display:block!important;padding:0!important;background:transparent!important}
.jm-report{min-height:100%;font-family:system-ui,-apple-system,'Noto Sans KR','Malgun Gothic',sans-serif;color:#0d3650;background:linear-gradient(180deg,#ddf6ff 0,#eefaf3 28%,#d9f5e8 100%);overflow:hidden}
.jm-report-hero{position:relative;padding:26px 20px 18px;text-align:center;background:radial-gradient(circle at 18% 15%,rgba(255,255,255,.92),transparent 28%),linear-gradient(180deg,#bce9ff 0,#d7f4ee 100%)}
.jm-report-hero:after{content:'';position:absolute;left:0;right:0;bottom:0;height:2px;background:linear-gradient(90deg,transparent,#47c58c,transparent)}
.jm-report-kicker{font-size:12px;font-weight:900;letter-spacing:.22em;color:#168a68}
.jm-report-title{font-size:clamp(30px,6vw,52px);line-height:1.05;font-weight:1000;letter-spacing:-.055em;color:#10384c;text-shadow:0 2px 0 #fff;margin:4px 0}
.jm-report-title b{color:#1ecb79}
.jm-report-sub{font-size:14px;font-weight:800;color:#47677a}
.jm-report-period{display:inline-flex;gap:7px;align-items:center;margin-top:12px;padding:7px 13px;border:1px solid rgba(255,255,255,.95);border-radius:999px;background:rgba(255,255,255,.72);font-size:13px;font-weight:900;color:#29516d}
.jm-dog{position:absolute;right:4.5%;bottom:8px;width:78px;height:78px;filter:drop-shadow(0 4px 2px rgba(0,0,0,.08))}
.jm-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;padding:15px 16px 10px}
.jm-summary-card{min-width:0;border-radius:18px;padding:13px 12px;background:rgba(255,255,255,.95);border:1px solid rgba(35,175,120,.2);box-shadow:0 7px 18px rgba(14,104,78,.09)}
.jm-summary-card small{display:block;font-weight:900;font-size:11px;color:#1a82b6;margin-bottom:3px}.jm-summary-card strong{display:block;font-size:clamp(22px,4vw,34px);letter-spacing:-.04em;color:#0b3150}.jm-summary-card em{font-style:normal;font-size:12px;color:#6d8795;font-weight:800}
.jm-report-section{margin:8px 16px 0;border-radius:20px;background:rgba(255,255,255,.96);border:1px solid #cde8dd;box-shadow:0 8px 22px rgba(13,90,68,.10);overflow:hidden}
.jm-report-section-title{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 14px;background:linear-gradient(90deg,#147e79,#158b6b);color:#fff}.jm-report-section-title strong{font-size:18px}.jm-report-section-title span{font-size:11px;font-weight:800;opacity:.88}
.jm-report-table-head,.jm-report-row{display:grid;grid-template-columns:minmax(90px,1fr) 76px 92px 92px minmax(190px,2.2fr);gap:8px;align-items:center}
.jm-report-table-head{padding:8px 12px;background:#edf7fb;color:#6b8799;font-size:11px;font-weight:900;text-align:center}
.jm-report-row{padding:10px 12px;border-top:1px solid #e6eff2;font-size:13px}.jm-report-row:nth-child(even){background:#fbfefd}.jm-report-name{font-weight:1000;color:#113a53}.jm-report-games{font-size:16px;font-weight:1000;color:#14a86b;text-align:center}.jm-report-time{text-align:center;font-weight:850;color:#294e67}.jm-report-partners{display:flex;flex-wrap:wrap;gap:5px;align-items:center;min-width:0}.jm-report-chip{display:inline-flex;align-items:center;white-space:nowrap;padding:4px 7px;border-radius:999px;background:#eef6ff;border:1px solid #d7e8fb;color:#2c5674;font-size:11px;font-weight:850}.jm-report-chip strong{margin-left:3px;color:#16775e}.jm-report-more{background:#fff8df;border-color:#f5df93;color:#8c6500;cursor:pointer}.jm-report-empty{font-size:11px;color:#91a3ad}
.jm-highlights{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;padding:12px}.jm-highlight{border-radius:16px;padding:13px;background:linear-gradient(180deg,#fff,#f8fffb);border:1px solid #d9eee4}.jm-highlight small{display:block;font-size:11px;font-weight:900;color:#1689a5}.jm-highlight strong{display:block;margin-top:4px;font-size:18px;color:#123b54;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.jm-highlight em{display:block;margin-top:2px;font-size:12px;font-style:normal;font-weight:900;color:#18a56a}
.jm-report-actions{position:sticky;bottom:0;z-index:7;display:flex;gap:8px;justify-content:center;padding:12px 14px 14px;background:linear-gradient(180deg,rgba(220,247,234,.25),rgba(220,247,234,.96) 30%)}.jm-report-save,.jm-report-close{min-height:42px;border:0;border-radius:14px;padding:0 17px;font-weight:1000;font-size:14px}.jm-report-save{background:#0eaa70;color:#fff;box-shadow:0 8px 16px rgba(14,170,112,.22)}.jm-report-close{background:#fff;color:#31566a;border:1px solid #cfe1e8}
@media(max-width:720px){#pairStatisticsModal{padding:4px!important}.jm-summary-grid{grid-template-columns:repeat(2,1fr)}.jm-report-table-head{display:none}.jm-report-row{grid-template-columns:1fr auto auto;grid-template-areas:'name game game' 'arrival departure departure' 'partners partners partners';gap:4px 8px;padding:10px}.jm-report-name{grid-area:name}.jm-report-games{grid-area:game}.jm-report-time:nth-of-type(1){grid-area:arrival;text-align:left}.jm-report-time:nth-of-type(2){grid-area:departure;text-align:right}.jm-report-partners{grid-area:partners;margin-top:4px}.jm-highlights{grid-template-columns:1fr}.jm-dog{width:62px;height:62px;right:2%;bottom:5px}.jm-report-title{padding-right:34px}}
</style>
'''

SCRIPT = r'''
<script id="jayumintonGameReportV20893Script">
/* JAYUMINTON_GAME_REPORT_V20893 */
(function(){
  'use strict';
  function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function hm(value){
    if(!value)return '-'; var d=new Date(String(value)); if(Number.isNaN(d.getTime()))return '-';
    try{var p=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(d);var h=(p.find(function(x){return x.type==='hour';})||{}).value||'';var m=(p.find(function(x){return x.type==='minute';})||{}).value||'';return h&&m?h+':'+m:'-';}catch(e){return String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');}
  }
  function dayLabel(){try{return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit',weekday:'short'}).format(new Date());}catch(e){return new Date().toLocaleDateString();}}
  function source(){return Array.isArray(window.ADMIN_PAIR_STATISTICS)?window.ADMIN_PAIR_STATISTICS:(Array.isArray(window.MD_PAIR_STATISTICS)?window.MD_PAIR_STATISTICS:[]);}
  function rows(){return source().slice().sort(function(a,b){return Number(b.games||0)-Number(a.games||0)||String(a.name||'').localeCompare(String(b.name||''),'ko');});}
  function stats(list){
    var totalGames=list.reduce(function(s,r){return s+Number(r.games||0);},0), attendees=list.filter(function(r){return r.arrivedAt||Number(r.games||0)>0;}).length;
    var avg=attendees?totalGames/attendees:0, pairSet=new Set();
    list.forEach(function(r){(r.partners||[]).forEach(function(p){var a=String(r.id||r.name),b=String(p.id||p.name);pairSet.add([a,b].sort().join('::'));});});
    var max=list.slice().sort(function(a,b){return Number(b.games||0)-Number(a.games||0);})[0]||null;
    var now=Date.now(), longest=null,longestMs=-1;
    list.forEach(function(r){if(!r.arrivedAt)return;var a=new Date(r.arrivedAt).getTime(),b=r.departedAt?new Date(r.departedAt).getTime():now;if(Number.isFinite(a)&&Number.isFinite(b)&&b>=a&&b-a>longestMs){longest=r;longestMs=b-a;}});
    var bestPair=null; list.forEach(function(r){(r.partners||[]).forEach(function(p){if(!bestPair||Number(p.count||0)>bestPair.count){bestPair={a:r.name,b:p.name,count:Number(p.count||0)};}});});
    return {attendees:attendees,totalGames:totalGames,avg:avg,pairs:pairSet.size,max:max,longest:longest,longestMs:longestMs,bestPair:bestPair};
  }
  function duration(ms){if(!Number.isFinite(ms)||ms<0)return '-';var min=Math.round(ms/60000);return Math.floor(min/60)+'시간 '+String(min%60).padStart(2,'0')+'분';}
  function dogSvg(){return '<svg class="jm-dog" viewBox="0 0 120 120" aria-hidden="true"><path d="M34 34c-11-10-19-8-19 4 0 9 8 15 16 13-4 13-4 35 2 47 9 17 45 17 55 0 7-12 7-34 2-48 8 2 16-4 16-13 0-12-8-14-19-4-15-7-37-7-53 1z" fill="#fff" stroke="#111" stroke-width="5" stroke-linejoin="round"/><circle cx="48" cy="61" r="3.5"/><circle cx="73" cy="61" r="3.5"/><path d="M58 69c2-3 5-3 7 0m-14 4c5 8 17 8 22 0" fill="none" stroke="#111" stroke-width="4" stroke-linecap="round"/><path d="M59 77c2 9 12 9 14 0-5 2-9 2-14 0z" fill="#ff6f75" stroke="#111" stroke-width="3"/></svg>';}
  function partnerHtml(r){var ps=(r.partners||[]),visible=ps.slice(0,4),more=Math.max(0,ps.length-visible.length);return visible.map(function(p){return '<span class="jm-report-chip">'+esc(p.name)+' <strong>'+Number(p.count||0)+'회</strong></span>';}).join('')+(more?'<span class="jm-report-chip jm-report-more" data-member="'+esc(r.id||r.name)+'">외 '+more+'명</span>':'')||'<span class="jm-report-empty">기록 없음</span>';}
  function build(){
    var list=rows(),s=stats(list),start=list.map(function(r){return r.arrivedAt;}).filter(Boolean).sort()[0],end=list.map(function(r){return r.departedAt;}).filter(Boolean).sort().slice(-1)[0];
    var body=list.map(function(r){return '<div class="jm-report-row"><div class="jm-report-name">'+esc(r.name)+'</div><div class="jm-report-games">'+Number(r.games||0)+'회</div><div class="jm-report-time">도착 '+esc(hm(r.arrivedAt))+'</div><div class="jm-report-time">귀가 '+esc(hm(r.departedAt))+'</div><div class="jm-report-partners" data-partners="'+esc(r.id||r.name)+'">'+partnerHtml(r)+'</div></div>';}).join('');
    var max=s.max?esc(s.max.name)+' · '+Number(s.max.games||0)+'회':'-';
    var long=s.longest?esc(s.longest.name)+' · '+duration(s.longestMs):'-';
    var pair=s.bestPair?esc(s.bestPair.a)+' · '+esc(s.bestPair.b)+' · '+s.bestPair.count+'회':'-';
    return '<div class="jm-report">'+
      '<section class="jm-report-hero"><div class="jm-report-kicker">GOOD PLAYERS · BETTER DAYS</div><div class="jm-report-title">자유<b>민턴</b><br>오늘의 게임 통계</div><div class="jm-report-sub">게임 종료 후 한눈에 보는 요약 리포트</div><div class="jm-report-period">📅 '+esc(dayLabel())+' · '+esc(hm(start))+' ~ '+esc(hm(end))+'</div>'+dogSvg()+'</section>'+
      '<section class="jm-summary-grid"><div class="jm-summary-card"><small>총 참석</small><strong>'+s.attendees+'명</strong><em>도착 기록 기준</em></div><div class="jm-summary-card"><small>총 게임 참여</small><strong>'+s.totalGames+'회</strong><em>회원별 게임 합계</em></div><div class="jm-summary-card"><small>평균 게임</small><strong>'+s.avg.toFixed(1)+'회</strong><em>참석자 평균</em></div><div class="jm-summary-card"><small>함께한 조합</small><strong>'+s.pairs+'쌍</strong><em>파트너 기록</em></div></section>'+
      '<section class="jm-report-section"><div class="jm-report-section-title"><strong>👥 참여자 통계</strong><span>파트너가 많으면 상위 4명 + 외 N명</span></div><div class="jm-report-table-head"><span>이름</span><span>총 게임</span><span>도착</span><span>귀가</span><span>함께 경기한 사람</span></div>'+body+'</section>'+
      '<section class="jm-report-section"><div class="jm-report-section-title"><strong>🏆 오늘의 하이라이트</strong><span>게임 종료 후 함께 보기</span></div><div class="jm-highlights"><div class="jm-highlight"><small>최다 경기</small><strong>'+max+'</strong><em>오늘 가장 많이 뛰었어요</em></div><div class="jm-highlight"><small>최장 참여</small><strong>'+long+'</strong><em>도착~귀가 기준</em></div><div class="jm-highlight"><small>인기 파트너</small><strong>'+pair+'</strong><em>가장 많이 함께 경기</em></div></div></section>'+
      '<div class="jm-report-actions"><button type="button" class="jm-report-save" onclick="window.jmSaveGameReportImage()">📷 이미지로 저장</button><button type="button" class="jm-report-close" onclick="closePairStatistics()">닫기</button></div></div>';
  }
  function render(){var list=document.getElementById('pairStatisticsList')||document.getElementById('mdPairStatisticsList');if(!list)return;list.innerHTML=build();}
  document.addEventListener('click',function(ev){var more=ev.target&&ev.target.closest?ev.target.closest('.jm-report-more'):null;if(!more)return;var key=more.getAttribute('data-member'),r=rows().find(function(x){return String(x.id||x.name)===String(key);});if(!r)return;var box=more.closest('.jm-report-partners');box.innerHTML=(r.partners||[]).map(function(p){return '<span class="jm-report-chip">'+esc(p.name)+' <strong>'+Number(p.count||0)+'회</strong></span>';}).join('')+'<span class="jm-report-chip jm-report-more" data-member="'+esc(r.id||r.name)+'">접기</span>';},{capture:false});
  function svgText(x,y,text,size,weight,fill,anchor){return '<text x="'+x+'" y="'+y+'" font-family="Arial,Noto Sans KR,sans-serif" font-size="'+size+'" font-weight="'+weight+'" fill="'+fill+'" text-anchor="'+(anchor||'start')+'">'+esc(text)+'</text>';}
  function svgDog(x,y){return '<g transform="translate('+x+' '+y+') scale(.65)"><path d="M34 34c-11-10-19-8-19 4 0 9 8 15 16 13-4 13-4 35 2 47 9 17 45 17 55 0 7-12 7-34 2-48 8 2 16-4 16-13 0-12-8-14-19-4-15-7-37-7-53 1z" fill="#fff" stroke="#111" stroke-width="5" stroke-linejoin="round"/><circle cx="48" cy="61" r="3.5"/><circle cx="73" cy="61" r="3.5"/><path d="M58 69c2-3 5-3 7 0m-14 4c5 8 17 8 22 0" fill="none" stroke="#111" stroke-width="4" stroke-linecap="round"/><path d="M59 77c2 9 12 9 14 0-5 2-9 2-14 0z" fill="#ff6f75" stroke="#111" stroke-width="3"/></g>';}
  function svgReport(){
    var list=rows(),s=stats(list),rowH=74,w=1080,top=525,tableH=72+list.length*rowH,highY=top+tableH+28,h=highY+260;
    var start=list.map(function(r){return r.arrivedAt;}).filter(Boolean).sort()[0],end=list.map(function(r){return r.departedAt;}).filter(Boolean).sort().slice(-1)[0];
    var out=['<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">','<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c7eeff"/><stop offset=".35" stop-color="#effbf4"/><stop offset="1" stop-color="#d5f3e5"/></linearGradient></defs>','<rect width="100%" height="100%" fill="url(#bg)"/>'];
    out.push(svgText(540,70,'자유민턴',74,900,'#12394d','middle'),svgText(540,134,'오늘의 게임 통계',46,900,'#12394d','middle'),svgText(540,172,'게임 종료 후 한눈에 보는 요약 리포트',22,700,'#496a7b','middle'),'<rect x="345" y="195" width="390" height="48" rx="24" fill="#ffffffcc" stroke="#fff"/>',svgText(540,227,dayLabel()+' · '+hm(start)+' ~ '+hm(end),20,800,'#2b5670','middle'),svgDog(855,118));
    var cards=[['총 참석',s.attendees+'명'],['총 게임 참여',s.totalGames+'회'],['평균 게임',s.avg.toFixed(1)+'회'],['함께한 조합',s.pairs+'쌍']];
    cards.forEach(function(c,i){var x=45+i*252;out.push('<rect x="'+x+'" y="280" width="225" height="150" rx="24" fill="#fff" stroke="#cfe8df"/>',svgText(x+22,320,c[0],18,800,'#1785aa'),svgText(x+22,379,c[1],42,900,'#10344f'));});
    out.push('<rect x="35" y="'+top+'" width="1010" height="'+tableH+'" rx="25" fill="#fff" stroke="#cce7dd"/>','<rect x="35" y="'+top+'" width="1010" height="58" rx="25" fill="#137f73"/>',svgText(65,top+38,'참여자 통계',28,900,'#fff'));
    var hy=top+90; [['이름',70],['게임',265],['도착',370],['귀가',485],['함께 경기한 사람',610]].forEach(function(a){out.push(svgText(a[1],hy,a[0],16,800,'#698797'));});
    list.forEach(function(r,i){var y=top+115+i*rowH;if(i%2)out.push('<rect x="45" y="'+(y-28)+'" width="990" height="'+rowH+'" fill="#fbfefd"/>');out.push(svgText(70,y, String(r.name||''),21,900,'#153b52'),svgText(285,y,Number(r.games||0)+'회',22,900,'#12a86b','middle'),svgText(405,y,hm(r.arrivedAt),18,800,'#31556b','middle'),svgText(520,y,hm(r.departedAt),18,800,'#31556b','middle'));var ps=(r.partners||[]),shown=ps.slice(0,6).map(function(p){return p.name+' '+Number(p.count||0)+'회';});if(ps.length>6)shown.push('외 '+(ps.length-6)+'명');var text=shown.join(' · ')||'기록 없음';if(text.length>45){var a=text.slice(0,45),b=text.slice(45,88);out.push(svgText(610,y-8,a,15,700,'#315b76'),svgText(610,y+15,b+(text.length>88?'…':''),15,700,'#315b76'));}else out.push(svgText(610,y,text,15,700,'#315b76'));});
    out.push('<rect x="35" y="'+highY+'" width="1010" height="210" rx="25" fill="#fff" stroke="#cce7dd"/>','<rect x="35" y="'+highY+'" width="1010" height="58" rx="25" fill="#16856f"/>',svgText(65,highY+38,'오늘의 하이라이트',28,900,'#fff'));
    var max=s.max?s.max.name+' · '+Number(s.max.games||0)+'회':'-',lng=s.longest?s.longest.name+' · '+duration(s.longestMs):'-',bp=s.bestPair?s.bestPair.a+' · '+s.bestPair.b+' · '+s.bestPair.count+'회':'-';[['최다 경기',max],['최장 참여',lng],['인기 파트너',bp]].forEach(function(c,i){var x=60+i*325;out.push(svgText(x,highY+102,c[0],17,800,'#1785a4'),svgText(x,highY+145,c[1],24,900,'#143a51'));});out.push(svgDog(905,highY+105),'</svg>');return out.join('');
  }
  window.jmSaveGameReportImage=function(){
    try{var svg=svgReport(),blob=new Blob([svg],{type:'image/svg+xml;charset=utf-8'}),url=URL.createObjectURL(blob),img=new Image();img.onload=function(){try{var canvas=document.createElement('canvas');canvas.width=img.naturalWidth||1080;canvas.height=img.naturalHeight||1600;var ctx=canvas.getContext('2d');ctx.drawImage(img,0,0);URL.revokeObjectURL(url);var data=canvas.toDataURL('image/png');var name='자유민턴_게임통계_'+new Date().toISOString().slice(0,10)+'.png';if(window.NativeBrowser&&typeof window.NativeBrowser.saveStatisticsPng==='function'){window.NativeBrowser.saveStatisticsPng(data,name);}else{var a=document.createElement('a');a.href=data;a.download=name;document.body.appendChild(a);a.click();a.remove();}}catch(e){alert('이미지 저장 실패: '+(e.message||e));}};img.onerror=function(){URL.revokeObjectURL(url);alert('통계 이미지를 만들지 못했습니다.');};img.src=url;}catch(e){alert('이미지 저장 실패: '+(e.message||e));}
  };
  window.renderPairStatistics=render; window.renderMdPairStatistics=render; window.__JAYUMINTON_GAME_REPORT_V20893__={render:render,svg:svgReport};
})();
</script>
'''

if '</head>' not in html or '</body>' not in html:
    raise SystemExit('HTML closing anchors missing')
html = html.replace('</head>', STYLE + '\n</head>', 1)
html = html.replace('</body>', SCRIPT + '\n</body>', 1)

# Native PNG saver for the packaged administrator app.
for imp in (
    'import android.content.ContentValues;\n',
    'import android.os.Environment;\n',
    'import android.provider.MediaStore;\n',
    'import android.util.Base64;\n',
    'import java.io.FileOutputStream;\n',
    'import java.io.OutputStream;\n',
):
    if imp not in java:
        if imp.startswith('import java.'):
            anchor='import java.io.File;\n' if 'import java.io.File;\n' in java else 'import java.util.ArrayList;\n'
        else:
            anchor='import android.annotation.SuppressLint;\n'
        java=java.replace(anchor,anchor+imp,1)

browser_anchor='''    public final class BrowserBridge {\n        @JavascriptInterface\n        public void openPwa() {\n            runOnUiThread(() -> openMemberPwaInBrowser(MEMBER_PWA_URL));\n        }\n    }'''
if browser_anchor not in java:
    raise SystemExit('BrowserBridge anchor missing')
browser_new='''    public final class BrowserBridge {\n        @JavascriptInterface\n        public void openPwa() {\n            runOnUiThread(() -> openMemberPwaInBrowser(MEMBER_PWA_URL));\n        }\n\n        @JavascriptInterface\n        public void saveStatisticsPng(String dataUrl, String requestedName) {\n            final String payload = dataUrl == null ? "" : dataUrl;\n            final String name = requestedName == null || requestedName.trim().isEmpty()\n                    ? "자유민턴_게임통계.png" : requestedName.trim();\n            runOnUiThread(() -> {\n                try {\n                    int comma = payload.indexOf(',');\n                    String encoded = comma >= 0 ? payload.substring(comma + 1) : payload;\n                    byte[] bytes = Base64.decode(encoded, Base64.DEFAULT);\n                    String safeName = name.replaceAll("[^0-9A-Za-z가-힣._-]", "_");\n                    if (!safeName.toLowerCase(Locale.ROOT).endsWith(".png")) safeName += ".png";\n                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {\n                        ContentValues values = new ContentValues();\n                        values.put(MediaStore.Images.Media.DISPLAY_NAME, safeName);\n                        values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");\n                        values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/자유민턴");\n                        values.put(MediaStore.Images.Media.IS_PENDING, 1);\n                        Uri uri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);\n                        if (uri == null) throw new IllegalStateException("image_insert_failed");\n                        try (OutputStream out = getContentResolver().openOutputStream(uri)) {\n                            if (out == null) throw new IllegalStateException("image_output_failed");\n                            out.write(bytes);\n                        }\n                        values.clear();\n                        values.put(MediaStore.Images.Media.IS_PENDING, 0);\n                        getContentResolver().update(uri, values, null, null);\n                    } else {\n                        File dir = new File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), "자유민턴");\n                        if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("image_dir_failed");\n                        try (OutputStream out = new FileOutputStream(new File(dir, safeName))) { out.write(bytes); }\n                    }\n                    Toast.makeText(MainActivity.this, "게임 통계 이미지를 저장했습니다.", Toast.LENGTH_LONG).show();\n                } catch (Exception error) {\n                    Toast.makeText(MainActivity.this, "통계 이미지 저장 실패: " + error.getMessage(), Toast.LENGTH_LONG).show();\n                }\n            });\n        }\n    }'''
java=java.replace(browser_anchor,browser_new,1)

for token in (MARKER,'이미지로 저장','파트너가 많으면 상위 4명 + 외 N명','jmSaveGameReportImage','saveStatisticsPng','MediaStore.Images.Media.RELATIVE_PATH'):
    if token not in html+java:
        raise SystemExit('v208.93 requirement missing: '+token)

html_path.write_text(html,encoding='utf-8')
java_path.write_text(java,encoding='utf-8')
print('ADMIN_GAME_REPORT_V20893_OK')
