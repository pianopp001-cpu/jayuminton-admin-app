#!/usr/bin/env python3
"""Harden announcement ducking and carry the latest v203 Cloudflare admin contract into bundled APK HTML."""
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

        for marker in ('__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__','__JAYUMINTON_ADMIN_CARD_INTERACTION_V2042__','__JAYUMINTON_ADMIN_CARD_INTERACTION_V2043__','__JAYUMINTON_ADMIN_CARD_INTERACTION_V2045__','__JAYUMINTON_ADMIN_MULTI_ACTION_V2046__'):
            while marker in final_html:
                p=final_html.find(marker); a=final_html.rfind('<script',0,p); b=final_html.find('</script>',p)
                if a<0 or b<0: raise SystemExit('stale bundled patch marker outside script tag: '+marker)
                final_html=final_html[:a]+final_html[b+len('</script>'):]

        layout_js=Path(__file__).with_name('admin_team_layout_v2038.js').read_text(encoding='utf-8')
        card_js=Path(__file__).with_name('admin_card_interaction_v2042.js').read_text(encoding='utf-8')
        tag='<script>\n'+layout_js+'\n</script>\n<script>\n'+card_js+'\n</script>\n'
        final_html=final_html.replace('</body>',tag+'</body>',1) if '</body>' in final_html else final_html+tag
        admin_html.write_text(final_html,encoding='utf-8')

        final_html=admin_html.read_text(encoding='utf-8')
        required=(
            '__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__',
            'killLegacyTeamSafety','__jmLegacyTeamSafetyGuard',
            '__JAYUMINTON_ADMIN_MULTI_ACTION_V2046__',
            'jayuminton-admin-multi-action-v2046-style',
            'jm-source-selected','jm-target-selected','jm-temp-team-v2046',
            '이동/교환','팀설정','같이 움직일 사람을 최대 4명까지',
            '#16a34a','#d4a017',
            "phase='target'",'sourceIds.length<2',
            "for(var i=0;i<ids.length-1;i++)existing.push",
            "await server('moveOrSwapMember'",
            "if(targets.length===sourceIds.length)executeMove();",
            "old=document.getElementById('jayuminton-admin-team-safety-v2037');if(old)old.remove();",
            'a.__jmV2046Observer.observe(a,{childList:true,subtree:true});'
        )
        for marker in required:
            if marker not in final_html: raise SystemExit('bundled admin v2046 guard missing: '+marker)
        if 'visualCard(' in card_js: raise SystemExit('v2046 must not expand styling to parent card wrappers')
        if 'releaseNativeSelection' in card_js: raise SystemExit('v2046 must not leave native blue-selection cleanup hack')
        if 'window.confirm(' in card_js: raise SystemExit('v2046 must use in-app action panel, not browser confirm')
        if final_html.count('__JAYUMINTON_ADMIN_MULTI_ACTION_V2046__') != 2: raise SystemExit('v2046 card interaction duplication detected')
        print('BUNDLED_ADMIN_MULTI_ACTION_V2046_OK')
        print('BUNDLED_ADMIN_MULTI_MOVE_SWAP_USES_EXISTING_ENGINE_OK')
        print('BUNDLED_ADMIN_2_TO_4_YELLOW_TEAM_CHAIN_OK')
        print('BUNDLED_ADMIN_LEGACY_TEAM_CSS_GUARD_OK')

print('NATIVE_AUDIO_V2021_OK music=audible<=6 voice=max restore=original')
# BUILD_TRIGGER: v2046-multi-source-action-target-yellow-team-new-guard-20260826-2356
