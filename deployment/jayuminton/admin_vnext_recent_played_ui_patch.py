#!/usr/bin/env python3
"""Remove noisy recent/partner statistics from admin member cards."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source-snapshot/current-main')
p=root/'Script.html'; s=p.read_text(encoding='utf-8')
marker="""function adminVnextMemberBadges(member) {"""
if marker not in s: raise SystemExit('member badge helper anchor not found')

def remove_function(text, name):
    needle = 'function ' + name + '('
    while needle in text:
        start = text.find(needle)
        brace = text.find('{', start)
        if brace < 0: raise SystemExit(name + ' function boundary missing')
        depth = 0
        quote = ''
        escape = False
        end = -1
        for i in range(brace, len(text)):
            ch = text[i]
            if quote:
                if escape: escape = False
                elif ch == '\\': escape = True
                elif ch == quote: quote = ''
                continue
            if ch in ("'", '"', '`'): quote = ch
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end < 0: raise SystemExit(name + ' function end missing')
        text = text[:start] + text[end:].lstrip('\n')
    return text

# Remove every previous deployment's helper/call/style before installing one
# canonical compact line. This also repairs the repeated timestamp regression.
s = remove_function(s, 'adminVnextRecentPlayed')
s = remove_function(s, 'openPairStatistics')
s = remove_function(s, 'closePairStatistics')
s = remove_function(s, 'renderPairStatistics')
s = s.replace('adminVnextRecentPlayed(member) + ', '')
s = re.sub(r'<style id="adminVnextRecentPlayedStyle">[\s\S]*?</style>\s*', '', s)

helper='''function adminVnextRecentPlayed(member) {
  return '';
}

function openPairStatistics() {
  const modal = document.getElementById('pairStatisticsModal');
  const list = document.getElementById('pairStatisticsList');
  if (!modal || !list) return;
  modal.classList.remove('hidden');
  list.innerHTML = '<div class="pair-statistics-empty">불러오는 중…</div>';
  server('getPairStatistics', [ADMIN_PIN_VALUE])
    .then(function(rows) {
      window.ADMIN_PAIR_STATISTICS = Array.isArray(rows) ? rows : [];
      renderPairStatistics();
    })
    .catch(function(error) {
      list.innerHTML = '<div class="pair-statistics-empty">통계를 불러오지 못했습니다.</div>';
      alert(error && error.message ? error.message : error);
    });
}

function closePairStatistics(event) {
  if (event && event.target && event.target.id !== 'pairStatisticsModal') return;
  const modal = document.getElementById('pairStatisticsModal');
  if (modal) modal.classList.add('hidden');
}

function renderPairStatistics() {
  const list = document.getElementById('pairStatisticsList');
  if (!list) return;
  const search = document.getElementById('pairStatisticsSearch');
  const query = String(search && search.value || '').trim().toLowerCase();
  const rows = (window.ADMIN_PAIR_STATISTICS || []).filter(function(row) {
    return !query || String(row.name || '').toLowerCase().indexOf(query) >= 0;
  });
  if (!rows.length) {
    list.innerHTML = '<div class="pair-statistics-empty">표시할 통계가 없습니다.</div>';
    return;
  }
  list.innerHTML = rows.map(function(row) {
    const partners = (row.partners || []).map(function(partner) {
      return '<span class="pair-statistics-chip">' + escapeMemberInfo(partner.name) +
        ' <strong>' + Number(partner.count || 0) + '회</strong></span>';
    }).join('');
    return '<div class="pair-statistics-row"><div class="pair-statistics-head">' +
      '<span class="pair-statistics-name">' + escapeMemberInfo(row.name) + '</span>' +
      '<span class="pair-statistics-games">게임 ' + Number(row.games || 0) + '회</span></div>' +
      '<div class="pair-statistics-partners">' +
      (partners || '<span class="pair-statistics-empty">함께 경기한 기록 없음</span>') +
      '</div></div>';
  }).join('');
}

'''
s=s.replace(marker,helper+marker,1)
s=s.replace('adminVnextRecentPlayed(member) + ', '')
while 'adminVnextMemberBadges(member) + adminVnextMemberBadges(member) +' in s:
  s=s.replace('adminVnextMemberBadges(member) + adminVnextMemberBadges(member) +', 'adminVnextMemberBadges(member) +')
style='''\n<style id="adminVnextRecentPlayedStyle">.member-vnext-recent{display:none!important}</style>\n'''
script_end = s.rfind('</script>')
if script_end < 0: raise SystemExit('script end anchor not found')
s = s[:script_end + len('</script>')] + style + s[script_end + len('</script>'):]
if s.count('function adminVnextRecentPlayed(member)') != 1 or s.count('function openPairStatistics()') != 1 or s.count('id="adminVnextRecentPlayedStyle"') != 1:
    raise SystemExit('compact partner UI must be unique')
p.write_text(s,encoding='utf-8')
print('admin vNext card statistics cleanup prepared')
