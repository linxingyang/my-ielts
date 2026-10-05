# 说明

由于词汇的输入主要来源于手打，为了方便手工输入做成了特殊格式 `vocabulary.txt`。页面使用的是由 `parser.py` 生成的拆分数据文件（`vocabulary-index.json` + `vocabulary-<source>.js` + `relationGroups.js`）。修改、编辑词汇的流程如下：

1. 编辑 `vocabulary.txt`
2. 执行（先切换目录到当前目录）提取和转换 `python parser.py`，自动生成数据文件，不要手工编辑任何生成文件

## 词汇分类（词库）

`vocabulary.txt` 的章节标题支持 `名称|source` 后缀，标记所属词库；无后缀默认 `ielts`。各词库在生成数据中带 `source` 字段，编号独立（都从 01 开始）：

| source | 词库 | 章节 |
|---|---|---|
| `ielts` | 雅思词汇真经 | 22 章（场景词） |
| `cet4` | 四级词汇 | 按字母序 A~Z（无词的字母跳过） |
| `cet6` | 六级词汇（含四级词） | 按字母序 A~Z |
| `awl` | AWL 学术词汇 | 官方子表 1~10 |
| `oxford5000` | 牛津 5000 | 按 CEFR 等级 A1~C1 |
| `ngsl` | NGSL 高频词（2800） | 按频率分段 1-1000 / 1001-2000 / 2001-2801 |
| `nawl` | NAWL 学术词（959） | 按频率每 250 词一段 |
| `opal` | OPAL 学术词汇 | 单词 / 短语两章（按是否含空格划分） |

页面（`index.vue` / `typing.vue`）通过 `~/composables/vocabularyCategory` 提供分类 + 章节两级下拉。**学习状态按单词全局共享**：一个词在任何词库标记"认识"后，其他词库同步生效。

## 数据文件结构（拆分产物）

`parser.py` 生成以下文件（**全部禁止手工编辑**）：

- `vocabulary-index.json`：清单（词库列表 + 章节元信息 + 每章纯词串列表）。体积小，打开页面即加载；章节/词库/全库统计只依赖它，还为未加载词库提供"仅单词"搜索
- `vocabulary-<source>.js`：每个词库一个全量数据文件（ielts/cet4/cet6/awl/oxford5000/ngsl/nawl 各一）。前端**只按需加载当前选中的词库**（`dynamic import`），切换词库时加载对应文件；搜索命中未加载词库时点击结果再加载
- `relationGroups.js`：关联组数据，供「关联组」视图（独立小文件，常驻加载）

性能注意：章节数据是有意设计的**普通对象**（非 Vue reactive），两万+ 词条做深层响应式代理会严重卡顿；数据到达通过 `vocabularyDataVersion`（shallowRef）版本号通知 computed 重算（`composables/vocabularyData.ts`）。

学习进度（`wordStatus.ts`）按单词字符串全局存储，与数据文件结构无关。

## 词表管线（四级/六级/AWL/牛津5000/NGSL/NAWL/OPAL）

数据来源（原始数据缓存在 `_cet_source/`）：

- 四级：`CET4_2.json`（有道"四级英语词汇"，3739 词）
- 六级：`CET6_2.json` ∪ `CET6_3.json` ∪ 四级（六级大纲包含四级，合并后 5964 词）
- AWL：`awl_words.json`（Academic Word List，572 词条，按官方子表分组）
- 牛津 5000：`oxford5k_raw.csv`（GitHub `nalgeon/words`，含 CEFR 等级与词性；同词多词性取最低等级）
- NGSL / NAWL：`NGSL_101_SFI.xlsx`（官方 NGSL 1.01 SFI 表，含 NGSL 2801 词与 NAWL 959 词及频率排名）
- OPAL：`oxford_opal.csv`（牛津学习者词典官方 OPAL 词表，GitHub `nalgeon/words` 镜像，含单词与学术短语）

生成流程（当前目录下执行）：

1. `python _fetch_wordlists.py`：下载并解包词表（可重复运行，已有文件跳过）
2. `python _build_wordlists.py`：生成 `vocabulary.txt` 追加章节 + 补充 `translations.json`
   - 词在真经中已存在 → **整行复用**真经词条（例句/翻译/note 沿用）
   - 新词用词库自带例句+翻译；缺失时走有道 blng 双语例句补
   - 各表不带中文释义时（AWL/牛津5000/NGSL/NAWL）走有道 ec 词典补（缓存在 `_convert_cache.json`）
   - 幂等：重新运行会先删除旧的生成章节再重新生成；无例句清单在 `_missing_examples.txt`
3. `python _prefill_phonetics.py`：用词表自带音标预填充 `phonetics.json`（可选，减少有道查询）
4. `python parser.py`：重新生成拆分数据文件（见上节）

