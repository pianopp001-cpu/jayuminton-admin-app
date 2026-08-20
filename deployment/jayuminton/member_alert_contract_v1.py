#!/usr/bin/env python3
"""Contract markers for member-targeted wait/court alerts and admin-only court voice."""
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text(encoding='utf-8')
marker='</body>'
if marker not in s: raise SystemExit('body marker missing')
addon=r'''
<script id="jayuminton-member-alert-contract-v1">
window.__JAYUMINTON_MEMBER_ALERT_CONTRACT_V1__={
  waitOne:{target:'selected-member-device',voice:false,popup:true,vibrate:true,text:'대기 1입니다. 라켓 들고 준비해 주세요.'},
  court:{target:'selected-member-device',voice:false,popup:true,vibrate:true},
  admin:{courtVoice:true,waitVoice:false,transitionVibrate:false}
};
</script>
'''
if 'jayuminton-member-alert-contract-v1' not in s:
    s=s.replace(marker,addon+'\n'+marker,1)
p.write_text(s,encoding='utf-8')
print('MEMBER_ALERT_CONTRACT_V1_OK')
