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

## 词条完整内容（note）

页面上每条例句下方的完整书本内容（例句译文、【记】记忆法、【搭】搭配、词源故事等，即书中该词条从例句起直到下一词条之前的全部文字），同样提取自原书 PDF：

- 由 `_extract_full.py` 从 `_ocr_pages.json` 提取，输出 `notes.json`（key 为单词的小写字母数字归一化形式，失败清单在 `_full_misses.json`）
- 提取逻辑：先按例句模糊匹配定位词条，再向后扫描到下一词条开头（跨页自动拼接）；以下一词条例句的起点为硬边界防止吞并下一词条
- 修改后重新执行 `python _extract_full.py`，再执行 `python parser.py` 重新生成 `vocabulary.js`
- 个别词条内容有误时，可直接在 `notes.json` 中手工修正该词的值（兜底路线的 20 多个词条因 OCR 质量差可能有残缺）


