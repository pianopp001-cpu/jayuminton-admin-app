#!/usr/bin/env python3
"""Fix the "게임횟수가 2배씩 올라간다" report (game count seems to double).

Root-cause audit performed first (see this session's investigation): every
addGames() call site in the Cloudflare state worker (finishCourtMutation,
moveMutation, swapMutation) is idempotent per legitimate court entry -- ids
are deduplicated via Set, undo/redo restores the exact prior member.games
value via a full state snapshot, and the games shown in the "게임통계"
report and pair-statistics screen are read directly from member.games (no
independent/duplicated counter). No server-side path awards +1 twice for
the same physical court entry.

What IS a real, reproducible defect: neither window.finishCourt (the
"경기종료" button handler, jayuminton-admin-finish-alert-v19) nor
window.increaseSelectedGames (the manual "게임횟수 +1" button) guards
against being invoked twice before the first call's async round trip
finishes. A quick double-tap -- very plausible on a shared tablet in a busy
club -- fires the handler twice:
  - finishCourt: the Cloudflare Durable Object serializes the two requests
    but has no way to recognize them as "the same human action" (each tap
    gets its own fresh operationId), so the second call legitimately
    finishes the court AGAIN using whatever now occupies it (the queue
    Cloudflare just auto-refilled from wait1). That silently skips a queue
    rotation and hands a second, unrelated group of members a +1 they did
    not actually earn -- exactly the kind of "count jumped unexpectedly"
    symptom multiple users would notice and describe as "doubling".
  - increaseSelectedGames: same shape -- a double-tap runs two full,
    overlapping id lists through adjustMemberGames, so a single button
    press can genuinely apply +2 instead of +1 to the selected members.

Fix: add a simple busy-flag re-entrancy guard to both handlers (and disable
the finish-court button visually while its request is in flight) so a
double-tap is a no-op instead of a second real mutation.
"""
from pathlib import Path
import sys

MARKER = "JAYUMINTON_GAME_COUNT_DOUBLE_TAP_GUARD_V20913"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"v209.13 {label} anchor mismatch: {count}")
    return text.replace(old, new, 1)


