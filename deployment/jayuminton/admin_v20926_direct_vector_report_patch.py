#!/usr/bin/env python3
"""Generate the full statistics PNG from pure SVG text at native resolution."""

from pathlib import Path
import re
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
html = html_path.read_text(encoding="utf-8")
MARKER = "JAYUMINTON_DIRECT_VECTOR_REPORT_V20926"

if MARKER in html:
    print("ADMIN_V20926_DIRECT_VECTOR_REPORT_ALREADY_OK")
    raise SystemExit(0)

for token in (
    "JAYUMINTON_REPORT_SINGLE_COLUMN_SHARP_TEXT_V20925",
    "function saveFullImage(){",
    "window.NativeBrowser.saveStatisticsPng",
):
    if token not in html:
        raise SystemExit("v209.26 prerequisite missing: " + token)

script = r'''
<script id="jmDirectVectorReportV20926">
/* JAYUMINTON_DIRECT_VECTOR_REPORT_V20926
   Pure SVG text -> full-resolution canvas -> PNG.
   No WebView screenshot, PixelCopy, viewport scale, or foreignObject. */
(function(){
  function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch];});}
  function rows(){
    var a=Array.isArray(window.ADMIN_PAIR_STATISTICS)?window.ADMIN_PAIR_STATISTICS:
      (Array.isArray(window.MD_PAIR_STATISTICS)?window.MD_PAIR_STATISTICS:[]);
    return a.slice().sort(function(x,y){return Number(y.games||0)-Number(x.games||0)||String(x.name||'').localeCompare(String(y.name||''),'ko');});
  }
  function hm(v){
    var d=v?new Date(String(v)):null;if(!d||Number.isNaN(d.getTime()))return '-';
    try{var p=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(d);
      var h=(p.find(function(x){return x.type==='hour';})||{}).value,m=(p.find(function(x){return x.type==='minute';})||{}).value;return h&&m?h+':'+m:'-';}catch(_){return '-';}
  }
  function partnerTokens(r){
    var p=Array.isArray(r.partners)?r.partners:[];
    return p.map(function(x){return String(x.name||'')+(Number(x.count||0)>1?' '+Number(x.count||0)+'회':'');});
  }
  function makeLines(tokens,maxUnits){
    var out=[],line='';
    tokens.forEach(function(t){
      var unit=Array.from(t).reduce(function(n,ch){return n+(/[\u0000-\u00ff]/.test(ch)?.58:1);},0)+2;
      var cur=Array.from(line).reduce(function(n,ch){return n+(/[\u0000-\u00ff]/.test(ch)?.58:1);},0);
      if(line&&cur+unit>maxUnits){out.push(line);line=t;}else line+=(line?'   ':'')+t;
    });
    if(line)out.push(line);if(!out.length)out.push('기록 없음');return out;
  }
  function build(){
    var data=rows(),W=2000,margin=36,gap=24,col=(W-margin*2-gap)/2;
    var cards=data.map(function(r){
      var lines=makeLines(partnerTokens(r),45);
      return {r:r,lines:lines,h:142+lines.length*38};
    });
    var y=250,placed=[];
    for(var i=0;i<cards.length;i+=2){
      var a=cards[i],b=cards[i+1],rh=Math.max(a.h,b?b.h:0);
      placed.push({c:a,x:margin,y:y,h:rh});
      if(b)placed.push({c:b,x:margin+col+gap,y:y,h:rh});
      y+=rh+16;
    }
    var H=y+150,parts=[];
    parts.push('<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">');
    parts.push('<rect width="100%" height="100%" fill="#ffffff"/>');
    parts.push('<rect x="0" y="0" width="'+W+'" height="170" fill="#e9fbf7"/>');
    parts.push('<rect x="0" y="170" width="'+W+'" height="58" fill="#007f68"/>');
    parts.push('<text x="'+(W/2)+'" y="65" text-anchor="middle" font-family="sans-serif" font-size="46" font-weight="900" fill="#082f3c">자유민턴</text>');
    parts.push('<text x="'+(W/2)+'" y="111" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="800" fill="#0a5360">오늘의 게임 통계</text>');
    parts.push('<text x="'+(W/2)+'" y="151" text-anchor="middle" font-family="sans-serif" font-size="22" font-weight="700" fill="#426773">전체 '+data.length+'명 · 전체 이력 펼침</text>');
    parts.push('<text x="30" y="208" font-family="sans-serif" font-size="27" font-weight="900" fill="#ffffff">참여자 통계</text>');
    placed.forEach(function(p){
      var r=p.c.r,x=p.x,cy=p.y,w=col,h=p.h;
      var name=esc(r.name||'-'),games=Number(r.games||0),arr=hm(r.arrivedAt),dep=hm(r.departedAt);
      parts.push('<rect x="'+x+'" y="'+cy+'" width="'+w+'" height="'+h+'" rx="14" fill="#ffffff" stroke="#bdd7dd" stroke-width="2"/>');
      parts.push('<circle cx="'+(x+34)+'" cy="'+(cy+36)+'" r="12" fill="#169bd5"/>');
      parts.push('<text x="'+(x+57)+'" y="'+(cy+46)+'" font-family="sans-serif" font-size="32" font-weight="900" fill="#071f2a">'+name+'</text>');
      parts.push('<text x="'+(x+w-315)+'" y="'+(cy+44)+'" font-family="sans-serif" font-size="27" font-weight="900" fill="#00956d">'+games+'회</text>');
      parts.push('<text x="'+(x+w-205)+'" y="'+(cy+25)+'" font-family="sans-serif" font-size="17" font-weight="800" fill="#607783">도착</text>');
      parts.push('<text x="'+(x+w-205)+'" y="'+(cy+48)+'" font-family="sans-serif" font-size="23" font-weight="900" fill="#173b49">'+esc(arr)+'</text>');
      parts.push('<text x="'+(x+w-92)+'" y="'+(cy+25)+'" font-family="sans-serif" font-size="17" font-weight="800" fill="#607783">귀가</text>');
      parts.push('<text x="'+(x+w-92)+'" y="'+(cy+48)+'" font-family="sans-serif" font-size="23" font-weight="900" fill="#173b49">'+esc(dep)+'</text>');
      parts.push('<line x1="'+(x+20)+'" y1="'+(cy+66)+'" x2="'+(x+w-20)+'" y2="'+(cy+66)+'" stroke="#d8e6e9" stroke-width="2"/>');
      parts.push('<text x="'+(x+22)+'" y="'+(cy+101)+'" font-family="sans-serif" font-size="22" font-weight="900" fill="#274d59">함께 경기한 사람 전체 '+(Array.isArray(r.partners)?r.partners.length:0)+'명</text>');
      p.c.lines.forEach(function(line,li){
        parts.push('<text x="'+(x+22)+'" y="'+(cy+139+li*38)+'" font-family="sans-serif" font-size="25" font-weight="800" fill="#073652">'+esc(line)+'</text>');
      });
    });
    parts.push('<rect x="0" y="'+(H-105)+'" width="'+W+'" height="105" fill="#e9fbf7"/>');
    parts.push('<text x="'+(W/2)+'" y="'+(H-57)+'" text-anchor="middle" font-family="sans-serif" font-size="21" font-weight="800" fill="#456873">자유민턴 게임 통계 · 원본 해상도 '+W+'×'+H+'</text>');
    parts.push('</svg>');
    return {svg:parts.join(''),w:W,h:H};
  }
  window.jmV20926SaveVectorReport=function(done){
    var made=build(),blob=new Blob([made.svg],{type:'image/svg+xml;charset=utf-8'}),url=URL.createObjectURL(blob),img=new Image();
    img.onload=function(){
      try{
        var cv=document.createElement('canvas');cv.width=made.w;cv.height=made.h;
        var ctx=cv.getContext('2d',{alpha:false});if(!ctx)throw new Error('canvas unavailable');
        ctx.fillStyle='#fff';ctx.fillRect(0,0,made.w,made.h);ctx.drawImage(img,0,0,made.w,made.h);
        URL.revokeObjectURL(url);
        var png=cv.toDataURL('image/png',1.0);
        if(!png||png.indexOf('data:image/png')!==0)throw new Error('PNG conversion failed');
        var d=new Date(),name='자유민턴_게임통계_'+d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')+'.png';
        if(window.NativeBrowser&&typeof window.NativeBrowser.saveStatisticsPng==='function')window.NativeBrowser.saveStatisticsPng(png,name);
        else{var a=document.createElement('a');a.href=png;a.download=name;document.body.appendChild(a);a.click();a.remove();}
        if(done)done(true);
      }catch(e){URL.revokeObjectURL(url);if(done)done(false,e);}
    };
    img.onerror=function(){URL.revokeObjectURL(url);if(done)done(false,new Error('vector render failed'));};
    img.src=url;
  };
})();
</script>
'''

