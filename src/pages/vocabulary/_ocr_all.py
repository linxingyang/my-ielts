"""OCR 全部 PDF 页面，输出 _ocr_pages.json（断点续跑）。"""
import json
import os
import time
from multiprocessing import Pool

PDF = r"d:\linxingyang\note\3\学习\当下\正在学习\2026-09-30-刘洪波《IELTS雅思词汇真经》\assets\IELTS雅思词汇真经 (刘洪波) (Z-Library).pdf"
OUT = '_ocr_pages.json'
PAGE_COUNT = 336

_ocr = None
_doc = None


def init_worker():
    global _ocr, _doc, pymupdf
    from rapidocr_onnxruntime import RapidOCR
    import pymupdf
    _ocr = RapidOCR()
    _doc = pymupdf.open(PDF)


def ocr_page(page_index):
    global _ocr, _doc
    cache_file = f'_ocr_cache/page_{page_index:03d}.json'
    if os.path.exists(cache_file):
        with open(cache_file, encoding='utf-8') as f:
            return page_index, json.load(f)
    import numpy as np
    page = _doc[page_index]
    zoom = 2400 / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        arr = arr[:, :, :3]
    result, _ = _ocr(arr)
    lines = []
    for item in (result or []):
        box, text = item[0], item[1]
        lines.append({
            'x': int(box[0][0]),
            'y': int(box[0][1]),
            'text': text,
        })
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(lines, f, ensure_ascii=False)
    return page_index, lines


if __name__ == '__main__':
    os.makedirs('_ocr_cache', exist_ok=True)
    done = set()
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            data = json.load(f)
        done = set(int(k) for k in data)
    todo = [i for i in range(PAGE_COUNT) if i not in done]
    print(f'待 OCR 页数: {len(todo)}')
    t0 = time.time()
    workers = min(8, os.cpu_count() or 4)
    print(f'workers: {workers}')
    all_data = {}
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            all_data = json.load(f)
    with Pool(workers, initializer=init_worker) as pool:
        for n, (page_index, lines) in enumerate(pool.imap_unordered(ocr_page, todo), 1):
            all_data[str(page_index)] = lines
            if n % 10 == 0 or n == len(todo):
                with open(OUT, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False)
                speed = n / (time.time() - t0)
                print(f'进度: {n}/{len(todo)}  预计剩余 {((len(todo) - n) / speed) / 60:.0f} 分钟', flush=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False)
    print('完成')
