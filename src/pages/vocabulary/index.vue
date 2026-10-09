<!-- eslint-disable eslint-comments/no-unlimited-disable -->
<script setup generic="T extends any, O extends any">
import { VOCAB_SOURCES } from '~/composables/vocabularyCategory'
import {
  cycleWordStatus,
  exportWordStatus,
  getWordStatus,
  importWordStatus,
  setWordStatus,
  wordsProgress,
} from '~/composables/wordStatus'

const { source, sourceOptions, category, chapterOptions, sourceLabel, sourceDesc } = useVocabularyCategory('vocabulary_chapter')

const isTrainingModel = ref(false)
const isRelationView = ref(false)
const isShowMeaning = ref(true)
const isAutoPlayWordAudio = ref(true)
const isOnlyShowErrors = ref(false)
const isFinishTraining = ref(false)
const isShowSource = ref(false)

const trainingStats = ref('')

// 全局搜索：输入防抖后跨词库搜索，结果展示在搜索框下方下拉面板
const searchInputRef = ref(null)
const searchKeywordRaw = ref('')
const isSearchPanelOpen = ref(false)
const debouncedKeyword = refDebounced(searchKeywordRaw, 200)
const searchResult = computed(() => searchVocabulary(debouncedKeyword.value, 20))

const loaded = ref(false)
// 当前章节的全量数据（词库数据按需加载，未就绪时为 undefined，模板显示加载态）。
// 数据为普通对象，订阅版本号以在加载完成时触发重渲染
const curChapter = computed(() => {
  touchVocabularyData()
  return getChapterData(category.value)
})
// 当前章节的元信息（来自 index 清单，打开即有：组数/词数/音频）
const curMeta = computed(() => VOCAB_MANIFEST.chapters[category.value])

watch(category, (newVal) => {
  // console.log(newVal, oldVal)
  localStorage.setItem('vocabulary_chapter', newVal)
  stopSequence()
})

// ===== 学习状态过滤（全部/未学/已认识/模糊）=====
// 隐藏用 visibility（行占位），切换只重绘不重排，大表格也零卡顿
// 过滤导航：不改变布局，用 上一个/下一个 在匹配词之间跳转
const statusFilter = ref('all')
const filterNavIndex = ref(-1)
const filteredWords = computed(() =>
  (curChapter.value?.words || []).flat().filter(item => !isRowHiddenByFilter(item)),
)
watch(statusFilter, () => (filterNavIndex.value = -1))

