#!/usr/bin/env python3
"""Harden announcement ducking and carry the latest Cloudflare admin contract into bundled APK HTML."""
from pathlib import Path
import subprocess
import sys

path = Path('app/src/main/java/com/jayuminton/admin/MainActivity.java')
text = path.read_text(encoding='utf-8')
old = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int duckedMusic = Math.max(0, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);
'''
new = '''                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int levelSix = Math.max(1, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));
                int duckedMusic = originalMediaVolume > 0
                        ? Math.min(originalMediaVolume, levelSix)
                        : 0;
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);
'''
if text.count(old) != 1: raise SystemExit('native music duck anchor mismatch')
text = text.replace(old, new, 1)
for marker in ('MEDIA_DUCK_VOLUME_STEP = 6','Math.min(originalMediaVolume, levelSix)','setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0)','setStreamVolume(AudioManager.STREAM_MUSIC, originalMediaVolume, 0)'):
    if marker not in text: raise SystemExit('native audio contract missing: '+marker)
path.write_text(text, encoding='utf-8')

admin_html = Path('app/src/main/assets/admin/index.html')
if admin_html.exists():
    bundled = admin_html.read_text(encoding='utf-8')
    if 'function usesAdminFullName(member)' in bundled and 'jayuminton-pair-statistics-disclosure-v2028' in bundled:
        if 'JAYUMINTON_ADMIN_CLOUDFLARE_SAVE_LOCK_V24' not in bundled:
            subprocess.run([sys.executable, str(Path(__file__).with_name('admin_cloudflare_post_contract_patch.py')), str(admin_html)], check=True)
        final_html = admin_html.read_text(encoding='utf-8')
        for marker in ('JAYUMINTON_ADMIN_CLOUDFLARE_SAVE_LOCK_V24','__JAYUMINTON_ADMIN_SAVING__','member-public-memo','publicMemo','__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_MD4__','__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__'):
            if marker not in final_html: raise SystemExit('bundled v203 post-contract missing: '+marker)
        if 'script.google.com/macros/s/' in final_html: raise SystemExit('GAS URL survived in bundled v203 administrator HTML')

        for marker in ('__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__','__JAYUMINTON_ADMIN_CARD_INTERACTION_V2042__','__JAYUMINTON_ADMIN_CARD_INTERACTION_V2043__','__JAYUMINTON_ADMIN_CARD_INTERACTION_V2045__','__JAYUMINTON_ADMIN_MULTI_ACTION_V2046__','__JAYUMINTON_ADMIN_MULTI_ACTION_V2047__','__JAYUMINTON_ADMIN_MULTI_ACTION_V2052__','__JAYUMINTON_ADMIN_MULTI_ACTION_V2053__','__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__'):
            while marker in final_html:
                p=final_html.find(marker); a=final_html.rfind('<script',0,p); b=final_html.find('</script>',p)
                if a<0 or b<0: raise SystemExit('stale bundled patch marker outside script tag: '+marker)
                final_html=final_html[:a]+final_html[b+len('</script>'):]

        layout_js=Path(__file__).with_name('admin_team_layout_v2038.js').read_text(encoding='utf-8')
        card_js=Path(__file__).with_name('admin_card_interaction_v2042.js').read_text(encoding='utf-8')
        hotfix_js=Path(__file__).with_name('admin_multiaction_v2054_hotfix.js').read_text(encoding='utf-8')
        tag='<script>\n'+layout_js+'\n</script>\n<script>\n'+card_js+'\n</script>\n<script>\n'+hotfix_js+'\n</script>\n'
        final_html=final_html.replace('</body>',tag+'</body>',1) if '</body>' in final_html else final_html+tag
        admin_html.write_text(final_html,encoding='utf-8')

        final_html=admin_html.read_text(encoding='utf-8')
        required=(
            '__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__',
            'killLegacyTeamSafety','__jmLegacyTeamSafetyGuard',
            '__JAYUMINTON_ADMIN_MULTI_ACTION_V2053__',
            '__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__',
            '__JAYUMINTON_ADMIN_MESSAGE_ANYWHERE_V2056__',
            'jm-admin-v2054-pass-through-style','jm-send-court-wait','코트배정대기로',
            'a.__jmV2053Observer.disconnect','a.__jmV2054FastObserver',
            'jayuminton-admin-multi-action-v2053-style',
            'jm-source-selected','jm-target-selected','jm-temp-team-v2047',
            '녹색 = 이동선택','2명일 때만 이동/교환인지 팀설정인지 선택합니다.',
            '1명·3명·4명은 자동으로 이동/교환입니다.',
            '이동/교환','팀설정','#16a34a','#d4a017',
            "phase='target'",'selected.length!==2','samePlace(selected)',
            'members:ids.map(String)',
            "rpc('swapMembers'", "rpc('moveOrSwapMember'", "rpc('sendMemberMessage'",
            'if(selected.length===1)', 'if(selected.length===3||selected.length===4)',
            "if(targets.length===selected.length)executeMove();",
            "var old=document.getElementById('jayuminton-admin-team-safety-v2037');if(old)old.remove();",
            'obs.observe(a,{childList:true,subtree:true})'
        )
        for marker in required:
            if marker not in final_html: raise SystemExit('bundled admin v2056 guard missing: '+marker)
        if 'window.google&&window.google.script&&window.google.script.run' in card_js: raise SystemExit('v2053 team interaction must use direct Cloudflare window.server RPC')
        if 'window.confirm(' in card_js: raise SystemExit('v2053 must use in-app action panel, not browser confirm')
        if final_html.count('__JAYUMINTON_ADMIN_MULTI_ACTION_V2053__') != 2: raise SystemExit('v2053 card interaction duplication detected')
        if final_html.count('__JAYUMINTON_ADMIN_MULTI_ACTION_V2054_HOTFIX__') != 2: raise SystemExit('v2054 hotfix duplication detected')
        print('BUNDLED_ADMIN_MULTI_ACTION_V2056_HOTFIX_OK')
        print('BUNDLED_ADMIN_MESSAGE_ANYWHERE_OK')
        print('BUNDLED_ADMIN_STABLE_TEAM_BORDER_OK')
        print('BUNDLED_ADMIN_COURT_WAIT_RETURN_BUTTON_OK')
        print('BUNDLED_ADMIN_FAST_LOCAL_REPAINT_OK')
        print('BUNDLED_ADMIN_GREEN_MOVE_YELLOW_TEAM_OK')
        print('BUNDLED_ADMIN_CROSS_LOCATION_DIRECT_SWAP_OK')
        print('BUNDLED_ADMIN_TEAM_DIRECT_CLOUDFLARE_RPC_OK')

print('NATIVE_AUDIO_V2021_OK music=audible<=6 voice=max restore=original')
# BUILD_TRIGGER: v2056-stable-team-message-anywhere-20260827
