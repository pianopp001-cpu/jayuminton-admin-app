from pathlib import Path
import sys

html = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/src/main/assets/admin/index.html')
s = html.read_text(encoding='utf-8')

# Exact APK baseline stays untouched. Do not replace existing interaction code.
# Only add a tiny presentation overlay so the 2-person action UI cannot block
# clicking the 3rd/4th card. Team setup remains available for exactly 2 people.
required = [
    '__JAYUMINTON_ADMIN_MULTI_ACTION_V2053__',
    '__JAYUMINTON_ADMIN_CONTINUE_SELECTION_V2067__',
]
for marker in required:
    if marker not in s:
        raise SystemExit('v203 baseline marker missing: ' + marker)

marker = 'JAYUMINTON_V203_BASELINE_CONTINUOUS_3_4_OVERLAY_V2'
if marker not in s:
    patch = r'''
<!-- JAYUMINTON_V203_BASELINE_CONTINUOUS_3_4_OVERLAY_V2 -->
<style id="jm-v203-continuous-overlay-v2">
/* The original v203 logic remains intact. Only the 2-person panel is reduced
   to a tiny team button so it cannot intercept 3rd/4th member taps. */
#jm-admin-multi-action.jm-v203-two-only {
  width:auto!important;
  max-width:132px!important;
  left:8px!important;
  right:auto!important;
  bottom:8px!important;
  transform:none!important;
  padding:4px!important;
  border-radius:12px!important;
  pointer-events:none!important;
}
#jm-admin-multi-action.jm-v203-two-only .jm-multi-head,
#jm-admin-multi-action.jm-v203-two-only .jm-multi-help,
#jm-admin-multi-action.jm-v203-two-only .jm-do-move,
#jm-admin-multi-action.jm-v203-two-only .jm-do-active,
#jm-admin-multi-action.jm-v203-two-only .jm-do-cancel {
  display:none!important;
}
#jm-admin-multi-action.jm-v203-two-only .jm-multi-actions {
  display:block!important;
}
#jm-admin-multi-action.jm-v203-two-only .jm-do-team {
  display:block!important;
  min-height:36px!important;
  padding:0 10px!important;
  font-size:12px!important;
  pointer-events:auto!important;
}
</style>
<script>
(function(){
  'use strict';
  function sync(){
    var p=document.getElementById('jm-admin-multi-action');
    if(!p)return;
    var title=p.querySelector('.jm-multi-title');
    var text=(title&&title.textContent||'').trim();
    var team=p.querySelector('.jm-do-team');
    if(team && /^2명\s*선택/.test(text)) p.classList.add('jm-v203-two-only');
    else p.classList.remove('jm-v203-two-only');
  }
  var obs=new MutationObserver(sync);
  function start(){
    obs.observe(document.body,{childList:true,subtree:true,characterData:true});
    sync();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
  else start();
})();
</script>
'''
    if '</body>' in s:
        s = s.replace('</body>', patch + '\n</body>', 1)
    else:
        s += patch

html.write_text(s, encoding='utf-8')
print('V203_BASELINE_CONTINUOUS_3_4_OVERLAY_V2_OK')
