#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_md_member_fields_patch.py INDEX_HTML')
path = Path(sys.argv[1])
html = path.read_text(encoding='utf-8')
marker = '__JAYUMINTON_ADMIN_MD_MEMBER_FIELDS_V2__'
if marker in html:
    raise SystemExit(0)
if '</body>' not in html:
    raise SystemExit('body marker missing')

# Add memo/new/sponsor controls immediately after the legacy experience field.
if 'id="mdPublicMemo"' not in html:
    m = re.search(r'<input\b[^>]*\bid=["\']newExperience["\'][^>]*>', html, re.I|re.S)
    if not m:
        raise SystemExit('newExperience input missing')
    fields = r'''
      <textarea id="mdPublicMemo" maxlength="120" rows="2" placeholder="메모(생일·특이사항·부상 등, 선택)"></textarea>
      <label class="md-member-check"><input id="mdIsNew" type="checkbox"> new 신규</label>
      <label class="md-member-check"><input id="mdIsSponsor" type="checkbox"> 🎁 찬조</label>
'''
    html = html[:m.end()] + fields + html[m.end():]

# The legacy addMember path calls google.script.run directly. Add the metadata argument there as well.
if 'mdIsSponsor' in html and "document.getElementById('mdPublicMemo')" not in html.split('google.script.run',1)[-1].split(');',1)[0]:
    pat = re.compile(
        r'(\.addMember\(\s*ADMIN_PIN_VALUE\s*,\s*name\s*,\s*gender\s*,\s*grade\s*,\s*experience)(\s*\))',
        re.S,
    )
    meta_arg = r"\1, {publicMemo:String(document.getElementById('mdPublicMemo')?.value||'').trim(),isNew:!!document.getElementById('mdIsNew')?.checked,isSponsor:!!document.getElementById('mdIsSponsor')?.checked}\2"
    html, count = pat.subn(meta_arg, html, count=1)
    if count != 1:
        raise SystemExit('direct addMember metadata patch failed')

# Include metadata on the optimistic temporary member card.
if "publicMemo: String(document.getElementById('mdPublicMemo')" not in html:
    old = "    experience: experience,\n    createdAt: new Date().toISOString()"
    new = "    experience: experience,\n    publicMemo: String(document.getElementById('mdPublicMemo')?.value || '').trim(),\n    isNew: !!document.getElementById('mdIsNew')?.checked,\n    isSponsor: !!document.getElementById('mdIsSponsor')?.checked,\n    createdAt: new Date().toISOString()"
    if old not in html:
        raise SystemExit('temporary member anchor missing')
    html = html.replace(old, new, 1)

# Pair statistics modal is created here if the downloaded Cloudflare source does not already contain it.
if 'id="pairStatisticsModal"' not in html:
    modal = r'''
<div id="pairStatisticsModal" class="modal-backdrop hidden">
  <div class="modal-card pair-statistics-modal">
    <div class="modal-head"><h2>함께 경기통계</h2><button type="button" class="modal-close" onclick="closeMdPairStatistics()">×</button></div>
    <div id="mdPairStatisticsList" class="pair-statistics-list"></div>
  </div>
</div>
'''
    html = html.replace('</body>', modal + '\n</body>', 1)

