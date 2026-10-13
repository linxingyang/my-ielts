# 口语模块单词音频准备：
# - 从 src/data/ 各数据文件提取全部单词（音素例词 + 对比组词对 + 各模块例词 + 字母表，去重）
# - 有道 dictvoice 下载美音（type=2，默认）与英音（type=1）两套 mp3
#   → public/speaking/audio/us/<word>.mp3、public/speaking/audio/uk/<word>.mp3
# - 跨池复用：词汇模块共享池（public/vocabulary/audio/_shared_us|uk，同为有道 TTS 同源音频）
#   已有的单词直接在索引中引用 vocabulary/audio/... 路径，不重复落盘；
#   本地口语池中与之重复的文件会被删除
# - 生成 src/pages/speaking/audioIndex.json：word → { us, uk } 相对路径（可能指向任一池）
#   前端播放时查索引；索引缺失时由前端在线兜底有道 dictvoice
# 幂等可重复运行（已存在的文件跳过）。
# 注意：跨池引用依赖词汇共享池的文件路径保持稳定。
import json
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
PUBLIC_DIR = CUR_DIR.parent.parent.parent / 'public'
AUDIO_DIR = PUBLIC_DIR / 'speaking' / 'audio'
INDEX_PATH = CUR_DIR / 'audioIndex.json'
MISSING_PATH = CUR_DIR / '_missing_audio.json'
# 词汇模块共享池索引（只读引用，不修改）
VOCAB_INDEX_PATH = CUR_DIR.parent / 'vocabulary' / 'audioIndex.json'

# 有道 dictvoice 口音参数
ACCENTS = {'us': 2, 'uk': 1}


def extract_words():
    # 借助 node 动态 import 解析 src/data/ 下各数据文件（ESM 导出），提取全部单词。
    # 各文件导出的数据形状不同，按导出名逐一收集；用 ?? [] 兼容未导出的文件。
    data_dir = CUR_DIR.parent.parent / 'data'
    data_files = [
        'phonetics.js', 'spelling.js', 'clusters.js', 'stress.js',
        'endings.js', 'homophones.js', 'numbers.js',
    ]
    imports = ',\n'.join(f"  import('file:///{(data_dir / f).as_posix()}')" for f in data_files)
    js = (
        'const mods = await Promise.all([\n'
        f'{imports}\n'
        '])\n'
        'const words = new Set()\n'
        'const add = (w) => { if (w) words.add(String(w).trim()) }\n'
        'for (const m of mods) {\n'
        '  for (const cat of m.PHONEME_CATEGORIES ?? [])\n'
        '    for (const p of cat.phonemes)\n'
        '      for (const w of p.examples) add(w)\n'
        '  for (const g of m.MINIMAL_PAIR_GROUPS ?? [])\n'
        '    for (const p of g.pairs) { add(p.a); add(p.b) }\n'
        '  for (const group of m.SPELLING_GROUPS ?? [])\n'
        '    for (const r of group.rules)\n'
        '      for (const e of r.examples) add(e.word)\n'
        '  for (const pos of m.CLUSTER_POSITIONS ?? [])\n'
        '    for (const c of pos.clusters)\n'
        '      for (const e of c.examples) add(e.word)\n'
        '  for (const group of m.STRESS_GROUPS ?? [])\n'
        '    for (const w of group.words) add(w.word)\n'
        '  for (const group of m.ENDING_GROUPS ?? [])\n'
        '    for (const s of group.sounds)\n'
        '      for (const w of s.words) add(w)\n'
        '  for (const g of [...(m.HOMOPHONE_GROUPS ?? []), ...(m.NUMBER_PAIR_GROUPS ?? [])])\n'
        '    for (const p of g.pairs) { add(p.a); add(p.b) }\n'
        '  for (const w of m.ALPHABET ?? []) add(w)\n'
        '}\n'
        'console.log(JSON.stringify([...words]))\n'
    )
    r = subprocess.run(['node', '--input-type=module', '-e', js],
                       cwd=CUR_DIR, capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        raise RuntimeError(f'node 解析 phonetics.js 失败: {r.stderr}')
    return sorted(json.loads(r.stdout.strip().splitlines()[-1]))


def download(word, dest, accent):
    url = f'https://dict.youdao.com/dictvoice?type={ACCENTS[accent]}&audio={urllib.parse.quote(word)}'
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
    words = extract_words()
    print(f'共 {len(words)} 个单词')
    index = {}
    try:
        index = json.loads(INDEX_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        pass
    try:
        vocab = json.loads(VOCAB_INDEX_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        vocab = {}

    # 0. 去重：本地口语池与词汇共享池重复的文件改为跨池引用，并删除本地重复文件
    deduped = 0
    for key, entry in index.items():
        ventry = vocab.get(key) or {}
        for accent in list(entry):
            path = entry[accent]
            vpath = ventry.get(accent)
            if (path.startswith('speaking/audio/')
                    and vpath and (PUBLIC_DIR / vpath).exists()):
                entry[accent] = vpath
                f = PUBLIC_DIR / path
                if f.exists():
                    f.unlink()
                deduped += 1
    if deduped:
        print(f'去重: {deduped} 个音频改为引用词汇共享池（本地重复文件已删除）')

    to_download = []  # (word, accent, dest, key)
    for word in words:
        key = word.lower()
        entry = index.setdefault(key, {})
        ventry = vocab.get(key) or {}
        for accent in ACCENTS:
            cur = entry.get(accent)
            if cur and (PUBLIC_DIR / cur).exists():
                continue  # 本地或跨池引用已有音频
            vpath = ventry.get(accent)
            if vpath and (PUBLIC_DIR / vpath).exists():
                # 词汇共享池已有同源 TTS 音频，跨池引用不落盘
                entry[accent] = vpath
                continue
            d = AUDIO_DIR / accent
            d.mkdir(parents=True, exist_ok=True)
            dest = d / f'{word}.mp3'
            if dest.exists():
                entry[accent] = f'speaking/audio/{accent}/{word}.mp3'
            else:
                to_download.append((word, accent, dest, key))
    print(f'需下载 {len(to_download)} 个音频')

    fail_words = set()
    if to_download:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(download, w, dest, a): (w, a) for w, a, dest, _ in to_download}
            for fut in futures:
                w, a = futures[fut]
                ok = False
                try:
                    ok = fut.result()
                except Exception:
                    ok = False
                if ok:
                    index[w.lower()][a] = f'speaking/audio/{a}/{w}.mp3'
                else:
                    fail_words.add(w)
        print('下载完成')

    # 清理索引中已无音频文件的条目（跨池引用的路径同样校验存在性）
    for key in list(index):
        for accent in list(index[key]):
            path = index[key][accent]
            if not (PUBLIC_DIR / path).exists():
                del index[key][accent]
        if not index[key]:
            del index[key]

    INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(',', ':')),
        encoding='utf-8')
    MISSING_PATH.write_text(
        json.dumps(sorted(fail_words), ensure_ascii=False, indent=1), encoding='utf-8')

    print(f'完成: 索引 {len(index)} 条 → audioIndex.json')
    if fail_words:
        print(f'无音频 {len(fail_words)} 个词（前端会在线兜底），清单: {MISSING_PATH.name}')


if __name__ == '__main__':
    main()
