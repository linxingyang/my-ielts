# 最终校验
import json
import re
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
d = json.loads(re.search(r'const vocabulary = (\{.*\})',
                 (CUR_DIR / 'vocabulary.js').read_text(encoding='utf-8'), re.S).group(1))
from collections import Counter
src = Counter(v['source'] for v in d.values())
total = sum(v['wordCount'] for v in d.values())
nophon = sum(1 for v in d.values() for g in v['words'] for w in g if not w['phonetic'])
print('章节:', dict(src), '总词条:', total, '无音标:', nophon)
awl_words = sum(v['wordCount'] for v in d.values() if v['source'] == 'awl')
print('AWL 词条:', awl_words)
idx = json.loads((CUR_DIR / 'audioIndex.json').read_text(encoding='utf-8'))
missing = [k for k, u in idx.items() if not (CUR_DIR.parent.parent.parent / 'public' / u).exists()]
print('索引条数:', len(idx), '指向缺失:', len(missing))
# 抽查新补的词
for k, v in d.items():
    if k == '10_AWL-10':
        for g in v['words']:
            for w in g:
                if w['word'][0] in ('welfare', 'technology', 'visible'):
                    print(f"  {w['word'][0]}: {w['phonetic']} | {w['meaning'][:20]} | 例句 {'有' if w['example'] != '-' else '无'} 翻译 {'有' if w['translation'] else '无'}")
