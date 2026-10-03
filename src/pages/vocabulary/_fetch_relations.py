"""构建单词关联数据（同义/反义/派生），供 parser.py 合并进 vocabulary.js。

数据源（全部构建期完成，站点为纯静态部署，运行时零外部请求）：
1. 同义词：Moby Thesaurus II（公有领域，CSV 格式：词,同义词1,同义词2,...）
   下载到 _moby/mthesaur.txt，与词库词汇求交集，按"共同邻居数"强度截断
   聚类输出到 relations_auto.json
2. 反义词：Datamuse API（免费无需 key，rel_ant 参数），增量缓存 _antonyms.json
3. 派生词：有道词典 rel_word 字段（happily/happiness 等），增量缓存 _derivations.json

缓存约定（与 phonetics.json 一致）：值为 []/'' 表示查询过但无结果，不再重复请求；
网络失败的词不写入缓存，下次运行自动重试。幂等可重跑。
"""
import json
import re
import time
from collections import defaultdict
from pathlib import Path
from urllib import request
from urllib.parse import quote

CUR_DIR = Path(__file__).absolute().parent
MOBY_PATH = CUR_DIR / '_moby' / 'mthesaur.txt'
ANTONYMS_PATH = CUR_DIR / '_antonyms.json'
DERIVATIONS_PATH = CUR_DIR / '_derivations.json'
AUTO_RELATIONS_PATH = CUR_DIR / 'relations_auto.json'

MOBY_URL = 'https://www.gutenberg.org/files/3202/files/mthesaur.txt'

# 同义聚类参数：共同邻居数阈值 + 每词最多同义词邻居 + 簇大小上限
SYNONYM_STRENGTH_MIN = 4
SYNONYM_TOP_N = 6
SYNONYM_CLUSTER_MAX = 10


def collect_words():
    """词库全部词形（含 jeopardise/jeopardize 变体拆分，小写），与 parser.py 逻辑一致"""
    words = set()
    vocabulary_path = CUR_DIR / 'vocabulary.txt'
    for line in vocabulary_path.read_text(encoding='utf-8').split('\n'):
        line = line.strip()
        if not line or line in ('===', '+++', '---'):
            continue
        word = line.split('|')[0].strip()
        if '|' not in line or not re.match(r'^[a-zA-Z]', word):
            continue
        for variant in word.split('/'):
            variant = variant.strip().lower()
            if variant:
                words.add(variant)
    return words


def fetch_moby():
    """下载 Moby Thesaurus II（已有缓存跳过）"""
    if MOBY_PATH.exists():
        print(f'Moby 词库已存在: {MOBY_PATH}')
        return
    MOBY_PATH.parent.mkdir(exist_ok=True)
    print(f'下载 Moby Thesaurus II ...')
    req = request.Request(MOBY_URL, headers={'User-Agent': 'Mozilla/5.0'})
    data = request.urlopen(req, timeout=60).read()
    MOBY_PATH.write_bytes(data)
    print(f'下载完成: {len(data) / 1024 / 1024:.1f} MB')


