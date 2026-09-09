#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
MARKER='JAYUMINTON_GAME_REPORT_HEADER_V20897'
if MARKER in s:
    print('ADMIN_GAME_REPORT_HEADER_V20897_ALREADY_OK'); raise SystemExit(0)
for token in ('JAYUMINTON_GAME_REPORT_POSTER_V20895','JAYUMINTON_GAME_REPORT_LOAD_FIX_V20896','window.__JAYUMINTON_GAME_REPORT_V20895__'):
    if token not in s: raise SystemExit('v208.97 prerequisite missing: '+token)

SCRIPT=r'''
<script id="jayumintonGameReportHeaderV20897Script">
/* JAYUMINTON_GAME_REPORT_HEADER_V20897 */
(function(){'use strict';
  var SAT_TIME='14:00~17:00';
  var SUN_TIME='14:30~17:30';
  var CSS=`
/* JAYUMINTON_GAME_REPORT_HEADER_V20897_CSS */
.j95-hero.j97-hero{padding-top:23px!important;padding-bottom:25px!important;background:radial-gradient(circle at 8% 7%,rgba(255,255,255,.98) 0 4%,transparent 18%),radial-gradient(circle at 72% 4%,rgba(255,255,255,.78) 0 7%,transparent 24%),radial-gradient(circle at 94% 13%,rgba(255,255,255,.84) 0 7%,transparent 22%),linear-gradient(180deg,#9edfff 0%,#dff7ff 53%,#b8f2cb 100%)!important}
.j97-kicker{position:relative;z-index:5;margin:0 auto 8px;width:max-content;max-width:80%;padding:6px 15px;border:1px solid rgba(10,71,95,.14);border-radius:999px;background:rgba(255,255,255,.64);backdrop-filter:blur(8px);color:#35637a;font-size:clamp(9px,1.2vw,13px);font-weight:900;letter-spacing:.22em;text-align:center}
.j95-brand.j97-brand{position:relative;z-index:6;width:max-content;max-width:82%;margin:0 auto!important;padding:0!important;line-height:.9!important;font-size:clamp(58px,9.7vw,104px)!important;font-weight:1000!important;letter-spacing:-.085em!important;color:#092f52!important;text-shadow:0 2px 0 rgba(255,255,255,.92),0 10px 28px rgba(2,65,95,.19)!important;filter:none!important}
.j97-brand-free{color:#092f52}.j97-brand-minton{color:#39d9a1;-webkit-text-stroke:1.2px #0a3b55;text-shadow:0 2px 0 rgba(255,255,255,.9),0 7px 18px rgba(27,169,129,.24)}
.j97-sportmarks{position:absolute;z-index:5;inset:0;pointer-events:none}.j97-mark{position:absolute;display:block;filter:drop-shadow(0 5px 8px rgba(3,69,98,.13))}.j97-mark svg{display:block;width:100%;height:auto}.j97-mark.left{left:23%;top:8%;width:7.2%;transform:rotate(-15deg)}.j97-mark.right{right:16%;top:13%;width:11%;transform:rotate(10deg)}
.j97-mark path,.j97-mark line,.j97-mark ellipse,.j97-mark circle{vector-effect:non-scaling-stroke}
.j95-dog,.j95-shuttle{display:none!important}
.j95-noteL{left:4%!important;top:5%!important;color:#14394c!important;opacity:.88}.j95-noteR{right:3.5%!important;top:4%!important;color:#5268c9!important;opacity:.86}.j95-motto{left:5%!important;top:27%!important;color:#5f74c9!important;opacity:.8}
.j95-sub{margin-top:17px!important;color:#0a2b4d!important;text-shadow:0 1px 0 rgba(255,255,255,.8)}.j95-cap{color:#4253b1!important}
.j95-date.j97-date{display:flex;align-items:center;justify-content:center;gap:8px;max-width:82%;padding:9px 21px!important;background:rgba(255,255,255,.91)!important;border:1px solid rgba(17,83,116,.11);color:#153b64!important;box-shadow:0 8px 22px rgba(8,78,104,.11)!important;letter-spacing:-.015em}.j97-cal{width:18px;height:18px;flex:0 0 auto}.j97-cal path,.j97-cal rect,.j97-cal line{stroke:#1764b5}
.j97-footer-sport{position:absolute;z-index:3;right:5.5%;bottom:13px;width:92px;transform:rotate(-7deg);opacity:.92}.j97-footer-sport svg{display:block;width:100%;height:auto;filter:drop-shadow(0 4px 5px rgba(0,69,75,.12))}
@media(max-width:720px){.j97-kicker{font-size:7px;padding:4px 10px;margin-bottom:5px}.j95-brand.j97-brand{font-size:clamp(42px,12.5vw,69px)!important;max-width:78%}.j97-mark.left{left:17%;top:7%;width:8%}.j97-mark.right{right:9%;top:14%;width:13%}.j95-noteL{font-size:8px!important}.j95-noteR{font-size:7px!important}.j95-motto{font-size:6px!important}.j95-date.j97-date{font-size:10px!important;padding:7px 13px!important}.j97-cal{width:14px;height:14px}.j97-footer-sport{width:66px;right:5%;bottom:9px}}
`;
  function rows(){return Array.isArray(window.ADMIN_PAIR_STATISTICS)?window.ADMIN_PAIR_STATISTICS:(Array.isArray(window.MD_PAIR_STATISTICS)?window.MD_PAIR_STATISTICS:[]);}
  function validDate(v){var d=v?new Date(String(v)):null;return d&&!Number.isNaN(d.getTime())?d:null;}
  function kstParts(d){
    try{
      var p=new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(d),o={};
      p.forEach(function(x){if(x.type!=='literal')o[x.type]=x.value;});
      return {y:Number(o.year),m:Number(o.month),d:Number(o.day)};
    }catch(_){return {y:d.getFullYear(),m:d.getMonth()+1,d:d.getDate()};}
  }
  function sessionDate(){
    var ds=[];rows().forEach(function(r){var a=validDate(r.arrivedAt),b=validDate(r.departedAt);if(a)ds.push(a);else if(b)ds.push(b);});
    ds.sort(function(a,b){return a-b;});return ds[0]||new Date();
  }
  function two(n){return String(n).padStart(2,'0');}
  function scheduleText(){
    var p=kstParts(sessionDate()),dow=new Date(Date.UTC(p.y,p.m-1,p.d)).getUTCDay(),label=dow===6?'토':dow===0?'일':['일','월','화','수','목','금','토'][dow],time=dow===6?SAT_TIME:dow===0?SUN_TIME:'';
    if(!time){
      var list=rows(),starts=list.map(function(r){return validDate(r.arrivedAt);}).filter(Boolean).sort(function(a,b){return a-b;}),ends=list.map(function(r){return validDate(r.departedAt);}).filter(Boolean).sort(function(a,b){return a-b;});
      function hm(d){if(!d)return '--:--';try{return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',hour:'2-digit',minute:'2-digit',hour12:false}).format(d);}catch(_){return two(d.getHours())+':'+two(d.getMinutes());}}
      time=hm(starts[0])+'~'+hm(ends.length?ends[ends.length-1]:null);
    }
    return p.y+'.'+two(p.m)+'.'+two(p.d)+' ('+label+') · '+time;
  }
  function calendarIcon(){return '<svg class="j97-cal" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3.5" y="5.5" width="17" height="15" rx="3" stroke-width="2"/><line x1="7" y1="3" x2="7" y2="8" stroke-width="2" stroke-linecap="round"/><line x1="17" y1="3" x2="17" y2="8" stroke-width="2" stroke-linecap="round"/><line x1="4" y1="10" x2="20" y2="10" stroke-width="2"/></svg>';}
  function sportMarks(){return '<div class="j97-sportmarks" aria-hidden="true"><span class="j97-mark left"><svg viewBox="0 0 80 80" fill="none"><path d="M31 45L17 61M34 48L23 69M39 50L34 72" stroke="#0b4670" stroke-width="3" stroke-linecap="round"/><path d="M28 42C34 31 44 22 58 15C63 23 65 31 64 40C53 41 41 42 28 42Z" fill="rgba(255,255,255,.9)" stroke="#0b4670" stroke-width="3" stroke-linejoin="round"/><path d="M30 42L63 39" stroke="#34d9a0" stroke-width="4" stroke-linecap="round"/></svg></span><span class="j97-mark right"><svg viewBox="0 0 120 120" fill="none"><ellipse cx="43" cy="41" rx="23" ry="31" transform="rotate(-25 43 41)" fill="rgba(255,255,255,.74)" stroke="#0b3658" stroke-width="3"/><path d="M27 19L58 65M20 31L51 76M34 12L66 58M18 45L46 82M45 11L70 46M24 59L37 82M16 37L65 24M21 53L70 38M29 68L73 53" stroke="#0b3658" stroke-width="1.5" opacity=".75"/><path d="M61 67L96 106" stroke="#0b3658" stroke-width="7" stroke-linecap="round"/><circle cx="98" cy="108" r="6" fill="#36d9a0" stroke="#0b3658" stroke-width="2"/></svg></span></div>';}
  function footerSport(){return '<div class="j97-footer-sport" aria-hidden="true"><svg viewBox="0 0 120 75" fill="none"><path d="M18 44C39 31 55 22 79 13" stroke="#15a77d" stroke-width="4" stroke-linecap="round"/><path d="M36 52C53 42 70 34 94 28" stroke="#6adcb7" stroke-width="3" stroke-linecap="round"/><path d="M78 10L94 17L100 35L86 43L72 31Z" fill="white" stroke="#0b4662" stroke-width="2.5" stroke-linejoin="round"/><path d="M79 11L73 30M87 14L81 36M94 18L89 40" stroke="#0b4662" stroke-width="2"/><path d="M71 31L87 43" stroke="#23ce97" stroke-width="4" stroke-linecap="round"/></svg></div>';}
  function appendCss(){var st=document.getElementById('jayumintonGameReportPosterV20895Style');if(st&&st.textContent.indexOf('JAYUMINTON_GAME_REPORT_HEADER_V20897_CSS')<0)st.textContent+='\n'+CSS;}
  function apply(){
    appendCss();
    var poster=document.getElementById('j95Poster');if(!poster)return;
    poster.setAttribute('data-jm-style','208.97');
    var hero=poster.querySelector('.j95-hero');if(hero){hero.classList.add('j97-hero');hero.querySelectorAll('.j95-dog,.j95-shuttle,.j97-sportmarks,.j97-kicker').forEach(function(n){n.remove();});var brand=hero.querySelector('.j95-brand');if(brand){brand.classList.add('j97-brand');brand.innerHTML='<span class="j97-brand-free">자유</span><span class="j97-brand-minton">민턴</span>';brand.insertAdjacentHTML('beforebegin','<div class="j97-kicker">JAYUMINTON · BADMINTON CLUB</div>');hero.insertAdjacentHTML('beforeend',sportMarks());}var date=hero.querySelector('.j95-date');if(date){date.classList.add('j97-date');date.innerHTML=calendarIcon()+'<span>'+scheduleText()+'</span>';}}
    poster.querySelectorAll('.j95-dog').forEach(function(n){n.remove();});
    var footer=poster.querySelector('.j95-footer');if(footer){footer.querySelectorAll('.j97-footer-sport').forEach(function(n){n.remove();});footer.insertAdjacentHTML('beforeend',footerSport());}
  }
  function install(){
    appendCss();var api=window.__JAYUMINTON_GAME_REPORT_V20895__;if(!api||typeof api.render!=='function')return;
    if(api.render.__jmV20897)return;
    var base=api.render;function wrapped(){var r=base.apply(this,arguments);apply();return r;}wrapped.__jmV20897=true;wrapped.__jmBase=base;api.render=wrapped;window.renderPairStatistics=wrapped;window.renderMdPairStatistics=wrapped;window.__JAYUMINTON_GAME_REPORT_HEADER_V20897__={apply:apply,scheduleText:scheduleText};
  }
  install();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});setTimeout(install,0);setTimeout(install,450);setTimeout(install,1200);
})();
</script>
'''
if '</body>' not in s: raise SystemExit('body anchor missing')
s=s.replace('</body>',SCRIPT+'\n</body>',1)
for token in (MARKER,"SAT_TIME='14:00~17:00'","SUN_TIME='14:30~17:30'",'data-jm-style','JAYUMINTON · BADMINTON CLUB','j97-brand-minton','window.__JAYUMINTON_GAME_REPORT_HEADER_V20897__'):
    if token not in s: raise SystemExit('v208.97 header contract missing: '+token)
p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_HEADER_V20897_OK')
