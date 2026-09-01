#!/usr/bin/env python3
from pathlib import Path
import sys
import re

# 2026-09-01 Play hotfix trigger: rebuild user bundle with route guard + code 2001646.
path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

pairs = (
    ('v1.3.4-cloudflare-complete.apk', 'v1.6.42-md-final.apk'),
    ('user-native-push-v1.3.4.txt', 'user-native-push-v1.6.42.txt'),
    ('VERSION="1.3.4"', 'VERSION="1.6.42"'),
    ('VERSION_CODE="2000134"', 'VERSION_CODE="2001642"'),
    ('versionCode 2000134', 'versionCode 2001642'),
    ("versionName '1.3.4'", "versionName '1.6.42'"),
    ('version=1.3.4', 'version=1.6.42'),
    ('version_code=2000134', 'version_code=2001642'),
    ("versionCode='2000134'", "versionCode='2001642'"),
    ("versionName='1.3.4'", "versionName='1.6.42'"),
    ('USER_APP_VERSION = "1.3.4"', 'USER_APP_VERSION = "1.6.42"'),
    ('JayumintonUserNative/1.3.4', 'JayumintonUserNative/1.6.42'),
    ('JayumintonNativeAndroid/1.3.4', 'JayumintonNativeAndroid/1.6.42'),
    ('APP_VERSION = "1.3.4"', 'APP_VERSION = "1.6.42"'),
)
for old, new in pairs:
    source = source.replace(old, new)

# Emergency route marker. Bumping this guarantees a fresh member URL after the
# Play update instead of reusing any stale document from an earlier build.
ROUTE_MARKER = '20260901a-play-user-route-hotfix'
USER_ROUTE = f'https://jayuminton-push.web.app/?mode=user&apkUser=1&userAppVersion=1.6.42&memberRoute={ROUTE_MARKER}'
source = re.sub(
    r'USER_URL="https://jayuminton-push\.web\.app/[^"\n]*"',
    f'USER_URL="{USER_ROUTE}"',
    source,
    count=1,
)

# Generated user MainActivity must refuse an explicit admin query even if the
# member page or a stale link attempts to navigate there.
old = '''            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
                return !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme));
            }'''
new = '''            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String requested = request.getUrl().toString();
                if (requested.contains("mode=admin") || requested.contains("/admin")) {
                    view.stopLoading();
                    view.clearHistory();
                    view.loadUrl(USER_URL + "&routeGuard=1&ts=" + System.currentTimeMillis());
                    return true;
                }
                String scheme = request.getUrl().getScheme();
                return !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme));
            }'''
if old not in source:
    raise SystemExit('user route guard anchor missing')
source = source.replace(old, new, 1)

required = (
    'VERSION="1.6.42"',
    'VERSION_CODE="2001642"',
    'private static final int MAX_GROUPS = 8;',
    'NativePushRegistrar.isCurrentMember(this, targetMemberId)',
    'AlertVibrationController.stop(',
    'stopPreviousMemberAlert(app);',
    f'USER_URL="{USER_ROUTE}"',
    'com.jayuminton.user',
    'requested.contains("mode=admin")',
    'routeGuard=1',
)
for marker in required:
    if marker not in source:
        raise SystemExit('v1642 MD final contract missing: ' + marker)
if 'script.google.com' in source or 'MAIN_DEPLOYMENT_ID' in source:
    raise SystemExit('v1642 must remain Cloudflare/Firebase-only')
if re.search(r'USER_URL="[^"\n]*[?&]mode=admin(?:[&#"\n]|$)', source):
    raise SystemExit('v1642 user APK must never contain admin mode routing')
if 'mode=user' not in source or ROUTE_MARKER not in source:
    raise SystemExit('v1642 fresh member route guard missing')

path.write_text(source, encoding='utf-8')
print('Prepared v1.6.42 MD-final user APK with forced fresh member route and admin-route block.')