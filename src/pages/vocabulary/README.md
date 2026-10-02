# 说明

由于词汇的输入主要来源于手打，为了方便手工输入做成了特殊格式 `vocabulary.txt`。但是最终页面上使用的是 `vocabulary.js`，其中的提取和转换通过 `parser.py` 实现。修改、编辑词汇的流程如下：

1. 编辑 `vocabulary.txt`
2. 执行（先切换目录到当前目录）提取和转换 `python parser.py`，自动生成 `vocabulary.js` 文件，不要手工编辑 `vocabulary.js` 文件

## 词汇分类（词库）

`vocabulary.txt` 的章节标题支持 `名称|source` 后缀，标记所属词库；无后缀默认 `ielts`。各词库在 `vocabulary.js` 中带 `source` 字段，编号独立（都从 01 开始）：

| source | 词库 | 章节 |
|---|---|---|
| `ielts` | 雅思词汇真经 | 22 章（场景词） |
| `cet4` | 四级词汇 | 按字母序 A~Z（无词的字母跳过） |
| `cet6` | 六级词汇（含四级词） | 按字母序 A~Z |
| `awl` | AWL 学术词汇 | 官方子表 1~10 |

页面（`index.vue` / `typing.vue`）通过 `~/composables/vocabularyCategory` 提供分类 + 章节两级下拉。**学习状态按单词全局共享**：一个词在任何词库标记"认识"后，其他词库同步生效。

## 四级 / 六级 / AWL 词表管线

数据来源：

- 四级：`CET4_2.json`（有道"四级英语词汇"，3739 词）
- 六级：`CET6_2.json` ∪ `CET6_3.json` ∪ 四级（六级大纲包含四级，合并后 5964 词）
- AWL：`awl_words.json`（Academic Word List，554 词条，按官方子表分组）

原始数据缓存在 `_cet_source/`，由 `_fetch_wordlists.py` 从 GitHub `kajweb/dict` 等开源仓库下载。

生成流程（当前目录下执行）：

1. `python _fetch_wordlists.py`：下载并解包词表（可重复运行，已有文件跳过）
2. `python _build_wordlists.py`：生成 `vocabulary.txt` 追加章节 + 补充 `translations.json`
   - 词在真经中已存在 → **整行复用**真经词条（例句/翻译/note 沿用）
   - 新词用词库自带例句+翻译；缺失时走有道 blng 双语例句补
   - AWL 中文释义走有道 ec 词典补（缓存在 `_convert_cache.json`）
   - 幂等：重新运行会先删除旧的生成章节再重新生成；无例句清单在 `_missing_examples.txt`
3. `python _prefill_phonetics.py`：用词表自带音标预填充 `phonetics.json`（可选，减少有道查询）
4. `python parser.py`：重新生成 `vocabulary.js`

## 单词音频（共享池模式）

目录结构（总共约 6900 个 mp3、560MB）：

- `public/vocabulary/audio/<01~22_真经章节>/<词>.mp3`：真经原书真人发音，保持原位
- `public/vocabulary/audio/_shared/<词>.mp3`：四级/六级/AWL 词的有道 TTS 美音，**每个词只存一份**（四六级重叠词、与真经重叠词不重复存放）

前端通过 `src/pages/vocabulary/audioIndex.json`（由 `_fetch_audio.py` 生成，`~/composables/vocabularyCategory` 的 `wordAudioUrl()` 消费）解析单词 → 音频路径；索引缺失时自动在线兜底有道 `dictvoice`，不会 404。

维护：

- 新增词条后运行 `python _fetch_audio.py`：增量下载缺失音频到 `_shared/` 并重新生成索引（幂等、断点续跑，失败清单在 `_missing_audio.json`）
- 旧版"按章节目录存放"的四/六/AWL 音频目录已废弃并自动清理




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


