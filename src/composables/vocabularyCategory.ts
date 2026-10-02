import audioIndex from '~/pages/vocabulary/audioIndex.json'
import vocabulary from '~/pages/vocabulary/vocabulary'

export interface VocabSource { key: string; label: string; desc: string }

const AUDIO_INDEX = audioIndex as Record<string, string>

// 单词发音地址：优先本地音频索引（真经真人发音 → 共享池 TTS），缺失时在线兜底有道 TTS
export function wordAudioUrl(word: string): string {
  const w = word.trim()
  return AUDIO_INDEX[w.toLowerCase()] || `https://dict.youdao.com/dictvoice?type=1&audio=${encodeURIComponent(w)}`
}

// 词汇分类（词库）：与 vocabulary.js 中每章的 source 字段对应
export const VOCAB_SOURCES: VocabSource[] = [
  { key: 'ielts', label: '雅思词汇真经', desc: '涵盖雅思必备核心词，逻辑词群记忆法' },
  { key: 'cet4', label: '四级词汇', desc: '大学英语四级词汇，与雅思真经重叠词自动复用词条内容' },
  { key: 'cet6', label: '六级词汇', desc: '大学英语六级词汇（含四级词），学习进度与四级、真经互通' },
  { key: 'awl', label: 'AWL 学术词汇', desc: 'Academic Word List 学术词汇表，雅思阅读写作高频词' },
]

const SOURCE_KEY = 'vocabulary_source'
const chapters = Object.keys(vocabulary)

/**
 * 词汇分类 + 章节两级联动选择。
 * @param chapterKey localStorage 中保存章节选择的 key（各页面独立）
 */
export function useVocabularyCategory(chapterKey: string) {
  const storedSource = localStorage.getItem(SOURCE_KEY) || 'ielts'
  const source = ref(VOCAB_SOURCES.some(s => s.key === storedSource) ? storedSource : 'ielts')

  const storedChapter = localStorage.getItem(chapterKey) || ''
  const category = ref(chapters.includes(storedChapter) ? storedChapter : chapters[0])

  const sourceOptions = VOCAB_SOURCES
  const chapterOptions = computed(() =>
    chapters.filter(k => (vocabulary as any)[k]?.source === source.value))
  const sourceLabel = computed(() =>
    VOCAB_SOURCES.find(s => s.key === source.value)?.label || '')
  const sourceDesc = computed(() =>
    VOCAB_SOURCES.find(s => s.key === source.value)?.desc || '')

  function fixCategory() {
    if (!chapterOptions.value.includes(category.value))
      category.value = chapterOptions.value[0]
  }

  watch(source, () => {
    localStorage.setItem(SOURCE_KEY, source.value)
    // 切换词库后，若当前章节不属于该词库，切到该词库第一章
    fixCategory()
  })
  // 初始化校正（处理旧存储指向已不存在的章节）
  fixCategory()

  return { source, sourceOptions, category, chapterOptions, sourceLabel, sourceDesc }
}
