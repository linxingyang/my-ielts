import json
import re
import time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from urllib import request
from urllib.parse import quote

CUR_DIR = Path(__file__).absolute().parent
PHONETICS_PATH = CUR_DIR / 'phonetics.json'
TRANSLATIONS_PATH = CUR_DIR / 'translations.json'
NOTES_PATH = CUR_DIR / 'notes.json'
RELATIONS_PATH = CUR_DIR / 'relations.json'  # 手工精选关联组（词根/同义/反义）
AUTO_RELATIONS_PATH = CUR_DIR / 'relations_auto.json'  # Moby 自动同义聚类
ANTONYMS_PATH = CUR_DIR / '_antonyms.json'  # Datamuse 反义词缓存
DERIVATIONS_PATH = CUR_DIR / '_derivations.json'  # 有道派生词缓存

# 每词各类型关联数量上限与总上限
MAX_RELATIONS = {'root': 8, 'syn': 6, 'ant': 3, 'der': 4, 'sim': 3}
MAX_RELATIONS_TOTAL = 12


def norm_example(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def load_translations():
    # 例句的书本翻译（由 _ocr_all.py + _extract_trans.py 从原书 PDF OCR 提取）
    if TRANSLATIONS_PATH.exists():
        return json.loads(TRANSLATIONS_PATH.read_text(encoding='utf-8'))
    return {}


def load_notes():
    # 词条完整书本内容（例句译文、【记】、【搭】等，由 _extract_full.py 从原书 PDF OCR 提取）
    if NOTES_PATH.exists():
        return json.loads(NOTES_PATH.read_text(encoding='utf-8'))
    return {}


def load_phonetics():
    if PHONETICS_PATH.exists():
        return json.loads(PHONETICS_PATH.read_text(encoding='utf-8'))
    return {}


def save_phonetics(mapping):
    PHONETICS_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')


def fetch_phonetic(word):
    time.sleep(0.2)  # 请求间隔，降低触发反爬的概率
    # 返回 (phonetic, ok)；ok=False 表示网络失败，不应写入缓存，下次运行时重试
    word_lower = word.lower()
    # 主源：有道词典接口（国内访问稳定）。注意：该接口偶尔会返回错误词条（反爬），
    # 必须校验 return-phrase 与查询词一致
    url = f"https://dict.youdao.com/jsonapi_s?doctype=json&jsonversion=4&q={quote(word)}"
    for _ in range(4):
        try:
            req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with request.urlopen(req, timeout=10) as resp:
                entries = json.loads(resp.read().decode('utf-8'))
            items = entries.get('simple', {}).get('word', [])
            if not items:
                break  # 响应正常但无结果，交给备用源
            item = items[0]
            if str(item.get('return-phrase', '')).strip().lower() != word_lower:
                time.sleep(0.5)
                continue  # 返回了错误词条，重试
            uk, us = item.get('ukphone', ''), item.get('usphone', '')
            if uk and us:
                return (f"UK /{uk}/ US /{us}/", True)
            if uk or us:
                return (f"/{uk or us}/", True)
            break  # 有该词但无音标字段，交给备用源
        except Exception:
            time.sleep(0.5)
    # 兜底源：必应词典（有道无结果/返回错误词条时使用，音标在 meta description 中）
    url = f"https://cn.bing.com/dict/search?q={quote(word)}"
    for _ in range(2):
        try:
            req = request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'})
            with request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            title = re.search(r'<title>(.*?)\s*-\s*搜索 词典', html)
            if title and title.group(1).strip().lower() != word_lower:
                time.sleep(0.5)
                continue  # 返回了错误词条，重试
            matched = re.search(r'美\[([^\]]*)\]\s*，\s*英\[([^\]]*)\]', html)
            if matched:
                us, uk = matched.group(1), matched.group(2)
                if us and uk:
                    return (f"UK /{uk}/ US /{us}/", True)
                if us or uk:
                    return (f"/{us or uk}/", True)
            return ('', True)  # 确认无此词或无音标
        except Exception:
            time.sleep(0.5)
    return ('', False)


def update_phonetics(words):
    # words: 所有不重复的单词（小写）；缓存中值为 '' 表示已查询过但查不到，不再重试
    mapping = load_phonetics()
    todo = [w for w in words if mapping.get(w) is None]
    print(f"需要获取音标的单词数: {len(todo)}")
    if todo:
        from concurrent.futures import ThreadPoolExecutor
        done = 0
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(fetch_phonetic, w): w for w in todo}
            for future in futures:
                word = futures[future]
                phonetic, ok = future.result()
                if ok:
                    mapping[word] = phonetic
                done += 1
                if done % 20 == 0 or done == len(todo):
                    save_phonetics(mapping)
                    print(f"进度: {done}/{len(todo)}")
    save_phonetics(mapping)
    failed = [w for w in mapping if mapping[w] is None]
    if failed:
        print(f"网络失败未获取到音标（下次运行会重试）: {len(failed)} 个")
    return mapping


