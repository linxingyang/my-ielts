# 排查：索引指向的真经文件是否有缺失、真经目录现状
import json
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
AUDIO_DIR = CUR_DIR.parent.parent.parent / 'public' / 'vocabulary' / 'audio'

idx = json.loads((CUR_DIR / 'audioIndex.json').read_text(encoding='utf-8'))

ielts_missing = [(k, u) for k, u in idx.items()
                 if '_shared' not in u and not (AUDIO_DIR.parent.parent / u).exists()]
shared_missing = [(k, u) for k, u in idx.items()
                  if '_shared' in u and not (AUDIO_DIR.parent.parent / u).exists()]
print('真经指向缺失:', len(ielts_missing))
for k, u in ielts_missing[:20]:
    print('  ', k, '->', u)
print('共享池指向缺失:', len(shared_missing), [k for k, _ in shared_missing[:10]])

for d in sorted(AUDIO_DIR.iterdir()):
    if d.is_dir():
        n = len(list(d.glob('*.mp3')))
        print(d.name, n)
