"""从 OCR 结果中按词表顺序提取每个词条的完整书本内容（例句译文、【记】、【搭】等，直到下一词条），输出 notes.json。

复用 _extract_trans.py 的行重排与匹配机制，但不做 marker 截断，块结束扫描不受 5 行限制。
"""
import json
import re
from difflib import SequenceMatcher

from _extract_trans import (CJK, GARBAGE, PHONETIC_LINE, SINGLE_WORD,
                            build_lines, load_entries, norm)

# 保留字符：中英文、数字、常用中英文标点与符号（→ + % 等）
KEEP = re.compile(r'[^\u4e00-\u9fff\u3000-\u303fA-Za-z0-9\s,.;:?!%\'"()\[\]/+-—×=·、。，；：？！（）《》“”‘’→]'
                  )
MAX_BLOCK_LINES = 60  # 单词条块的最大行数（防失控）


def find_example_span(norm_lines, target, ptr, max_window=600):
    """在 seq 中从 ptr 开始模糊匹配例句，返回 (ratio, start, end)，找不到返回 (0, -1, -1)"""
    best = (0.0, -1, -1)
    window_end = min(ptr + max_window, len(norm_lines))
    for i in range(ptr, window_end):
        for span in (2, 3, 1):
            if i + span > len(norm_lines):
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
            if ratio > 0.97:
                break
        if best[0] > 0.97:
            break
    return best


def find_headword(norm_lines, word_norm, ptr, max_window=400):
    """从 ptr 开始查找词条头部行，返回 (ratio, line_index)"""
    best = (0.0, -1)
    window_end = min(ptr + max_window, len(norm_lines))
    for i in range(ptr, window_end):
        line_norm = norm_lines[i]
        if not line_norm:
            continue
        # 词头行：以单词开头（后面可能跟音标/释义）
        ratio = SequenceMatcher(None, word_norm, line_norm[:len(word_norm) + 4]).quick_ratio()
        if ratio < 0.6:
            continue
        n = min(len(word_norm), len(line_norm))
        ratio = SequenceMatcher(None, word_norm[:n], line_norm[:n]).ratio()
        if ratio > best[0]:
            best = (ratio, i)
        if ratio > 0.9:
            break
    return best


def is_block_end_full(text, next_word_norm=''):
    """完整块模式的块结束判断：[记]/[搭]/[例] 标记行属于当前词条，不作为结束；
    仅以下一词条开头（独立单词行/音标行/下一词匹配）等为结束。
    纯符号/数字噪声行（页码等）由 scan_block_end 跳过，不在此判断。"""
    text = text.strip()
    if PHONETIC_LINE.match(text):
        return True
    if text.startswith(('字根', '词根')):
        return True
    if SINGLE_WORD.match(text) and len(text) <= 13:
        return True
    if next_word_norm and len(next_word_norm) >= 3:
        line_norm = norm(text)
        if line_norm.startswith(next_word_norm):
            return True
        if len(next_word_norm) >= 4 and (
                line_norm.startswith(next_word_norm[:6])
                or (len(line_norm) < 30 and line_norm.startswith(next_word_norm[:5]))):
            return True
        if len(line_norm) <= 16 and SequenceMatcher(None, next_word_norm, line_norm).ratio() > 0.7:
            return True
    return False


def join_block_lines(seq, ms, block_end):
    """拼接块内行文本，过滤页码/纯符号噪声行"""
    return ''.join(seq[k]['text'] for k in range(ms, block_end)
                   if not GARBAGE.match(seq[k]['text'].strip()))


def scan_block_end(seq, me, next_word_norm, ptr_next_hint=None):
    """从例句结束行 me 起向后扫描，返回块结束行号（不含）。
    不限制行数，直到命中下一词条开头/块标记/音标行等。"""
    limit = min(me + MAX_BLOCK_LINES, len(seq))
    block_end = me
    j = me
    while j < limit:
        text = seq[j]['text'].strip()
        if GARBAGE.match(text):
            j += 1  # 页码/纯符号噪声行：跳过，不结束也不收录
            continue
        if j >= me and is_block_end_full(text, next_word_norm):
            break
        block_end = j + 1
        j += 1
    return block_end