def collect_words():
    words = set()
    vocabulary_path = CUR_DIR / 'vocabulary.txt'
    for line in vocabulary_path.read_text(encoding='utf-8').split('\n'):
        line = line.strip()
        if not line or line in ('===', '+++', '---'):
            continue
        word = line.split('|')[0].strip()
        if '|' not in line or not re.match(r'^[a-zA-Z]', word):
            continue  # 跳过分类标题等非词条行
        for variant in word.split('/'):
            variant = variant.strip().lower()
            if variant:
                words.add(variant)
    return words


def lookup_phonetic(mapping, word_variants):
    for variant in word_variants:
        phonetic = mapping.get(variant.strip().lower())
        if phonetic:
            return phonetic
    return ''


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    print(f'[关联词] 缺少 {path.name}，跳过该数据源')
    return default


def add_relation(rel_map, word, rtype, other, root=None):
    """添加一条关联（含去重与数量上限）。root 组的关联携带词根说明"""
    key = (rtype, other)
    for r in rel_map[word]:
        if (r['t'], r['w']) == key:
            return
        # 已有其他类型的同词关联（如派生）时，形近词不再重复添加
        if rtype == 'sim' and r['w'] == other:
            return
    if sum(1 for r in rel_map[word] if r['t'] == rtype) >= MAX_RELATIONS.get(rtype, 3):
        return
    if len(rel_map[word]) >= MAX_RELATIONS_TOTAL:
        return
    entry = {'t': rtype, 'w': other}
    if root:
        entry['r'] = root
    rel_map[word].append(entry)


def compute_similar_words(words):
    """形近词：SequenceMatcher ratio >= 0.82，仅长度 >= 5、前 2 字母相同
    （形近词绝大多数共享开头），每词上限 3 个"""
    buckets = defaultdict(list)  # (前2字母, 长度) → 词列表
    word_list = sorted(words)
    for w in word_list:
        if len(w) >= 5:
            buckets[(w[:2], len(w))].append(w)
    similar = {}
    for w in word_list:
        if len(w) < 5:
            continue
        cands = set()
        for length in range(len(w) - 2, len(w) + 3):
            cands.update(buckets.get((w[:2], length), []))
        best = []
        for v in cands:
            if v == w:
                continue
            ratio = SequenceMatcher(None, w, v).ratio()
            if ratio >= 0.82:
                best.append((v, ratio))
        best.sort(key=lambda x: -x[1])
        if best:
            similar[w] = [v for v, _ in best[:MAX_RELATIONS['sim']]]
    return similar


