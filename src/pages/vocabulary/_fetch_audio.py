# 单词音频准备（共享池模式）：
# - 真经 22 章的真人发音保持原位：public/vocabulary/audio/<01~22_真经章节>/<词>.mp3
# - 四级/六级/AWL 的单词音频唯一副本放 _shared/（四级与六级重叠词只存一份）
# - 生成 src/pages/vocabulary/audioIndex.json：单词(小写) → 音频 URL 路径
#   前端播放时查索引；索引缺失时由前端在线兜底有道 dictvoice
# 幂等可重复运行；旧的四/六/AWL 章节目录会被自动清理。
import json
import re
import shutil
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
AUDIO_DIR = CUR_DIR.parent.parent.parent / 'public' / 'vocabulary' / 'audio'
SHARED_DIR = AUDIO_DIR / '_shared'
INDEX_PATH = CUR_DIR / 'audioIndex.json'
MISSING_PATH = CUR_DIR / '_missing_audio.json'

# 真经章节目录名（真人发音，保持原位）
IELTS_LABELS = [f'{i:02d}_{n}' for i, n in enumerate([
    '自然地理', '植物研究', '动物保护', '太空探索', '学校教育', '科技发明',
    '文化历史', '语言演化', '娱乐运动', '物品材料', '时尚潮流', '饮食健康',
    '建筑场所', '交通旅行', '国家政府', '社会经济', '法律法规', '沙场争锋',
    '社会角色', '行为动作', '身心健康', '时间日期'], start=1)]


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def parse_labels():
    # 从 vocabulary.txt 解析生成章节：标题行 `名称|source` → (序号, 目录名, 词条列表)
    labels = []
    cur = None
    for line in (CUR_DIR / 'vocabulary.txt').read_text(encoding='utf-8').splitlines():
        t = line.strip()
        if t in ('===', '+++', '---'):
            continue
        if '|' in t and t.rsplit('|', 1)[1] in ('cet4', 'cet6', 'awl', 'oxford5000', 'ngsl', 'nawl'):
            name, source = t.rsplit('|', 1)
            cur = {'name': name.strip(), 'source': source, 'words': []}
            labels.append(cur)
        elif cur is not None and t:
            cur['words'].append(t.split('|')[0].strip())
    # 编号：每词库从 01 开始（与 parser.py 一致）
    counters = {}
    out = []
    for ch in labels:
        counters[ch['source']] = counters.get(ch['source'], 0) + 1
        out.append((f"{counters[ch['source']]:02d}_{ch['name']}", ch['words']))
    return out


def download(word, dest):
    url = f'https://dict.youdao.com/dictvoice?type=1&audio={urllib.parse.quote(word)}'
    tmp = dest.with_suffix('.tmp')
    subprocess.run([
        'curl.exe', '-s', '--max-time', '30',
        '-H', 'User-Agent: Mozilla/5.0',
        '-o', str(tmp), url,
    ], check=False)
    if tmp.exists() and tmp.stat().st_size > 1000:  # 小于 1KB 视为无效响应
        tmp.replace(dest)
        return True
    if tmp.exists():
        tmp.unlink()
    return False


def main():
    # 1. 真经发音索引：文件名小写 → URL 路径
    audio_index = {}
    for label in IELTS_LABELS:
        d = AUDIO_DIR / label
        if d.is_dir():
            for f in d.iterdir():
                if f.suffix.lower() == '.mp3':
                    audio_index.setdefault(f.stem.lower(), f'vocabulary/audio/{label}/{f.name}')
    print(f'真经发音: {len(audio_index)} 个文件')

    # 2. 生成词库（四级/六级/AWL/牛津5000/NGSL/NAWL）：唯一副本迁入/下载到 _shared/
    SHARED_DIR.mkdir(exist_ok=True)
    chapters = parse_labels()
    total = 0
    to_download = []  # (word, dest, key)
    fail_words = {}
    for label, words in chapters:
        old_dir = AUDIO_DIR / label
        for word in words:
            total += 1
            # 斜杠变体词（如 analyse/analyze）：音频按第一个变体命名（与页面播放一致）
            first = word.split('/')[0].strip()
            key = first.lower()
            if key in audio_index:
                continue  # 真经发音或已入共享池
            shared_file = SHARED_DIR / f'{first}.mp3'
            old_file = old_dir / f'{first}.mp3'
            if shared_file.exists():
                audio_index[key] = f'vocabulary/audio/_shared/{first}.mp3'
            elif old_file.exists():
                shutil.move(str(old_file), str(shared_file))
                audio_index[key] = f'vocabulary/audio/_shared/{first}.mp3'
            else:
                to_download.append((first, shared_file, key))
    print(f'新词库词条 {total}, 需下载 {len(to_download)}')

    downloaded = 0
    if to_download:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(download, w, dest): (w, dest, key) for w, dest, key in to_download}
            for fut in futures:
                w, dest, key = futures[fut]
                ok = False
                try:
                    ok = fut.result()
                except Exception:
                    ok = False
                if not ok and w[:1].isupper():
                    # 大写词重试小写形式（dictvoice 对部分大写词返回空响应）
                    ok = bool(download(w.lower(), dest))
                if ok:
                    downloaded += 1
                    audio_index[key] = f'vocabulary/audio/_shared/{dest.name}'
                else:
                    fail_words.setdefault(w, []).append('shared')
            print(f'  下载完成 {downloaded}/{len(to_download)}')

    # 3. 清理旧的生成章节目录（音频已迁入共享池或属重复副本）
    removed = 0
    for label, _ in chapters:
        d = AUDIO_DIR / label
        if d.is_dir():
            shutil.rmtree(d)
            removed += 1
    print(f'清理旧章节目录 {removed} 个')

    # 4. 写音频索引（供前端 import）
    INDEX_PATH.write_text(
        json.dumps(audio_index, ensure_ascii=False, sort_keys=True, separators=(',', ':')),
        encoding='utf-8')
    MISSING_PATH.write_text(
        json.dumps(fail_words, ensure_ascii=False, indent=1), encoding='utf-8')

    print(f'\n完成: 词条 {total}, 索引 {len(audio_index)} 条 → audioIndex.json')
    if fail_words:
        print(f'无音频 {len(fail_words)} 个词（前端会在线兜底），清单: {MISSING_PATH.name}')


if __name__ == '__main__':
    main()
