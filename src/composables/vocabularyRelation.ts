import { VOCAB_SOURCES } from './vocabularyCategory'
import { VOCAB_MANIFEST, getChapterData, touchVocabularyData } from './vocabularyData'
import relationGroupsData from '~/pages/vocabulary/relationGroups'

/** relationGroups.js 中的关联组结构 */
interface RelationGroup { type: string; root?: string; words: string[] }

export interface RelationRef { t: string; w: string; r?: string }

export interface ResolvedRelation {
  type: string
  typeLabel: string
  tagClass: string
  word: string
  root?: string
  /** 目标词释义与位置，供行内标签点击跳转 */
  meaning: string
  pos: string
  id: number
  chapter: string
  source: string
  sourceLabel: string
}

export interface RelationGroupItem {
  type: string
  typeLabel: string
  tagClass: string
  root: string
  /** 组内词的解析结果（词库中不存在的词已剔除） */
  members: ResolvedRelation[]
}

export interface WordLocation {
  item: any
  chapter: string
  source: string
  sourceLabel: string
}

// 关联类型元信息：中文标签 + 标签配色（左边框/文字色，仅亮色模式有底色，暗色模式纯文字色）
export const RELATION_TYPE_META: Record<string, { label: string; tagClass: string }> = {
  root: {
    label: '词根',
    tagClass: 'border-l-2 border-blue-600 text-blue-600 bg-blue-50 dark:bg-transparent dark:text-blue-400',
  },
  syn: {
    label: '同义',
    tagClass: 'border-l-2 border-green-600 text-green-600 bg-green-50 dark:bg-transparent dark:text-green-400',
  },
  ant: {
    label: '反义',
    tagClass: 'border-l-2 border-red-600 text-red-600 bg-red-50 dark:bg-transparent dark:text-red-400',
  },
  der: {
    label: '派生',
    tagClass: 'border-l-2 border-purple-600 text-purple-600 bg-purple-50 dark:bg-transparent dark:text-purple-400',
  },
  sim: {
    label: '形近',
    tagClass: 'border-l-2 border-orange-500 text-orange-500 bg-orange-50 dark:bg-transparent dark:text-orange-400',
  },
}

// 词形（含变体）→ 词条位置 的解析索引：随词库加载按版本号重建（数据为普通对象，重建仅需几十毫秒）。
// 未加载词库的词暂不可解析，切换到对应词库（触发加载）后自动补全
const WORD_INDEX = computed(() => {
  touchVocabularyData()
  const map = new Map<string, WordLocation>()
  for (const meta of Object.values(VOCAB_MANIFEST.chapters)) {
    const ch = getChapterData(meta.label)
    if (!ch)
      continue
    const sourceLabel = VOCAB_SOURCES.find(s => s.key === meta.source)?.label || meta.source
    for (const group of ch.words as any[][]) {
      for (const item of group as any[]) {
        for (const w of item.word as string[]) {
          const key = w.toLowerCase().trim()
          if (!map.has(key))
            map.set(key, { item, chapter: meta.label, source: meta.source, sourceLabel })
        }
      }
    }
  }
  return map
})

/** 查找一个单词的词条位置（跨词库首次出现） */
export function lookupWord(word: string): WordLocation | undefined {
  return WORD_INDEX.value.get(word.toLowerCase().trim())
}

/** 把词条的 relations 字段解析为带目标词信息的关联列表（目标词缺失时跳过） */
export function resolveRelations(item: any): ResolvedRelation[] {
  const relations: RelationRef[] = item.relations || []
  const index = WORD_INDEX.value
  const resolved: ResolvedRelation[] = []
  for (const r of relations) {
    const loc = index.get(r.w)
    if (!loc)
      continue
    const meta = RELATION_TYPE_META[r.t]
    resolved.push({
      type: r.t,
      typeLabel: meta?.label || r.t,
      tagClass: meta?.tagClass || '',
      word: r.w,
      root: r.r,
      meaning: loc.item.meaning,
      pos: loc.item.pos,
      id: loc.item.id,
      chapter: loc.chapter,
      source: loc.source,
      sourceLabel: loc.sourceLabel,
    })
  }
  return resolved
}

/** 全部关联组（手工精选词根族 + Moby 同义聚类），已解析组内词信息（响应式） */
export const resolvedRelationGroups = computed<RelationGroupItem[]>(() => {
  const index = WORD_INDEX.value
  return (relationGroupsData as RelationGroup[])
    .map((g) => {
      const meta = RELATION_TYPE_META[g.type] || { label: g.type, tagClass: '' }
      const members = (g.words as string[])
        .map(w => index.get(w))
        .filter(loc => !!loc)
        .map(loc => ({
          type: g.type,
          typeLabel: meta.label,
          tagClass: meta.tagClass,
          word: loc!.item.word[0],
          meaning: loc!.item.meaning,
          pos: loc!.item.pos,
          id: loc!.item.id,
          chapter: loc!.chapter,
          source: loc!.source,
          sourceLabel: loc!.sourceLabel,
        }))
      return { type: g.type, typeLabel: meta.label, tagClass: meta.tagClass, root: g.root || '', members }
    })
    .filter(g => g.members.length >= 2)
})