def build_relations(vocab):
    """合并手工/自动同义/反义/派生数据，组内两两双向生成 词 → [关联] 映射。
    返回 (rel_map, relation_groups)：rel_map 供词条合并；relation_groups 供关联组视图"""
    rel_map = defaultdict(list)

    # 1. 手工精选组（词根/同义/反义）+ 2. Moby 自动同义聚类
    manual_groups = load_json(RELATIONS_PATH, [])
    auto_groups = load_json(AUTO_RELATIONS_PATH, [])

    type_mapping = {'root': 'root', 'synonym': 'syn', 'antonym': 'ant'}
    relation_groups = []
    seen_groups = set()
    for group in manual_groups + auto_groups:
        words = [w.strip().lower() for w in group.get('words', [])]
        valid = [w for w in words if w in vocab]
        missing = [w for w in words if w not in vocab]
        if missing:
            print(f'[关联词] 警告: {group.get("type")} 组含词库外词汇已跳过: {missing}')
        if len(valid) < 2:
            continue
        rtype = type_mapping[group['type']]
        signature = (rtype, tuple(valid))
        if signature not in seen_groups:
            seen_groups.add(signature)
            relation_groups.append({'type': rtype, 'root': group.get('root', ''), 'words': valid})
        for w in valid:
            for other in valid:
                if other != w:
                    add_relation(rel_map, w, rtype, other, group.get('root'))

    # 3. 反义词（Datamuse 缓存，成对双向）
    antonyms = load_json(ANTONYMS_PATH, {})
    ant_pairs = 0
    for word, ants in antonyms.items():
        if word not in vocab:
            continue
        for ant in ants:
            if ant in vocab:
                add_relation(rel_map, word, 'ant', ant)
                add_relation(rel_map, ant, 'ant', word)
                ant_pairs += 1
    print(f'[关联词] 反义关系: {ant_pairs} 对')

    # 4. 派生词（有道 rel_word 缓存，成对双向）
    derivations = load_json(DERIVATIONS_PATH, {})
    der_pairs = 0
    for word, ders in derivations.items():
        if word not in vocab:
            continue
        for dw in ders:
            if dw in vocab:
                add_relation(rel_map, word, 'der', dw)
                add_relation(rel_map, dw, 'der', word)
                der_pairs += 1
    print(f'[关联词] 派生关系: {der_pairs} 对')

    # 5. 形近词（构建时自动计算，成对双向）
    similar = compute_similar_words(vocab)
    sim_pairs = 0
    for word, sims in similar.items():
        for sv in sims:
            add_relation(rel_map, word, 'sim', sv)
            add_relation(rel_map, sv, 'sim', word)
            sim_pairs += 1
    print(f'[关联词] 形近关系: {sim_pairs} 对')

    covered = sum(1 for rs in rel_map.values() if rs)
    print(f'[关联词] 覆盖 {covered}/{len(vocab)} 词')
    return rel_map, relation_groups


