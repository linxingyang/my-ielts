# 将 四级/六级/AWL 词表转换为 vocabulary.txt 追加章节 + translations.json 补充
#
# 逻辑：
# 1. 解析现有 vocabulary.txt，建立真经词条索引（按归一化单词）
# 2. 目标词表：四级 = CET4_2；六级 = CET4_2 ∪ CET6_2 ∪ CET6_3（大纲包含关系）；AWL = awl_words.json
# 3. 词在真经中已存在 → 整行复用（例句/翻译/note/音频全部沿用）
#    否则用词库自带 例句+翻译 构造词条；缺失例句走有道 blng 补；AWL 中文释义走有道 ec 补
# 4. 例句翻译并入 translations.json；无例句的词输出失败清单
# 5. 幂等：重新运行时先删除旧的生成章节（标题含 |cet4/|cet6/|awl）再重新生成
#
# 章节标题格式：`四级 A|cet4`（parser.py 按 | 拆出名称与 source）
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
TXT_PATH = CUR_DIR / 'vocabulary.txt'
TRANS_PATH = CUR_DIR / 'translations.json'
SRC_DIR = CUR_DIR / '_cet_source'
CACHE_PATH = CUR_DIR / '_convert_cache.json'   # 有道接口增量缓存（释义/例句/机翻）
MISSING_PATH = CUR_DIR / '_missing_examples.txt'
GENERATED_SOURCES = {'cet4', 'cet6', 'awl'}
GROUP_SIZE = 8  # 每组词条数（对应 txt 中 --- 分组，与真经粒度一致）

# 词表原始数据的拼写错误修正（key 为小写）
WORD_FIXES = {'reservior': 'reservoir'}


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def http_json(url, headers=None, timeout=15, retries=3):
    h = {'User-Agent': 'Mozilla/5.0'}
    if headers:
        h.update(headers)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except Exception as e:
            if i == retries - 1:
                print(f'  [youdao 失败] {url[:80]}: {e}')
                return None
            time.sleep(0.5 * (i + 1))


# ---------------- 真经索引 ----------------

def load_jingjing_index():
    index = {}
    jj_text, _ = split_generated(TXT_PATH.read_text(encoding='utf-8'))
    for line in jj_text.splitlines():
        t = line.strip()
        if not t or t in ('===', '+++', '---'):
            continue
        word = t.split('|')[0].strip()
        if not word or word == '-' or '|' in word:
            continue
        for variant in word.split('/'):
            v = variant.strip()
            if v:
                index.setdefault(norm(v), line)
    return index


# ---------------- 词表数据 ----------------

def load_ndjson(path):
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


def kajweb_entries(path):
    # 返回 [{word, pos, meaning, example, example_cn}]
    out = []
    for item in load_ndjson(path):
        c = item['content']['word']['content']
        word = item['content']['word']['wordHead'].strip()
        word = WORD_FIXES.get(word.lower(), word)
        trans = c.get('trans') or []
        pos = '/'.join(dict.fromkeys(
            (t.get('pos') or '').strip().rstrip('.') + '.' for t in trans if t.get('pos')))
        meaning = '；'.join(t.get('tranCn', '').strip() for t in trans if t.get('tranCn'))
        sents = (c.get('sentence') or {}).get('sentences') or []
        example = sents[0]['sContent'].strip() if sents else ''
        example_cn = sents[0].get('sCn', '').strip() if sents else ''
        out.append({'word': word, 'pos': pos or '-', 'meaning': meaning or '-',
                    'example': example, 'example_cn': example_cn})
    return out


def load_awl_entries():
    # 返回 [{word, sublist, example, example_cn}]
    raw = json.loads((SRC_DIR / 'awl_words.json').read_text(encoding='utf-8'))
    out = []
    for item in raw:
        out.append({'word': item['word'].strip(), 'sublist': item['sublist'],
                    'example': (item.get('example_sentence') or '').strip(),
                    'example_cn': ''})
    return out


# ---------------- 有道接口 ----------------

def open_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding='utf-8'))
    return {'meaning': {}, 'example': {}, 'fanyi': {}}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')


