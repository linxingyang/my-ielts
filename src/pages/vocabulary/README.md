# 说明

由于词汇的输入主要来源于手打，为了方便手工输入做成了特殊格式 `vocabulary.txt`。但是最终页面上使用的是 `vocabulary.js`，其中的提取和转换通过 `parser.py` 实现。修改、编辑词汇的流程如下：

1. 编辑 `vocabulary.txt`
2. 执行（先切换目录到当前目录）提取和转换 `python parser.py`，自动生成 `vocabulary.js` 文件，不要手工编辑 `vocabulary.js` 文件

## 音标（读音）

音标不需要手工录入。`parser.py` 会自动从有道词典接口获取每个单词的英/美式音标，并缓存到 `phonetics.json`（`vocabulary.js` 中每个词条会带上 `phonetic` 字段，页面在单词下方显示）。

- `phonetics.json` 为增量缓存：值为 `''` 表示查询过但该词查不到音标，不会重复请求。
- 新增/修改单词后重新执行 `python parser.py`，只会请求缓存中没有的单词。
- 极少数查不到音标的词，可以在 `phonetics.json` 中手工补上该词的音标后重新执行 `python parser.py`。

## 例句翻译

例句的中文翻译**直接提取自原书 PDF**（《IELTS雅思词汇真经》扫描版），而非机器翻译。提取管线：

1. `_ocr_all.py`：用 RapidOCR 并行识别 PDF 全部 336 页（结果缓存在 `_ocr_cache/`，汇总到 `_ocr_pages.json`，支持断点续跑）
2. `_extract_trans.py`：将 OCR 行按"页→栏→行"重排后，与 `vocabulary.txt` 的例句按书序模糊匹配，提取例句后书本自带的中文翻译，输出 `translations.json`（失败清单在 `_misses.json`）
3. `parser.py` 生成 `vocabulary.js` 时按例句文本合并 `translation` 字段，页面在例句下方显示

- 覆盖率约 99%（3670 条例句中 3644 条提取成功）；失败的 26 条多为：词表例句与书中原句不一致、该书页面 OCR 质量差
- 翻译有误/缺失时，直接在 `translations.json` 中手工修改（key 为例句的小写字母数字归一化形式），改完重新执行 `python parser.py`

