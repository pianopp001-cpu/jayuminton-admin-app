#!/usr/bin/env python3
"""v209.34 combined fix:
1) stack admin/member profile text vertically inside court/wait cards,
2) make Select All -> Away/status use the complete member-id set and verify server result,
3) replace opening AGC/RMS-bucket boost with deterministic pre-playback fixed gain.
"""

from pathlib import Path
import re
import sys

html_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app/src/main/assets/admin/index.html")
java_path = Path(sys.argv[2] if len(sys.argv) > 2 else "app/src/main/java/com/jayuminton/admin/MainActivity.java")
html = html_path.read_text(encoding="utf-8")
java = java_path.read_text(encoding="utf-8")

HTML_MARKER = "JAYUMINTON_CARD_STACK_BULK_STATUS_V20934"
VOICE_MARKER = "JAYUMINTON_BLUETOOTH_OPENING_FIXED_GAIN_V20934"

if HTML_MARKER in html and VOICE_MARKER in java:
    print("ADMIN_V20934_THREE_CRITICAL_FIXES_ALREADY_OK")
    raise SystemExit(0)

# ---------------------------------------------------------------------------
# 1) COURT/WAIT CARD LAYOUT
# v209.16 appends userMemo as a direct flex child of .person. Court/wait cards
# are horizontal rows, so that puts the purple user memo beside the profile.
# Move it into the same first content span that already holds name/games/profile.
# Active "코트배정 대기" cards are intentionally left unchanged.
# ---------------------------------------------------------------------------
for token in (
    "JAYUMINTON_ADMIN_MEMBER_MEMO_OWNERSHIP_V20916",
    "member.userMemo",
    "jm-member-owned-memo",
):
    if token not in html:
        raise SystemExit("v209.34 HTML prerequisite missing: " + token)

old_node = "      var node=card.querySelector(':scope > .jm-member-owned-memo');"
new_node = """      var stackedCard=!!card.closest('.court-card,.wait-card,.v4-court-card,.v4-wait-card');
      var host=stackedCard?(card.querySelector(':scope > span')||card):card;
      var node=card.querySelector('.jm-member-owned-memo');"""
if html.count(old_node) != 1:
    raise SystemExit("v209.34 memo node anchor mismatch: " + str(html.count(old_node)))
html = html.replace(old_node, new_node, 1)

old_create = """      if(!node){
        node=document.createElement('span');
        node.className='jm-member-owned-memo';
        card.appendChild(node);
      }
      if(node.textContent!==memo)node.textContent=memo;"""
new_create = """      if(!node){
        node=document.createElement('span');
        node.className='jm-member-owned-memo';
        host.appendChild(node);
      }else if(stackedCard&&node.parentElement!==host){
        host.appendChild(node);
      }
      if(node.textContent!==memo)node.textContent=memo;"""
if html.count(old_create) != 1:
    raise SystemExit("v209.34 memo create anchor mismatch: " + str(html.count(old_create)))
html = html.replace(old_create, new_create, 1)