def youdao_meaning(word, cache):
    # 返回 (pos, meaning) 或 ('', '')
    key = norm(word)
    if key in cache['meaning']:
        return cache['meaning'][key]
    time.sleep(0.25)
    d = http_json('https://dict.youdao.com/jsonapi_s?doctype=json&jsonversion=4&q=' + urllib.parse.quote(word))
    result = ['', '']
    try:
        trs = ((d or {}).get('ec') or {}).get('word', {}).get('trs') or []
        parts = [f"{(t.get('pos') or '').strip()} {(t.get('tran') or '').strip()}".strip()
                 for t in trs if t.get('tran')]
        if parts:
            pos = '/'.join(dict.fromkeys(
                (t.get('pos') or '').strip().rstrip('.') + '.' for t in trs if t.get('pos')))
            meaning = '；'.join((t.get('tran') or '').strip() for t in trs if t.get('tran'))
            result = [pos or '-', meaning]
    except Exception:
        pass
    cache['meaning'][key] = result
    return result


def youdao_example(word, cache):
    # 返回 (example, example_cn) 或 ('', '')
    key = norm(word)
    if key in cache['example']:
        return cache['example'][key]
    time.sleep(0.25)
    d = http_json('https://dict.youdao.com/jsonapi_s?doctype=json&jsonversion=4&q=' + urllib.parse.quote(word))
    result = ['', '']
    try:
        pairs = ((d or {}).get('blng_sents_part') or {}).get('sentence-pair') or []
        for p in pairs:
            sent = re.sub(r'</?b>', '', p.get('sentence-eng') or p.get('sentence') or '').strip()
            if sent:
                result = [sent, (p.get('sentence-translation') or '').strip()]
                break
    except Exception:
        pass
    cache['example'][key] = result
    return result


def youdao_fanyi(text, cache):
    # 例句机器翻译（用于 AWL 自带例句），返回译文或 ''
    key = norm(text)
    if key in cache['fanyi']:
        return cache['fanyi'][key]
    time.sleep(0.25)
    url = ('https://fanyi.youdao.com/translate?doctype=json&type=EN2ZH_CN&i='
           + urllib.parse.quote(text))
    d = http_json(url, timeout=20)
    result = ''
    try:
        result = d['translateResult'][0][0]['tgt'].strip()
    except Exception:
        pass
    cache['fanyi'][key] = result
    return result


# ---------------- 生成 ----------------

def build_entry(item, jj_index, seen, cache, stats, new_translations):
    # 返回 (line 或 None, chapter 或 None)
    w = item['word']
    key = norm(w)
    if not key or key in seen:
        return None, None
    seen.add(key)

    if key in jj_index:
        stats['reused'] += 1
        return jj_index[key], None  # 整行复用真经词条

    pos, meaning, example, example_cn = item.get('pos', '-'), item.get('meaning', '-'), item.get('example', ''), item.get('example_cn', '')
    if 'sublist' in item and (not meaning or meaning == '-'):
        # AWL：中文释义走有道
        pos, meaning = youdao_meaning(w, cache)
    if 'sublist' in item and example:
        # AWL 自带例句无翻译，优先换用有道 blng 双语例句；blng 没有再保留自带例句
        blng, blng_cn = youdao_example(w, cache)
        if blng:
            example, example_cn = blng, blng_cn
    if not example:
        example, example_cn = youdao_example(w, cache)
    if example and not example_cn:
        example_cn = youdao_fanyi(example, cache)

    if not example:
        stats['no_example'].append(w)
        line = f"{w}|{pos}|{meaning}|-"
    else:
        if example_cn:
            new_translations[norm(example)] = example_cn
        line = f"{w}|{pos}|{meaning}|{example}"
    stats['built'] += 1
    return line, item.get('sublist')


def group_words(lines):
    # 每 GROUP_SIZE 个词一组，组内用换行分隔，组间用 --- 分隔
    blocks = []
    for i in range(0, len(lines), GROUP_SIZE):
        blocks.append('\n'.join(lines[i:i + GROUP_SIZE]))
    return '\n---\n'.join(blocks)


def letter_chapters(entries, source_name, source_tag, jj_index, cache, new_translations):
    seen = set()  # 词库内去重（六级包含四级词是设计意图，跨词库不去重）
    stats = {'reused': 0, 'built': 0, 'no_example': []}
    by_letter = {}
    order = []
    for item in entries:
        line, _ = build_entry(item, jj_index, seen, cache, stats, new_translations)
        if line is None:
            continue
        w = line.split('|')[0].strip()
        letter = w[0].upper()
        if not letter.isalpha():
            letter = '#'
        if letter not in by_letter:
            by_letter[letter] = []
            order.append(letter)
        by_letter[letter].append(line)
    sections = []
    for letter in order:
        title = f"{source_name} {letter if letter != '#' else '其他'}|{source_tag}"
        sections.append(f"===\n{title}\n+++\n{group_words(by_letter[letter])}\n")
    return sections, stats


