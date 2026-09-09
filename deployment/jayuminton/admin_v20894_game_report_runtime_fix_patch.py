#!/usr/bin/env python3
from pathlib import Path
import re, sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
s = p.read_text(encoding='utf-8')
MARKER = 'JAYUMINTON_GAME_REPORT_RUNTIME_V20894'

if MARKER in s:
    print('ADMIN_GAME_REPORT_RUNTIME_V20894_ALREADY_OK')
    raise SystemExit(0)

for token in (
    'JAYUMINTON_GAME_REPORT_V20893',
    'id="pairStatisticsModal"',
    'function openPairStatistics()',
    'window.__JAYUMINTON_GAME_REPORT_V20893__',
):
    if token not in s:
        raise SystemExit('v208.94 prerequisite missing: ' + token)

# Normalize every visible legacy statistics title. The old renderer may still exist in
# the document for compatibility, but it must no longer be the user-facing route.
s = s.replace('📊 함께 경기 통계', '📊 게임 통계')
s = s.replace('함께 경기통계', '게임 통계')
s = s.replace('함께 경기 통계', '게임 통계')

STYLE = r'''
<style id="jayumintonGameReportRuntimeV20894Style">
/* JAYUMINTON_GAME_REPORT_RUNTIME_V20894 */
#pairStatisticsModal .pair-statistics-modal{
  width:min(980px,98vw)!important;
  max-width:980px!important;
  max-height:94vh!important;
  padding:0!important;
  overflow:auto!important;
  border:0!important;
  border-radius:24px!important;
  background:#eaf8f1!important;
  box-shadow:0 24px 72px rgba(0,37,27,.34)!important;
}
#pairStatisticsModal .modal-head{
  margin:0!important;
  padding:10px 14px!important;
  min-height:48px!important;
  background:rgba(255,255,255,.97)!important;
  border-bottom:1px solid #d7ebe2!important;
}
#pairStatisticsModal .modal-head .eyebrow{display:none!important}
#pairStatisticsModal .modal-head h2{font-size:17px!important;color:#103f34!important;margin:0!important}
#pairStatisticsModal .modal-close{border-radius:999px!important;background:#edf8f3!important;color:#24584a!important}
#pairStatisticsList,#mdPairStatisticsList{padding:0!important;display:block!important;background:transparent!important}
.jm-report-runtime-loading{padding:44px 20px;text-align:center;font-size:15px;font-weight:900;color:#2b6453;background:linear-gradient(180deg,#dff5ff,#e5f8ee)}
</style>
'''

SCRIPT = r'''
<script id="jayumintonGameReportRuntimeV20894Script">
/* JAYUMINTON_GAME_REPORT_RUNTIME_V20894 */
(function(){
  'use strict';

  function modal(){ return document.getElementById('pairStatisticsModal'); }
  function list(){
    return document.getElementById('pairStatisticsList') ||
           document.getElementById('mdPairStatisticsList') ||
           (modal() && modal().querySelector('.pair-statistics-list'));
  }
  function setTitle(){
    var m=modal(); if(!m)return;
    m.setAttribute('data-jm-game-report-runtime','208.94');
    var h=m.querySelector('.modal-head h2'); if(h)h.textContent='게임 통계';
    var eyebrow=m.querySelector('.modal-head .eyebrow'); if(eyebrow)eyebrow.textContent='TODAY · JAYUMINTON';
  }
  function reportApi(){
    var api=window.__JAYUMINTON_GAME_REPORT_V20893__;
    return api && typeof api.render==='function' ? api : null;
  }
  function renderPretty(){
    setTitle();
    var api=reportApi();
    if(!api)throw new Error('게임 통계 리포트 화면을 찾을 수 없습니다.');
    api.render();
    var target=list();
    if(!target || !target.querySelector('.jm-report'))throw new Error('게임 통계 리포트 렌더링에 실패했습니다.');
  }

  async function openPrettyGameReport(){
    var m=modal(), target=list();
    if(!m||!target){alert('게임 통계 화면을 찾을 수 없습니다.');return;}
    setTitle();
    m.classList.remove('hidden');
    target.innerHTML='<div class="jm-report-runtime-loading">게임 통계를 불러오는 중...</div>';
    try{
      var rows=await server('getPairStatistics',[ADMIN_PIN_VALUE]);
      window.ADMIN_PAIR_STATISTICS=Array.isArray(rows)?rows:[];
      window.MD_PAIR_STATISTICS=window.ADMIN_PAIR_STATISTICS;
      renderPretty();
    }catch(error){
      target.innerHTML='<div class="jm-report-runtime-loading">통계를 불러오지 못했습니다.</div>';
      alert(error&&error.message?error.message:error);
    }
  }

  function install(){
    // Critical v208.94 fix: the legacy openPairStatistics() called its own lexical
    // renderPairStatistics(), so merely replacing window.renderPairStatistics did not
    // change the screen. Replace the OPEN route itself and explicitly invoke the new report.
    window.openPairStatistics=openPrettyGameReport;
    window.openMdPairStatistics=openPrettyGameReport;
    window.renderPairStatistics=renderPretty;
    window.renderMdPairStatistics=renderPretty;
    setTitle();
  }

  install();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
  setTimeout(install,0);
  setTimeout(install,400);
  window.__JAYUMINTON_GAME_REPORT_RUNTIME_V20894__={open:openPrettyGameReport,render:renderPretty,install:install};
})();
</script>
'''

if '</head>' not in s or '</body>' not in s:
    raise SystemExit('HTML closing anchors missing')
s = s.replace('</head>', STYLE + '\n</head>', 1)
s = s.replace('</body>', SCRIPT + '\n</body>', 1)

for token in (
    MARKER,
    'window.openPairStatistics=openPrettyGameReport',
    "api.render()",
    "target.querySelector('.jm-report')",
    "data-jm-game-report-runtime",
    '게임 통계',
):
    if token not in s:
        raise SystemExit('v208.94 runtime contract missing: ' + token)

p.write_text(s,encoding='utf-8')
print('ADMIN_GAME_REPORT_RUNTIME_V20894_OK')