function gotoFilteredWord(delta) {
  const list = filteredWords.value
  if (!list.length)
    return
  if (delta === 'first')
    filterNavIndex.value = 0
  else if (delta === 'last')
    filterNavIndex.value = list.length - 1
  else
    filterNavIndex.value = (filterNavIndex.value + delta + list.length) % list.length
  const id = list[filterNavIndex.value].id
  nextTick(() => {
    const el = document.getElementById(`tr_${id}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (el) {
      el.classList.add('search-flash')
      setTimeout(() => el.classList.remove('search-flash'), 2000)
    }
  })
}
const statusFilterOptions = [
  { value: 'all', label: '全部' },
  { value: 'known', label: '已认识' },
  { value: 'fuzzy', label: '模糊' },
  { value: 'unknown', label: '未学' },
]

function isRowHiddenByFilter(item) {
  return statusFilter.value !== 'all' && getWordStatus(item.word[0]) !== statusFilter.value
}

const statusIconMap = {
  known: 'i-ph-check-circle-bold text-green-500',
  fuzzy: 'i-ph-circle-half-bold text-yellow-500',
  unknown: 'i-ph-circle-dashed text-gray-400 dark:text-gray-500',
}
const statusTitleMap = {
  known: '已认识（点击改为未学）',
  fuzzy: '模糊（点击改为已认识）',
  unknown: '未学（点击改为模糊）',
}

// 章节进度：基于 index 清单的纯词串列表统计，无需等待全量词条数据
const progress = computed(() => {
  const result = wordsProgress(curMeta.value?.wordList ?? [])
  const total = result.known + result.fuzzy + result.unknown
  return {
    ...result,
    total,
    knownPct: total > 0 ? `${(result.known / total) * 100}%` : '0%',
    fuzzyPct: total > 0 ? `${(result.fuzzy / total) * 100}%` : '0%',
    learnedPct: total > 0 ? Math.round(((result.known + result.fuzzy) / total) * 100) : 0,
  }
})

// 聚合多个章节的三态统计；total 取自清单中的 wordCount（固定值），进度 = 已学（认识+模糊）/ 总数
function aggregateProgress(keys) {
  const totals = { known: 0, fuzzy: 0, unknown: 0, total: 0 }
  for (const k of keys) {
    const meta = VOCAB_MANIFEST.chapters[k]
    if (!meta)
      continue
    const p = wordsProgress(meta.wordList)
    totals.known += p.known
    totals.fuzzy += p.fuzzy
    totals.unknown += p.unknown
    totals.total += meta.wordCount
  }
  const learned = totals.known + totals.fuzzy
  return {
    ...totals,
    learned,
    pct: totals.total > 0 ? Math.round((learned / totals.total) * 100) : 0,
  }
}

// 全部词库的总统计（学习总览面板用，纯清单计算，打开即准确）
const allSourcesProgress = computed(() =>
  VOCAB_SOURCES.map(s => ({
    ...s,
    ...aggregateProgress(Object.keys(VOCAB_MANIFEST.chapters).filter(k => VOCAB_MANIFEST.chapters[k].source === s.key)),
  })))

// 全词库去重后的单词列表：同一单词出现在多个词库时只保留一次（大小写不敏感）
const allUniqueWords = computed(() => {
  const seen = new Set()
  const unique = []
  for (const meta of Object.values(VOCAB_MANIFEST.chapters)) {
    for (const w of meta.wordList) {
      const key = w.toLowerCase()
      if (!seen.has(key)) {
        seen.add(key)
        unique.push(w)
      }
    }
  }
  return unique
})

// 全词库去重统计：排除跨词库重复单词后的三态数量与进度
const allUniqueProgress = computed(() => {
  const p = wordsProgress(allUniqueWords.value)
  const total = allUniqueWords.value.length
  return {
    ...p,
    total,
    pct: total > 0 ? Math.round(((p.known + p.fuzzy) / total) * 100) : 0,
  }
})

const fileInput = ref(null)

function exportStatus() {
  const blob = new Blob([exportWordStatus()], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `vocabulary-status-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 导入学习记录：选文件后弹出方式选择（合并/覆盖），确认后执行
const pendingImport = ref(null)

async function onImportFile(e) {
  const target = e.target
  const file = target.files?.[0]
  if (!file)
    return
  const text = await file.text()
  target.value = ''
  pendingImport.value = { text }
}

function confirmImport(mode) {
  if (!pendingImport.value)
    return
  const ok = importWordStatus(pendingImport.value.text, mode)
  pendingImport.value = null
  // eslint-disable-next-line no-alert
  window.alert(ok ? '导入成功' : '导入失败：文件格式不正确')
}

// 完成练习：拼写正确且当前为"未学"的词自动标记为"模糊"
function finishTraining() {
  isFinishTraining.value = true
  const cur = curChapter.value
  if (!cur)
    return
  for (const group of cur.words) {
    for (const item of group) {
      if (item.spellValue && !item.spellError && getWordStatus(item.word[0]) === 'unknown')
        setWordStatus(item.word[0], 'fuzzy')
    }
  }
}

function calcStats() {
  let error = 0
  let missing = 0
  let correct = 0
  if (isTrainingModel.value) {
    const cur = curChapter.value
    if (!cur)
      return ''
    // 遍历所有单词的属性
    for (const group of cur.words) {
      for (const item of group) {
        if (item.spellValue) {
          if (item.spellError)
            error++
          else
            correct++
        }
        else { missing++ }
      }
    }
  }
  return `${missing} 个未完成，${correct} 个正确，${error} 个错误`
}

// 当前词库数据变化时按需加载（只加载当前词库，不做后台全量预载）
watch(source, s => loadVocabularySource(s))

onMounted(() => {
  loaded.value = true
  loadVocabularySource(source.value)

  // 只能同时播放一个音频
  const audioTags = document.getElementsByTagName('audio')
  for (const audio of audioTags) {
    audio.onplay = () => {
      for (const _audio of audioTags) {
        _audio.blur()
        if (audio !== _audio)
          _audio.pause()
      }
    }
  }
})

onUpdated(() => {
  // 音频再切换 SRC 之后需要调用一下 load() 不然看不到效果
  for (const el of document.getElementsByTagName('audio'))
    el.load()
})

document.addEventListener('keydown', (ev) => {
  // 激活的那个音频可以通过方向键进行快进/退
  if (['ArrowLeft', 'ArrowRight', ' '].includes(ev.key)) {
    ev.preventDefault()
    const audioTags = document.getElementsByTagName('audio')
    const keyMap = {
      ArrowLeft: -5,
      ArrowRight: 5,
    }
    for (const audioTag of audioTags) {
      audioTag.blur()
      if (keyMap[ev.key]) {
        const step = keyMap[ev.key]
        audioTag.currentTime = audioTag.currentTime + step
        // console.log(step, audioT ag.currentTime)
      }
      if (ev.key === ' ') {
        if (audioTag.paused)
          audioTag.play()
        else
          audioTag.pause()
      }
    }
  }
})

let audio = null
function play(audioPath) {
  stopSequence()
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }
  audio = document.createElement('audio')
  audio.src = audioPath
  audio.play()
}

// ===== 章节连读（原书/英音/美音 逐词连播）=====
let seqAudio = null
let seqToken = 0
let seqResume = null // 暂停时挂起的队列继续函数
const isSeqPlaying = ref(false)
const isSeqPaused = ref(false)

function playChapterSequence(accent) {
  stopSequence()
  // 与表格行相同的可见性过滤：连读只播当前过滤模式下显示的词
  const words = (curChapter.value?.words || [])
    .flat()
    .filter(item => !isRowHiddenByFilter(item))
    .map(item => item.word[0])
  if (words.length < 1)
    return
  const token = ++seqToken
  isSeqPlaying.value = true
  seqAudio = seqAudio || document.createElement('audio')
  let i = 0
  const playNext = () => {
    if (token !== seqToken)
      return
    // 暂停中（无论点暂停时是在播词中还是词间间隙）：挂起队列，恢复时从此处继续
    if (isSeqPaused.value) {
      seqResume = playNext
      return
    }
    if (i >= words.length) {
      isSeqPlaying.value = false
      isSeqPaused.value = false
      return
    }
    const w = words[i++]
    seqAudio.src = wordAudioUrl(w, accent)
    // 音频缺失/加载失败、或播放被浏览器拒绝时跳过继续，否则整个连读会卡停
    seqAudio.onerror = () => { if (token === seqToken) setTimeout(playNext, 50) }
    seqAudio.onended = () => { if (token === seqToken) setTimeout(playNext, 500) }
    seqAudio.play().catch(() => { if (token === seqToken) setTimeout(playNext, 100) })
  }
  playNext()
}

function pauseOrResumeSequence() {
  if (!seqAudio || !isSeqPlaying.value)
    return
  if (!isSeqPaused.value) {
    // 暂停：词中则停下当前发音；词间则挂起待播队列
    isSeqPaused.value = true
    seqAudio.pause()
  }
  else {
    // 继续：优先执行挂起的队列，否则恢复当前词的播放
    isSeqPaused.value = false
    if (seqResume) {
      const fn = seqResume
      seqResume = null
      fn()
    }
    else {
      seqAudio.play().catch(() => {})
    }
  }
}

function stopSequence() {
  seqToken++
  seqResume = null
  if (seqAudio) {
    seqAudio.pause()
    seqAudio.onended = null
    seqAudio.onerror = null
  }
  isSeqPlaying.value = false
  isSeqPaused.value = false
}

function copyText(item) {
  const text = `${item.word} ${item.pos} ${item.meaning}`
  navigator.clipboard.writeText(text)
}

function onInputKeydown(e) {
  e.stopPropagation()
  const { key, target } = e
  // console.log(key, target.id)
  if (key === 'Enter') {
    // 切换到下一个 input
    document.getElementById((Number(target.id) + 1).toString())?.focus()
  }
}

function onInputFocusIn(e, audioPath) {
  if (isAutoPlayWordAudio.value)
    play(audioPath)
}

function onInputFocusOut(e, item) {
  const { target } = e
  const spellValue = target.value.toLowerCase().trim()
  if (spellValue.length < 1) {
    item.spellValue = ''
    item.spellError = false
  }
  else {
    item.spellValue = spellValue
    item.spellError = !item.word.map(v => v.toLowerCase().trim()).includes(spellValue)
  }
  trainingStats.value = calcStats()
}

function getInputStyleClass(item) {
  const cls = {
    error: 'ml-4 bg-red-50 border border-red-500 text-red-900 placeholder-red-700 text-sm rounded-lg focus:ring-red-500 dark:bg-gray-700 focus:border-red-500 inline-block p-2.5 dark:text-red-500 dark:placeholder-red-500 dark:border-red-500',
    normal: 'ml-4 inline-block border border-gray-300 rounded-lg bg-gray-50 p-2.5 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500 dark:placeholder-gray-400',
    success: 'ml-4 bg-green-50 border border-green-500 text-green-900 dark:text-green-400 placeholder-green-700 dark:placeholder-green-500 text-sm rounded-lg focus:ring-green-500 focus:border-green-500 inline-block p-2.5 dark:bg-gray-700 dark:border-green-500',
  }
  if (isFinishTraining.value) {
    if (item.spellError)
      return cls.error
    if (item.spellValue.length > 0 && !item.spellError)
      return cls.success
  }
  return cls.normal
}

// 在已加载的章节数据中按词形查找词条 id（清单纯词串结果跳转用）
function findWordId(chapterLabel, word) {
  const ch = getChapterData(chapterLabel)
  if (!ch || !word)
    return null
  const lower = word.toLowerCase()
  for (const group of ch.words) {
    for (const item of group) {
      if (item.word.some(v => v.toLowerCase() === lower))
        return item.id
    }
  }
  return null
}

// 点击搜索结果：切换到对应词库/章节，滚动到该词所在行并短暂高亮。
// 未加载词库的纯词串结果会先按需加载数据，再按单词文本定位词条
async function gotoResult(r) {
  isSearchPanelOpen.value = false
  searchKeywordRaw.value = ''
  await loadVocabularySource(r.source)
  source.value = r.source
  category.value = r.chapter
  const id = r.item ? r.item.id : findWordId(r.chapter, r.word)
  if (id == null)
    return
  nextTick(() => {
    const el = document.getElementById(`tr_${id}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (el) {
      el.classList.add('search-flash')
      setTimeout(() => el.classList.remove('search-flash'), 2000)
    }
  })
}

// 点击关联词标签：跳转到目标词所在词库/章节并高亮（复用搜索跳转逻辑）
async function gotoRelation(r) {
  await loadVocabularySource(r.source)
  source.value = r.source
  category.value = r.chapter
  nextTick(() => {
    const el = document.getElementById(`tr_${r.id}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (el) {
      el.classList.add('search-flash')
      setTimeout(() => el.classList.remove('search-flash'), 2000)
    }
  })
}

// 按 / 快速聚焦搜索框（在输入框/选择框内时不生效）
document.addEventListener('keydown', (ev) => {
  if (ev.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(ev.target.tagName)) {
    ev.preventDefault()
    searchInputRef.value?.focus()
  }
})

// 音标拆成英/美两行显示（"UK /a/ US /b/" 拆为两行），单个音标原样单行
function phoneticLines(phonetic) {
  const m = phonetic.match(/^(UK\s*\/[^/]*\/)\s*(US\s*\/.*)$/)
  return m ? [m[1], m[2]] : [phonetic]
}

// 播放音标行对应的口音发音：UK 行播英音，US 行播美音，无口音前缀跟随当前设置
function playPhonetic(item, line) {
  const acc = line.startsWith('UK') ? 'uk' : line.startsWith('US') ? 'us' : undefined
  play(wordAudioUrl(item.word[0], acc))
}

function copyAllError() {
  const words = curChapter.value?.words
  if (!words)
    return
  const errorWords = []
  for (const group of words) {
    for (const item of group) {
      if (item.spellError)
        errorWords.push(`${item.word} ${item.pos} ${item.meaning}`)
    }
  }
  navigator.clipboard.writeText(errorWords.join('\n\n'))
}
</script>

<template>
  <div class="px-4 pt-6 2xl:px-0">
    <div class="border border-gray-200 rounded-lg bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800 sm:p-6">
      <!-- 学习总览：全部词库统计，点击行切换词库 -->
      <div class="mb-4 border border-gray-200 rounded-lg p-3 dark:border-gray-700">
        <div class="mb-2 flex items-center justify-between">
          <span class="text-sm font-medium text-gray-500 dark:text-gray-400">
            学习总览（共 {{ allSourcesProgress.reduce((sum, s) => sum + s.total, 0) }} 词，点击行切换词库）
          </span>
          <span class="flex shrink-0 items-center">
            <button
              type="button"
              class="inline-block border border-gray-300 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-gray-700 dark:border-gray-600 dark:bg-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-600"
              @click="exportStatus"
            >
              导出学习进度
            </button>
            <button
              type="button"
              class="ml-2 inline-block border border-gray-300 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-gray-700 dark:border-gray-600 dark:bg-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-600"
              @click="fileInput?.click()"
            >
              导入学习进度
            </button>
            <input ref="fileInput" type="file" accept="application/json,.json" class="hidden" @change="onImportFile">
          </span>
        </div>
        <!-- 全部词库去重汇总行：跨词库重复单词只计一次 -->
        <div class="mb-1 flex items-center border-b border-gray-100 rounded-lg bg-gray-50 px-2 py-1.5 dark:border-gray-700 dark:bg-gray-700/40">
          <span class="w-28 shrink-0 text-sm font-bold text-gray-900 dark:text-white">全部（去重）</span>
          <span class="w-80 shrink-0 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
            共 <b class="inline-block w-9 text-right tabular-nums">{{ allUniqueProgress.total }}</b> 词 ·
            已认识 <b class="inline-block w-8 text-right tabular-nums text-green-500">{{ allUniqueProgress.known }}</b> ·
            模糊 <b class="inline-block w-8 text-right tabular-nums text-yellow-500">{{ allUniqueProgress.fuzzy }}</b> ·
            未学 <b class="inline-block w-8 text-right tabular-nums">{{ allUniqueProgress.unknown }}</b>
          </span>
          <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
            <div class="h-full bg-green-500" :style="{ width: `${allUniqueProgress.pct}%` }" />
          </div>
          <span class="ml-3 w-12 shrink-0 text-right text-xs text-gray-500 dark:text-gray-400">{{ allUniqueProgress.pct }}%</span>
        </div>
        <div
          v-for="row in allSourcesProgress"
          :key="row.key"
          class="flex cursor-pointer items-center rounded-lg px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-700"
          @click="source = row.key"
        >
          <span
            class="w-28 shrink-0 text-sm"
            :class="row.key === source ? 'font-bold text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'"
          >{{ row.label }}</span>
          <span class="w-80 shrink-0 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
            共 <b class="inline-block w-9 text-right tabular-nums">{{ row.total }}</b> 词 ·
            已认识 <b class="inline-block w-8 text-right tabular-nums text-green-500">{{ row.known }}</b> ·
            模糊 <b class="inline-block w-8 text-right tabular-nums text-yellow-500">{{ row.fuzzy }}</b> ·
            未学 <b class="inline-block w-8 text-right tabular-nums">{{ row.unknown }}</b>
          </span>
          <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
            <div class="h-full bg-green-500" :style="{ width: `${row.pct}%` }" />
          </div>
          <span class="ml-3 w-12 shrink-0 text-right text-xs text-gray-500 dark:text-gray-400">{{ row.pct }}%</span>
        </div>
      </div>
      <!-- Card header：上=操作区，分隔线下=章节信息区；滚动时吸顶 -->
      <div class="sticky top-16 z-20 mb-4 flex flex-col border border-gray-200 rounded-lg bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <!-- 章节信息区 -->
        <div class="order-2 mt-3 border-t border-gray-200 pt-3 dark:border-gray-700">
          <div class="flex flex-wrap items-center gap-x-2 gap-y-1 px-2">
            <span class="truncate text-xs text-gray-500 dark:text-gray-400">{{ sourceDesc }}</span>
            <span class="rounded-full bg-primary-50 px-2.5 py-0.5 text-sm font-bold text-primary-600 dark:bg-primary-500/15 dark:text-primary-400" :title="sourceDesc">{{ category }}</span>
            <span class="text-sm text-gray-500 dark:text-gray-400">
              共 <b class="tabular-nums text-gray-700 dark:text-gray-200">{{ curMeta?.wordCount ?? '-' }}</b> 词 ·
              已认识 <b class="tabular-nums text-green-500">{{ progress.known }}</b> ·
              模糊 <b class="tabular-nums text-yellow-500">{{ progress.fuzzy }}</b> ·
              未学 <b class="tabular-nums">{{ progress.unknown }}</b> ·
              进度 <b class="tabular-nums text-green-500">{{ progress.learnedPct }}%</b>
            </span>
            <!-- 章节连读：原书(仅真经)/英音/美音 逐词连播 -->
            <div v-if="curChapter" class="ml-auto flex flex-wrap items-center gap-1.5">
              <!-- 学习状态过滤：浅底容器自成一组，与连读按钮区分 -->
              <div class="flex flex-wrap items-center gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
                <button
                  v-for="opt in statusFilterOptions"
                  :key="opt.value"
                  type="button"
                  class="cursor-pointer rounded-full px-3 py-1 text-sm transition-colors duration-200"
                  :class="statusFilter === opt.value
                    ? 'bg-primary-500 text-white'
                    : 'text-gray-600 hover:text-primary-500 dark:text-gray-300 dark:hover:text-primary-400'"
                  title="按学习状态过滤行；隐藏的行保留占位（空白行），切换零卡顿"
                  @click="statusFilter = opt.value"
                >
                  {{ opt.label }}
                </button>
              </div>
              <!-- 过滤导航：首个/上一个/下一个/末个匹配词 -->
              <span v-if="statusFilter !== 'all' && filteredWords.length" class="flex items-center gap-1">
                <button
                  type="button"
                  class="cursor-pointer rounded border border-gray-300 px-1.5 py-0.5 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  title="跳转到第一个匹配词"
                  @click="gotoFilteredWord('first')"
                >
                  ⇤ 首个
                </button>
                <button
                  type="button"
                  class="cursor-pointer rounded border border-gray-300 px-1.5 py-0.5 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  title="跳转到上一个匹配词"
                  @click="gotoFilteredWord(-1)"
                >
                  ↑ 上一个
                </button>
                <span class="w-12 shrink-0 text-center text-xs tabular-nums text-gray-500 dark:text-gray-400">
                  {{ filterNavIndex >= 0 ? `${filterNavIndex + 1}/${filteredWords.length}` : `共${filteredWords.length}` }}
                </span>
                <button
                  type="button"
                  class="cursor-pointer rounded border border-gray-300 px-1.5 py-0.5 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  title="跳转到下一个匹配词"
                  @click="gotoFilteredWord(1)"
                >
                  下一个 ↓
                </button>
                <button
                  type="button"
                  class="cursor-pointer rounded border border-gray-300 px-1.5 py-0.5 text-xs text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                  title="跳转到最后一个匹配词"
                  @click="gotoFilteredWord('last')"
                >
                  末个 ⇥
                </button>
              </span>
              <span class="mx-0.5 h-4 w-px shrink-0 bg-gray-300 dark:bg-gray-600" />
              <button
                v-if="source === 'ielts'"
                class="cursor-pointer rounded border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                @click="playChapterSequence('book')"
              >
                原书连读
              </button>
              <button
                class="cursor-pointer rounded border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                @click="playChapterSequence('uk')"
              >
                英音连读
              </button>
              <button
                class="cursor-pointer rounded border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                @click="playChapterSequence('us')"
              >
                美音连读
              </button>
              <button
                v-if="isSeqPlaying"
                class="cursor-pointer rounded border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                @click="pauseOrResumeSequence"
              >
                {{ isSeqPaused ? '继续' : '暂停' }}
              </button>
              <button
                v-if="isSeqPlaying"
                class="cursor-pointer rounded border border-red-300 px-2 py-1 text-sm text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/30"
                @click="stopSequence"
              >
                停止
              </button>
            </div>
          </div>
          <!-- 章节进度条 -->
          <div class="mt-2.5 h-1.5 w-full flex overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
            <div class="bg-green-500" :style="{ width: progress.knownPct }" />
            <div class="bg-yellow-400" :style="{ width: progress.fuzzyPct }" />
          </div>
        </div>
        <!-- 操作区 -->
        <div class="order-1">
          <div class="flex flex-wrap items-center">
            <select
              v-model="source"
              class="block w-40 shrink-0 border border-gray-300 rounded-lg bg-gray-50 px-2.5 py-1.5 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500 dark:placeholder-gray-400"
            >
              <option v-for="s in sourceOptions" :key="s.key" :value="s.key">
                {{ s.label }}
              </option>
            </select>
            <select
              v-model="category"
              class="ml-2 block w-52 shrink-0 border border-gray-300 rounded-lg bg-gray-50 px-2.5 py-1.5 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500 dark:placeholder-gray-400"
            >
              <option v-for="k in chapterOptions" :key="k" :value="k">
                {{ k }}
              </option>
            </select>
            <div class="relative ml-2 w-56">
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <i class="i-ph-magnifying-glass h-4 w-4 text-gray-500 dark:text-gray-400" />
              </div>
              <input
                ref="searchInputRef" v-model="searchKeywordRaw" type="search"
                class="block w-full border border-gray-300 rounded-lg bg-gray-50 py-1.5 pl-10 pr-2.5 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:placeholder-gray-400"
                placeholder="搜索 / 释义（按 / 聚焦）"
                @focus="isSearchPanelOpen = true"
                @input="isSearchPanelOpen = true"
                @keydown.stop
                @keydown.esc="isSearchPanelOpen = false"
              >
              <!-- 搜索结果下拉面板：点击结果跳转到对应词库/章节的单词行 -->
              <div
                v-if="isSearchPanelOpen && searchKeywordRaw.trim()"
                class="absolute left-0 top-full z-50 mt-1 max-h-80 max-w-[80vw] w-96 overflow-y-auto border border-gray-200 rounded-lg bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
              >
                <div
                  v-for="r in searchResult.results"
                  :key="`${r.chapter}_${r.item ? r.item.id : r.word}`"
                  class="flex cursor-pointer items-center px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
                  :title="`位于 ${r.sourceLabel} · ${r.chapter}${r.item ? '' : '（点击加载该词库）'}`"
                  @mousedown.prevent="gotoResult(r)"
                >
                  <i
                    v-if="r.item"
                    :class="statusIconMap[getWordStatus(r.item.word[0])]"
                    :title="statusTitleMap[getWordStatus(r.item.word[0])]"
                    class="mr-2 inline-block shrink-0 text-base"
                  />
                  <i v-else class="i-ph-circle-dashed mr-2 inline-block shrink-0 text-base text-gray-300 dark:text-gray-600" />
                  <span class="shrink-0 font-medium text-gray-900 dark:text-white">{{ r.item ? r.item.word[0] : r.word }}</span>
                  <span v-if="r.item" class="ml-2 shrink-0 text-xs italic text-gray-400">{{ r.item.pos }}</span>
                  <span v-if="r.item" class="ml-2 truncate text-gray-600 dark:text-gray-300">{{ r.item.meaning }}</span>
                  <span v-else class="ml-2 truncate text-xs text-gray-400">未加载，点击载入</span>
                  <span class="ml-2 shrink-0 text-xs text-gray-400">{{ r.chapter }}</span>
                </div>
                <div
                  v-if="searchResult.results.length && searchResult.total > searchResult.results.length"
                  class="border-t border-gray-100 px-3 py-1.5 text-xs text-gray-400 dark:border-gray-700"
                >
                  共 {{ searchResult.total }} 条匹配，仅显示前 {{ searchResult.results.length }} 条
                </div>
                <div v-if="!searchResult.results.length" class="px-3 py-3 text-sm text-gray-400">
                  无匹配结果
                </div>
              </div>
            </div>
            <label class="ml-auto inline-flex shrink-0 cursor-pointer items-center pl-2">
              <input v-model="isTrainingModel" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-300">练习模式</span>
            </label>
            <label class="ml-2 inline-flex shrink-0 cursor-pointer items-center" title="按词根/同义/反义组成组学习">
              <input v-model="isRelationView" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-300">关联组</span>
            </label>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isShowMeaning" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-300">释义</span>
            </label>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isShowSource" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-300">原词</span>
            </label>
            <label v-if="isTrainingModel" class="ml-2 inline-flex cursor-pointer items-center">
              <input v-model="isAutoPlayWordAudio" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-300">自动播放</span>
            </label>
          </div>
        </div>
      </div>
      <!-- Table -->
      <div v-if="!isRelationView" class="mt-6 flex flex-col">
        <div class="overflow-x-auto rounded-lg">
          <div class="inline-block min-w-full align-middle">
            <div class="overflow-hidden shadow sm:rounded-lg">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                <thead class="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      #
                    </th>
                    <th class="p-4 text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      <br>
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      词
                    </th>
                    <th class="w-0 text-left text-xs font-medium text-gray-500 dark:text-white">
                      词性
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      词义
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      例句
                    </th>
                    <th class="p-4 text-left text-xs font-medium tracking-wider text-gray-500 dark:text-white">
                      拓展
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-800">
                  <template v-if="curChapter">
                    <template v-for="(wordGroup, i) of curChapter.words" :key="wordGroup.label">
                      <tr
                        v-for="item of wordGroup"
                        v-show="!(isTrainingModel && isOnlyShowErrors && !item.spellError)" :id="`tr_${item.id}`"
                        :key="item.id"
                        :class="[
                          { 'bg-gray-50 dark:bg-gray-700': item.id % 2 === 0, [`group-color-${i % 15}`]: true, 'row-hidden': isRowHiddenByFilter(item) },
                        ]" class="text-sm text-gray-900 dark:text-white"
                      >
                        <td class="p-4">
                          {{ item.id }}
                        </td>
                        <td>
                          <!-- 左侧大喇叭：仅有真经原书真人音频的词显示（真经词及其他词库中源自真经的词） -->
                          <i
                            v-if="wordHasBookAudio(item.word[0])"
                            class="i-ph-speaker-simple-high-bold inline-block cursor-pointer"
                            title="播放原书真人发音"
                            @click="play(wordAudioUrl(item.word[0], 'book'))"
                          />

                          <i
                            :class="statusIconMap[getWordStatus(item.word[0])]"
                            :title="statusTitleMap[getWordStatus(item.word[0])]"
                            class="ml-4 inline-block cursor-pointer align-middle text-base"
                            @click="cycleWordStatus(item.word[0])"
                          />

                          <template v-if="isTrainingModel">
                            <i
                              :class="`${item.showSource ? 'i-ph-eye-slash-bold' : 'i-ph-eye-bold'} inline-block cursor-pointer ml-4`"
                              title="显示原词" @click="item.showSource = !item.showSource"
                            />
                            <input
                              :id="item.id" autocomplete="off" :class="getInputStyleClass(item)"
                              type="text"
                              @focusout="onInputFocusOut($event, item)"
                              @focusin="onInputFocusIn($event, wordAudioUrl(item.word[0]))"
                              @keydown="onInputKeydown"
                            >
                          </template>
                        </td>
                        <!-- 高频词的有道音标含全部变体读音，可能极长：max-width 必须放在 td 上
                             （auto 表格布局下 p 的 max-width 不参与列宽计算），超出部分省略，悬停看全文 -->
                        <td class="group relative max-w-55 truncate p-4">
                          <div v-if="!isTrainingModel || item.showSource || (isTrainingModel && isOnlyShowErrors && item.spellError) || isShowSource">
                            <p v-for="w in item.word" :key="w">
                              <a
                                class="hover:underline" :title="`在剑桥词典中查询 ${w}`" target="_blank"
                                :href="`https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${w}`"
                              >{{ w }}</a>
                            </p>
                            <p v-if="item.phonetic" class="text-sm" :title="item.phonetic">
                              <span v-for="(line, idx) in phoneticLines(item.phonetic)" :key="idx" class="flex items-center">
                                <i
                                  class="i-ph-speaker-simple-high-bold mr-1 inline-block shrink-0 cursor-pointer text-gray-400 hover:text-primary-500 dark:text-gray-500 dark:hover:text-primary-400"
                                  title="播放该口音发音"
                                  @click="playPhonetic(item, line)"
                                />
                                {{ line }}
                              </span>
                            </p>

                            <div
                              class="absolute right-0 top-0 hidden h-100% items-center group-hover:flex"
                              @click="copyText(item)"
                            >
                              <i class="i-ph-copy block cursor-pointer px-4" />
                            </div>
                          </div>
                        </td>
                        <td style="font-style: italic; font-family: times;">
                          {{ item.pos }}
                        </td>
                        <!-- 词义完整显示（限宽不限高，自动换行） -->
                        <td class="max-w-70 p-4">
                          {{ isShowMeaning ? item.meaning : '' }}
                        </td>
                        <td class="p-4">
                          <template v-if="!isTrainingModel">
                            <p>{{ item.example }}</p>
                            <p v-if="item.note" class="mt-1 text-sm text-gray-600 dark:text-gray-300">
                              {{ item.note }}
                            </p>
                            <p v-else-if="item.translation" class="mt-1 text-sm text-gray-600 dark:text-gray-300">
                              {{ item.translation }}
                            </p>
                          </template>
                        </td>
                        <td class="p-4">
                          {{ isTrainingModel ? '' : item.extra }}
                          <!-- 关联词标签：同义/反义/词根/派生/形近，点击跳转高亮 -->
                          <div
                            v-if="!isTrainingModel && item.relations?.length"
                            class="mt-2 flex flex-wrap gap-1.5"
                          >
                            <button
                              v-for="rel in resolveRelations(item)"
                              :key="`${rel.type}_${rel.word}`"
                              type="button"
                              :class="rel.tagClass"
                              class="inline-flex cursor-pointer items-center rounded px-1.5 py-0.5 text-xs transition-transform duration-150 hover:underline hover:-translate-y-px"
                              :title="`${rel.typeLabel}：${rel.meaning}（位于 ${rel.sourceLabel} · ${rel.chapter}）`"
                              @click="gotoRelation(rel)"
                            >
                              <span class="mr-1 opacity-70">{{ rel.typeLabel }}</span>{{ rel.word }}
                            </button>
                          </div>
                        </td>
                      </tr>
                    </template>
                  </template>
                  <tr v-else>
                    <td colspan="7" class="px-4 py-8 text-center text-sm text-gray-400 dark:text-gray-500">
                      章节词条加载中…
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <!-- 关联组学习视图 -->
      <RelationGroupView
        v-else
        class="mt-6"
        :source="source"
        :play="play"
        @goto="gotoRelation"
      />
      <!-- Card Footer -->
      <div class="flex items-center justify-between pt-3 sm:pt-6">
        <div>
          <p v-if="isTrainingModel">
            {{ trainingStats }}
          </p>
        </div>
        <div v-if="isTrainingModel" class="flex-shrink-0">
          <button
            type="button"
            class="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
            @click="finishTraining"
          >
            完成练习
          </button>
          <button
            type="button"
            class="ml-2 rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
            @click="isOnlyShowErrors = !isOnlyShowErrors"
          >
            {{ isOnlyShowErrors ? '展示所有' : '仅展示错词' }}
          </button>
          <button
            type="button"
            class="ml-2 rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
            @click="copyAllError"
          >
            拷贝错词
          </button>
        </div>
      </div>
    </div>
    <!-- 导入学习记录：选择合并或覆盖 -->
    <div
      v-if="pendingImport"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="pendingImport = null"
    >
      <div class="mx-4 w-96 rounded-lg bg-white p-5 shadow-xl dark:bg-gray-800">
        <h4 class="mb-2 text-base font-bold text-gray-900 dark:text-white">
          导入学习记录
        </h4>
        <p class="mb-1 text-sm text-gray-600 dark:text-gray-300">
          请选择导入方式：
        </p>
        <ul class="mb-4 text-xs text-gray-500 dark:text-gray-400">
          <li>· 合并导入：保留当前所有记录，文件中的同名单词以文件为准</li>
          <li>· 覆盖导入：丢弃当前所有记录，完全使用文件内容</li>
        </ul>
        <div class="flex justify-end gap-2">
          <button
            type="button"
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 dark:border-gray-600 dark:bg-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-600"
            @click="pendingImport = null"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded-lg bg-gray-600 px-3 py-2 text-sm text-white hover:bg-gray-700"
            @click="confirmImport('merge')"
          >
            合并导入
          </button>
          <button
            type="button"
            class="rounded-lg bg-blue-700 px-3 py-2 text-sm text-white dark:bg-blue-600 hover:bg-blue-800 dark:hover:bg-blue-700"
            @click="confirmImport('overwrite')"
          >
            覆盖导入
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 大表格优化：视口外的行跳过排版与渲染，切换显隐/滚动时明显减少卡顿。
   contain-intrinsic-size 给视口外行一个预估行高，保证滚动条稳定 */
tbody tr {
  content-visibility: auto;
  contain-intrinsic-size: auto 64px;
}

/* 学习状态过滤：visibility 隐藏（行占位），切换时只重绘不重排，避免全表重排卡顿 */
tr.row-hidden {
  visibility: hidden;
}

tr.search-flash {
  animation: search-flash 2s ease-out;
}

@keyframes search-flash {
  0%, 60% {
    box-shadow: inset 0 0 0 2px rgb(59 130 246);
  }
  100% {
    box-shadow: none;
  }
}
</style>
