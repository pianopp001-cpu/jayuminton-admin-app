from pathlib import Path
import sys

html = Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
s = html.read_text(encoding='utf-8')
marker = 'JAYUMINTON_V203_EXACT_APK_OVERLAY_ONLY'
if marker in s:
    print('already patched')
    raise SystemExit(0)
if '</body>' not in s:
    raise SystemExit('body end not found')

patch = r'''
<style id="jm-v203-exact-overlay-style">
#jm-admin-multi-action.jm-v203-exact-two-only{width:auto!important;max-width:132px!important;left:8px!important;right:auto!important;bottom:8px!important;transform:none!important;padding:4px!important;border-radius:12px!important;pointer-events:none!important}
#jm-admin-multi-action.jm-v203-exact-two-only .jm-multi-head,
#jm-admin-multi-action.jm-v203-exact-two-only .jm-multi-help,
#jm-admin-multi-action.jm-v203-exact-two-only .jm-do-move,
#jm-admin-multi-action.jm-v203-exact-two-only .jm-do-active,
#jm-admin-multi-action.jm-v203-exact-two-only .jm-do-cancel{display:none!important}
#jm-admin-multi-action.jm-v203-exact-two-only .jm-multi-actions{display:block!important}
#jm-admin-multi-action.jm-v203-exact-two-only .jm-do-team{display:block!important;min-height:36px!important;padding:0 10px!important;font-size:12px!important;pointer-events:auto!important}
</style>
<script id="JAYUMINTON_V203_EXACT_APK_OVERLAY_ONLY">
(function(){
  function apply(){
    var p=document.getElementById('jm-admin-multi-action');
    if(!p)return;
    var title=p.querySelector('.jm-multi-title');
    var isTwo=!!(title&&/^2명 선택/.test(String(title.textContent||'').trim()));
    p.classList.toggle('jm-v203-exact-two-only',isTwo);
  }
  var mo=new MutationObserver(apply);
  function start(){mo.observe(document.documentElement,{subtree:true,childList:true,characterData:true,attributes:true});apply();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
</script>
'''
s = s.replace('</body>', patch + '\n</body>', 1)
html.write_text(s, encoding='utf-8')
print('V203_EXACT_APK_OVERLAY_ONLY_OK')
