#!/usr/bin/env python3
from pathlib import Path
import re
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
MARKER='JAYUMINTON_GAME_REPORT_VISUAL_FIX_V20900'
if MARKER in s:
    print('ADMIN_GAME_REPORT_VISUAL_FIX_V20900_ALREADY_OK'); raise SystemExit(0)
for token in ('JAYUMINTON_GAME_REPORT_POSTER_V20895','JAYUMINTON_GAME_REPORT_USABILITY_V20898','JAYUMINTON_GAME_REPORT_POLISH_V20899','window.__JAYUMINTON_GAME_REPORT_V20895__'):
    if token not in s: raise SystemExit('v209.00 prerequisite missing: '+token)

DOG_URI='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAF4AAABdCAYAAAAsRtHAAAAbKklEQVR42u1dd1hUV9r/TYHBoQwDAzOAQ1FgCIh0VESBqFjQhdiiEYNRYyUxq6gENjGJxiS7X+yJRo0xGBU3KsG+qwKCT0SlSIJSlV6kD9UCvN8fZm4YRQQZsrb3ed6HMnfOued3T3n7ZRERXtEDksvlJxobG/3u3LkDIoK6ujpMTU1ZfdEXVxWNNDc3hzY2Nn6hoaFxSEdHZ8bzBvilS5coJycHubm5KCsrQ2NjI9ra2qCpqQk3Nzfy8PCAo6OjSh8A62lnfH5+Pilu9NatWygrK4Oenh7c3NwwePBgDBw4kPWsA15VVUV79uzB8ePHkZ2djdraWty/f1/pGqFQCDc3N8ycORNz5sxR3ZiIqEeck5NDW7dupTfeeIOcnJzI1NSUtLS0iM1mE5/PJ5lMRlOmTKHIyEiSy+WRPW3/r+Tly5eTnp4eAXgim5mZ0ebNm0lVfffo4tjYWJo8eTJJJBJis9mPvUkul0uOjo506tQpelZBT0lJIX19fQJALBaLhEIhvf766zR37lwKDQ2l1atXk6+vL2lrazPjMjIyooiICPpLgb969Sr5+fkRj8dTAtnQ0JCGDx9OkydPJltbWyXwx48fT9evX3/mwM/NzaXAwEDicDgEgHR1dWnjxo2UnZ1NJSUlVF1dnVlVVVWck5ND69atI5FIpDTzN27cSH8J8I2NjevCwsJIU1OTuQFHR0fatGkTJScnU0lJCd2+fZuuXbtG8+fPZwbE4/FozZo1VFNTk/SsgF5ZWUlTp05VGouZmRkVFxd3CmZ9ff3u1atXM9ezWCyysrKitLQ06nPgU1JSaMyYMcyNjhs3jvLz8zvtOD09nQICAphrpVIpJSUldesmb926RfHx8XTx4kW6fv065efn07FjxysiIoKqqqqKiQilpaW0d+9e+vTTT+nnn3+mmJgYOnDgAP3yyy+UlZX1xH727t1LxsbGSitz2bJlT/xeSEgIcblcAkBaWlr02Wef9T3w+/fvp/79+xMA4nA4dOzYsS47PXr0KFlaWjKDGzt2LJWXl9PjZmBMTAzNnTuXOTs4HA5paWmRUCgkAKShoUELFiyg4uJiWrRoEdMui8UiFovF/K2trU2+vr4UERFBdXV1Jx7uq66u7oS/vz8DoJqaGn3yySfdBlAmkzH92tvb040bN6jPgK+trY1buXIlc5gOGTKEsrOzu+ywqqqqeMmSJaSmpsaAMn36dKqurs7sKB0tXLiQLCwsSENDo0uJgs1m09ChQ2nfvn00YMCAJ0ogampq5OrqSoGBgTR27Fh6//336fLly5Senk5Dhw5l2lyxYkWPgNu+fTuDg6GhIW3btq3vgM/IyCB/f3/mSb/33ntUUVFB3TmMx48fr3QYr1q1ihTbxcyZMx8BjM/nk0QiISMjIzIwMCB9fX2SSCTk5ORE+/fvp/T0dBo/fjyJRCLmGpFIRGZmZiSVSkkgECitgI48depUSk9Pp8WLF5NUKiUXFxe6detWj4CTy+WRipWvo6NDoaGhTw38EzVXhYIEAP369YOTkxMMDAyeqEi4urqyQkND6d69e0hISMC9e/eQlJQEAIiNjcXBgwcBAGpqatDV1YVIJIKnpyeGDx8OLpeLhoYG3LlzB0KhEC4uLhg0aBALAP7xj39QUlISRCIRamtr0dbWBltbW7S0tODq1av4z3/+g6ysLNy9excaGhq4c+cO2traUF1djebmZoSHh2PUqFGwsbGBhYVFjxQiHR2dGf3793+zuLgY9+7dQ2VlZd+ZDIqKilBaWgoAsLCwgI2NTbcbHzlyJCssLIx27dqFiooKLFiwAACQnZ0NDocDLpcLV1dX+Pv7w8XFBc7Ozhd0dXW9u2rTw8OD5eHh0elnkyZNwsyZMykyMhK3b9+GRCJBWVkZmpqa4OvrCysrqwu6urreU6ZMeSqwioqKqKKi4oHKz2KBy+X2jeZaV1d34tNPP2XEw4kTJ1JmZmaPl1dRURFlZGQw30tOTqbAwEAKCgqi06dP94mcX19fv1vxs7KyklSl6Sq2MrFYTDt37uybPb66ujozNDSU2SdHjBhBiYmJKhlEUVERFRYW0rNsUujIu3fvZjRdNTU1mjBhAhUUFPQN8E1NTaFbt24lPp/PHCjBwcGPFQ1fVD548CDJZDJmtpuYmNCJEyf6Vo5PSUmhCRMmMLKvmZlZtxWi552Li4vp888/p9dee43ZbtXV1emLL774a0wGGzZsIB0dHQJA5ubmlJKS8sIDn56eTm+//Tbp6+srGQRDQkJUYgJ54rFcW1ubVFpaiqamJgAAn88Hj8d7oT1RxcXFtHHjRvz73//GnTt3mHGvWLECISEhKnH2sLsh9Wi1traira0NAJCVlYWvv/4adXV1cc8iaHl5eaSCNpCens6AbmFhgQMHDuCzzz5jqczD1p1lcfr0aXJwcFDSCrtjWFIlV1RUUFRUFB05ckRJNH1Y3BMIBDR//vxObTU96SssLIzEYjGNGjWKkpOTVT7Wbl945swZcnd3Zw4ZAPTRRx9RQ0PDJlXJ3T/88AMFBwdTTEwMPSx6drSOvvbaa3T06FF6WPRViHumpqZ09erVHoMll8sjKysrqampKbSxsXFddnZ2n3nRenTxkSNHyMHBQQn8r776SiWz4eTJkzRo0CACQJ6ennT79m2m3RMnTjxiBPv4448feegfffQR2dnZ0dKlS3t8AN66dSv99ttvKCgoQHV1NRoaGph+dHR0EBAQgGXLlvVYOXwhge8YGq7wcUZERIDFYoHNZuPy5cuoq2uDx+PBx8cHNjY2r1DuhHbs2MGAzuFwIJPJMHHiRAwbNgwDBgyAubl5jxIWuK2tregYxqejo/MK5Q5UVVVFUVFRSExMRHt7O7hcLmbOnIlFixbBysqqW8nWnQKvqakJDofD/KOsrOwV2h1o165d2LFjB8rKyuDq6ooPPvgAo0eP7rUfgG1sbMx4wYEHIRuv6AHV1NRk/vrrrygpKUFbWxscHR0xa9YsliqcL2wLCwsYGxszs/7q1auvEP+DWltbZQAYt93DheJ6Q1ypVMqytLSkK1euoK2tDcePH8dHH31Ea9euVXqq2dnZFB8fD7lcjtbWVly/fh3Nzc3Q1dWFlZUVxo8fj8GDB7+QypbiDOyYLKGSRvft20cGBgZKdcYuXbpEityiffv2kaurK5NkjE7qyTg5Ob1wicdZWVk0fPhwJjY0JCREZeNjA8Df/va3Q2PGjIFEIoFQKISNjQ369++P0tJS2rx5sywkJARJSUlo7RA2x+FwoK6uzpiIi4qKkJCQ8ELN9Js3b6K6uvoBUGw27OzsVLfV/CFCzvjnP//5ZlRUFOrq6jBmzBgIhcLPDx48GL5161bU1tYCeBAVZWRkBA6HA5FIBENDQygqlEqlUpWH8D0LwCsyUAQCAVxdXVULPACYmJiwgoODmQ+uX79OkZGRqK2tBYvFgrW1NebPnw8PDw9wuVyIxWKIRKLPb968GR4fHw+JRAJvb+8XyhHS0NCAe/fuAXgQKmhqanpIpXt8Z/z9998z9nkTExPasGHDS2c8W7duHZOA4OjoqNLzq9Njura2Nik2NpYRn5ydnTF+/PiXzngml8uZGd+vXz+Vtt0p8Hl5eS6K7Dc+n4/BgwfDxsbmpbLLl5WVUV5eHhMPb2Zm1vfAZ2Vloby8nOlQlYfK80KFhYWMxgoATk5OfQ/8H9Y2aGhowM3NDUOHDn3pgC8qKmJceFwuV+VW207DO2Qy2YVp06Z55ebmYtWqVZBIJC+d+69jKIulpSXjp6ipqcnk8XiHb9++HZ6ZmYny8nIYGhrC3d0dhoaG3cepsxM3IiKCBAIBWVpa0p49e17KKIK1a9cy2X3W1ta0aNEicnZ2JjMzM7K1tWXS+xWa+4QJE3pU6LnTf86ZM4dp1M/P77mqlqcKLi0tpaCgoC5r5HfGYWFh3c567HSPHzRoEGORy8vLQ2pq6ku1zdy8eRNZWVmMi09BPB4PAoEAOjo60NPTg1gsVjKpFxQUoL6+3uWp9/hRo0ZBLBajvLwcN2/exNmzZ+Hh4UEikeil2OtTUlKQlZX1J0hcLkxMTODp6QkbGxvcvXsXQqEQ6urq2L59O27cuAEWiwWxWNx9ef9xCb6LFy9mrHIymazXGdvPC2dnZ9O0adOU0uWnTJlCBw4cUEpilsvlkRs3bmQ0W0NDw0fS75+qQlN8fDxZWVkxcZIBAQG9qpf+vPDFixfJzc2NiXlcv349k43dsQzX1q1bmZoLbDabpk+f3q0XBzwR+Lq6uhPr169nagqIxWLau3fvCw98UVERrVmzhoYOHUpz5859JLUoNTWVQkJClApd2NnZdZla3+OaZMnJyUqF7ocNG0abNm3qtH58bm4uXbp0iU6ePEmJiYmMQa2+vn53Xl4eZWRkUF5eXq+q4/1V1f6io6Pp4MGDj8zgw4cPk4+PDxPzjj/STLdt29bjcXWZEWJubp41atQomSKz+fLly8jPz0dpaSlmz55NxcXFKCoqQnJyMjIyMtDU1ISWlhbw+XzY2Nh49e/fn8rKylBcXIy7d++Cy+XC2NjYTyaTkbu7O9zc3JgKT88C5efn05YtW5CQkID+/ftDW1sb1tbWKC0tpe+++w6RkZFQZHew2WzY2Nhg+fLlCAgIKBEIBBNVYhZWcGJiIvn4+CjXjdHVJScnJxo4cCAZGRkpVbRAh/BkbW1t4vF4SvUq1dXVSVdXl6ysrGjq1KkUHR1NjY2N656F2X7+/HkmxFpNTY28vLxox44dNGPGDKX6NOrq6jR27Fg6ffr0U9fH6dZF165do/DwcKVg+8e9EqInrK6uTlKplObPn0+nT5+m8+fPU0REBB05cuR/YvvPyMggPz8/pTR6PT09pddtqKmpUVhY2GNLZnWXe1QMbv/+/bR27Vrk5OQwyoWuri6CgoKgp6cHoVAIAwMDpKam4uLFi6iuroZIJIKLiwuMjY1RUVGBpKQkJCcnM2GDijcPKBSR1tZWsFgsODk5Yfny5RgzZsz32tra8/+q7SY9PZ0+/vhjREVFPfKZsbExNm3a1K2qHU+iHlfhKygooMOHDyMtLQ3m5uaYPXs2rKysenQjqamptGfPHuzfvx91dXXo6h5kMhn8/f0xaNAgiEQiODg4wNjYuM8UufLycvrkk0/w3XffAQAcHR1hamoKc3NzhIaGqi5f4H+5p547d478/f1JJBKRjo4O6erqkp6eHvH5/E63MjU1NfL19aUrV670mViblpZG48aNY/p8/fXXeySf90mlVVXTqFGjWC4uLnGpqaleBQUF4PP5EAqFuHDhAqKjo1FeXg65XM64IFtbW5GWloZTp06By+WSoaEhTExMVDr7jYyM4ODggISEBDQ1NSE2NhanTp1SeU2cpy742df022+/UXx8POLi4pCXl4f79++DiHD37l20t7ejtbUVEydOxOrVq1Wei5WWlkarVq3C2bNnQUSYPXs2Nm/enKyKsl9dGsmeBRo8eDBr8ODBmD179on8/Hy/hoYGlJeXY8eOHYiLi0NbWxsuXbqEiooKSKVSlfYtEAggEAiUjGQsFquxz11/zxIJBIKJDg4OLE9PT5a6ujpyc3PR1tYGPp8PHx8fpcJtqqL4+HgkJSWBiMDhcGBvb6/yCItnHngFKUKmCwoKmOgHOzs7lbslz507R/v27WP6sbe3x8iRI1U+Hu7zAnx7e7usY5h0Q0MDYmNj4e3tTT19dVxndOHCBTp//jz++9//4vfff0d7ezv4fD6CgoIgk8k2v7TAi0Qilre3Nx07dgy5ubm4e/cuSkpKmFoBT+nQpuTkZJw7dw7nzp1DYWEhEysJPCj95efnp1Sn/qUDHniQkWhvb8/UbszPz8e2bdsgFApJW1sb7777Lng83vdpaWnztLW1oaenh379+qGxsRENDQ0Qi8VMJMCPP/5IP/zwAwoKClBdXY2GhgamHx0dHQQEBGDZsmU9Vg5fSOA7hoYrfJwRERFgsVhgs9m4fPky2tra5iUlJUFdXR06Ojrg8XhoaWlBc3MzzM3NsWHDBhIKhfjyyy+Rk5PDBCwpAPf29sZbb70FLy+vvg1red4cFR3fnPAwczgcpcgAxRuOFVowm82mr776ipKTk8nIyEipFv2MGTPo7Nmzf5mj55lVoLqi06dP09GjR5GZmYmKigrcu3cPlpaWmDFjBrZs2YKMjIw/za/4M4dJR0cHe/fuxaRJk1jHjx+n6OhoyGQyjBs3Dvb29n+pI/+5BP5hMbO1tVWm2Lvz8vIoNjYWtbW1qKioQHNzMzQ1NZl6kq6urp+rqg5xb+j/Afh/a9jwq7yfAAAAAElFTkSuQmCC'
s,n=re.subn(r"var DOG='data:image/[^']+',SHUTTLE=",lambda m:"var DOG='"+DOG_URI+"',SHUTTLE=",s,count=1)
if n!=1: raise SystemExit('v209.00 DOG source anchor mismatch')

