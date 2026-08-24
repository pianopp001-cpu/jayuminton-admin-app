#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: admin_md_card_timer_patch.py INDEX_HTML')
path=Path(sys.argv[1])
html=path.read_text(encoding='utf-8')
marker='__JAYUMINTON_ADMIN_MD_CARD_TIMER_V1__'
if marker not in html:
    addon=r'''
<style id="jayuminton-admin-md-card-timer-v1">
.member-md-badges{display:flex;gap:4px;flex-wrap:wrap;justify-content:center;margin-top:2px;font-size:10px;font-weight:900}
.member-md-badge{display:inline-flex;align-items:center;gap:2px;padding:1px 5px;border-radius:999px;background:rgba(255,255,255,.72)}
.member-md-memo{display:block;font-size:10px;line-height:1.25;margin-top:2px;font-weight:700;opacity:.86;white-space:normal;word-break:break-word}
</style>
<script id="jayuminton-admin-md-card-timer-script-v1">
(function(){
  function mdProfileParts(member){
    if(!member)return [];
    try{if(typeof normalizeMemberProfile==='function')normalizeMemberProfile(member);}catch(e){}
    var parts=[];
    var grade=String(member.grade||'').trim();
    var exp=String(member.experience||member.career||'').trim().replace(/^구력\s*/i,'').trim();
    var memo=String(member.publicMemo||member.memo||'').trim();
    if(grade)parts.push(escapeMemberInfo(grade));
    if(exp)parts.push(escapeMemberInfo('구력 '+exp));
    if(memo)parts.push('<span class="member-md-memo">'+escapeMemberInfo(memo)+'</span>');
    return parts;
  }

  memberInfoDetailHtml=function(member){
    var parts=mdProfileParts(member);
    if(!parts.length)return '';
    var inline=parts.filter(function(x){return x.indexOf('member-md-memo')<0;});
    var memo=parts.filter(function(x){return x.indexOf('member-md-memo')>=0;}).join('');
    return (inline.length?'<span class="member-info-detail">'+inline.join(' · ')+'</span>':'')+memo;
  };

  function mdBadges(member){
    var badges=[];
    if(member&&member.isNew)badges.push('<span class="member-md-badge">new 신규</span>');
    if(member&&member.isSponsor)badges.push('<span class="member-md-badge">🎁 찬조</span>');
    return badges.length?'<span class="member-md-badges">'+badges.join('')+'</span>':'';
  }

  memberCard=function(member,showGames,clickable){
    if(!member)return '<div class="person empty">비어 있음</div>';
    var selected=SELECTED.has(member.id)?' selected':'';
    var onclick=clickable?' onclick="handleSelectableMemberClick(\\''+member.id+'\\',event)"':'';
    var games=showGames?'<span class="meta">'+(member.games||0)+'게임</span>':'';
    var selfStar=(typeof isSelfMember==='function'&&isSelfMember(member))?'<span class="member-self-star" aria-label="내 이름">★ 나</span>':'';
    var selfClass=(typeof isSelfMember==='function'&&isSelfMember(member))?' is-self-member':'';
    var displayName=String(member.name||'');
    if(IS_ADMIN&&!member.isNew&&typeof compactMemberName==='function')displayName=compactMemberName(displayName);
    return '<button class="'+(clickable?'member ':'person member-info-card ')+genderClass(member)+selected+selfClass+'" data-member-id="'+member.id+'"'+(clickable?memberLongPressAttributes(member.id):'')+onclick+'>'+selfStar+'<span class="name">'+escapeMemberInfo(displayName)+'</span>'+mdBadges(member)+games+memberInfoDetailHtml(member)+'</button>';
  };

  if(typeof applyBatchAssignLocally==='function'){
    var originalApplyBatchAssignLocally=applyBatchAssignLocally;
    applyBatchAssignLocally=function(ids,targetType,targetIndex){
      originalApplyBatchAssignLocally(ids,targetType,targetIndex);
      if(targetType==='court'){
        var no=Number(targetIndex), group=(STATE.courts[no]||[]);
        if(group.length>0&&!STATE.courtStartedAt[no])STATE.courtStartedAt[no]=new Date().toISOString();
        if(!group.length)STATE.courtStartedAt[no]='';
      }
    };
  }
  window.__JAYUMINTON_ADMIN_MD_CARD_TIMER_V1__=true;
})();
</script>
<!-- __JAYUMINTON_ADMIN_MD_CARD_TIMER_V1__ -->
'''
    if '</body>' not in html: raise SystemExit('body missing')
    html=html.replace('</body>',addon+'\n</body>',1)
    for req in (marker,'new 신규','🎁 찬조','member.publicMemo','!member.isNew','group.length>0&&!STATE.courtStartedAt[no]'):
        if req not in html: raise SystemExit('missing '+req)
    path.write_text(html,encoding='utf-8')

helper=Path(__file__).with_name('admin_md_member_fields_patch.py')
if not helper.exists(): raise SystemExit('member fields helper missing')
subprocess.run([sys.executable,str(helper),str(path)],check=True)
final=path.read_text(encoding='utf-8')
for req in ('__JAYUMINTON_ADMIN_MD_CARD_TIMER_V1__','__JAYUMINTON_ADMIN_MD_MEMBER_FIELDS_V1__','id="mdPublicMemo"','id="mdIsNew"','id="mdIsSponsor"',"server('getPairStatistics',[ADMIN_PIN_VALUE])"):
    if req not in final: raise SystemExit('final admin MD chain missing '+req)
print('ADMIN_MD_CARD_TIMER_AND_MEMBER_FIELDS_OK')