def build_synonym_groups(vocab):
    """Moby 与词库交集 → 共同邻居强度 → 互惠 Top-K 边 → 并查集聚类 → relations_auto.json"""
    print('解析 Moby 词库 ...')
    moby_neighbors = defaultdict(set)  # 词 → moby 同义词（含词库外词汇，用于强度计算）
    for line in MOBY_PATH.read_text(encoding='utf-8', errors='ignore').split('\n'):
        if not line:
            continue
        parts = [p.strip().lower() for p in line.split(',')]
        head = parts[0]
        if not head:
            continue
        moby_neighbors[head].update(p for p in parts[1:] if p and p != head)

    # 词库内词汇的在词库同义邻居
    vocab_neighbors = {}
    for w in vocab:
        if w in moby_neighbors:
            vocab_neighbors[w] = moby_neighbors[w] & vocab

    print(f'词库 {len(vocab)} 词，Moby 命中 {len(vocab_neighbors)} 词')

    # 候选边强度 = 两词在 Moby 中的共同邻居数
    def strength(w, ns, v):
        return len(ns & vocab_neighbors.get(v, set()))

    # 每词按强度取 Top-K 最强同义邻居（要求共同邻居 >= 2）
    top = {}
    for w, ns in vocab_neighbors.items():
        ranked = sorted(((strength(w, ns, v), v) for v in ns if strength(w, ns, v) >= 2), reverse=True)
        if ranked:
            top[w] = {v for _, v in ranked[:SYNONYM_TOP_N]}

    # 互惠边：v 在 w 的 Top-K 且 w 在 v 的 Top-K（高精度，避免 Moby 宽泛语义链成巨型簇）
    mutual = [(w, v) for w, ts in top.items() for v in ts if v in top and w in top[v] and w < v]
    print(f'互惠同义边: {len(mutual)}')

    # 并查集聚类
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for w, v in mutual:
        union(w, v)

    clusters = defaultdict(set)
    for w in list(parent):
        clusters[find(w)].add(w)

    groups = []
    for members in clusters.values():
        if len(members) > SYNONYM_CLUSTER_MAX:
            continue  # 过大簇视为噪音（Moby 语义太宽泛），丢弃
        groups.append({'type': 'synonym', 'words': sorted(members)})

    AUTO_RELATIONS_PATH.write_text(
        json.dumps(groups, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')
    covered = len({w for g in groups for w in g['words']})
    print(f'同义簇: {len(groups)} 组，覆盖 {covered} 词 → relations_auto.json')
    return groups


def load_cache(path):
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


def save_cache(path, mapping):
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')


def fetch_batch(words, mapping, fetch_one, label, path):
    """通用增量批量抓取：网络失败的词不写缓存，下次重试"""
    todo = [w for w in words if mapping.get(w) is None]
    print(f'{label} 需要抓取: {len(todo)}')
    if not todo:
        return mapping
    from concurrent.futures import ThreadPoolExecutor
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_one, w): w for w in todo}
        for future in futures:
            word = futures[future]
            try:
                result, ok = future.result()
            except Exception:
                result, ok = None, False
            if ok:
                mapping[word] = result
            done += 1
            if done % 50 == 0 or done == len(todo):
                save_cache(path, mapping)
                print(f'{label} 进度: {done}/{len(todo)}')
    save_cache(path, mapping)
    return mapping


def fetch_antonyms_datamuse(word):
    time.sleep(0.1)
    url = f'https://api.datamuse.com/words?rel_ant={quote(word)}&max=5'
    req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with request.urlopen(req, timeout=10) as resp:
        items = json.loads(resp.read().decode('utf-8'))
    # 不筛词库：缓存原始结果，合并时校验
    return [it['word'].lower() for it in items if it.get('word')], True


def fetch_derivations_youdao(word):
    time.sleep(0.2)
    url = f'https://dict.youdao.com/jsonapi_s?doctype=json&jsonversion=4&q={quote(word)}'
    req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with request.urlopen(req, timeout=10) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    item = d.get('simple', {}).get('word', [])
    if item and str(item[0].get('return-phrase', '')).strip().lower() != word:
        return [], True  # 反爬返回错误词条，按无派生处理
    words = []
    for rel in (d.get('rel_word') or {}).get('rels', []):
        for w in (rel.get('rel') or {}).get('words', []):
            dw = str(w.get('word', '')).strip().lower()
            if dw and dw != word:
                words.append(dw)
    return sorted(set(words)), True


if __name__ == '__main__':
    vocab = collect_words()
    fetch_moby()
    build_synonym_groups(vocab)
    fetch_batch(vocab, load_cache(ANTONYMS_PATH), fetch_antonyms_datamuse, '反义词(Datamuse)', ANTONYMS_PATH)
    fetch_batch(vocab, load_cache(DERIVATIONS_PATH), fetch_derivations_youdao, '派生词(有道)', DERIVATIONS_PATH)
    print('完成')