def strip_example_prefix(joined, target):
    """在块文本中定位例句结束位置，返回其后的内容；失败返回 None"""
    joined_norm = norm(joined)
    index_map = []
    for orig_i, ch in enumerate(joined):
        if re.match(r'[a-z0-9]', ch.lower()):
            index_map.append(orig_i)
    if not index_map:
        return None
    sm = SequenceMatcher(None, target, joined_norm)
    blocks = [b for b in sm.get_matching_blocks() if b.size > 0]
    if not blocks:
        return None
    # 匹配总量不足说明例句没有真正对齐上（如书中用 “12” 词表用 “Twelve”）
    if sum(b.size for b in blocks) < len(target) * 0.6:
        return None
    end_norm = blocks[-1].b + blocks[-1].size  # 例句在 joined_norm 中的结束位置
    if end_norm < len(target) * 0.6:
        return None
    orig_end = index_map[min(end_norm, len(index_map)) - 1] + 1  # 例句最后一个字符之后
    return joined[orig_end:]


def clean_note(text):
    """去掉保留字符集以外的 OCR 噪声，压缩空白"""
    text = KEEP.sub('', text)
    text = re.sub(r'\s+', '', text)  # 书本排版行连接处不留空格，与原提取逻辑一致
    return text.strip(' 。,.、')


def extract_by_example(seq, norm_lines, entry, next_word_norm, ptr):
    """例句匹配路线：返回 (note, new_ptr, matched)"""
    example = entry['example']
    if not example or example == '-':
        return '', ptr, False
    target = norm(example)
    if len(target) < 10:
        return '', ptr, False
    ratio, ms, me = find_example_span(norm_lines, target, ptr)
    if ms < 0 or ratio < 0.6:
        return '', ptr, False
    block_end = scan_block_end(seq, me, next_word_norm)
    joined = ''.join(seq[k]['text'] for k in range(ms, block_end))
    rest = strip_example_prefix(joined, target)
    if rest is None:
        return '', me, False
    return clean_note(rest), me, True


POS_DEF = re.compile(r'^\s*[ nvajdrt.\u4e00-\u9fff\uFF0C\uFF1B\uFF1A\u3001]+\s*$')  # 独立的 “n.小灾难” 释义行
PHONETIC = re.compile(r"^[\[\]Il1|/Ｉｌ\s]*/[^/]+/[\[\]Il1|]*$")


def extract_by_headword(seq, norm_lines, entry, next_word_norm, ptr):
    """兜底路线：直接定位词头行，取词头（含音标/释义行）之后到块结束的内容"""
    word_norm = norm(entry['word'])
    if len(word_norm) < 3:
        return '', ptr, False
    ratio, hi = find_headword(norm_lines, word_norm, ptr)
    if hi < 0 or ratio < 0.75:
        return '', ptr, False
    # 跳过词头行及其后的音标行/释义行
    start = hi + 1
    while start < len(seq):
        t = seq[start]['text'].strip()
        if PHONETIC_LINE := PHONETIC.match(t):
            start += 1
            continue
        if POS_DEF.match(t):
            start += 1
            continue
        break
    block_end = scan_block_end(seq, start, next_word_norm)
    # 词头行里可能已带释义甚至整个词条（OCR 合并行），先拼出完整文本
    head_text = seq[hi]['text'].strip()
    m = re.match(r'^[A-Za-z][A-Za-z\'\- ]*', head_text)
    first = head_text[m.end():] if m else head_text
    joined = first + join_block_lines(seq, hi + 1, block_end)
    target = norm(entry['example']) if entry['example'] and entry['example'] != '-' else ''
    if len(target) >= 10:
        # 优先按例句精确定位，跳过词头行残留的音标/释义
        rest = strip_example_prefix(joined, target)
        if rest:
            return clean_note(rest), max(hi + 1, start), True
    # 没有可用例句时，去掉开头残留的音标与词性释义
    joined = re.sub(r'^\s*/[^/]*/', '', joined)
    joined = re.sub(r'^\s*[nvadjrt]{1,2}\.\s*', '', joined)
    # 释义残片（如 “v.除以；除”后接正文）从首个 [例]/[记]/[搭] 标记处截取
    mm = re.search(r'[\[\uFF3B]\s*[例记搭链近]', joined)
    if mm and mm.start() < 20:
        joined = joined[mm.start():]
    return clean_note(joined), max(hi + 1, start), True


