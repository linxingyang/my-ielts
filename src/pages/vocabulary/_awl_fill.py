# 补全 AWL 缺失词头：追加到 _cet_source/awl_words.json（释义/例句由 _build_wordlists.py 走有道自动补）
import json
import re
import urllib.request
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
AWL_PATH = CUR_DIR / '_cet_source' / 'awl_words.json'

# 粗词干归一后确认缺失的 18 个词头
MISSING = [
    'compensation', 'concentration', 'distortion', 'expansion', 'identical',
    'infrastructure', 'intervention', 'justification', 'publication', 'release',
    'solely', 'submit', 'technology', 'thesis', 'transport', 'visible',
    'voluntary', 'welfare',
]

req = urllib.request.Request(
    'https://api.github.com/repos/UltraClr/570words/contents/pos.js',
    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.raw'})
pos = json.loads(re.search(r'const POS = (\{.*\})', urllib.request.urlopen(req, timeout=30).read().decode('utf-8'), re.S).group(1))

# UltraClr 570 表按字母序排列，官方子表即每 60 个一组（最后一个 30）
sorted_words = sorted(w.lower() for w in pos)
sublist_of = {w: i // 60 + 1 for i, w in enumerate(sorted_words)}

awl = json.loads(AWL_PATH.read_text(encoding='utf-8'))
have = {i['word'].lower() for i in awl}
added = 0
for w in MISSING:
    if w in have:
        continue
    awl.append({'word': w, 'arabic_translation': '', 'english_definition': '',
                'example_sentence': '', 'synonyms': [],
                'sublist': sublist_of.get(w, 10)})
    added += 1

AWL_PATH.write_text(json.dumps(awl, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'awl_words.json 追加 {added} 个词头，现共 {len(awl)} 条')
for w in MISSING:
    print(f'  {w}  -> AWL-{sublist_of.get(w, 10)}')
