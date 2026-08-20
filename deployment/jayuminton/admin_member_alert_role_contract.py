#!/usr/bin/env python3
"""Admin role separation: admin speaks court call only; member devices own wait/court vibration notifications."""
from pathlib import Path
import sys

path=Path(sys.argv[1])
html=path.read_text(encoding='utf-8')
marker='</body>'
if marker not in html:
    raise SystemExit('body marker missing')
addon=r'''
<script id="jayuminton-admin-member-alert-role-v1">
(function(){
  // Member phones own WAIT_ONE / COURT assignment popups and vibration.
  // Admin only announces the court call by voice through finishCourt().
  window.__JAYUMINTON_ADMIN_MEMBER_ALERT_ROLE_V1__={
    memberWaitAlertOnMemberDevice:true,
    memberCourtAlertOnMemberDevice:true,
    adminWaitVoice:false,
    adminTransitionVibration:false,
    adminCourtVoice:true
  };
  window.__JAYUMINTON_TRANSITION_ALERT__=function(){ return; };
})();
</script>
'''
if 'jayuminton-admin-member-alert-role-v1' not in html:
    html=html.replace(marker,addon+'\n'+marker,1)
path.write_text(html,encoding='utf-8')
print('ADMIN_MEMBER_ALERT_ROLE_CONTRACT_OK')
