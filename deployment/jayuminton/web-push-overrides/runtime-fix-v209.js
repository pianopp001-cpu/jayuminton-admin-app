(() => {
  'use strict';

  // The original v199 administrator app still uses this Apps Script deployment.
  // The same deployment serves the member court screen with mode=user/app=user.
  const STABLE_MEMBER_PAGE_URL =
    'https://script.google.com/macros/s/AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q/exec';

  const standalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  // Uninstalling a PWA does not erase Chrome site storage. The old code treated this
  // stale flag as proof that the app was still installed, permanently disabling install.
  if (!standalone) {
    try {
      localStorage.removeItem('jayuminton_user_app_installed_confirmed_v206');
      if (localStorage.getItem('jayuminton_user_app_download_choice_v170') === 'on') {
        localStorage.removeItem('jayuminton_user_app_download_choice_v170');
      }
    } catch (_) {}
  }

  const previous = window.JAYUMINTON_PUSH_SETUP_CONFIG || {};
  window.JAYUMINTON_PUSH_SETUP_CONFIG = Object.freeze(Object.assign({}, previous, {
    memberPageUrl: STABLE_MEMBER_PAGE_URL
  }));

  window.__JAYUMINTON_MEMBER_PAGE_URL_V209__ = STABLE_MEMBER_PAGE_URL;
})();
