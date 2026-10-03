# 从 kajweb/dict（GitHub）下载四六级词表 zip 并解包为 JSON
# 走 api.github.com 的 raw 通道（raw.githubusercontent.com 在部分网络不可达）
# 网络不稳，用 curl.exe 断点续传直到文件完整
import io
import json
import subprocess
import zipfile
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
OUT_DIR = CUR_DIR / '_cet_source'
OUT_DIR.mkdir(exist_ok=True)

# (本地保存名, 仓库内路径, zip 完整字节数)
FILES = [
    ('CET4_2.json', 'book/1521164635506_CET4_2.zip', 2542778),   # 四级英语词汇（正序版） 3739 词
    ('CET6_2.json', 'book/1524052554766_CET6_2.zip', 1111633),   # 六级英语词汇（有道版） 2078 词
    ('CET6_3.json', 'book/1521164633851_CET6_3.zip', 1452645),   # 新东方六级词汇 2345 词
]

API = 'https://api.github.com/repos/kajweb/dict/contents/{}'

# (本地保存名, API 内容地址, 完整字节数)——非 zip 的原始文件，经 api.github.com raw 通道下载
RAW_FILES = [
    # Oxford 5000（含 CEFR 等级 a1~c1 与词性），同词多词性多行
    ('oxford5k_raw.csv', 'https://api.github.com/repos/nalgeon/words/contents/data/oxford-5k.csv?ref=main', 1114693),
    # NGSL 1.01 官方 SFI 表：Wordlist 列区分 1-NGSL(2801) / 2-Sup(47) / 3-NAWL(959)，带频率 Rank
    ('NGSL_101_SFI.xlsx', 'https://api.github.com/repos/antdurrant/word.lists/contents/data-raw/list_ngsl/NGSL%2B1.01%2Bwith%2BSFI.xlsx?ref=master', 4046430),
]


def load_ndjson(path):
    # kajweb/dict 的数据为 NDJSON：每行一个 JSON 对象
    words = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            words.append(json.loads(line))
    return words


def download_zip(repo_path, expect_size, zip_path):
    # curl 断点续传：-C - 从已下载位置继续，循环直到大小符合
    url = API.format(repo_path)
    for attempt in range(30):
        have = zip_path.stat().st_size if zip_path.exists() else 0
        if have >= expect_size:
            break
        subprocess.run([
            'curl.exe', '-s', '--max-time', '300', '--speed-time', '30', '--speed-limit', '1000',
            '-C', '-', '-H', 'User-Agent: Mozilla/5.0',
            '-H', 'Accept: application/vnd.github.raw',
            '-o', str(zip_path), url,
        ], check=False)
    else:
        raise RuntimeError(f'下载未完成: {repo_path}')
    if zip_path.stat().st_size != expect_size:
        raise RuntimeError(f'大小不符: {zip_path.stat().st_size} != {expect_size}')


def download_raw(url, expect_size, out_path):
    # 同样走 curl 断点续传
    for attempt in range(30):
        have = out_path.stat().st_size if out_path.exists() else 0
        if have >= expect_size:
            break
        subprocess.run([
            'curl.exe', '-s', '--max-time', '300', '--speed-time', '30', '--speed-limit', '1000',
            '-C', '-', '-H', 'User-Agent: Mozilla/5.0',
            '-H', 'Accept: application/vnd.github.raw',
            '-o', str(out_path), url,
        ], check=False)
    else:
        raise RuntimeError(f'下载未完成: {url}')
    if out_path.stat().st_size != expect_size:
        raise RuntimeError(f'大小不符: {out_path.stat().st_size} != {expect_size}')


for name, repo_path, size in FILES:
    out_file = OUT_DIR / name
    if out_file.exists():
        print(f'[skip] {name} 已存在')
        continue
    print(f'[down] {repo_path} ...')
    zip_path = OUT_DIR / (name + '.zip')
    download_zip(repo_path, size, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        jsons = [n for n in zf.namelist() if n.endswith('.json')]
        assert len(jsons) == 1, f'{repo_path} 内 JSON 数量异常: {jsons}'
        out_file.write_bytes(zf.read(jsons[0]))
    zip_path.unlink()
    words = load_ndjson(out_file)
    print(f'[ok]   {name}: {len(words)} 词')

for name, url, size in RAW_FILES:
    out_file = OUT_DIR / name
    if out_file.exists():
        print(f'[skip] {name} 已存在')
        continue
    print(f'[down] {url} ...')
    download_raw(url, size, out_file)
    print(f'[ok]   {name}: {out_file.stat().st_size} bytes')

# 打印第一条数据看结构
sample = load_ndjson(OUT_DIR / 'CET4_2.json')[0]
print(json.dumps(sample, ensure_ascii=False, indent=2)[:2000])
