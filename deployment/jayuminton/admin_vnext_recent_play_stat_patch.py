#!/usr/bin/env python3
"""Admin-only pair statistics API; never adds statistics to member cards."""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('source-snapshot/current-main')
path = root / 'Code.js'
source = path.read_text(encoding='utf-8')

def remove_function(text, name):
    needle = 'function ' + name + '('
    while needle in text:
        start = text.find(needle); brace = text.find('{', start)
        if brace < 0: raise SystemExit(name + ' boundary missing')
        depth, quote, escape, end = 0, '', False, -1
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
                if depth == 0: end = i + 1; break
        if end < 0: raise SystemExit(name + ' end missing')
        text = text[:start] + text[end:].lstrip('\n')
    return text

source = remove_function(source, 'readLastPlayedAtMap_')
source = source.replace('  const lastPlayedAtMap = readLastPlayedAtMap_();\n', '')
source = source.replace("    member.lastPlayedAt = lastPlayedAtMap[member.id] || '';\n", '')
source = remove_function(source, 'getPairStatistics')

api = r'''function getPairStatistics(pin) {
  auth_(pin);
  const members = readMembers_();
  const names = {};
  members.forEach(function(member) { names[String(member.id)] = String(member.name || ''); });
  const pairCounts = readPairCounts_();
  const partnersByMember = {};
  Object.keys(pairCounts).forEach(function(key) {
    const ids = String(key).split('::');
    if (ids.length !== 2 || !names[ids[0]] || !names[ids[1]]) return;
    partnersByMember[ids[0]] = partnersByMember[ids[0]] || [];
    partnersByMember[ids[1]] = partnersByMember[ids[1]] || [];
    partnersByMember[ids[0]].push({name: names[ids[1]], count: Number(pairCounts[key]) || 0});
    partnersByMember[ids[1]].push({name: names[ids[0]], count: Number(pairCounts[key]) || 0});
  });
  return members.map(function(member) {
    const partners = (partnersByMember[String(member.id)] || []).sort(function(a, b) {
      return b.count - a.count || a.name.localeCompare(b.name);
    });
    return {id: String(member.id), name: String(member.name || ''), games: Number(member.games) || 0, partners: partners};
  }).sort(function(a, b) { return b.games - a.games || a.name.localeCompare(b.name); });
}

'''
marker = 'function getPublicState() {'
if marker not in source: raise SystemExit('getPublicState anchor not found')
source = source.replace(marker, api + marker, 1)
if source.count('function getPairStatistics(pin)') != 1: raise SystemExit('pair statistics API must be unique')
path.write_text(source, encoding='utf-8')
print('admin vNext pair statistics API prepared')
