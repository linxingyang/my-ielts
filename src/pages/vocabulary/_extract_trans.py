"""从 OCR 结果中按词表顺序提取例句的书本翻译，输出 translations.json。"""
import json
import re
from difflib import SequenceMatcher


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


CJK = re.compile(r'[\u4e00-\u9fff]')


def load_entries():
    entries = []
    for line in open('vocabulary.txt', encoding='utf-8'):
        line = line.strip()
        if '|' not in line or not re.match(r'^[a-zA-Z]', line.split('|')[0]):
            continue
        parts = line.split('|')
        word = parts[0].strip()
        example = parts[3].strip() if len(parts) > 3 else ''
        entries.append({'word': word, 'example': example})
    return entries


def build_lines():
    """按 页->栏->y 重排成全局行序列，过滤页眉页脚"""
    data = json.load(open('_ocr_pages.json', encoding='utf-8'))
    seq = []
    for page_index in range(336):
        lines = data.get(str(page_index), [])
        # 过滤页眉（y<100）与页脚索引区（y>=3120）
        lines = [l for l in lines if 100 <= l['y'] < 3120]
        left = sorted([l for l in lines if l['x'] < 1000], key=lambda l: l['y'])
        right = sorted([l for l in lines if l['x'] >= 1000], key=lambda l: l['y'])
        for l in left + right:
            l2 = dict(l)
            l2['page'] = page_index
            seq.append(l2)
    return seq


BLOCK_MARK = re.compile(r'^[\[\]Il1|Ｉｌ]{1,2}\s*[例记搭链近]')      # [记]/[搭]/[例] 及 OCR 变体
SINGLE_WORD = re.compile(r"^[A-Za-z][A-Za-z'-]{0,13}$")            # 独立的短单词行 = 下一词条
PHONETIC_LINE = re.compile(r"^[\[\]Il1|/Ｉｌ\s]*/[^/]+/[\[\]Il1|]*$")  # 独立音标行
GARBAGE = re.compile(r'^[^A-Za-z\u4e00-\u9fff]+$')                 # 纯符号/数字行
MARKER_IN_TEXT = re.compile(r'[记搭同反派辨参](?=\s*[a-zA-Z])')       # 翻译正文中的拓展 marker


def is_block_end(text, next_word_norm=''):
    text = text.strip()
    if BLOCK_MARK.match(text) or PHONETIC_LINE.match(text) or GARBAGE.match(text):
        return True
    if text.startswith(('字根', '词根')):
        return True
    if SINGLE_WORD.match(text) and len(text) <= 13:
        return True
    # 下一词条开始行（词条单词可能与其音标/释义在同一 OCR 行）
    if next_word_norm and len(next_word_norm) >= 4:
        line_norm = norm(text)
        if line_norm.startswith(next_word_norm[:6]) or (
                len(line_norm) < 30 and next_word_norm[:5] in line_norm):
            return True
        if len(line_norm) <= 16 and SequenceMatcher(None, next_word_norm, line_norm).ratio() > 0.7:
            return True
    return False


def extract_translation(lines, target):
    """lines: 例句起至块结束的行文本列表；从例句结束位置之后提取中文"""
    joined = ''.join(lines)
    joined_norm = norm(joined)
    # 建立 norm 索引 -> 原文索引 映射
    index_map = []
    for orig_i, ch in enumerate(joined):
        if re.match(r'[a-z0-9]', ch.lower()):
            index_map.append(orig_i)
    if not index_map:
        return ''
    # 例句在 joined_norm 中的近似结束位置
    sm = SequenceMatcher(None, target, joined_norm)
    blocks = [b for b in sm.get_matching_blocks() if b.size > 0]
    if not blocks:
        return ''
    end_norm = blocks[-1].b
    orig_end = index_map[min(end_norm, len(index_map) - 1)]
    rest = joined[orig_end:]
    m = CJK.search(rest)
    if not m:
        return ''
    trans = rest[m.start():]
    # 去掉尾部可能混入的下一词条英文，只保留中文/数字/常用符号
    trans = re.sub(r'[^\u4e00-\u9fff\u3001\u3002\uff0c\uff1b\uff1a\uff1f\uff01a-zA-Z0-9%.\'\s]+', '', trans)
    # 截断到 [记]/[搭] 等 marker（防止混入拓展内容）
    cut = MARKER_IN_TEXT.search(trans)
    if cut:
        trans = trans[:cut.start()]
    cut = re.search(r'字根|词根', trans)
    if cut:
        trans = trans[:cut.start()]
    return trans.strip(' 。,.')


def main():
    entries = load_entries()
    seq = build_lines()
    norm_lines = [norm(l['text']) for l in seq]

    translations = {}
    ptr = 0
    matched_count = 0
    misses = []
    for idx, entry in enumerate(entries):
        example = entry['example']
        if not example or example == '-':
            continue
        target = norm(example)
        if len(target) < 10:
            continue
        best = (0.0, -1, -1)
        window_end = min(ptr + 600, len(seq))
        for i in range(ptr, window_end):
            for span in (2, 3, 1):
                if i + span > len(seq):
                    continue
                joined = ''.join(norm_lines[i:i + span])
                if not joined:
                    continue
                if abs(len(joined) - len(target)) > max(len(joined), len(target)) * 0.5:
                    continue
                ratio = SequenceMatcher(None, target, joined[:len(target) + 30]).quick_ratio()
                if ratio < 0.55 and ratio < best[0]:
                    continue
                ratio = SequenceMatcher(None, target, joined[:len(target) + 30]).ratio()
                if ratio > best[0]:
                    best = (ratio, i, i + span)
                if ratio > 0.92:
                    break
            if best[0] > 0.92:
                break
        ratio, ms, me = best
        if ms < 0 or ratio < 0.6:
            misses.append({'word': entry['word'], 'example': example, 'reason': f'no match (best={ratio:.2f})'})
            continue
        match_page = seq[ms]['page']
        next_word_norm = norm(entries[idx + 1]['word']) if idx + 1 < len(entries) else ''
        block_end = me
        for j in range(me, min(me + 5, len(seq))):
            text = seq[j]['text'].strip()
            if j > me and is_block_end(text, next_word_norm):
                break
            block_end = j + 1
        lines = [seq[k]['text'] for k in range(ms, block_end)]
        trans = extract_translation(lines, target)
        if trans:
            matched_count += 1
            translations[target] = trans
        else:
            misses.append({'word': entry['word'], 'example': example,
                           'reason': f'match but no CJK (ratio={ratio:.2f})', 'page': match_page})
        ptr = me

    json.dump(translations, open('translations.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2, sort_keys=True)
    json.dump(misses, open('_misses.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    total = sum(1 for e in entries if e['example'] and e['example'] != '-')
    print(f'总词条(有例句): {total}')
    print(f'成功提取翻译: {matched_count}')
    print(f'失败: {len(misses)}')


if __name__ == '__main__':
    main()
