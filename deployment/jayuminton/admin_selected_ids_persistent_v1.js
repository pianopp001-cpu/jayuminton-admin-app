/* __JAYUMINTON_ADMIN_SELECTED_IDS_PERSISTENT_V1__
   The REAL governing code path for "select members, then tap an empty
   slot" is installDirectPlacement()'s capture-phase click listener
   (assignSelectedToClicked -> assign()), NOT handleEmptySlotTap -- it
   intercepts and stopImmediatePropagation()s the click first whenever
   selectedIds() is non-empty. (An earlier fix targeted
   handleEmptySlotTap directly; harmless to leave in place, but it is
   rarely the function that actually runs.)

   selectedIds() itself (the last of several identical redefinitions in
   this file) determines "who's selected" by scanning the DOM for
   .jm-unlimited-check badges. That badge only exists on a member's
   CURRENTLY RENDERED card. The quick-roster panel's 남자/여자 filter
   chips rebuild that list's HTML filtered by gender, so a previously
   selected member of the other gender has no card in the DOM at all
   while the filter excludes them -- their checkmark (and thus their
   entry in selectedIds()) silently disappears even though they were
   never actually deselected. Whoever you select AFTER switching the
   filter is the only one still visible to selectedIds(), which is
   exactly "select a man, switch to 여자, select a woman, only the
   woman gets placed."

   Fix: read the toolbar's own persistent selection Set directly
   (exposed as window.__jmUnlimitedSelected by a base-HTML patch) --
   it is never affected by which cards happen to be rendered right
   now. Falls back to the old DOM-scan if that Set isn't available for
   some reason.
*/
(function(){
  if (window.__JAYUMINTON_ADMIN_SELECTED_IDS_PERSISTENT_V1__) return;
  window.__JAYUMINTON_ADMIN_SELECTED_IDS_PERSISTENT_V1__ = true;

  function domScanFallback(){
    var ids = [];
    try {
      document.querySelectorAll('#adminApp .jm-unlimited-check').forEach(function(check){
        var card = check.closest('[data-member-id],[data-memberid],[data-player-id],[data-id],[data-member],.member,.person,.quick-member,.member-card,.member-item,.player-card,.court-player');
        var id = card && (
          card.getAttribute('data-member-id') ||
          card.getAttribute('data-memberid') ||
          card.getAttribute('data-player-id') ||
          card.getAttribute('data-id')
        );
        if (id && ids.indexOf(id) < 0) ids.push(id);
      });
    } catch (e) {}
    return ids;
  }

  window.selectedIds = function(){
    try {
      var live = window.__jmUnlimitedSelected;
      if (live && typeof live.forEach === 'function') {
        var ids = [];
        live.forEach(function(id){ id = String(id); if (id && ids.indexOf(id) < 0) ids.push(id); });
        if (ids.length) return ids;
      }
    } catch (e) {}
    return domScanFallback();
  };
})();
