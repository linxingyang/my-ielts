# 校验音频共享池与索引一致性
import json
import re
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
AUDIO_DIR = CUR_DIR.parent.parent.parent / 'public' / 'vocabulary' / 'audio'

IELTS_LABELS = [f'{i:02d}_{n}' for i, n in enumerate([
    '自然地理', '植物研究', '动物保护', '太空探索', '学校教育', '科技发明',
    '文化历史', '语言演化', '娱乐运动', '物品材料', '时尚潮流', '饮食健康',
    '建筑场所', '交通旅行', '国家政府', '社会经济', '法律法规', '沙场争锋',
    '社会角色', '行为动作', '身心健康', '时间日期'], start=1)]


def parse_labels():
    labels = []
    cur = None
    for line in (CUR_DIR / 'vocabulary.txt').read_text(encoding='utf-8').splitlines():
        t = line.strip()
        if t in ('===', '+++', '---'):
            continue
        if '|' in t and t.rsplit('|', 1)[1] in ('cet4', 'cet6', 'awl'):
            name, source = t.rsplit('|', 1)
            cur = {'name': name.strip(), 'source': source, 'words': []}
            labels.append(cur)
        elif cur is not None and t:
            cur['words'].append(t.split('|')[0].strip())
    counters = {}
    out = []
    for ch in labels:
        counters[ch['source']] = counters.get(ch['source'], 0) + 1
        out.append((f"{counters[ch['source']]:02d}_{ch['name']}", ch['words']))
    return out


idx = json.loads((CUR_DIR / 'audioIndex.json').read_text(encoding='utf-8'))
print('索引条数:', len(idx))

# 磁盘上的目录
dirs = sorted(d.name for d in AUDIO_DIR.iterdir() if d.is_dir())
ielts_dirs = [d for d in dirs if d in IELTS_LABELS]
other_dirs = [d for d in dirs if d not in IELTS_LABELS and d != '_shared']
print('真经目录:', len(ielts_dirs), ' 其他目录(应为空):', other_dirs)
print('_shared 文件数:', len(list((AUDIO_DIR / '_shared').glob('*.mp3'))))

# 索引指向的文件是否存在
missing_files = []
for k, url in idx.items():
    p = AUDIO_DIR.parent.parent / url  # url 形如 vocabulary/audio/...
    if not p.exists():
        missing_files.append((k, url))
print('索引指向但不存在的文件:', len(missing_files), missing_files[:10])

# 全部词条覆盖检查
chapters = parse_labels()
print('章节数:', len(chapters))
missing_words = {}
for label, words in chapters:
    for w in words:
        first = w.split('/')[0].strip()
        if first.lower() not in idx:
            missing_words.setdefault(first, []).append(label)
print('索引中缺失的词条数:', sum(len(v) for v in missing_words.values()), '唯一词:', len(missing_words))
print(list(missing_words.items())[:10])

# abandon 具体情况
print('abandon 在索引:', idx.get('abandon'))
print('abandon 在真经目录:', any((AUDIO_DIR / l / 'abandon.mp3').exists() for l in IELTS_LABELS))
