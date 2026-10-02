# 问题 2 分析：无音标词条清单 + AWL 缺失词头
import json
import re
import urllib.request
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent

t = (CUR_DIR / 'vocabulary.js').read_text(encoding='utf-8')
d = json.loads(re.search(r'const vocabulary = (\{.*\})', t, re.S).group(1))

print('--- 无音标词条 ---')
n = 0
for k, v in d.items():
    for g in v['words']:
        for w in g:
            if not w['phonetic']:
                n += 1
                print(f"{k}  {'/'.join(w['word'])}  {w['pos']} {w['meaning'][:40]}")
print('合计', n)

print()
print('--- AWL 缺失词头分析 ---')
awl = {i['word'].lower() for i in json.loads((CUR_DIR / '_cet_source' / 'awl_words.json').read_text(encoding='utf-8'))}
req = urllib.request.Request(
    'https://api.github.com/repos/UltraClr/570words/contents/pos.js',
    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.raw'})
pos = json.loads(re.search(r'const POS = (\{.*\})', urllib.request.urlopen(req, timeout=30).read().decode('utf-8'), re.S).group(1))
p570 = {w.lower() for w in pos}

# 常见英美拼写变体归一，避免误报
def variants(w):
    vs = {w}
    vs |= {w.replace('ise', 'ize'), w.replace('ize', 'ise')}
    vs |= {w.replace('our', 'or'), w.replace('or', 'our')}
    vs |= {w.replace('yse', 'yze'), w.replace('yze', 'yse')}
    vs |= {w.replace('isation', 'ization'), w.replace('ization', 'isation')}
    vs |= {w.replace('logue', 'log'), w.replace('log', 'logue')}
    return vs

awl_n = set()
for w in awl:
    awl_n |= variants(w)

missing = sorted(w for w in p570 if w not in awl_n)
print(f'570 词表中有、AWL 数据中没有（含拼写变体归一后）: {len(missing)} 个')
print(missing)
