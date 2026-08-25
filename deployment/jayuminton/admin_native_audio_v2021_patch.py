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
                // Announcement ducking is not music mute. Keep audible music at
                // level <= 6 and never raise a user's already quieter setting.
                int duckedMusic = originalMediaVolume > 0
                        ? Math.min(originalMediaVolume, levelSix)
                        : 0;
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, duckedMusic, 0);
'''
if text.count(old) != 1:
    raise SystemExit('native music duck anchor mismatch')
text = text.replace(old, new, 1)

required = [
    'MEDIA_DUCK_VOLUME_STEP = 6',
    'int levelSix = Math.max(1, Math.min(MEDIA_DUCK_VOLUME_STEP, maxMedia));',
    'Math.min(originalMediaVolume, levelSix)',
    'setStreamVolume(AudioManager.STREAM_ALARM, maxAlarm, 0)',
    'setStreamVolume(AudioManager.STREAM_MUSIC, originalMediaVolume, 0)',
]
for marker in required:
    if marker not in text:
        raise SystemExit('native audio contract missing: ' + marker)

path.write_text(text, encoding='utf-8')

admin_html = Path('app/src/main/assets/admin/index.html')
if admin_html.exists():
    bundled = admin_html.read_text(encoding='utf-8')
    if 'function usesAdminFullName(member)' in bundled and 'jayuminton-pair-statistics-disclosure-v2028' in bundled:
        if 'JAYUMINTON_ADMIN_CLOUDFLARE_SAVE_LOCK_V24' not in bundled:
            post_patch = Path(__file__).with_name('admin_cloudflare_post_contract_patch.py')
            subprocess.run([sys.executable, str(post_patch), str(admin_html)], check=True)
        final_html = admin_html.read_text(encoding='utf-8')
        for marker in (
            'JAYUMINTON_ADMIN_CLOUDFLARE_SAVE_LOCK_V24',
            '__JAYUMINTON_ADMIN_SAVING__',
            'member-public-memo',
            'publicMemo',
            '__JAYUMINTON_ADMIN_EMPTY_COURT_FINISH_MD4__',
            '__JAYUMINTON_ADMIN_STATISTICS_NO_CLIP_FINAL__',
        ):
            if marker not in final_html:
                raise SystemExit('bundled v203 post-contract missing: ' + marker)
        if 'script.google.com/macros/s/' in final_html:
            raise SystemExit('GAS URL survived in bundled v203 administrator HTML')

        layout_marker = '__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__'
        while layout_marker in final_html:
            marker_pos = final_html.find(layout_marker)
            script_start = final_html.rfind('<script', 0, marker_pos)
            script_end = final_html.find('</script>', marker_pos)
            if script_start < 0 or script_end < 0:
                raise SystemExit('stale bundled team layout marker is outside script tag')
            final_html = final_html[:script_start] + final_html[script_end + len('</script>'):]

        layout_js = Path(__file__).with_name('admin_team_layout_v2038.js').read_text(encoding='utf-8')
        tag = '<script>\n' + layout_js + '\n</script>\n'
        if '</body>' in final_html:
            final_html = final_html.replace('</body>', tag + '</body>', 1)
        else:
            final_html += tag
        admin_html.write_text(final_html, encoding='utf-8')

        final_html = admin_html.read_text(encoding='utf-8')
        for marker in (
            '__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__',
            'compactSameTeams',
            'jayuminton-admin-team-layout-v2038',
            '.jm-team-bottom-label',
            'has-member-team.jm-temp-pair',
            "if(type==='wait')return [a[0],b[0],a[1],b[1]]",
            "return [a[0],a[1],b[0],b[1]]",
        ):
            if marker not in final_html:
                raise SystemExit('bundled team layout guard missing: ' + marker)
        if final_html.count('__JAYUMINTON_ADMIN_TEAM_LAYOUT_V2038__') != 2:
            raise SystemExit('bundled team layout script duplication detected')
        print('BUNDLED_ADMIN_V203_TEAM_LAYOUT_V2038_FRESH_OK')
        print('BUNDLED_ADMIN_V203_POST_CONTRACT_V24_OK')

print('NATIVE_AUDIO_V2021_OK music=audible<=6 voice=max restore=original')
# BUILD_TRIGGER: wait-left-right-court-top-bottom-line-only-20260826
