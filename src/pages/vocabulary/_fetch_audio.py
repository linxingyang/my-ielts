# 单词音频准备（共享池模式，美/英双口音 + 原书音频）：
# - 真经 22 章的真人发音保持原位：public/vocabulary/audio/<01~22_真经章节>/<词>.mp3，索引记在 book 键
# - 所有词库单词（含真经词）的英/美 TTS 按口音分池：_shared_us/（有道 TTS 美音 type=2，默认）、_shared_uk/（英音 type=1）
# - 历史兼容：旧 _shared/ 里的文件当初以 type=1（英音）下载，首次运行自动整体迁入 _shared_uk/
# - 生成 src/pages/vocabulary/audioIndex.json：单词(小写) → {us: 路径, uk: 路径, book: 原书音频路径(如有)}
#   前端播放时按口音查索引；索引缺失时由前端在线兜底有道 dictvoice
# 幂等可重复运行；旧的生成章节目录会被自动清理。
import json
import re
import shutil
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
AUDIO_DIR = CUR_DIR.parent.parent.parent / 'public' / 'vocabulary' / 'audio'
SHARED_US_DIR = AUDIO_DIR / '_shared_us'  # 美音（默认）
SHARED_UK_DIR = AUDIO_DIR / '_shared_uk'  # 英音
LEGACY_SHARED_DIR = AUDIO_DIR / '_shared'  # 旧共享池（内容实为英音 type=1）
INDEX_PATH = CUR_DIR / 'audioIndex.json'
MISSING_PATH = CUR_DIR / '_missing_audio.json'

# 有道 dictvoice 口音参数：type=1 英音，type=2 美音
ACCENT_TYPE = {'us': 2, 'uk': 1}
ACCENTS = ('us', 'uk')

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
        if '|' in t and t.rsplit('|', 1)[1] in ('cet4', 'cet6', 'awl', 'oxford5000', 'ngsl', 'nawl', 'opal'):
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


def download(word, dest, accent='us'):
    t = ACCENT_TYPE[accent]
    url = f'https://dict.youdao.com/dictvoice?type={t}&audio={urllib.parse.quote(word)}'
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


def migrate_legacy_shared():
    # 旧 _shared/ 文件当初以 type=1（英音）下载，一次性迁入 _shared_uk/；迁移后目录删除视为完成
    if not LEGACY_SHARED_DIR.is_dir():
        return 0
    SHARED_UK_DIR.mkdir(exist_ok=True)
    moved = 0
    for f in LEGACY_SHARED_DIR.iterdir():
        if f.suffix.lower() != '.mp3':
            continue
        dest = SHARED_UK_DIR / f.name
        if not dest.exists():
            shutil.move(str(f), str(dest))
            moved += 1
    shutil.rmtree(LEGACY_SHARED_DIR)
    return moved


def main():
    # 0. 旧共享池英音迁移
    migrated = migrate_legacy_shared()
    if migrated:
        print(f'旧 _shared 英音迁移到 _shared_uk: {migrated} 个文件')

    # 1. 真经发音索引：文件名小写 → {book: 路径}（原书真人发音，左侧大喇叭专用）
    audio_index = {}
    for label in IELTS_LABELS:
        d = AUDIO_DIR / label
        if d.is_dir():
            for f in d.iterdir():
                if f.suffix.lower() == '.mp3':
                    audio_index[f.stem.lower()] = {'book': f'vocabulary/audio/{label}/{f.name}'}
    print(f'真经发音: {len(audio_index)} 个文件')

    # 2. 生成词库（四级/六级/AWL/牛津5000/NGSL/NAWL/OPAL）：美/英两份 TTS，分池存放
    SHARED_US_DIR.mkdir(exist_ok=True)
    SHARED_UK_DIR.mkdir(exist_ok=True)
    chapters = parse_labels()
    total = 0
    to_download = []  # (word, dest, key, accent)
    fail_words = {}
    for label, words in chapters:
        old_dir = AUDIO_DIR / label
        for word in words:
            total += 1
            # 斜杠变体词（如 analyse/analyze）：音频按第一个变体命名（与页面播放一致）
            first = word.split('/')[0].strip()
            key = first.lower()
            # 真经词不再跳过：book 键保留原书音频，英/美 TTS 照常补齐
            if old_dir.is_dir() and (old_dir / f'{first}.mp3').exists():
                # 旧生成章节目录残留文件（同为 TTS）：视为英音迁入 _shared_uk
                dest = SHARED_UK_DIR / f'{first}.mp3'
                if not dest.exists():
                    shutil.move(str(old_dir / f'{first}.mp3'), str(dest))
            for accent in ACCENTS:
                if accent in audio_index.get(key, {}):
                    continue
                pool = SHARED_US_DIR if accent == 'us' else SHARED_UK_DIR
                f = pool / f'{first}.mp3'
                if f.exists():
                    audio_index.setdefault(key, {})[accent] = f'vocabulary/audio/{pool.name}/{f.name}'
                else:
                    to_download.append((first, f, key, accent))
    print(f'新词库词条 {total}, 需下载 {len(to_download)}')

    downloaded = 0
    if to_download:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(download, w, dest, accent): (w, dest, key, accent)
                       for w, dest, key, accent in to_download}
            for fut in futures:
                w, dest, key, accent = futures[fut]
                ok = False
                try:
                    ok = fut.result()
                except Exception:
                    ok = False
                if not ok and w[:1].isupper():
                    # 大写词重试小写形式（dictvoice 对部分大写词返回空响应）
                    ok = bool(download(w.lower(), dest, accent))
                if ok:
                    downloaded += 1
                    audio_index.setdefault(key, {})[accent] = f'vocabulary/audio/{dest.parent.name}/{dest.name}'
                else:
                    fail_words.setdefault(w, []).append(accent)
            print(f'  下载完成 {downloaded}/{len(to_download)}')

    # 3. 清理旧的生成章节目录（音频已迁入共享池或属重复副本）
    removed = 0
    for label, _ in chapters:
        d = AUDIO_DIR / label
        if d.is_dir():
            shutil.rmtree(d)
            removed += 1
    if removed:
        print(f'清理旧章节目录 {removed} 个')

    # 4. 写音频索引（供前端 import）：单词 → {us, uk, book?}
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
