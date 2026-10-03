import { VOCAB_SOURCES } from './vocabularyCategory'
import { VOCAB_MANIFEST, getChapterData, isSourceLoaded, touchVocabularyData } from './vocabularyData'

export interface VocabSearchItem {
  id: number
  word: string[]
  pos: string
  meaning: string
  phonetic?: string
  example?: string
  translation?: string
  note?: string
}

export interface VocabSearchResult {
  source: string
  sourceLabel: string
  chapter: string
  /** 已加载词库的完整词条（全文搜索结果） */
  item?: VocabSearchItem
  /** 未加载词库的纯词串结果（清单单词匹配），点击时按需加载后跳转 */
  word?: string
}

// 扁平索引：随词库加载按版本号重建（数据为普通对象，无深层依赖追踪，重建仅需几十毫秒）
const FLAT_INDEX = computed(() => {
  touchVocabularyData()
  const out: { item: VocabSearchItem; chapter: string; source: string; sourceLabel: string }[] = []
  for (const meta of Object.values(VOCAB_MANIFEST.chapters)) {
    const ch = getChapterData(meta.label)
    if (!ch)
      continue
    const sourceLabel = VOCAB_SOURCES.find(s => s.key === meta.source)?.label || meta.source
    for (const group of ch.words as any[][]) {
      for (const item of group as VocabSearchItem[])
        out.push({ item, chapter: meta.label, source: meta.source, sourceLabel })
    }
  }
  return out
})

/** 未加载词库的清单单词匹配（纯词串，成本仅几毫秒） */
function searchManifest(keyword: string, kwLower: string): { entry: VocabSearchResult; score: number }[] {
  const out: { entry: VocabSearchResult; score: number }[] = []
  for (const meta of Object.values(VOCAB_MANIFEST.chapters)) {
    if (isSourceLoaded(meta.source))
      continue // 已加载的库走全文搜索，避免重复
    const sourceLabel = VOCAB_SOURCES.find(s => s.key === meta.source)?.label || meta.source
    for (const w of meta.wordList) {
      const lower = w.toLowerCase()
      let score = -1
      if (lower === kwLower)
        score = 0
      else if (lower.startsWith(kwLower))
        score = 1
      else if (lower.includes(kwLower))
        score = 2
      if (score >= 0)
        out.push({ entry: { source: meta.source, sourceLabel, chapter: meta.label, word: w }, score })
    }
  }
  return out
}

/**
 * 跨词库全局搜索词汇。
 * 已加载词库：匹配单词、中文释义/翻译/笔记、英文例句（全文）。
 * 未加载词库：仅匹配单词本身（基于清单纯词串，无需加载全量数据），点击结果时按需加载。
 * 排序：单词精确匹配 > 前缀匹配 > 包含匹配 > 文本字段匹配。
 * @param keyword 关键词（英文单词或中文释义）
 * @param limit 最多返回的结果条数
 */
export function searchVocabulary(keyword: string, limit = 20): { results: VocabSearchResult[]; total: number } {
  const kw = keyword.trim()
  if (!kw)
    return { results: [], total: 0 }
  const kwLower = kw.toLowerCase()

  function scoreOf(item: VocabSearchItem): number {
    const words: string[] = item.word.map((w: string) => w.toLowerCase())
    if (words.includes(kwLower))
      return 0
    if (words.some(w => w.startsWith(kwLower)))
      return 1
    if (words.some(w => w.includes(kwLower)))
      return 2
    return 3
  }

  const matched: { entry: VocabSearchResult; score: number }[] = []
  for (const { item, chapter, source, sourceLabel } of FLAT_INDEX.value) {
    if (scoreOf(item) < 3
      || (item.meaning || '').includes(kw)
      || (item.translation || '').includes(kw)
      || (item.note || '').includes(kw)
      || (item.example || '').toLowerCase().includes(kwLower))
      matched.push({ entry: { item, chapter, source, sourceLabel }, score: scoreOf(item) })
  }
  matched.push(...searchManifest(kw, kwLower))

  matched.sort((a, b) => a.score - b.score)
  return {
    results: matched.map(x => x.entry).slice(0, limit),
    total: matched.length,
  }
}