if "</body>" not in html:
    raise SystemExit("v209.26 body close missing")
html = html.replace("</body>", script + "\n</body>", 1)

new_save = r'''function saveFullImage(){
  if(busy)return;
  if(typeof window.jmV20926SaveVectorReport!=='function'){alert('고해상도 저장 기능을 불러오지 못했습니다.');return;}
  setBusy(true,'고해상도 이미지 만드는 중…');
  var finished=false;
  function done(ok,err){if(finished)return;finished=true;setBusy(false);if(!ok)alert('전체 이미지 저장 실패: '+((err&&err.message)||'다시 시도해 주세요.'));}
  try{window.jmV20926SaveVectorReport(done);}catch(e){done(false,e);}
  setTimeout(function(){if(!finished)done(false,new Error('저장 시간 초과'));},45000);
}'''

pat = re.compile(r"function saveFullImage\(\)\{.*?\n\}\nfunction install\(\)\{", re.S)
m = pat.search(html)
if not m:
    raise SystemExit("v209.26 active saveFullImage boundaries missing")
html = html[:m.start()] + new_save + "\nfunction install(){" + html[m.end():]

for token in (
    MARKER,
    "window.jmV20926SaveVectorReport",
    "W=2000",
    "ctx.drawImage(img,0,0,made.w,made.h)",
    "window.NativeBrowser.saveStatisticsPng(png,name)",
    "전체 이력 펼침",
):
    if token not in html:
        raise SystemExit("v209.26 output missing: " + token)

active = re.search(r"function saveFullImage\(\)\{.*?\n\}\nfunction install\(\)\{", html, re.S)
if not active or "NativeReportCapture" in active.group(0):
    raise SystemExit("v209.26 screenshot exporter still active")

html_path.write_text(html, encoding="utf-8")
print("ADMIN_V20926_DIRECT_VECTOR_REPORT_OK")