STYLE=r"""
<style id="jmReportVisualFixV20900Style">
/* JAYUMINTON_GAME_REPORT_VISUAL_FIX_V20900_CSS */
.j97-kicker{display:none!important}
.j97-sportmarks{display:none!important}
.j98-shuttle{display:block!important;left:56%!important;top:5px!important;width:7.4%!important;min-width:42px!important;max-width:66px!important;transform:translateX(-50%) rotate(5deg)!important;z-index:6!important;pointer-events:none!important;object-fit:contain!important;filter:drop-shadow(0 4px 5px rgba(5,60,72,.13))!important}
.j95-brand.j97-brand{margin-top:56px!important;max-width:79%!important}
.j98-dog-top{right:4.1%!important;top:19%!important;width:12.5%!important;min-width:72px!important;max-width:110px!important;transform:none!important;z-index:8!important}
.j100-racket-held{position:absolute;right:.8%;top:12.8%;width:8.8%;min-width:54px;max-width:80px;z-index:7;pointer-events:none;filter:drop-shadow(0 4px 5px rgba(4,57,78,.14));transform:rotate(1deg)}
.j100-racket-held svg{display:block;width:100%;height:auto}
.j98-dog-bottom{right:4%!important;bottom:-24px!important;width:84px!important;min-width:0!important;max-width:84px!important;transform:none!important;clip-path:inset(0 0 36% 0)!important;z-index:6!important}
.j95-hc strong{font-size:clamp(14px,1.65vw,19px)!important;line-height:1.2!important;letter-spacing:-.025em!important;word-break:keep-all!important;overflow-wrap:anywhere!important}
.j95-hc em{font-size:clamp(13px,1.5vw,17px)!important;line-height:1.2!important}
body.jm-report-open-v20900 #jmAdminReplyButton{display:none!important}
.j95-partners{min-width:0!important;max-width:100%!important;overflow:visible!important;white-space:normal!important;word-break:keep-all!important}
.j95-expand-card{max-width:100%!important;overflow:visible!important}
.j95-more{position:relative!important;z-index:2!important;touch-action:manipulation!important}
@media(max-width:720px){
 .j98-shuttle{left:56%!important;top:4px!important;width:10%!important;min-width:38px!important;max-width:52px!important}
 .j95-brand.j97-brand{margin-top:43px!important;max-width:78%!important}
 .j98-dog-top{right:3.2%!important;top:18.5%!important;width:16%!important;min-width:58px!important;max-width:78px!important}
 .j100-racket-held{right:-.1%;top:12.8%;width:11.5%;min-width:43px;max-width:59px}
 .j98-dog-bottom{right:3%!important;bottom:-20px!important;width:68px!important;max-width:68px!important;clip-path:inset(0 0 34% 0)!important}
 .j95-hc strong{font-size:12.5px!important;line-height:1.18!important}
 .j95-hc em{font-size:12px!important}
 .j95-partners{font-size:9.5px!important;line-height:1.55!important;width:100%!important}
}
</style>
"""