def patch_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    finish_old = '''  window.finishCourt=async function(courtNo){
    var previousState=JSON.parse(JSON.stringify(STATE));
    var waitingMembers=waitingOneMembers();
    var message=finishText(courtNo,waitingMembers);
    var voice=directSpeak(message);
    window.__JAYUMINTON_SUPPRESS_TRANSITION_ALERTS__=true;
    try{
      var state=await server('finishCourt',[ADMIN_PIN_VALUE,courtNo]);
      // Apply the authoritative shifted queues immediately. Some legacy
      // renderState implementations ignore their argument and read STATE.
      if(state&&state.members){STATE=state;}
      SELECTED.clear();renderState();setUndoState(previousState);rememberVoiceAnnouncement(Number(courtNo),waitingMembers);
      // Confirm once from Cloudflare after the mutation so a stale poll cannot
      // repaint the pre-finish queue order.
      try{
        var confirmed=await server('getPublicState',[ADMIN_PIN_VALUE]);
        if(confirmed&&confirmed.members){STATE=confirmed;renderState();}
      }catch(refreshError){}
      window.__JAYUMINTON_SUPPRESS_TRANSITION_ALERTS__=false;
      if(!voice.ok)alert('음성 실행 실패: '+voice.reason);
    }catch(error){
      window.__JAYUMINTON_SUPPRESS_TRANSITION_ALERTS__=false;
      stopAlertVibration();
      alert('저장 실패\\n'+String(error&&error.message||error||'경기종료 처리에 실패했습니다.'));
    }
  };'''
    finish_new = '''  window.finishCourt=async function(courtNo){
    /* ''' + MARKER + ''': a rapid double-tap on "경기종료" used to run this
       whole async handler twice before the first tap's UI update landed.
       The server has no way to recognize the second tap as a duplicate of
       the first (each gets its own fresh operationId), so it would
       legitimately finish the just-refilled court again -- skipping a
       queue rotation and handing an extra, unearned +1 game to a second
       group of members. Guard against that instead of relying on the
       server to detect it. */
    if(window.__jmFinishCourtBusy)return;
    window.__jmFinishCourtBusy=true;
    var jmFinishBusyButtons=[];
    try{jmFinishBusyButtons=Array.prototype.slice.call(document.querySelectorAll('.finish-court-button'));}catch(_){}
    jmFinishBusyButtons.forEach(function(b){b.disabled=true;});
    try{
      var previousState=JSON.parse(JSON.stringify(STATE));
      var waitingMembers=waitingOneMembers();
      var message=finishText(courtNo,waitingMembers);
      var voice=directSpeak(message);
      window.__JAYUMINTON_SUPPRESS_TRANSITION_ALERTS__=true;
      try{
        var state=await server('finishCourt',[ADMIN_PIN_VALUE,courtNo]);
        // Apply the authoritative shifted queues immediately. Some legacy
        // renderState implementations ignore their argument and read STATE.
        if(state&&state.members){STATE=state;}
        SELECTED.clear();renderState();setUndoState(previousState);rememberVoiceAnnouncement(Number(courtNo),waitingMembers);
        // Confirm once from Cloudflare after the mutation so a stale poll cannot
        // repaint the pre-finish queue order.
        try{
          var confirmed=await server('getPublicState',[ADMIN_PIN_VALUE]);
          if(confirmed&&confirmed.members){STATE=confirmed;renderState();}
        }catch(refreshError){}
        window.__JAYUMINTON_SUPPRESS_TRANSITION_ALERTS__=false;
        if(!voice.ok)alert('음성 실행 실패: '+voice.reason);
      }catch(error){
        window.__JAYUMINTON_SUPPRESS_TRANSITION_ALERTS__=false;
        stopAlertVibration();
        alert('저장 실패\\n'+String(error&&error.message||error||'경기종료 처리에 실패했습니다.'));
      }
    }finally{
      window.__jmFinishCourtBusy=false;
      jmFinishBusyButtons.forEach(function(b){b.disabled=false;});
    }
  };'''
    text = replace_once(text, finish_old, finish_new, "finishCourt")

    games_old = '''  window.increaseSelectedGames=function(){
    var ids=allStoredSelectionIds();
    if(!ids.length){alert('게임횟수를 올릴 멤버를 선택하세요.');return;}
    var index=0,lastState=null;
    function next(){
      if(index>=ids.length){clearBothSelections();if(lastState)renderState(lastState);else loadState();return;}
      var id=ids[index++];
      server('adjustMemberGames',[ADMIN_PIN_VALUE,id,1]).then(function(state){lastState=state;next();})
        .catch(function(error){alert(error.message||error);});
    }
    next();
  };'''
    games_new = '''  window.increaseSelectedGames=function(){
    /* ''' + MARKER + ''': same double-tap hazard as finishCourt -- without
       this guard, tapping "게임횟수 +1" twice quickly could genuinely send
       two overlapping adjustMemberGames sequences and apply +2. */
    if(window.__jmIncreaseGamesBusy)return;
    var ids=allStoredSelectionIds();
    if(!ids.length){alert('게임횟수를 올릴 멤버를 선택하세요.');return;}
    window.__jmIncreaseGamesBusy=true;
    var index=0,lastState=null;
    function next(){
      if(index>=ids.length){window.__jmIncreaseGamesBusy=false;clearBothSelections();if(lastState)renderState(lastState);else loadState();return;}
      var id=ids[index++];
      server('adjustMemberGames',[ADMIN_PIN_VALUE,id,1]).then(function(state){lastState=state;next();})
        .catch(function(error){window.__jmIncreaseGamesBusy=false;alert(error.message||error);});
    }
    next();
  };'''
    text = replace_once(text, games_old, games_new, "increaseSelectedGames")

    required = [
        MARKER,
        "window.__jmFinishCourtBusy",
        "window.__jmIncreaseGamesBusy",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit("v209.13 marker missing: " + needle)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
    patch_html(html_path)
    print("ADMIN_V20913_GAME_COUNT_DOUBLE_TAP_GUARD_OK")
