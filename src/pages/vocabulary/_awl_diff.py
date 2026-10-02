# AWL 真缺失词头：570 官方词表 vs awl_words.json（554），粗词干归一后取差集
import json
import re
import urllib.request
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent

awl = {i['word'].lower() for i in json.loads((CUR_DIR / '_cet_source' / 'awl_words.json').read_text(encoding='utf-8'))}
req = urllib.request.Request(
    'https://api.github.com/repos/UltraClr/570words/contents/pos.js',
    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.raw'})
pos = json.loads(re.search(r'const POS = (\{.*\})', urllib.request.urlopen(req, timeout=30).read().decode('utf-8'), re.S).group(1))
p570 = {w.lower() for w in pos}


def stem(w):
    # 粗词干归一：去复数/时态/派生后缀，便于跨拼写变体匹配
    w = w.lower()
    for suf in ('isations', 'ization', 'isations', 'ising', 'ised', 'ises', 'ise',
                'ization', 'yzing', 'yzed', 'yzes', 'yze',
                'ations', 'ation', 'ating', 'ated', 'ates', 'ate',
                'ingly', 'ings', 'ing', 'ed', 'es', 's', 'ly'):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[:len(w) - len(suf)]
    return w


awl_stems = {stem(w) for w in awl}
missing = sorted(w for w in p570 if stem(w) not in awl_stems)
print(f'AWL 数据 {len(awl)} 词，570 词表 {len(p570)} 词，粗词干归一后真缺失 {len(missing)} 个:')
for w in missing:
    print(' ', w, pos.get(w, pos.get(w.capitalize(), '')))
