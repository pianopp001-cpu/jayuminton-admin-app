#!/usr/bin/env python3
"""Keep reset logout behavior and add a member-to-admin pairing request composer."""

from pathlib import Path
import sys


MARKER = "JAYUMINTON_MEMBER_FORCE_LOGOUT_ON_RESET_V1"
PREFERENCE_MARKER = "JAYUMINTON_MEMBER_ADMIN_PREFERENCE_COMPOSER_V1"

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

PREFERENCE_ADDON = r'''
<style id="jayuminton-member-admin-preference-composer-v1-style">
#jmAdminPreferenceComposer{margin:10px 14px 2px;padding:12px;border:1px solid #dbeafe;border-radius:12px;background:#f8fbff;box-shadow:0 3px 12px rgba(49,94,251,.08)}
#jmAdminPreferenceComposer .jm-pref-title{font-size:14px;font-weight:950;color:#172554;margin-bottom:7px}
#jmAdminPreferenceComposer .jm-pref-sentence{font-size:13px;line-height:1.75;color:#334155}
#jmAdminPreferenceComposer .jm-pref-name{display:inline-block;width:112px;max-width:40vw;height:34px;box-sizing:border-box;margin:0 4px;padding:4px 8px;border:1px solid #93c5fd;border-radius:8px;background:#fff;color:#0f172a;font-size:14px;font-weight:850;text-align:center;vertical-align:middle;outline:none}
#jmAdminPreferenceComposer .jm-pref-name:focus{border-color:#315efb;box-shadow:0 0 0 3px rgba(49,94,251,.12)}
#jmAdminPreferenceComposer .jm-pref-help{margin-top:6px;font-size:11px;color:#64748b}
#jmAdminPreferenceComposer .jm-pref-send{width:100%;min-height:40px;margin-top:9px;border:0;border-radius:9px;background:#315efb;color:#fff;font-size:14px;font-weight:900}
#jmAdminPreferenceComposer .jm-pref-send:disabled{opacity:.55}
</style>
<script>
/* JAYUMINTON_MEMBER_ADMIN_PREFERENCE_COMPOSER_V1
   The existing speech-bubble button still opens the normal admin-message inbox.
   This composer is inserted above that inbox. Replies to received admin messages
   remain unrestricted; only this proactive request uses the fixed sentence. */
(function installMemberAdminPreferenceComposerV1(){
  if (typeof IS_ADMIN!=='undefined' && IS_ADMIN) return;
  if (window.__JAYUMINTON_MEMBER_ADMIN_PREFERENCE_COMPOSER_V1__) return;
  window.__JAYUMINTON_MEMBER_ADMIN_PREFERENCE_COMPOSER_V1__ = true;
  var sending = false;

  function sessionArgs(){
    try { return (typeof memberWaitSeatSessionArgs==='function') ? memberWaitSeatSessionArgs() : null; }
    catch(error){ return null; }
  }

  function notice(text){
    try {
      if (typeof showMemberSettingMessage==='function') {
        showMemberSettingMessage(String(text||''));
        return;
      }
    } catch(error) {}
    try { alert(String(text||'')); } catch(error) {}
  }

  function ensureComposer(){
    var list = document.getElementById('jmMessageInboxList');
    if (!list || !list.parentNode) return null;
    var existing = document.getElementById('jmAdminPreferenceComposer');
    if (existing) return existing;

    var card = document.createElement('div');
    card.id = 'jmAdminPreferenceComposer';
    card.innerHTML =
      '<div class="jm-pref-title">관리자에게 배정 요청</div>' +
      '<div class="jm-pref-sentence">대기에서 좀 밀려나도 되니 다음에는 최대한' +
      '<input id="jmAdminPreferenceName" class="jm-pref-name" type="text" maxlength="20" autocomplete="off" inputmode="text" aria-label="함께 배정할 회원 이름" placeholder="회원 이름">' +
      '와 배정해주세요.</div>' +
      '<div class="jm-pref-help">이름만 입력할 수 있고, 나머지 문장은 고정돼요.</div>' +
      '<button type="button" id="jmAdminPreferenceSend" class="jm-pref-send">관리자에게 전송</button>';
    list.parentNode.insertBefore(card, list);

    var input = card.querySelector('#jmAdminPreferenceName');
    var button = card.querySelector('#jmAdminPreferenceSend');

    async function send(){
      if (sending) return;
      var a = sessionArgs();
      if (!a || !a.member || !a.member.id) {
        notice('먼저 내 이름을 선택해 주세요.');
        return;
      }
      var partner = String(input && input.value || '').trim().replace(/\s+/g,' ');
      if (!partner) {
        notice('함께 배정할 회원 이름을 입력해 주세요.');
        try { input.focus(); } catch(error) {}
        return;
      }
      sending = true;
      if (button) { button.disabled = true; button.textContent = '전송 중...'; }
      try {
        await server('memberSendAdminPreference',[a.token,String(a.member.id),partner]);
        if (input) input.value = '';
        notice('관리자에게 배정 요청을 보냈어요.');
      } catch(error) {
        notice(String(error && error.message || error || '전송에 실패했습니다.'));
      } finally {
        sending = false;
        if (button) { button.disabled = false; button.textContent = '관리자에게 전송'; }
      }
    }

    if (button) button.addEventListener('click', send);
    if (input) input.addEventListener('keydown', function(event){
      if (event.key === 'Enter') { event.preventDefault(); send(); }
    });
    return card;
  }

  document.addEventListener('click', function(event){
    var target = event.target && event.target.closest ? event.target.closest('#jmMessageInboxFab') : null;
    if (target) setTimeout(ensureComposer, 0);
  }, true);

  new MutationObserver(function(){
    try { ensureComposer(); } catch(error) {}
  }).observe(document.documentElement,{childList:true,subtree:true});

  document.addEventListener('DOMContentLoaded', function(){ setTimeout(ensureComposer,0); }, {once:true});
  setInterval(ensureComposer, 1500);
  setTimeout(ensureComposer, 0);
})();
</script>
'''


def insert_before_body(text: str, addon: str, marker: str) -> str:
    if marker in text:
        return text
    closing = text.lower().rfind("</body>")
    if closing < 0:
        raise SystemExit("member page closing body tag missing")
    return text[:closing] + addon + "\n" + text[closing:]


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    if MARKER not in text:
        required = ["getMemberPasswordVersion", "memberLoginBox", "memberApp"]
        for needle in required:
            if needle not in text:
                raise SystemExit(f"member logout patch anchor missing: {needle}")
        text = insert_before_body(text, ADDON, MARKER)

    text = insert_before_body(text, PREFERENCE_ADDON, PREFERENCE_MARKER)

    for needle in [
        MARKER,
        PREFERENCE_MARKER,
        "memberSendAdminPreference",
        "대기에서 좀 밀려나도 되니 다음에는 최대한",
        "jmAdminPreferenceName",
    ]:
        if needle not in text:
            raise SystemExit("member page patch missing: " + needle)

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_member_force_logout_on_reset_v1.py INDEX_HTML")
    patch(Path(sys.argv[1]))