addon = r'''
<style id="jayuminton-admin-md-member-fields-v2">
#mdPublicMemo{min-width:180px;min-height:46px;resize:vertical}
.md-member-check{display:inline-flex!important;align-items:center!important;gap:5px!important;min-height:42px!important;padding:7px 10px!important;border:1px solid #dce2ee!important;border-radius:11px!important;background:#fff!important;font-weight:900!important;white-space:nowrap!important}
.md-member-check input{width:18px!important;height:18px!important;min-height:0!important;margin:0!important}
#pairStatisticsModal .pair-statistics-modal{max-width:620px;width:min(94vw,620px);max-height:86vh;overflow:auto}
#mdPairStatisticsList{display:grid;gap:8px;padding-bottom:24px}
.md-pair-row{border:1px solid #dce2ee;border-radius:12px;padding:10px;background:#fff}
.md-pair-head{display:flex;justify-content:space-between;gap:8px;font-weight:950}
.md-pair-partners{font-size:12px;line-height:1.55;margin-top:5px;color:#475569;white-space:normal}
</style>
<script id="jayuminton-admin-md-member-fields-script-v2">
(function(){
  'use strict';
  window.__JAYUMINTON_ADMIN_MD_MEMBER_FIELDS_V1__=true;
  window.__JAYUMINTON_ADMIN_MD_MEMBER_FIELDS_V2__=true;

  function meta(){
    var memo=document.getElementById('mdPublicMemo');
    var isNew=document.getElementById('mdIsNew');
    var sponsor=document.getElementById('mdIsSponsor');
    return {
      publicMemo:String(memo&&memo.value||'').trim(),
      isNew:!!(isNew&&isNew.checked),
      isSponsor:!!(sponsor&&sponsor.checked)
    };
  }
  function clearMeta(){
    var memo=document.getElementById('mdPublicMemo'); if(memo)memo.value='';
    var isNew=document.getElementById('mdIsNew'); if(isNew)isNew.checked=false;
    var sponsor=document.getElementById('mdIsSponsor'); if(sponsor)sponsor.checked=false;
  }
  function loadMeta(member){
    if(!member)return;
    var memo=document.getElementById('mdPublicMemo'); if(memo)memo.value=String(member.publicMemo||member.memo||'');
    var isNew=document.getElementById('mdIsNew'); if(isNew)isNew.checked=!!member.isNew;
    var sponsor=document.getElementById('mdIsSponsor'); if(sponsor)sponsor.checked=!!member.isSponsor;
  }

  // updateMemberProfile uses server(), so augment its optional metadata argument centrally.
  if(typeof server==='function'){
    var mdOriginalServer=server;
    server=function(name,args){
      var next=Array.isArray(args)?args.slice():[];
      if(name==='addMember' && next.length<6)next[5]=meta();
      if(name==='updateMemberProfile')next[6]=meta();
      return mdOriginalServer(name,next);
    };
  }

  var lastEdit='';
  setInterval(function(){
    var id=''; try{id=String(EDIT_MEMBER_ID||'');}catch(e){}
    if(id===lastEdit)return;
    var previous=lastEdit;
    lastEdit=id;
    if(!id){if(previous)clearMeta();return;}
    var member=null;
    try{member=(STATE.members||[]).find(function(m){return String(m.id)===id;})||null;}catch(e){}
    loadMeta(member);
  },200);

  // Successful registration resets all three MD-only fields as well.
  document.addEventListener('click',function(event){
    var button=event.target&&event.target.closest&&event.target.closest('#addMemberButton');
    if(!button)return;
    var beforeCount=0; try{beforeCount=(STATE.members||[]).length;}catch(e){}
    setTimeout(function check(){
      var busy=false; try{busy=!!ADD_MEMBER_IN_FLIGHT;}catch(e){}
      if(busy){setTimeout(check,150);return;}
      var afterCount=0; try{afterCount=(STATE.members||[]).length;}catch(e){}
      if(afterCount>beforeCount)clearMeta();
    },150);
  },true);

  window.closeMdPairStatistics=function(){
    var modal=document.getElementById('pairStatisticsModal'); if(modal)modal.classList.add('hidden');
  };
  window.openPairStatistics=async function(){
    var modal=document.getElementById('pairStatisticsModal');
    var list=document.getElementById('mdPairStatisticsList') || (modal&&modal.querySelector('.pair-statistics-list'));
    if(!modal||!list){alert('경기통계 화면을 찾을 수 없습니다.');return;}
    modal.classList.remove('hidden');
    list.innerHTML='<div class="meta">통계를 불러오는 중...</div>';
    try{
      var rows=await server('getPairStatistics',[ADMIN_PIN_VALUE]);
      if(!Array.isArray(rows))rows=[];
      if(!rows.length){list.innerHTML='<div class="meta">기록된 경기통계가 없습니다.</div>';return;}
      list.innerHTML=rows.map(function(row){
        var p=Array.isArray(row.partners)?row.partners:[];
        var detail=p.length?p.map(function(x){return escapeMemberInfo(String(x.name||''))+' '+Number(x.count||0)+'회';}).join(' · '):'함께 경기한 기록 없음';
        return '<div class="md-pair-row pair-statistics-row"><div class="md-pair-head"><span>'+escapeMemberInfo(String(row.name||''))+'</span><span>'+Number(row.games||0)+'게임</span></div><div class="md-pair-partners pair-statistics-partners">'+detail+'</div></div>';
      }).join('');
    }catch(error){list.innerHTML='<div class="meta">통계를 불러오지 못했습니다.</div>';alert(error.message||error);}
  };
})();
</script>
<!-- __JAYUMINTON_ADMIN_MD_MEMBER_FIELDS_V1__ -->
<!-- __JAYUMINTON_ADMIN_MD_MEMBER_FIELDS_V2__ -->
'''
html = html.replace('</body>', addon + '\n</body>', 1)

for req in (
    marker,'id="mdPublicMemo"','id="mdIsNew"','id="mdIsSponsor"',
    "publicMemo:String(document.getElementById('mdPublicMemo')", 'isSponsor:!!document.getElementById',
    "if(name==='updateMemberProfile')next[6]=meta()",
    'window.openPairStatistics=async function()', "server('getPairStatistics',[ADMIN_PIN_VALUE])",
    'new 신규','🎁 찬조','pairStatisticsModal'
):
    if req not in html:
        raise SystemExit('missing member-field requirement: '+req)
path.write_text(html,encoding='utf-8')
print('ADMIN_MD_MEMBER_FIELDS_V2_OK')
