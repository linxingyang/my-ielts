import { VOCAB_SOURCES } from './vocabularyCategory'
import vocabulary from '~/pages/vocabulary/vocabulary'

export interface VocabSearchResult {
  source: string
  sourceLabel: string
  chapter: string
  item: {
    id: number
    word: string[]
    pos: string
    meaning: string
    phonetic?: string
    example?: string
    translation?: string
    note?: string
  }
}

// 启动时构建一次扁平索引：词条 → { 所属词库, 章节 }，供跨词库搜索
const FLAT_INDEX = Object.entries(vocabulary as Record<string, any>).flatMap(([chapter, ch]) =>
  (ch.words as any[]).flat().map(item => ({
    item,
    chapter,
    source: ch.source as string,
    sourceLabel: VOCAB_SOURCES.find(s => s.key === ch.source)?.label || ch.source,
  })))

/**
 * 跨词库全局搜索词汇。
 * 匹配字段：单词（不区分大小写）、中文释义/翻译/笔记、英文例句。
 * 排序：单词精确匹配 > 前缀匹配 > 包含匹配 > 文本字段匹配。
 * @param keyword 关键词（英文单词或中文释义）
 * @param limit 最多返回的结果条数
 */
export function searchVocabulary(keyword: string, limit = 20): { results: VocabSearchResult[]; total: number } {
  const kw = keyword.trim()
  if (!kw)
    return { results: [], total: 0 }
  const kwLower = kw.toLowerCase()

  function scoreOf(item: any): number {
    const words: string[] = item.word.map((w: string) => w.toLowerCase())
    if (words.includes(kwLower))
      return 0
    if (words.some(w => w.startsWith(kwLower)))
      return 1
    if (words.some(w => w.includes(kwLower)))
      return 2
    return 3
  }

  const matched = FLAT_INDEX.filter(({ item }) =>
    scoreOf(item) < 3
    || (item.meaning || '').includes(kw)
    || (item.translation || '').includes(kw)
    || (item.note || '').includes(kw)
    || (item.example || '').toLowerCase().includes(kwLower))

  const withScore = matched.map(entry => ({ entry, score: scoreOf(entry.item) }))
  withScore.sort((a, b) => a.score - b.score)

  return {
    results: withScore.map(x => x.entry).slice(0, limit),
    total: matched.length,
  }
}
