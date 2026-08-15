#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: v3_admin_ops_v2_backend_extra.py WORKDIR')
work=Path(sys.argv[1])
code=work/'Code.js'
s=code.read_text(encoding='utf-8')

# Empty court finish must be a harmless no-op; partially occupied courts may finish.
marker='  /* Partial courts may be ended too. Existing players are cycled; an empty court is a no-op. */'
if marker in s and 'if (finished.length === 0)' not in s[s.find(marker):s.find(marker)+500]:
    repl=marker+"\n  if (finished.length === 0) {\n    startedAt[courtNo] = '';\n    writeCourts_(courts, startedAt);\n    touch_();\n    return getPublicState();\n  }"
    s=s.replace(marker,repl,1)

# Auto-fill only the missing number of seats. Existing occupants (including members who
# placed themselves) are immutable inputs and therefore have priority.
helper=r'''

/* JAYUMINTON_SELF_SEAT_PRIORITY_AUTOFILL_V2 */
function pickAutoFillIdsV2_(existingIds, needed, members) {
  existingIds = normalizeIds_(existingIds);
  needed = Number(needed) || 0;
  if (needed <= 0) return [];
  const occupied = {};
  const courts = readCourts_();
  Object.keys(courts).forEach(function(no){
    (courts[no] || []).forEach(function(id){ occupied[String(id)] = true; });
  });
  (readWaitGroups_() || []).forEach(function(group){
    (group || []).forEach(function(id){ occupied[String(id)] = true; });
  });
  existingIds.forEach(function(id){ occupied[String(id)] = true; });
  const active = (members || []).filter(function(member){
    return member && member.status === 'active' && !occupied[String(member.id)];
  }).slice().sort(function(a,b){
    const games=(Number(a.games)||0)-(Number(b.games)||0);
    return games || String(a.createdAt||'').localeCompare(String(b.createdAt||''));
  });
  let existingMale=0;
  existingIds.forEach(function(id){
    const m=(members||[]).find(function(item){return String(item.id)===String(id);});
    if(m && m.gender !== 'female') existingMale += 1;
  });
  const finalMaleTargets=[4,0,2];
  for(let i=0;i<finalMaleTargets.length;i+=1){
    const needMale=finalMaleTargets[i]-existingMale;
    const needFemale=needed-needMale;
    if(needMale<0 || needFemale<0) continue;
    const males=active.filter(function(m){return m.gender!=='female';}).slice(0,needMale);
    const females=active.filter(function(m){return m.gender==='female';}).slice(0,needFemale);
    if(males.length===needMale && females.length===needFemale){
      return males.concat(females).map(function(m){return String(m.id);});
    }
  }
  throw new Error('현재 코트배정 대기 인원으로 빈자리를 채울 복식 조합을 만들 수 없습니다.');
}
'''
if 'JAYUMINTON_SELF_SEAT_PRIORITY_AUTOFILL_V2' not in s:
    pos=s.find('function autoFillCourtUnlocked_(pin, courtNo, ids) {')
    if pos<0: raise SystemExit('autoFillCourtUnlocked_ marker missing')
    s=s[:pos]+helper+'\n'+s[pos:]

old="  const needed = GROUP_SIZE - existingIds.length;\n\n  if (needed <= 0 || ids.length !== needed) {"
new="  const needed = GROUP_SIZE - existingIds.length;\n\n  if (needed > 0 && ids.length === 0) {\n    ids = pickAutoFillIdsV2_(existingIds, needed, readMembers_());\n  }\n\n  if (needed <= 0 || ids.length !== needed) {"
# There may already be an older helper. Only insert V2 call if absent in the court function.
start=s.find('function autoFillCourtUnlocked_(pin, courtNo, ids) {')
end=s.find('function ', start+20)
segment=s[start:end if end>start else len(s)]
if 'pickAutoFillIdsV2_' not in segment:
    if old not in segment:
        # tolerate prior v1 auto fill and replace it with v2 selection
        segment2=segment.replace('ids = pickAutoFillIds_(existingIds, needed, readMembers_());','ids = pickAutoFillIdsV2_(existingIds, needed, readMembers_());')
        if segment2==segment: raise SystemExit('auto fill needed guard marker missing')
        s=s[:start]+segment2+s[end if end>start else len(s):]
    else:
        s=s[:start]+segment.replace(old,new,1)+s[end if end>start else len(s):]

code.write_text(s,encoding='utf-8')
text=code.read_text(encoding='utf-8')
for needle in ['JAYUMINTON_SELF_SEAT_PRIORITY_AUTOFILL_V2','pickAutoFillIdsV2_','if (finished.length === 0)','ids = pickAutoFillIdsV2_(existingIds, needed, readMembers_());']:
    if needle not in text: raise SystemExit('missing '+needle)
print('ADMIN_OPS_V2_BACKEND_EXTRA_OK')
