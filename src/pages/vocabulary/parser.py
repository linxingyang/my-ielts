import json
import re
import time
from pathlib import Path
from collections import defaultdict
from urllib import request
from urllib.parse import quote

CUR_DIR = Path(__file__).absolute().parent
PHONETICS_PATH = CUR_DIR / 'phonetics.json'
TRANSLATIONS_PATH = CUR_DIR / 'translations.json'


def norm_example(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def load_translations():
    # 例句的书本翻译（由 _ocr_all.py + _extract_trans.py 从原书 PDF OCR 提取）
    if TRANSLATIONS_PATH.exists():
        return json.loads(TRANSLATIONS_PATH.read_text(encoding='utf-8'))
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


def parse(phonetics):
    translations = load_translations()
    part_mapping = {
        0: 'word',
        1: 'pos',
        2: 'meaning',
        3: 'example',
        4: 'extra',
    }
    result = defaultdict(lambda: {'label': '', 'audio': '', 'groupCount': 0, 'wordCount': 0, 'words': []})
    vocabulary_path = CUR_DIR / 'vocabulary.txt'
    contents = '\n'.join([l.strip() for l in vocabulary_path.read_text(encoding='utf-8').split('\n')])
    categories = contents.split('===\n')
    cur_id = 0
    category_index = 0
    for category in categories:
        category_index += 1
        category_parts = category.split('+++\n')
        label = f"{str(category_index).zfill(2)}_{category_parts[0].strip()}"
        category_body = result[label]
        word_groups = category_parts[1].split('---\n')
        category_body['label'] = label
        category_body['audio'] = f"{label}.mp3"
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
                word_dict['word'] = word_dict['word'].split('/')
                word_dict['phonetic'] = lookup_phonetic(phonetics, word_dict['word'])
                word_dict['translation'] = translations.get(norm_example(word_dict['example']), '')
                group.append(word_dict)
            if group:
                category_body['words'].append(group)
        category_body['wordCount'] = word_count

    js_code = f"""
/**
  * pos = part of speech
  */

const vocabulary = {json.dumps(result, ensure_ascii=False)}

export default vocabulary
"""
    vocabulary_js_file = CUR_DIR / 'vocabulary.js'
    vocabulary_js_file.write_text(js_code, encoding='utf-8')


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
