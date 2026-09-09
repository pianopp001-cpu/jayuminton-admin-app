#!/usr/bin/env python3
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app/src/main/assets/admin/index.html')
s=p.read_text(encoding='utf-8')
MARKER='JAYUMINTON_GAME_REPORT_LOAD_FIX_V20896'
if MARKER in s:
    print('ADMIN_GAME_REPORT_LOAD_FIX_V20896_ALREADY_OK'); raise SystemExit(0)
for token in ('JAYUMINTON_GAME_REPORT_RUNTIME_V20894','JAYUMINTON_GAME_REPORT_POSTER_V20895','window.__JAYUMINTON_GAME_REPORT_V20895__'):
    if token not in s: raise SystemExit('v208.96 prerequisite missing: '+token)

SCRIPT=r'''
<script id="jayumintonGameReportLoadFixV20896Script">
/* JAYUMINTON_GAME_REPORT_LOAD_FIX_V20896 */
(function(){'use strict';
  function modal(){return document.getElementById('pairStatisticsModal');}
  function list(){return document.getElementById('pairStatisticsList')||document.getElementById('mdPairStatisticsList')||(modal()&&modal().querySelector('.pair-statistics-list'));}
  function show(message){var t=list();if(t)t.innerHTML='<div style="padding:44px 20px;text-align:center;font-size:15px;font-weight:900;color:#285e52;background:linear-gradient(180deg,#dff5ff,#e5f8ee)">'+String(message||'')+'</div>';}
  async function openGameReportV20896(){
    var m=modal(),t=list();if(!m||!t){alert('게임 통계 화면을 찾을 수 없습니다.');return;}
    m.classList.remove('hidden');show('게임 통계를 불러오는 중...');
    var rows;
    try{
      /* getPairStatistics is authenticated by the Bearer session token in server().
         The compat worker ignores positional args for this RPC, so do not depend on
         ADMIN_PIN_VALUE here. That global is not guaranteed to exist in every APK runtime. */
      rows=await server('getPairStatistics',[]);
    }catch(fetchError){
      var fm=String(fetchError&&fetchError.message||fetchError||'알 수 없는 오류');
      show('통계를 불러오지 못했습니다.<br><small style="display:block;margin-top:8px;color:#64748b">'+fm.replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];})+'</small>');
      alert('게임 통계 불러오기 실패: '+fm);return;
    }
    window.ADMIN_PAIR_STATISTICS=Array.isArray(rows)?rows:[];
    window.MD_PAIR_STATISTICS=window.ADMIN_PAIR_STATISTICS;
    try{
      var api=window.__JAYUMINTON_GAME_REPORT_V20895__;
      if(!api||typeof api.render!=='function')throw new Error('v208.95 포스터 렌더러를 찾을 수 없습니다.');
      api.render();
      if(!t.querySelector('[data-jm-poster="208.95"]'))throw new Error('포스터 화면 생성 확인에 실패했습니다.');
    }catch(renderError){
      var rm=String(renderError&&renderError.message||renderError||'알 수 없는 오류');
      show('통계 데이터는 받았지만 화면을 만들지 못했습니다.<br><small style="display:block;margin-top:8px;color:#64748b">'+rm.replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];})+'</small>');
      alert('게임 통계 화면 생성 실패: '+rm);
    }
  }
  function install(){window.openPairStatistics=openGameReportV20896;window.openMdPairStatistics=openGameReportV20896;}
  install();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});setTimeout(install,0);setTimeout(install,500);setTimeout(install,1300);
  window.__JAYUMINTON_GAME_REPORT_LOAD_FIX_V20896__={open:openGameReportV20896,install:install};
})();
</script>
'''
if '</body>' not in s: raise SystemExit('body anchor missing')
s=s.replace('</body>',SCRIPT+'\n</body>',1)
for token in (MARKER,"server('getPairStatistics',[])",'window.openPairStatistics=openGameReportV20896','data-jm-poster=\\"208.95\\"','게임 통계 화면 생성 실패'):
    if token not in s: raise SystemExit('v208.96 load-fix contract missing: '+token)
p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_LOAD_FIX_V20896_OK')
