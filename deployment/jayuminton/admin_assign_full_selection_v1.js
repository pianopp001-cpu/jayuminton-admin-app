/* __JAYUMINTON_ADMIN_ASSIGN_FULL_SELECTION_V1__
   Some code path calling assignMembersToCourt/assignMembersToWaitGroup
   (not directly traceable to assign()/assignSelectedToClicked/
   handleEmptySlotTap in live testing -- likely another closure-local
   caller) ends up sending only ONE selected member instead of the
   whole current selection when placing multiple selected members
   (e.g. one from each gender, selected across a quick-roster filter
   switch) into an empty court/wait slot at once. Empirically confirmed
   by wrapping window.server directly: the call already arrives with a
   truncated ids array by the time it reaches here.

   Fix at the one point proven (via live testing) to reliably see
   every such call: window.server itself. If the outgoing ids array is
   shorter than the toolbar's own full current selection AND there is
   room for more in the target court/wait group, expand it to the full
   selection (capped at remaining capacity) before it goes out. Uses
   the same defensive re-wrap-on-interval pattern as
   admin_server_timeout_v1.js, since other scripts also wrap
   window.server and load order isn't guaranteed.
*/
(function(){
  if (window.__JAYUMINTON_ADMIN_ASSIGN_FULL_SELECTION_V1__) return;
  window.__JAYUMINTON_ADMIN_ASSIGN_FULL_SELECTION_V1__ = true;

  function wrap(){
    var current = window.server;
    if (typeof current !== 'function' || current.__jmAssignFullSelectionV1) return;
    var wrapped = function(name, args){
      try {
        if ((name === 'assignMembersToCourt' || name === 'assignMembersToWaitGroup') &&
            Array.isArray(args) && Array.isArray(args[2]) &&
            typeof window.selectedIds === 'function') {
          var full = window.selectedIds();
          if (Array.isArray(full) && full.length > args[2].length) {
            var key = args[1];
            var current2;
            try {
              current2 = (name === 'assignMembersToCourt')
                ? ((window.STATE && window.STATE.courts && window.STATE.courts[key]) || [])
                : ((window.STATE && window.STATE.waitGroups && window.STATE.waitGroups[Number(key)]) || []);
            } catch (e) { current2 = []; }
            var free = Math.max(0, 4 - current2.length);
            var expanded = full.slice(0, free);
            if (expanded.length > args[2].length) {
              args = [args[0], args[1], expanded];
            }
          }
        }
      } catch (e) {}
      return current.apply(this, arguments);
    };
    wrapped.__jmAssignFullSelectionV1 = true;
    window.server = wrapped;
  }
  wrap();
  var tries = 0, timer = setInterval(function(){ wrap(); if (++tries > 150) clearInterval(timer); }, 200);
})();