def parse(phonetics):
    translations = load_translations()
    notes = load_notes()
    rel_map, relation_groups = build_relations(collect_words())
    part_mapping = {
        0: 'word',
        1: 'pos',
        2: 'meaning',
        3: 'example',
        4: 'extra',
    }
    result = defaultdict(lambda: {'label': '', 'source': 'ielts', 'audio': '', 'groupCount': 0, 'wordCount': 0, 'words': []})
    vocabulary_path = CUR_DIR / 'vocabulary.txt'
    contents = '\n'.join([l.strip() for l in vocabulary_path.read_text(encoding='utf-8').split('\n')])
    categories = contents.split('===\n')
    public_audio_dir = CUR_DIR.parent.parent.parent / 'public' / 'vocabulary' / 'audio'
    cur_id = 0
    source_counters = defaultdict(int)
    for category in categories:
        category_parts = category.split('+++\n')
        title = category_parts[0].strip()
        # 章节标题支持 `名称|source` 后缀，指定所属词库（ielts/cet4/cet6/awl），各词库独立编号
        if '|' in title:
            name, source = title.rsplit('|', 1)
            name, source = name.strip(), source.strip()
        else:
            name, source = title, 'ielts'
        source_counters[source] += 1
        label = f"{str(source_counters[source]).zfill(2)}_{name}"
        category_body = result[label]
        word_groups = category_parts[1].split('---\n')
        category_body['label'] = label
        category_body['source'] = source
        # 整章朗读音频仅真经章节有，文件不存在时置空（前端据此隐藏播放器）
        category_body['audio'] = f"{label}.mp3" if (public_audio_dir / f"{label}.mp3").exists() else ''
        category_body['groupCount'] = len(word_groups)
        word_count = 0
        for word_group in word_groups:
            words = word_group.strip().split('\n')
            group = []
            for word in words:
                if not word:
                    continue
                word_count += 1
                cur_id += 1
                word_parts = word.split('|')
                # if category_index == 5:
                #     print(word_parts[0])
                word_dict = {'id': cur_id, 'spellError': False, 'spellValue': '', 'showSource': False}
                for part_index in part_mapping:
                    dict_key = part_mapping[part_index]
                    word_dict[dict_key] = word_parts[part_index] if part_index < len(word_parts) else '-'
                # 拓展内容缺失时置空（避免前端显示占位符 '-'）
                if word_dict['extra'] == '-':
                    word_dict['extra'] = ''
                word_dict['word'] = word_dict['word'].split('/')
                word_dict['phonetic'] = lookup_phonetic(phonetics, word_dict['word'])
                word_dict['translation'] = translations.get(norm_example(word_dict['example']), '')
                word_dict['note'] = notes.get(norm_example(word_dict['word'] if isinstance(word_dict['word'], str) else ' '.join(word_dict['word'])), '')
                # 关联词：合并各变体的关联（已全局去重），按 root/syn/ant/der/sim 顺序
                merged = []
                seen = set()
                for variant in word_dict['word']:
                    for r in rel_map.get(variant.strip().lower(), []):
                        key = (r['t'], r['w'])
                        if key not in seen:
                            seen.add(key)
                            merged.append(r)
                if merged:
                    word_dict['relations'] = merged
                group.append(word_dict)
            if group:
                category_body['words'].append(group)
        category_body['wordCount'] = word_count

    # ---------------- 输出：index 清单 + 每词库独立 js + relationGroups ----------------
    # index 清单：章节元信息 + 纯词串列表（word[0]），体积小、打开页面即加载；
    # 统计（章节/词库/全库进度）只依赖清单，无需等待全量数据
    manifest = {
        'sources': list(dict.fromkeys(ch['source'] for ch in result.values())),
        'chapters': {
            label: {
                'label': ch['label'],
                'source': ch['source'],
                'audio': ch['audio'],
                'groupCount': ch['groupCount'],
                'wordCount': ch['wordCount'],
                'wordList': [item['word'][0] for group in ch['words'] for item in group],
            }
            for label, ch in result.items()
        },
    }
    (CUR_DIR / 'vocabulary-index.json').write_text(
        json.dumps(manifest, ensure_ascii=False), encoding='utf-8')

    # 每词库一个 js 文件（前端按需 dynamic import，切换词库时才加载）
    by_source = defaultdict(dict)
    for label, ch in result.items():
        by_source[ch['source']][label] = ch
    for source, chapters in by_source.items():
        js_code = f"""/**
  * 由 parser.py 自动生成，禁止手工编辑；与同目录其他 vocabulary-*.js 配套
  */

const data = {json.dumps(chapters, ensure_ascii=False)}

export default data
"""
        (CUR_DIR / f'vocabulary-{source}.js').write_text(js_code, encoding='utf-8')

    # 关联组独立文件（体积远小于全量词条，供「关联组」视图使用）
    (CUR_DIR / 'relationGroups.js').write_text(f"""/**
  * 单词关联组（手工精选词根族 + Moby 同义聚类），由 parser.py 自动生成，禁止手工编辑
  */

const relationGroups = {json.dumps(relation_groups, ensure_ascii=False)}

export default relationGroups
""", encoding='utf-8')

    # 旧的单文件产物已拆分，删除避免继续被打包（7MB+）
    old_file = CUR_DIR / 'vocabulary.js'
    if old_file.exists():
        old_file.unlink()
        print('[parser] 已删除旧的 vocabulary.js（数据已拆分为 vocabulary-<source>.js + vocabulary-index.json）')


def download_audio():
    names = ['01_自然地理', '02_植物研究', '03_动物保护', '04_太空探索', '05_学校教育', '06_科技发明', '07_文化历史', '08_语言演化', '09_娱乐运动', '10_物品材料', '11_时尚潮流',
             '12_饮食健康', '13_建筑场所', '14_交通旅行', '15_国家政府', '16_社会经济', '17_法律法规', '18_沙场争锋', '19_社会角色', '20_行为动作', '21_身心健康', '22_时间日期']

    for index in range(22):
        url = f"https://down.guixue.com/mp3/ielts_lexicon/{index + 1}.mp3"
        file_name, headers = request.urlretrieve(url)
        Path(file_name).rename(CUR_DIR / f'audio/{names[index]}.mp3')


if __name__ == '__main__':
    # download_audio()
    phonetics = update_phonetics(collect_words())
    parse(phonetics)
    pass
