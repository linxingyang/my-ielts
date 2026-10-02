# 用 kajweb 词表自带的英/美音标预填充 phonetics.json，减少 parser.py 的有道查询量
import json
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
PHON_PATH = CUR_DIR / 'phonetics.json'
SRC_DIR = CUR_DIR / '_cet_source'

phon = json.loads(PHON_PATH.read_text(encoding='utf-8'))
added = 0
for name in ['CET4_2.json', 'CET6_2.json', 'CET6_3.json']:
    for line in (SRC_DIR / name).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        word = item['content']['word']['wordHead'].strip().lower()
        c = item['content']['word']['content']
        uk, us = c.get('ukphone', ''), c.get('usphone', '')
        if word in phon and phon[word]:
            continue
        if uk and us:
            phon[word] = f'UK /{uk}/ US /{us}/'
        elif uk or us:
            phon[word] = f'/{uk or us}/'
        else:
            continue
        added += 1

PHON_PATH.write_text(json.dumps(phon, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
print(f'预填充音标 {added} 条，phonetics.json 现有 {len(phon)} 条')
