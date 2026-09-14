#!/usr/bin/env python3
"""Make a successful full reset clear every member login/identity locally."""

from pathlib import Path
import sys


MARKER = "JAYUMINTON_MEMBER_FORCE_LOGOUT_ON_RESET_V1"

ADDON = r'''
<script>
/* JAYUMINTON_MEMBER_FORCE_LOGOUT_ON_RESET_V1
   resetAll increments memberPasswordVersion on the state worker.  This guard
   observes that revocation boundary and removes every persisted member-login
   and self-identity value, including the native app identity binding. */
(function installMemberForceLogoutOnResetV1(){
  if (window.__JAYUMINTON_MEMBER_FORCE_LOGOUT_ON_RESET_V1__) return;
  window.__JAYUMINTON_MEMBER_FORCE_LOGOUT_ON_RESET_V1__ = true;
  var checking = false;
  var AUTH_KEYS = [
    'jayuminton_member_password_version_v2',
    'jayuminton_member_auth_v164'
  ];
  var MEMBER_KEYS = [
    'jayuminton_member_session_token_v1',
    'jayuminton_member_session_token_v164',
    'jayuminton_web_push_selected_member_v1',
    'jayuminton_web_push_connection_v1',
    'jayuminton_push_setup_member_v164',
    'jayuminton_push_token_v158'
  ];

  function firstStored(keys){
    for (var i = 0; i < keys.length; i += 1) {
      try {
        var value = String(localStorage.getItem(keys[i]) || '');
        if (value) return value;
      } catch (error) {}
    }
    return '';
  }

  function clearMemberLogin(){
    try {
      if (window.JayumintonPwaPush && typeof window.JayumintonPwaPush.unregister === 'function') {
        window.JayumintonPwaPush.unregister();
      }
    } catch (error) {}
    AUTH_KEYS.concat(MEMBER_KEYS).forEach(function(key){
      try { localStorage.removeItem(key); } catch (error) {}
    });
    try {
      if (typeof storeMemberSessionToken === 'function') storeMemberSessionToken('');
    } catch (error) {}
    try { if (typeof MEMBER_SESSION_VALUE !== 'undefined') MEMBER_SESSION_VALUE = ''; } catch (error) {}
    try { if (typeof LAST_PUBLIC_STATE !== 'undefined') LAST_PUBLIC_STATE = null; } catch (error) {}
    try {
      if (window.NativeUserApp && typeof window.NativeUserApp.clearMember === 'function') {
        window.NativeUserApp.clearMember();
      }
    } catch (error) {}
    try {
      if (typeof postUnifiedMemberMessage === 'function') {
        postUnifiedMemberMessage('JAYUMINTON_MEMBER_FORCE_LOGOUT', {});
      }
    } catch (error) {}
    var loading = document.getElementById('memberAuthLoading');
    var login = document.getElementById('memberLoginBox');
    var app = document.getElementById('memberApp');
    if (loading) loading.classList.add('hidden');
    if (app) app.classList.add('hidden');
    if (login) login.classList.remove('hidden');
  }

  async function checkRevocation(){
    if (checking || (typeof IS_ADMIN !== 'undefined' && IS_ADMIN)) return;
    var storedVersion = firstStored(AUTH_KEYS);
    var storedSession = firstStored(MEMBER_KEYS.slice(0, 2));
    if (!storedVersion && !storedSession) return;
    checking = true;
    try {
      var currentVersion = String(await server('getMemberPasswordVersion', []));
      if (storedVersion && storedVersion !== currentVersion) clearMemberLogin();
    } catch (error) {
      // A temporary network failure must never sign a member out.
    } finally {
      checking = false;
    }
  }

  window.jmClearMemberLoginAfterReset = clearMemberLogin;
  setInterval(checkRevocation, 2000);
  document.addEventListener('visibilitychange', function(){
    if (!document.hidden) checkRevocation();
  });
  window.addEventListener('message', function(event){
    if (event && event.data && event.data.type === 'JAYUMINTON_MEMBER_FORCE_LOGOUT') {
      clearMemberLogin();
    }
  });
  setTimeout(checkRevocation, 0);
})();
</script>
'''


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return
    required = ["getMemberPasswordVersion", "memberLoginBox", "memberApp"]
    for needle in required:
        if needle not in text:
            raise SystemExit(f"member logout patch anchor missing: {needle}")
    closing = text.lower().rfind("</body>")
    if closing < 0:
        raise SystemExit("member page closing body tag missing")
    text = text[:closing] + ADDON + "\n" + text[closing:]
    if MARKER not in text:
        raise SystemExit("member force-logout patch did not apply")
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_force_logout_on_reset_v1.py INDEX_HTML")
    patch(Path(sys.argv[1]))