def awl_chapters(entries, jj_index, cache, new_translations):
    seen = set()
    stats = {'reused': 0, 'built': 0, 'no_example': []}
    by_sub = {}
    for item in sorted(entries, key=lambda x: x['sublist']):
        line, _ = build_entry(item, jj_index, seen, cache, stats, new_translations)
        if line is None:
            continue
        by_sub.setdefault(item['sublist'], []).append(line)
    sections = []
    for sub in sorted(by_sub):
        title = f"AWL-{sub}|awl"
        sections.append(f"===\n{title}\n+++\n{group_words(by_sub[sub])}\n")
    return sections, stats


def split_generated(txt):
    # 返回 (真经部分文本, 是否含生成章节)
    lines = txt.splitlines()
    gen_start = None
    for i, line in enumerate(lines):
        if line.strip() == '===' and i + 1 < len(lines):
            title = lines[i + 1].strip()
            if '|' in title and title.rsplit('|', 1)[1] in GENERATED_SOURCES:
                gen_start = i
                break
    if gen_start is None:
        return txt.rstrip() + '\n', False
    kept = [l for l in lines[:gen_start]]
    while kept and not kept[-1].strip():
        kept.pop()
    return '\n'.join(kept) + '\n', True


def main():
    jj_index = load_jingjing_index()
    print(f'真经索引词条数: {len(jj_index)}')

    cache = open_cache()
    new_translations = {}

    cet4 = kajweb_entries(SRC_DIR / 'CET4_2.json')
    cet6_2 = kajweb_entries(SRC_DIR / 'CET6_2.json')
    cet6_3 = kajweb_entries(SRC_DIR / 'CET6_3.json')

    # 六级 = 四级 ∪ 两个六级词表（优先保留带例句的条目）
    cet6_map = {}
    for item in cet4 + cet6_2 + cet6_3:
        key = norm(item['word'])
        old = cet6_map.get(key)
        if old is None or (not old['example'] and item['example']):
            cet6_map[key] = item
    cet6 = list(cet6_map.values())
    awl = load_awl_entries()
    print(f'词表规模: 四级 {len(cet4)}, 六级(合并去重) {len(cet6)}, AWL {len(awl)}')

    txt = TXT_PATH.read_text(encoding='utf-8')
    jj_text, had_generated = split_generated(txt)
    print(f'保留真经部分: {len(jj_text.splitlines())} 行（含旧生成章节: {had_generated}）')

    sections = []
    all_stats = {}
    for name, entries, fn in [
        ('四级', cet4, lambda: letter_chapters(cet4, '四级', 'cet4', jj_index, cache, new_translations)),
        ('六级', cet6, lambda: letter_chapters(cet6, '六级', 'cet6', jj_index, cache, new_translations)),
        ('AWL', awl, lambda: awl_chapters(awl, jj_index, cache, new_translations)),
    ]:
        secs, stats = fn()
        sections += secs
        all_stats[name] = stats
        print(f"{name}: 词条 {len(entries)}, 复用真经 {stats['reused']}, 新构造 {stats['built']}, 无例句 {len(stats['no_example'])}")

    TXT_PATH.write_text(jj_text.rstrip() + '\n' + '\n'.join(sections), encoding='utf-8')
    save_cache(cache)

    # 例句翻译并入 translations.json（已存在的 key 不覆盖）
    translations = json.loads(TRANS_PATH.read_text(encoding='utf-8')) if TRANS_PATH.exists() else {}
    added = 0
    for k, v in new_translations.items():
        if k and k not in translations:
            translations[k] = v
            added += 1
    TRANS_PATH.write_text(json.dumps(translations, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')

    all_missing = []
    for name, stats in all_stats.items():
        all_missing += [f'{name}\t{w}' for w in stats['no_example']]
    MISSING_PATH.write_text('\n'.join(all_missing), encoding='utf-8')

    print(f"\n完成: 新增例句翻译 {added} 条, 生成章节 {len(sections)} 个")
    print(f"无例句词条 {len(all_missing)} 个, 清单: {MISSING_PATH.name}")


if __name__ == '__main__':
    main()