addon = r'''
<style id="jayuminton-admin-card-stack-v20934">
/* JAYUMINTON_CARD_STACK_BULK_STATUS_V20934 */
#adminApp .court-card .person:not(.empty)>span:first-of-type,
#adminApp .wait-card .person:not(.empty)>span:first-of-type,
#adminApp .v4-court-card .person:not(.empty)>span:first-of-type,
#adminApp .v4-wait-card .person:not(.empty)>span:first-of-type{
  display:flex!important;
  flex:1 1 auto!important;
  min-width:0!important;
  width:auto!important;
  flex-direction:column!important;
  align-items:stretch!important;
  justify-content:center!important;
  gap:1px!important;
}
#adminApp .court-card .person:not(.empty)>span:first-of-type>.name,
#adminApp .court-card .person:not(.empty)>span:first-of-type>.meta,
#adminApp .court-card .person:not(.empty)>span:first-of-type>.member-info-detail,
#adminApp .court-card .person:not(.empty)>span:first-of-type>.member-public-memo,
#adminApp .court-card .person:not(.empty)>span:first-of-type>.jm-member-owned-memo,
#adminApp .wait-card .person:not(.empty)>span:first-of-type>.name,
#adminApp .wait-card .person:not(.empty)>span:first-of-type>.meta,
#adminApp .wait-card .person:not(.empty)>span:first-of-type>.member-info-detail,
#adminApp .wait-card .person:not(.empty)>span:first-of-type>.member-public-memo,
#adminApp .wait-card .person:not(.empty)>span:first-of-type>.jm-member-owned-memo{
  display:block!important;
  position:static!important;
  float:none!important;
  clear:both!important;
  width:100%!important;
  max-width:100%!important;
  margin-left:0!important;
  margin-right:0!important;
  text-align:center!important;
  white-space:normal!important;
  overflow-wrap:anywhere!important;
}
#adminApp .court-card .person:not(.empty)>.small,
#adminApp .wait-card .person:not(.empty)>.small{
  flex:0 0 auto!important;
  align-self:center!important;
}
</style>
<script id="jayuminton-admin-bulk-status-v20934">
(function(){
  'use strict';
  if(window.__JAYUMINTON_CARD_STACK_BULK_STATUS_V20934__)return;
  window.__JAYUMINTON_CARD_STACK_BULK_STATUS_V20934__=true;

  function currentState(){
    try{return window.STATE||(typeof STATE!=='undefined'?STATE:null);}catch(_){return null;}
  }
  function validIds(){
    var s=currentState(), ids=[];
    try{(s&&Array.isArray(s.members)?s.members:[]).forEach(function(m){
      var id=String(m&&m.id!=null?m.id:''); if(id&&ids.indexOf(id)<0)ids.push(id);
    });}catch(_){}
    return ids;
  }
  function selectedIdsCompleteV20934(){
    var valid=new Set(validIds()), ids=new Set();
    try{Array.from(SELECTED||[]).forEach(function(id){id=String(id);if(valid.has(id))ids.add(id);});}catch(_){}
    try{Array.from(window.__jmUnlimitedSelected||[]).forEach(function(id){id=String(id);if(valid.has(id))ids.add(id);});}catch(_){}
    try{
      document.querySelectorAll('#adminApp [data-member-id].selected,#adminApp [data-member-id].jm-v2074-selected,#adminApp [data-member-id].quick-picked').forEach(function(card){
        var id=String(card.getAttribute('data-member-id')||'');if(valid.has(id))ids.add(id);
      });
    }catch(_){}
    return Array.from(ids);
  }
  window.selectedIdsDomScanV20934=selectedIdsCompleteV20934;

  function syncBoth(ids){
    ids=(ids||[]).map(String).filter(Boolean);
    try{
      SELECTED.clear();
      ids.forEach(function(id){SELECTED.add(id);});
    }catch(_){
      try{SELECTED=new Set(ids);}catch(__){}
    }
    try{
      var live=window.__jmUnlimitedSelected;
      if(live&&typeof live.clear==='function'&&typeof live.add==='function'){
        live.clear();ids.forEach(function(id){live.add(id);});
      }
    }catch(_){}
  }
  function clearBoth(){
    try{SELECTED.clear();}catch(_){}
    try{
      if(typeof window.__jmClearUnlimitedSelectedV1==='function')window.__jmClearUnlimitedSelectedV1();
      else if(window.__jmUnlimitedSelected&&window.__jmUnlimitedSelected.clear)window.__jmUnlimitedSelected.clear();
    }catch(_){}
    try{if(typeof cancelQuickPick==='function')cancelQuickPick();}catch(_){}
  }

  function selectAllV20934(){
    var ids=validIds();
    syncBoth(ids);
    try{renderState();}catch(_){}
    return ids;
  }
  window.jmSelectAllMembersV20934=selectAllV20934;
  window.selectAllMembers=selectAllV20934;

  async function applyStatusV20934(status,label){
    var ids=selectedIdsCompleteV20934();
    if(!ids.length){alert('멤버를 선택하세요.');return;}
    var before=null;
    try{before=JSON.parse(JSON.stringify(currentState()));}catch(_){}
    try{
      var result=await server('setMemberStatus',[ADMIN_PIN_VALUE,ids,status]);
      var state=result&&result.state?result.state:result;
      if(state&&state.members){try{STATE=state;}catch(_){};renderState(state);}

      // Verify the authoritative state once. If any selected ID was omitted by
      // an older selection bridge/race, retry only those IDs once.
      var check=await server('getPublicState',[ADMIN_PIN_VALUE]);
      check=check&&check.state?check.state:check;
      var byId={};
      (check&&Array.isArray(check.members)?check.members:[]).forEach(function(m){byId[String(m.id)]=m;});
      var missing=ids.filter(function(id){return !byId[id]||String(byId[id].status)!==String(status);});
      if(missing.length){
        var retry=await server('setMemberStatus',[ADMIN_PIN_VALUE,missing,status]);
        check=retry&&retry.state?retry.state:retry;
      }
      if(check&&check.members){try{STATE=check;}catch(_){};renderState(check);}
      clearBoth();
      if(before&&typeof setUndoState==='function')setUndoState(before);
    }catch(error){
      if(before){try{STATE=before;renderState(before);}catch(_){}}
      alert((error&&error.message)||error);
    }
  }
  window.jmSetSelectedStatusV20934=applyStatusV20934;
  window.setSelectedStatus=function(status){
    var labels={away:'귀가',before:'도착전',rest:'휴식',active:'배정대기'};
    return applyStatusV20934(status,labels[status]||status);
  };

  function bind(){
    [
      ['jmQuickAll',function(e){e.preventDefault();e.stopImmediatePropagation();selectAllV20934();}],
      ['jmQuickAway',function(e){e.preventDefault();e.stopImmediatePropagation();applyStatusV20934('away','귀가');}],
      ['jmQuickBefore',function(e){e.preventDefault();e.stopImmediatePropagation();applyStatusV20934('before','도착전');}],
      ['jmQuickActive',function(e){e.preventDefault();e.stopImmediatePropagation();applyStatusV20934('active','배정대기');}],
      ['jmQuickClear',function(e){e.preventDefault();e.stopImmediatePropagation();clearBoth();try{renderState();}catch(_){}}]
    ].forEach(function(item){
      var b=document.getElementById(item[0]);
      if(!b||b.__jmV20934Bound)return;
      b.__jmV20934Bound=true;
      b.addEventListener('click',item[1],true);
    });
  }
  function boot(){
    bind();
    var root=document.getElementById('adminApp')||document.body;
    if(root&&!root.__jmV20934StatusObserver){
      root.__jmV20934StatusObserver=new MutationObserver(bind);
      root.__jmV20934StatusObserver.observe(root,{childList:true,subtree:true});
    }
    setInterval(bind,1500);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
</script>
'''

