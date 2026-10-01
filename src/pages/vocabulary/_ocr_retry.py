"""用原始分辨率（2400px）重新 OCR 指定页，恢复 _ocr_pages.json。"""
import json

import numpy as np
import pymupdf
from rapidocr_onnxruntime import RapidOCR

PDF = r"d:\linxingyang\note\3\学习\当下\正在学习\2026-09-30-刘洪波《IELTS雅思词汇真经》\assets\IELTS雅思词汇真经 (刘洪波) (Z-Library).pdf"

pages = [59, 60, 69, 74, 79, 80, 142, 279]
ocr = RapidOCR()
data = json.load(open('_ocr_pages.json', encoding='utf-8'))
doc = pymupdf.open(PDF)
for p in pages:
    page = doc[p]
    zoom = 2400 / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        arr = arr[:, :, :3]
    result, _ = ocr(arr)
    lines = [{'x': int(b[0][0]), 'y': int(b[0][1]), 'text': t} for b, t, *rest in (result or [])]
    data[str(p)] = lines
    print(f'page {p}: {len(lines)} 行')

json.dump(data, open('_ocr_pages.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('done')
