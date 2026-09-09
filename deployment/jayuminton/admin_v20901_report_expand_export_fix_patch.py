#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
MARKER='JAYUMINTON_GAME_REPORT_EXPAND_EXPORT_V20901'
if MARKER in s:
    print('ADMIN_GAME_REPORT_EXPAND_EXPORT_V20901_ALREADY_OK'); raise SystemExit(0)
for token in ('JAYUMINTON_GAME_REPORT_POSTER_V20895','JAYUMINTON_GAME_REPORT_POLISH_V20899','JAYUMINTON_GAME_REPORT_VISUAL_FIX_V20900','window.__JAYUMINTON_GAME_REPORT_V20895__'):
    if token not in s: raise SystemExit('v209.01 prerequisite missing: '+token)

STYLE=r'''
<style id="jmReportExpandExportV20901Style">
/* JAYUMINTON_GAME_REPORT_EXPAND_EXPORT_V20901_CSS */
.j95-actions{flex-wrap:wrap!important;align-items:center!important;gap:7px!important;padding:9px 10px!important}
.j101-tool{min-height:36px!important;padding:0 13px!important;border-radius:999px!important;border:1px solid #badbd2!important;background:rgba(255,255,255,.96)!important;color:#24594d!important;font-size:12px!important;font-weight:950!important;letter-spacing:-.02em!important;box-shadow:0 3px 9px rgba(23,90,73,.08)!important;cursor:pointer!important;touch-action:manipulation!important}
.j101-tool:disabled{opacity:.43!important;box-shadow:none!important;cursor:default!important}
.j101-tool:not(:disabled):active{transform:translateY(1px)!important}
.j95-save{min-height:38px!important;padding:0 16px!important;border-radius:999px!important;font-size:12px!important;white-space:nowrap!important}
.j95-close{min-height:38px!important;padding:0 15px!important;border-radius:999px!important;font-size:12px!important}
.j101-exporting{opacity:.7!important;pointer-events:none!important}
@media(max-width:720px){
 .j95-actions{gap:5px!important;padding:7px 6px!important}
 .j101-tool,.j95-save,.j95-close{min-height:34px!important;padding-left:10px!important;padding-right:10px!important;font-size:10.5px!important}
}
</style>
'''

