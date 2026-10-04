import { VOCAB_MANIFEST } from './vocabularyData'
import { accent, type Accent } from './accent'
import audioIndex from '~/pages/vocabulary/audioIndex.json'

export interface VocabSource { key: string; label: string; desc: string }

// 口音偏好：us/uk 为有道 TTS，book 为真经原书真人音频
export type AccentPref = Accent | 'book'

// 单词 → {us, uk, book?} 本地音频路径；兼容旧版纯字符串格式
const AUDIO_INDEX = audioIndex as Record<string, { us?: string; uk?: string; book?: string } | string>

// 该词是否有真经原书真人音频（决定单词行左侧大喇叭是否显示）
export function wordHasBookAudio(word: string): boolean {
  const entry = AUDIO_INDEX[word.trim().toLowerCase()]
  return !!entry && typeof entry !== 'string' && !!entry.book
}

// 单词发音地址：prefer 指定口音时优先取该口音的本地音频（无则在线兜底该口音）；
// 未指定时优先真经原书音频（与原有行为一致），否则跟随全局口音设置
// （缺失回落另一口音，索引也缺失时在线兜底有道 TTS：type=1 英音 / type=2 美音）
export function wordAudioUrl(word: string, prefer?: AccentPref): string {
  const w = word.trim()
  const entry = AUDIO_INDEX[w.toLowerCase()]
  if (entry) {
    if (typeof entry === 'string')
      return entry
    // 显式指定 book（左侧大喇叭）或未指定口音时，优先真经原书音频
    if ((prefer === 'book' || !prefer) && entry.book)
      return entry.book
    const acc: Accent = !prefer || prefer === 'book' ? accent.value : prefer
    const path = acc === 'uk' ? entry.uk : entry.us
    if (path)
      return path
    if (!prefer && (entry.uk || entry.us))
      return (entry.uk || entry.us)!
  }
  const type = prefer === 'uk' ? 1 : 2
  return `https://dict.youdao.com/dictvoice?type=${type}&audio=${encodeURIComponent(w)}`
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
  opal: { label: 'OPAL 学术词汇', desc: 'Oxford Phrasal Academic Lexicon · 学术单词与短语' },
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
