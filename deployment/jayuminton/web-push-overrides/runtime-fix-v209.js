(() => {
  'use strict';

  const HOTFIX_VERSION = 'v209.2';

  // Use the freshly recovered and live-verified member Apps Script deployment.
  const STABLE_MEMBER_PAGE_URL =
    'https://script.google.com/macros/s/AKfycbzYRVItaMK0WOFfo0sCnxmuKR8p3mZHwYYTXos4jeLUmIzR-S211NtfQCcdzNtTJz138w/exec';

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
  window.__JAYUMINTON_HOTFIX_VERSION__ = HOTFIX_VERSION;
})();