## 单词音频（共享池模式，美/英双口音）

目录结构：

- `public/vocabulary/audio/<01~22_真经章节>/<词>.mp3`：真经原书真人发音，保持原位（索引 `book` 键，左侧大喇叭专用）
- 章节整读 mp3（原 `01_自然地理.mp3` 等 22 个，246MB）已移除：GitHub Pages 发布大体量站点时会截断后续目录，导致英/美 TTS 文件 404。页面改为「原书连读/英音连读/美音连读」按钮逐词连播
- `public/vocabulary/audio/_shared_us/<词>.mp3`：全部词库（含真经词）的有道 TTS **美音**（`dictvoice type=2`，默认口音）
- `public/vocabulary/audio/_shared_uk/<词>.mp3`：同上的有道 TTS **英音**（`dictvoice type=1`）

每个词每个口音只存一份（四六级重叠词、与真经重叠词不重复存放）。页面单词行有两个播放入口：左侧大喇叭仅有真经原书音频的词显示（真经词及其他词库中源自真经的词），播放原书真人发音；每行音标（UK/US）前各有小喇叭，点哪行播哪国口音。`wordAudioUrl(word, prefer?)` 不传口音时优先原书音频、否则跟随全局口音设置（默认美音，与口语页共用）。

前端通过 `src/pages/vocabulary/audioIndex.json`（由 `_fetch_audio.py` 生成，`~/composables/vocabularyCategory` 的 `wordAudioUrl()` / `wordHasBookAudio()` 消费）解析单词 → `{us, uk, book?}` 音频路径；指定口音缺失时在线兜底该口音的有道 `dictvoice`，不会 404。

维护：
- 新增词条后运行 `python _fetch_audio.py`：增量下载缺失音频到对应口音池并重新生成索引（幂等、断点续跑，失败清单在 `_missing_audio.json`）
- 历史兼容：旧 `_shared/` 里的文件当初以 type=1（英音）下载，脚本首次运行会自动整体迁入 `_shared_uk/`




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

## 单词关联词（relations）

每个词条在 `vocabulary.js` 中带可选 `relations` 字段（`[{t, w, r?}]`，t 为类型缩写，w 为关联词，r 为词根说明），页面在词条行内显示彩色标签（点击跳转高亮），另有「关联组」视图按组成组学习。关联分五类：

| t | 类型 | 来源 | 文件 |
|---|---|---|---|
| `root` | 词根 | 手工精选词根族 | `relations.json` |
| `syn` | 同义 | 手工精选组 + Moby Thesaurus II 自动聚类 | `relations.json` + `relations_auto.json` |
| `ant` | 反义 | Datamuse API 抓取 | `_antonyms.json`（增量缓存） |
| `der` | 派生 | 有道 rel_word 字段抓取 | `_derivations.json`（增量缓存） |
| `sim` | 形近 | parser.py 构建时自动计算（前 2 字母相同 + 相似度 ≥ 0.82） | 无需数据文件 |

生成流程（当前目录下执行）：

1. `python _fetch_relations.py`：下载 Moby Thesaurus（缓存 `_moby/`）+ 同义聚类生成 `relations_auto.json` + 增量抓取反义词/派生词（幂等断点续跑，网络失败下次重试）
2. （可选）编辑 `relations.json` 手工补充关联组，格式：`[{"type": "root|synonym|antonym", "root": "词根说明（仅 root 组）", "words": [...]}]`
3. `python parser.py`：合并三层关联数据（手工优先、同对词去重），组内两两双向生成，写进 `vocabulary.js`（含 `relationGroups` 导出，供关联组视图）

注意：全部外部数据获取都在构建期完成并有缓存，站点为纯静态部署、运行时零外部依赖。手工/自动组中词库外词汇会在合并时警告跳过；`_gen_manual_relations.py` 可重新生成分步的手工种子组（`--force` 覆盖手工编辑）。

## 词条完整内容（note）

页面上每条例句下方的完整书本内容（例句译文、【记】记忆法、【搭】搭配、词源故事等，即书中该词条从例句起直到下一词条之前的全部文字），同样提取自原书 PDF：

- 由 `_extract_full.py` 从 `_ocr_pages.json` 提取，输出 `notes.json`（key 为单词的小写字母数字归一化形式，失败清单在 `_full_misses.json`）
- 提取逻辑：先按例句模糊匹配定位词条，再向后扫描到下一词条开头（跨页自动拼接）；以下一词条例句的起点为硬边界防止吞并下一词条
- 修改后重新执行 `python _extract_full.py`，再执行 `python parser.py` 重新生成 `vocabulary.js`
- 个别词条内容有误时，可直接在 `notes.json` 中手工修正该词的值（兜底路线的 20 多个词条因 OCR 质量差可能有残缺）