close = html.lower().rfind("</body>")
if close < 0:
    raise SystemExit("v209.34 body close missing")
html = html[:close] + addon + "\n" + html[close:]

# ---------------------------------------------------------------------------
# 2) BLUETOOTH OPENING: FIXED PRE-PLAYBACK GAIN, NO AGC ATTACK/RELEASE.
# The existing v209.19 logic measures ~2.1s as one RMS bucket and boosts that
# bucket dynamically in the final loop. Replace it with one constant gain for
# the detected "N번 코트 나왔습니다" region. The first voiced sample receives
# the full gain immediately. The gain ends in the natural pause after the phrase.
# ---------------------------------------------------------------------------
for token in (
    "JAYUMINTON_BLUETOOTH_COURT_OPENING_PRIORITY_V20919",
    "JAYUMINTON_REPORT_SQUARE_LAYOUT_V20933",
    "COURT_FINISH_OPENING_TARGET_RMS_DBFS = -4.5",
    "COURT_FINISH_OPENING_MAX_GAIN_DB = 12.0",
    "courtOpeningBoost",
    "double finalPeak = 0.0;",
):
    if token not in java:
        raise SystemExit("v209.34 voice prerequisite missing: " + token)

old_consts = '''    private static final String BLUETOOTH_COURT_OPENING_PRIORITY = "JAYUMINTON_BLUETOOTH_COURT_OPENING_PRIORITY_V20919";
    private static final double COURT_FINISH_OPENING_TARGET_RMS_DBFS = -4.5;
    private static final double COURT_FINISH_OPENING_MAX_GAIN_DB = 12.0;
    private static final double COURT_FINISH_OPENING_SECONDS = 2.10;
    private static final double COURT_FINISH_OPENING_RELEASE_SECONDS = 0.14;
    private static final double COURT_FINISH_OPENING_ONSET_DBFS = -44.0;
'''
new_consts = '''    private static final String BLUETOOTH_COURT_OPENING_PRIORITY = "JAYUMINTON_BLUETOOTH_COURT_OPENING_PRIORITY_V20919";
    private static final String BLUETOOTH_COURT_OPENING_FIXED_GAIN = "''' + VOICE_MARKER + '''";
    // v209.34: fixed offline gain. No AGC/envelope attack or release is used.
    private static final double COURT_FINISH_OPENING_TARGET_RMS_DBFS = -7.0;
    private static final double COURT_FINISH_OPENING_MAX_GAIN_DB = 18.0;
    private static final double COURT_FINISH_OPENING_MAX_SECONDS = 2.80;
    private static final double COURT_FINISH_OPENING_MIN_SECONDS = 1.30;
    private static final double COURT_FINISH_OPENING_ONSET_DBFS = -46.0;
    private static final double COURT_FINISH_OPENING_PAUSE_DBFS = -40.0;
    private static final double COURT_FINISH_OPENING_PAUSE_SECONDS = 0.12;
    private static final double COURT_FINISH_OPENING_FRAME_SECONDS = 0.020;
'''
if java.count(old_consts) != 1:
    raise SystemExit("v209.34 voice constants anchor mismatch: " + str(java.count(old_consts)))