SCRIPT=r"""
<script id="jayumintonGameReportVisualV20900Script">
/* JAYUMINTON_GAME_REPORT_VISUAL_FIX_V20900 */
(function(){'use strict';
function racket(){
  return '<span class="j100-racket-held" aria-hidden="true"><svg viewBox="0 0 100 125" fill="none">'+
    '<ellipse cx="68" cy="28" rx="20" ry="27" transform="rotate(18 68 28)" fill="rgba(255,255,255,.9)" stroke="#123a58" stroke-width="4"/>'+
    '<path d="M53 8L81 47M47 18L76 57M62 3L88 37M46 31L72 64M74 4L91 26M49 43L65 66M47 12L87 14M47 25L90 27M51 39L88 41" stroke="#123a58" stroke-width="1.5" opacity=".78"/>'+
    '<path d="M61 52L48 78" stroke="#123a58" stroke-width="6" stroke-linecap="round"/>'+
    '<path d="M48 77L42 91" stroke="#23a382" stroke-width="9" stroke-linecap="round"/>'+
    '</svg></span>';
}
function syncReportState(){
  var m=document.getElementById('pairStatisticsModal');
  document.body.classList.toggle('jm-report-open-v20900',!!(m&&!m.classList.contains('hidden')));
}
function apply(){
  var poster=document.getElementById('j95Poster');
  if(!poster){syncReportState();return;}
  poster.setAttribute('data-jm-style','209.00');
  var hero=poster.querySelector('.j95-hero');
  if(hero){
    hero.querySelectorAll('.j100-racket-held').forEach(function(n){n.remove();});
    var dog=hero.querySelector('.j98-dog-top');
    if(dog)dog.insertAdjacentHTML('afterend',racket());
  }
  syncReportState();
}
function observe(){
  var m=document.getElementById('pairStatisticsModal');
  if(!m||m.__jmV20900Observed)return;
  m.__jmV20900Observed=true;
  new MutationObserver(function(){syncReportState();}).observe(m,{attributes:true,attributeFilter:['class','style']});
  syncReportState();
}
function install(){
  var api=window.__JAYUMINTON_GAME_REPORT_V20895__;
  if(api&&typeof api.render==='function'&&!api.render.__jmV20900){
    var base=api.render;
    function wrapped(){var r=base.apply(this,arguments);apply();return r;}
    wrapped.__jmV20900=true;wrapped.__jmBase=base;
    api.render=wrapped;
    window.renderPairStatistics=wrapped;
    window.renderMdPairStatistics=wrapped;
  }
  observe();
  syncReportState();
}
install();
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
setTimeout(install,0);setTimeout(install,450);setTimeout(install,1200);
window.__JAYUMINTON_GAME_REPORT_VISUAL_FIX_V20900__={apply:apply,sync:syncReportState};
})();
</script>
"""

if '</head>' not in s or '</body>' not in s: raise SystemExit('v209.00 html anchors missing')
s=s.replace('</head>',STYLE+'\n</head>',1)
s=s.replace('</body>',SCRIPT+'\n</body>',1)
for token in (MARKER,'JAYUMINTON_GAME_REPORT_VISUAL_FIX_V20900_CSS','jm-report-open-v20900','j100-racket-held','data-jm-style','209.00','j98-shuttle{display:block!important'):
    if token not in s: raise SystemExit('v209.00 contract missing: '+token)
p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_VISUAL_FIX_V20900_OK')