def is_headword_like(text, next_word_norm=''):
    """疑似下一词条的词头/音标/释义行（用于吞并分支的尾部剥除）"""
    text = text.strip()
    if PHONETIC_LINE.match(text) or POS_DEF.match(text):
        return True
    if SINGLE_WORD.match(text):
        return True
    # 词头+音标（可能带释义）混在一行，如 “piug /plAg/n.塞子”
    if len(text) < 70 and '/' in text and re.match(r'^[A-Za-z]', text):
        return True
    # OCR 损坏的词头行，如 “coed/;kau'ed/（=co-educational...”，按下一词模糊前缀判断
    if next_word_norm and len(next_word_norm) >= 3:
        t = norm(text)[:len(next_word_norm)]
        if t and SequenceMatcher(None, next_word_norm[:len(t)], t).ratio() > 0.6:
            return True
    # 损坏的音标行，如 “//svp/snp”（无中文的短符号行）
    if len(text) < 30 and not CJK.search(text) and re.match(r'^[/\[\]A-Za-z1-9Il\s\'.,()-]+$', text):
        return True
    return False


def main():
    entries = load_entries()
    seq = build_lines()
    norm_lines = [norm(l['text']) for l in seq]

    notes = {}
    misses = []
    ptr = 0
    spans = [None] * len(entries)  # 例句匹配跨度 (ms, me)
    ptrs = [0] * len(entries)

    # 第一遍：顺序定位所有例句跨度
    for idx, entry in enumerate(entries):
        ptrs[idx] = ptr
        example = entry['example']
        if not example or example == '-':
            continue
        target = norm(example)
        if len(target) < 10:
            continue
        ratio, ms, me = find_example_span(norm_lines, target, ptr)
        if ms >= 0 and ratio >= 0.6:
            spans[idx] = (ms, me)
            ptr = me

    # 第二遍：提取完整块；块边界受下一词条例句起始行约束，防止吞并
    n_example = n_fallback = 0
    for idx, entry in enumerate(entries):
        next_word_norm = norm(entries[idx + 1]['word']) if idx + 1 < len(entries) else ''
        span = spans[idx]
        if span:
            ms, me = span
            block_end = scan_block_end(seq, me, next_word_norm)
            # 下一词条的例句起点是硬边界
            next_ms = spans[idx + 1][0] if idx + 1 < len(entries) and spans[idx + 1] else None
            swallowed = next_ms is not None and block_end > next_ms
            if swallowed:
                block_end = next_ms
                # 剥除混入的下一词条词头/音标/释义行
                while block_end - 1 >= me and is_headword_like(seq[block_end - 1]['text'], next_word_norm):
                    block_end -= 1
            joined = join_block_lines(seq, ms, block_end)
            rest = strip_example_prefix(joined, norm(entry['example']))
            if rest is not None:
                note = clean_note(rest)
                n_example += 1
                ptr = me
            else:
                note = ''
                ptr = me
        else:
            # 兜底：按词头定位
            note, fb_ptr, ok2 = extract_by_headword(seq, norm_lines, entry, next_word_norm, ptrs[idx])
            if ok2:
                n_fallback += 1
                ptr = fb_ptr
            else:
                note = ''
                misses.append({'word': entry['word'], 'example': entry['example'][:60]})
        if note:
            notes.setdefault(norm(entry['word']), note)

    json.dump(notes, open('notes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2, sort_keys=True)
    json.dump(misses, open('_full_misses.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'总词条: {len(entries)}')
    print(f'例句路线成功: {n_example}')
    print(f'词头兜底成功: {n_fallback}')
    print(f'失败: {len(misses)}')


if __name__ == '__main__':
    main()
