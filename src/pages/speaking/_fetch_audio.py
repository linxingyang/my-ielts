# 口语模块单词音频准备：
# - 从 phonetics.js 提取全部单词（音素例词 + 对比组词对，去重）
# - 有道 dictvoice 下载美音（type=2，默认）与英音（type=1）两套 mp3
#   → public/speaking/audio/us/<word>.mp3、public/speaking/audio/uk/<word>.mp3
# - 生成 src/pages/speaking/audioIndex.json：word → { us, uk } 相对路径
#   前端播放时查索引；索引缺失时由前端在线兜底有道 dictvoice
# 幂等可重复运行（已存在的文件跳过）。
import json
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
AUDIO_DIR = CUR_DIR.parent.parent.parent / 'public' / 'speaking' / 'audio'
INDEX_PATH = CUR_DIR / 'audioIndex.json'
MISSING_PATH = CUR_DIR / '_missing_audio.json'

# 有道 dictvoice 口音参数
ACCENTS = {'us': 2, 'uk': 1}


def extract_words():
    # 借助 node 动态 import 解析 phonetics.js（ESM 导出），提取全部单词
    js = (
        "import('../data/phonetics.js').then(m => {\n"
        '  const words = new Set();\n'
        '  for (const cat of m.PHONEME_CATEGORIES)\n'
        '    for (const p of cat.phonemes)\n'
        '      for (const w of p.examples) words.add(w);\n'
        '  for (const g of m.MINIMAL_PAIR_GROUPS)\n'
        '    for (const p of g.pairs) { words.add(p.a); words.add(p.b); }\n'
        '  console.log(JSON.stringify([...words]));\n'
        '})'
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

    to_download = []  # (word, accent, dest, key)
    for word in words:
        key = word.lower()
        entry = index.setdefault(key, {})
        for accent in ACCENTS:
            if entry.get(accent):
                continue  # 已有本地音频
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

    # 清理索引中已无音频文件的条目
    for key in list(index):
        for accent in list(index[key]):
            path = index[key][accent]
            if not (CUR_DIR.parent.parent.parent / 'public' / path).exists():
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