java = java.replace(old_consts, new_consts, 1)

start = java.find("            int courtOpeningStartSample = -1;")
end = java.find("            double finalPeak = 0.0;", start)
if start < 0 or end < 0:
    raise SystemExit("v209.34 old opening block boundaries missing")
old_opening = java[start:end]
if "courtOpeningBoost" not in old_opening or "openingSquares" not in old_opening:
    raise SystemExit("v209.34 old opening block unexpected")
java = java[:start] + '''            if (maximizeFullCourtFinish) {
                applyCourtOpeningFixedGain(pcm, makeup, sampleRate, channels);
            }

''' + java[end:]

old_dynamic = '''                if (maximizeFullCourtFinish && courtOpeningStartSample >= 0 &&
                        i >= courtOpeningStartSample && i < courtOpeningReleaseEndSample) {
                    double localBoost = courtOpeningBoost;
                    if (i >= courtOpeningEndSample && courtOpeningReleaseEndSample > courtOpeningEndSample) {
                        double t = (i - courtOpeningEndSample) /
                                (double) (courtOpeningReleaseEndSample - courtOpeningEndSample);
                        localBoost = 1.0 + (courtOpeningBoost - 1.0) * Math.max(0.0, 1.0 - t);
                    }
                    y *= localBoost;
                }
'''
if java.count(old_dynamic) != 1:
    raise SystemExit("v209.34 old dynamic boost anchor mismatch: " + str(java.count(old_dynamic)))
java = java.replace(old_dynamic, "", 1)

helper_anchor = "    private double dbToLinear(double db) {\n"
if java.count(helper_anchor) != 1:
    raise SystemExit("v209.34 db helper anchor mismatch")

