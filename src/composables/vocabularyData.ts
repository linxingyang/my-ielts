import { shallowRef } from 'vue'
import manifest from '~/pages/vocabulary/vocabulary-index.json'

/** 章节元信息（来自构建产物 vocabulary-index.json，打开页面即加载） */
export interface VocabChapterMeta {
  label: string
  source: string
  /** 整章朗读音频文件名（仅真经章节有），空串表示无 */
  audio: string
  groupCount: number
  wordCount: number
  /** 纯词串列表（word[0]），供三态统计与跨词库单词搜索使用，无需加载全量数据 */
  wordList: string[]
}

export const VOCAB_MANIFEST = manifest as { sources: string[]; chapters: Record<string, VocabChapterMeta> }

/**
 * 已加载的全量章节数据。
 * 注意：故意使用普通对象而非 reactive —— 两万+词条做深层响应式代理会造成严重卡顿。
 * 数据变更通过 dataVersion 通知订阅方（computed 里读取一次即可感知）。
 */
const chapterStore: Record<string, any> = {}
const loadedSources = new Set<string>()
const pendingSources = new Set<string>()

/** 数据版本号：每加载完成一个词库 +1，搜索/关联索引据此重建 */
export const vocabularyDataVersion = shallowRef(0)

/** 在 computed 中调用以订阅数据版本（新词库加载完成后自动重算） */
export function touchVocabularyData(): number {
  return vocabularyDataVersion.value
}

// vite 静态分析 glob，每个词库文件独立分包
const chunks = import.meta.glob('~/pages/vocabulary/vocabulary-*.js') as Record<string, () => Promise<any>>

/** 加载一个词库的全量数据（幂等；完成后搜索/关联/统计自动生效） */
export async function loadVocabularySource(source: string): Promise<void> {
  if (loadedSources.has(source) || pendingSources.has(source))
    return
  pendingSources.add(source)
  try {
    const key = Object.keys(chunks).find(k => k.endsWith(`/vocabulary-${source}.js`))
    if (!key) {
      console.warn(`[vocabulary] 未找到词库数据文件: vocabulary-${source}.js`)
      return
    }
    const mod = await chunks[key]()
    for (const [label, chapter] of Object.entries<any>(mod.default))
      chapterStore[label] = chapter
    loadedSources.add(source)
    vocabularyDataVersion.value++
  }
  finally {
    pendingSources.delete(source)
  }
}

/** 章节全量数据（未加载完成时为 undefined，页面据此显示加载态）。返回原始对象，非响应式 */
export function getChapterData(label: string) {
  return chapterStore[label]
}

export function isSourceLoaded(source: string): boolean {
  return loadedSources.has(source)
}