SCRIPT=r'''
<script id="jayumintonGameReportExpandExportV20901Script">
/* JAYUMINTON_GAME_REPORT_EXPAND_EXPORT_V20901 */
(function(){'use strict';
var busy=false;
function poster(){return document.getElementById('j95Poster');}
function actionBar(){var p=poster();return p&&p.parentElement?p.parentElement.querySelector('.j95-actions'):document.querySelector('#pairStatisticsModal .j95-actions');}
function makeTool(id,text,fn){var b=document.createElement('button');b.type='button';b.id=id;b.className='j101-tool';b.textContent=text;b.addEventListener('click',fn);return b;}
function updateTools(){
  var p=poster(),ex=document.getElementById('jmReportExpandAllV20901'),co=document.getElementById('jmReportCollapseAllV20901');
  if(ex)ex.disabled=!p||!p.querySelector('.j95-more')||busy;
  if(co)co.disabled=!p||!p.querySelector('.j95-collapse')||busy;
}
function ensureControls(){
  var bar=actionBar();if(!bar)return;
  var save=bar.querySelector('.j95-save');if(!save)return;
  if(!document.getElementById('jmReportExpandAllV20901'))bar.insertBefore(makeTool('jmReportExpandAllV20901','전체 펼침',expandAll),save);
  if(!document.getElementById('jmReportCollapseAllV20901'))bar.insertBefore(makeTool('jmReportCollapseAllV20901','전체 접힘',collapseAll),save);
  save.type='button';save.textContent='📷 전체 이미지 저장';
  updateTools();
}
function expandAll(){
  var p=poster();if(!p||busy)return;
  var list=Array.prototype.slice.call(p.querySelectorAll('.j95-more'));
  list.forEach(function(b){try{b.click();}catch(_){}});
  requestAnimationFrame(function(){requestAnimationFrame(function(){ensureControls();});});
}
function collapseAll(){
  var p=poster();if(!p||busy)return;
  var list=Array.prototype.slice.call(p.querySelectorAll('.j95-collapse'));
  list.forEach(function(b){try{b.click();}catch(_){}});
  requestAnimationFrame(function(){requestAnimationFrame(function(){ensureControls();});});
}
function reportCss(){
  var out=['*{box-sizing:border-box}html,body{margin:0;padding:0;background:#d8f7e8}'];
  Array.prototype.forEach.call(document.querySelectorAll('style'),function(st){
    var id=String(st.id||'');
    if(/GameReport|Report.*V20|jmReport/i.test(id))out.push(st.textContent||'');
  });
  return out.join('\n');
}
function cleanClone(c){
  c.id='j101ExportPoster';
  c.style.margin='0';c.style.maxWidth='none';c.style.maxHeight='none';c.style.height='auto';c.style.overflow='visible';
  c.querySelectorAll('.j95-collapse,.j95-more').forEach(function(n){n.remove();});
  c.querySelectorAll('[aria-expanded]').forEach(function(n){n.removeAttribute('aria-expanded');});
}
function b64utf8(s){return btoa(unescape(encodeURIComponent(s)));}
function setBusy(v,msg){
  busy=v;
  var bar=actionBar(),save=bar&&bar.querySelector('.j95-save');
  if(bar)bar.classList.toggle('j101-exporting',v);
  if(save){if(!save.dataset.j101Label)save.dataset.j101Label='📷 전체 이미지 저장';save.textContent=v?(msg||'이미지 만드는 중…'):save.dataset.j101Label;}
  updateTools();
}
function fail(host,msg){if(host&&host.parentNode)host.parentNode.removeChild(host);setBusy(false);alert(msg);}
function saveFullImage(){
  var p=poster();if(!p){alert('저장할 통계 화면이 없습니다.');return;}if(busy)return;
  setBusy(true,'이미지 만드는 중…');
  var rect=p.getBoundingClientRect(),w=Math.max(320,Math.ceil(rect.width||p.offsetWidth||941));
  var c=p.cloneNode(true);cleanClone(c);c.style.width=w+'px';
  var host=document.createElement('div');host.setAttribute('aria-hidden','true');host.style.cssText='position:fixed;left:-20000px;top:0;width:'+w+'px;z-index:-2147483647;pointer-events:none;overflow:visible;background:#d8f7e8';host.appendChild(c);document.body.appendChild(host);
  requestAnimationFrame(function(){requestAnimationFrame(function(){
    try{
      var h=Math.max(600,Math.ceil(c.scrollHeight||c.getBoundingClientRect().height));
      if(h>30000){fail(host,'전체 이미지 높이가 너무 큽니다. 일부 항목을 접은 뒤 다시 저장해 주세요.');return;}
      var css=reportCss();
      var markup='<div xmlns="http://www.w3.org/1999/xhtml" style="margin:0;padding:0;width:'+w+'px;background:#d8f7e8"><style>'+css+'</style>'+c.outerHTML+'</div>';
      var svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'"><foreignObject x="0" y="0" width="'+w+'" height="'+h+'">'+markup+'</foreignObject></svg>';
      var im=new Image(),done=false;
      var finish=function(){if(done)return;done=true;try{
        var cv=document.createElement('canvas');cv.width=w;cv.height=h;var ctx=cv.getContext('2d');
        if(!ctx)throw new Error('canvas context unavailable');
        ctx.fillStyle='#d8f7e8';ctx.fillRect(0,0,w,h);ctx.drawImage(im,0,0,w,h);
        var data=cv.toDataURL('image/png',1.0);if(!data||data.indexOf('data:image/png')!==0)throw new Error('PNG conversion failed');
        if(host.parentNode)host.parentNode.removeChild(host);
        var now=new Date(),yy=now.getFullYear(),mm=String(now.getMonth()+1).padStart(2,'0'),dd=String(now.getDate()).padStart(2,'0');
        var name='자유민턴_게임통계_'+yy+'-'+mm+'-'+dd+'.png';
        if(window.NativeBrowser&&typeof window.NativeBrowser.saveStatisticsPng==='function'){
          window.NativeBrowser.saveStatisticsPng(data,name);setBusy(false);
        }else{
          var a=document.createElement('a');a.href=data;a.download=name;document.body.appendChild(a);a.click();a.remove();setBusy(false);
        }
      }catch(err){fail(host,'전체 이미지 저장 실패: '+(err&&err.message?err.message:err));}};
      im.onload=finish;
      im.onerror=function(){if(done)return;try{
        var blob=new Blob([svg],{type:'image/svg+xml;charset=utf-8'}),url=URL.createObjectURL(blob),im2=new Image();
        im2.onload=function(){try{im=im2;URL.revokeObjectURL(url);finish();}catch(e){URL.revokeObjectURL(url);fail(host,'전체 이미지 저장 실패: '+(e.message||e));}};
        im2.onerror=function(){URL.revokeObjectURL(url);fail(host,'전체 이미지를 만들지 못했습니다.');};im2.src=url;
      }catch(e){fail(host,'전체 이미지를 만들지 못했습니다: '+(e.message||e));}};
      im.src='data:image/svg+xml;base64,'+b64utf8(svg);
    }catch(err){fail(host,'전체 이미지 저장 실패: '+(err&&err.message?err.message:err));}
  });});
}
function install(){
  var api=window.__JAYUMINTON_GAME_REPORT_V20895__;
  if(api&&typeof api.render==='function'&&!api.render.__jmV20901){
    var base=api.render;
    function wrapped(){var r=base.apply(this,arguments);setTimeout(ensureControls,0);requestAnimationFrame(ensureControls);return r;}
    wrapped.__jmV20901=true;wrapped.__jmBase=base;api.render=wrapped;window.renderPairStatistics=wrapped;window.renderMdPairStatistics=wrapped;
  }
  window.jmExpandAllGameReport=expandAll;window.jmCollapseAllGameReport=collapseAll;window.jmSaveGameReportImage=saveFullImage;
  ensureControls();
}
document.addEventListener('click',function(ev){if(ev.target&&ev.target.closest&&ev.target.closest('.j95-more,.j95-collapse'))setTimeout(ensureControls,0);},false);
install();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});setTimeout(install,50);setTimeout(install,500);setTimeout(install,1300);
})();
</script>
'''

if '</head>' not in s or '</body>' not in s: raise SystemExit('v209.01 html anchors missing')
s=s.replace('</head>',STYLE+'\n</head>',1)
s=s.replace('</body>',SCRIPT+'\n</body>',1)
for token in (MARKER,'JAYUMINTON_GAME_REPORT_EXPAND_EXPORT_V20901_CSS','전체 펼침','전체 접힘','saveFullImage','window.jmSaveGameReportImage=saveFullImage','j101ExportPoster'):
    if token not in s: raise SystemExit('v209.01 contract missing: '+token)
p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_EXPAND_EXPORT_V20901_OK')