helper = r'''    private void applyCourtOpeningFixedGain(
            float[] pcm, double makeup, int sampleRate, int channels) {
        if (pcm == null || pcm.length == 0 || sampleRate < 8000 || channels < 1 ||
                !Double.isFinite(makeup) || makeup <= 0.0) return;

        final int samplesPerSecond = Math.max(channels, sampleRate * channels);
        final int frameSamples = Math.max(
                channels,
                (int) Math.round(COURT_FINISH_OPENING_FRAME_SECONDS * samplesPerSecond));
        final double onsetThreshold = dbToLinear(COURT_FINISH_OPENING_ONSET_DBFS);
        final double pauseThreshold = dbToLinear(COURT_FINISH_OPENING_PAUSE_DBFS);
        final int searchEnd = Math.min(pcm.length, samplesPerSecond * 2);

        int speechStart = -1;
        for (int pos = 0; pos < searchEnd; pos += frameSamples) {
            int limit = Math.min(searchEnd, pos + frameSamples);
            double sq = 0.0;
            int count = 0;
            for (int i = pos; i < limit; i++) {
                double v = pcm[i] * makeup;
                sq += v * v;
                count++;
            }
            if (count > 0 && Math.sqrt(sq / count) >= onsetThreshold) {
                speechStart = pos;
                break;
            }
        }
        if (speechStart < 0) return;

        final int minimumEnd = Math.min(
                pcm.length,
                speechStart + (int) Math.round(
                        COURT_FINISH_OPENING_MIN_SECONDS * samplesPerSecond));
        final int maximumEnd = Math.min(
                pcm.length,
                speechStart + (int) Math.round(
                        COURT_FINISH_OPENING_MAX_SECONDS * samplesPerSecond));
        final int pauseFramesNeeded = Math.max(
                2,
                (int) Math.ceil(
                        COURT_FINISH_OPENING_PAUSE_SECONDS /
                        COURT_FINISH_OPENING_FRAME_SECONDS));

        int speechEnd = maximumEnd;
        int quietFrames = 0;
        for (int pos = minimumEnd; pos < maximumEnd; pos += frameSamples) {
            int limit = Math.min(maximumEnd, pos + frameSamples);
            double sq = 0.0;
            int count = 0;
            for (int i = pos; i < limit; i++) {
                double v = pcm[i] * makeup;
                sq += v * v;
                count++;
            }
            double rms = count > 0 ? Math.sqrt(sq / count) : 0.0;
            if (rms < pauseThreshold) {
                quietFrames++;
                if (quietFrames >= pauseFramesNeeded) {
                    speechEnd = Math.max(
                            minimumEnd,
                            pos - (quietFrames - 1) * frameSamples);
                    break;
                }
            } else {
                quietFrames = 0;
            }
        }
        if (speechEnd <= speechStart) return;

        // Measure only voiced frames. Silence between "N번", "코트", and
        // "나왔습니다" must not trick the gain calculation.
        double activeSquares = 0.0;
        double openingPeak = 0.0;
        long activeSamples = 0L;
        for (int pos = speechStart; pos < speechEnd; pos += frameSamples) {
            int limit = Math.min(speechEnd, pos + frameSamples);
            double frameSq = 0.0;
            int frameCount = 0;
            for (int i = pos; i < limit; i++) {
                double v = pcm[i] * makeup;
                frameSq += v * v;
                openingPeak = Math.max(openingPeak, Math.abs(v));
                frameCount++;
            }
            double frameRms = frameCount > 0 ? Math.sqrt(frameSq / frameCount) : 0.0;
            if (frameRms >= onsetThreshold) {
                activeSquares += frameSq;
                activeSamples += frameCount;
            }
        }
        if (activeSamples <= 0L || activeSquares <= 1.0e-12 || openingPeak <= 1.0e-9) return;

        double openingRms = Math.sqrt(activeSquares / activeSamples);
        double targetRms = dbToLinear(COURT_FINISH_OPENING_TARGET_RMS_DBFS);
        double maxGain = dbToLinear(COURT_FINISH_OPENING_MAX_GAIN_DB);
        double ceiling = dbToLinear(VOICE_PEAK_CEILING_DBFS);
        double fixedGain = Math.max(
                1.0,
                Math.min(
                        maxGain,
                        Math.min(targetRms / openingRms, ceiling / openingPeak)));
        if (!Double.isFinite(fixedGain) || fixedGain <= 1.0001) return;

        // Constant gain from the first voiced sample to the pause after
        // "N번 코트 나왔습니다". No attack. No release. No runtime AGC.
        for (int i = speechStart; i < speechEnd; i++) {
            pcm[i] = (float) (pcm[i] * fixedGain);
        }
    }

'''
java = java.replace(helper_anchor, helper + helper_anchor, 1)

status_old = '+ ":" + BLUETOOTH_COURT_OPENING_PRIORITY + ":ready="'
status_new = '+ ":" + BLUETOOTH_COURT_OPENING_PRIORITY + ":" + BLUETOOTH_COURT_OPENING_FIXED_GAIN + ":ready="'
if status_old not in java:
    raise SystemExit("v209.34 voice status anchor missing")
java = java.replace(status_old, status_new, 1)

for required in (
    HTML_MARKER,
    "stackedCard",
    "host.appendChild(node);",
    "selectedIdsDomScanV20934",
    "jmSelectAllMembersV20934",
    "jmSetSelectedStatusV20934",
    "missing=ids.filter",
    VOICE_MARKER,
    "applyCourtOpeningFixedGain(pcm, makeup, sampleRate, channels)",
    "COURT_FINISH_OPENING_TARGET_RMS_DBFS = -7.0",
    "COURT_FINISH_OPENING_MAX_GAIN_DB = 18.0",
    "No attack. No release. No runtime AGC.",
):
    if required not in html + java:
        raise SystemExit("v209.34 output missing: " + required)

for forbidden in (
    "courtOpeningBoost",
    "courtOpeningReleaseEndSample",
    "COURT_FINISH_OPENING_RELEASE_SECONDS",
):
    if forbidden in java:
        raise SystemExit("v209.34 obsolete dynamic opening behavior survived: " + forbidden)

html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")
print("ADMIN_V20934_THREE_CRITICAL_FIXES_OK")
