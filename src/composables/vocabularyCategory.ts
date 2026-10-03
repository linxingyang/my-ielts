import { VOCAB_MANIFEST } from './vocabularyData'
import audioIndex from '~/pages/vocabulary/audioIndex.json'

export interface VocabSource { key: string; label: string; desc: string }

const AUDIO_INDEX = audioIndex as Record<string, string>

// 单词发音地址：优先本地音频索引（真经真人发音 → 共享池 TTS），缺失时在线兜底有道 TTS
export function wordAudioUrl(word: string): string {
  const w = word.trim()
  return AUDIO_INDEX[w.toLowerCase()] || `https://dict.youdao.com/dictvoice?type=1&audio=${encodeURIComponent(w)}`
}

// 各词库的展示信息（label/desc 仅前端展示；可用词库列表以构建产物 vocabulary-index.json 为准，
// 未来新增词表只需跑构建脚本 + 在此补充 label/desc）
const SOURCE_META: Record<string, { label: string; desc: string }> = {
  ielts: { label: '雅思词汇真经', desc: '雅思核心词 · 逻辑词群记忆法' },
  cet4: { label: '四级词汇', desc: '大学英语四级词汇' },
  cet6: { label: '六级词汇', desc: '大学英语六级词汇（含四级词）' },
  awl: { label: 'AWL 学术词汇', desc: 'Academic Word List · 雅思读写高频' },
  oxford5000: { label: '牛津 5000', desc: 'Oxford 5000 核心词 · CEFR A1~C1 分级' },
  ngsl: { label: 'NGSL 高频词', desc: '通用高频词 2801 · 按频率分段' },
  nawl: { label: 'NAWL 学术词', desc: 'NAWL 新学术词汇表（AWL 新版）· 按频率分段' },
}

export const VOCAB_SOURCES: VocabSource[] = VOCAB_MANIFEST.sources
  .map(key => ({ key, ...(SOURCE_META[key] || { label: key, desc: '' }) }))

const SOURCE_KEY = 'vocabulary_source'
const chapters = Object.keys(VOCAB_MANIFEST.chapters)

/**
 * 词汇分类 + 章节两级联动选择。
 * @param chapterKey localStorage 中保存章节选择的 key（各页面独立）
 */
export function useVocabularyCategory(chapterKey: string) {
  const storedSource = localStorage.getItem(SOURCE_KEY) || 'ielts'
  const source = ref(VOCAB_SOURCES.some(s => s.key === storedSource) ? storedSource : VOCAB_SOURCES[0].key)

  const storedChapter = localStorage.getItem(chapterKey) || ''
  const category = ref(VOCAB_MANIFEST.chapters[storedChapter] ? storedChapter : chapters[0])

  const sourceOptions = VOCAB_SOURCES
  const chapterOptions = computed(() =>
    chapters.filter(k => VOCAB_MANIFEST.chapters[k]?.source === source.value))
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
