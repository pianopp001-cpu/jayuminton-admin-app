/* __JAYUMINTON_ADMIN_EMPTY_SLOT_MANUAL_ASSIGN_FIX_V1__
   Root cause of "select men, switch to the 여자 quick-roster filter,
   select women, tap an empty slot -> only the women go in":

   Member selection (court/wait card taps AND the quick-roster panel,
   including its 남자/여자 filter chips) is tracked by the unlimited-
   selection toolbar's own private `selected` Set (exposed globally as
   window.__jmUnlimitedSelected by a base-HTML patch that runs before
   this script). Tapping an empty slot directly, though, calls
   handleEmptySlotTap, which reads the OLD, separate global `SELECTED`
   Set -- a set nothing in the current UI actually writes members into
   any more (its own click path is intercepted earlier by the
   toolbar's capture-phase listener). So handleEmptySlotTap always saw
   zero selected members and fell through to "set this as the
   auto-assign target" instead of batch-assigning -- UNLESS an
   auto-assign target from a PREVIOUS empty-slot tap happened to still
   be active, in which case member taps got assigned one at a time via
   a completely different path (assignMemberToChosenEmpty), so
   whichever gender was tapped last after the target filled up is what
   looked like "only X got in." Nothing was ever actually forgotten by
   switching the filter -- the private Set was never being read in the
   first place.

   Fix: right before handleEmptySlotTap's own logic runs, mirror the
   live private Set into the legacy global SELECTED set, so its
   existing ids.length-based branch (manual batch-assign vs. set
   auto-assign target) sees the real, current, filter-independent
   selection.
*/
(function(){
  if (window.__JAYUMINTON_ADMIN_EMPTY_SLOT_MANUAL_ASSIGN_FIX_V1__) return;
  window.__JAYUMINTON_ADMIN_EMPTY_SLOT_MANUAL_ASSIGN_FIX_V1__ = true;

  var original = window.handleEmptySlotTap;
  if (typeof original !== 'function') return;

  window.handleEmptySlotTap = function(type, index, slotIndex, event){
    try {
      var live = window.__jmUnlimitedSelected;
      if (live && live.size && typeof SELECTED !== 'undefined' && SELECTED && typeof SELECTED.add === 'function') {
        live.forEach(function(id){ SELECTED.add(id); });
      }
    } catch (e) {}
    return original(type, index, slotIndex, event);
  };
})();
