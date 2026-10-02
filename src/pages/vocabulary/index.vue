<!-- eslint-disable eslint-comments/no-unlimited-disable -->
<script setup generic="T extends any, O extends any">
import vocabulary from './vocabulary'
import { VOCAB_SOURCES } from '~/composables/vocabularyCategory'
import {
  chapterProgress,
  cycleWordStatus,
  exportWordStatus,
  getWordStatus,
  importWordStatus,
  setWordStatus,
} from '~/composables/wordStatus'

const { source, sourceOptions, category, chapterOptions, sourceLabel, sourceDesc } = useVocabularyCategory('vocabulary_chapter')

const isTrainingModel = ref(false)
const isShowMeaning = ref(true)
const isAutoPlayWordAudio = ref(true)
const isOnlyShowErrors = ref(false)
const isOnlyShowUnknown = ref(false)
const isFinishTraining = ref(false)
const isShowSource = ref(false)

const trainingStats = ref('')
const keyword = ref('')

const loaded = ref(false)
const refVocabulary = reactive(vocabulary)
const wordList = computed(() => {
  const result = structuredClone(vocabulary) // deep clone
  // const keywordValue = keyword.value.trim().toLowerCase()
  const categoryValue = category.value

  if (categoryValue !== '') {
    // for (const key in result) {
    //   if (key !== categoryValue)
    //     delete result[key]
    // }
    return { [categoryValue]: result[categoryValue] }
  }

  /* if (keywordValue !== '') {
    for (const key in result) {
      const category = result[key]
      const words = []
      category.words.forEach((group) => {
        words.push(group.filter((item) => {
          return item.word.toLowerCase().includes(keywordValue)
        }))
      })
      category.words = words
    }
  } */
  return {}
})

watch(category, (newVal) => {
  // console.log(newVal, oldVal)
  localStorage.setItem('vocabulary_chapter', newVal)
})

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

const progress = computed(() => {
  const cur = refVocabulary[category.value]
  const result = chapterProgress(cur?.words.flat() ?? [])
  const total = result.known + result.fuzzy + result.unknown
  return {
    ...result,
    total,
    knownPct: total > 0 ? `${(result.known / total) * 100}%` : '0%',
    fuzzyPct: total > 0 ? `${(result.fuzzy / total) * 100}%` : '0%',
  }
})

// 聚合多个章节的三态统计；total 取自数据中的 wordCount（固定值），进度 = 已学（认识+模糊）/ 总数
function aggregateProgress(keys) {
  const totals = { known: 0, fuzzy: 0, unknown: 0, total: 0 }
  for (const k of keys) {
    const chapter = refVocabulary[k]
    if (!chapter)
      continue
    const p = chapterProgress(chapter.words.flat())
    totals.known += p.known
    totals.fuzzy += p.fuzzy
    totals.unknown += p.unknown
    totals.total += chapter.wordCount
  }
  const learned = totals.known + totals.fuzzy
  return {
    ...totals,
    learned,
    pct: totals.total > 0 ? Math.round((learned / totals.total) * 100) : 0,
  }
}

// 当前词库的总统计
const sourceProgress = computed(() => aggregateProgress(chapterOptions.value))

// 全部词库的总统计（学习总览面板用）
const allSourcesProgress = computed(() =>
  VOCAB_SOURCES.map(s => ({
    ...s,
    ...aggregateProgress(Object.keys(refVocabulary).filter(k => refVocabulary[k].source === s.key)),
  })))

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

async function onImportFile(e) {
  const target = e.target
  const file = target.files?.[0]
  if (!file)
    return
  const text = await file.text()
  // eslint-disable-next-line no-alert
  window.alert(importWordStatus(text) ? '导入成功' : '导入失败：文件格式不正确')
  target.value = ''
}

// 完成练习：拼写正确且当前为"未学"的词自动标记为"模糊"
function finishTraining() {
  isFinishTraining.value = true
  const cur = refVocabulary[category.value]
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
    const cur = refVocabulary[category.value]
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

onMounted(() => {
  loaded.value = true

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
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }
  audio = document.createElement('audio')
  audio.src = audioPath
  audio.play()
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

function copyAllError() {
  const words = refVocabulary[category.value].words
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
      <!-- Card header -->
      <div class="items-center justify-between lg:flex">
        <div class="mb-4 lg:mb-0">
          <h3 class="mb-2 text-xl font-bold text-gray-900 dark:text-white">
            {{ sourceLabel }}
          </h3>
          <span class="text-base font-normal text-gray-500 dark:text-gray-400">{{ sourceDesc }}</span>
          <div class="mt-2 text-sm text-gray-600 dark:text-gray-300">
            共 <b>{{ sourceProgress.total }}</b> 词 ·
            已认识 <b class="text-green-500">{{ sourceProgress.known }}</b> ·
            模糊 <b class="text-yellow-500">{{ sourceProgress.fuzzy }}</b> ·
            未学 <b>{{ sourceProgress.unknown }}</b> ·
            进度 <b class="text-green-500">{{ sourceProgress.pct }}%</b>
          </div>
          <div class="mt-2 h-1.5 w-64 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
            <div class="h-full bg-green-500" :style="{ width: `${sourceProgress.pct}%` }" />
          </div>
        </div>
        <div class="items-center sm:flex sm:flex-wrap">
          <div class="flex flex-wrap items-center">
            <select
              v-model="source"
              class="block w-40 shrink-0 border border-gray-300 rounded-lg bg-gray-50 p-2.5 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500 dark:placeholder-gray-400"
            >
              <option v-for="s in sourceOptions" :key="s.key" :value="s.key">
                {{ s.label }}
              </option>
            </select>
            <select
              v-model="category"
              class="ml-2 block w-52 shrink-0 border border-gray-300 rounded-lg bg-gray-50 p-2.5 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500 dark:placeholder-gray-400"
            >
              <option v-for="k in chapterOptions" :key="k" :value="k">
                {{ k }}
              </option>
            </select>
            <!-- <input type="text" name="email" class="ml-3 block w-full border border-gray-300 rounded-lg bg-gray-50 p-2.5 text-gray-900 dark:border-gray-600 focus:border-primary-500 dark:bg-gray-700 sm:text-sm dark:text-white focus:ring-primary-500 dark:focus:border-primary-500 dark:focus:ring-primary-500 dark:placeholder-gray-400" placeholder="关键词"> -->
            <!-- <div class="relative ml-2 flex-1">
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <svg class="h-4 w-4 text-gray-500 dark:text-gray-400" aria-hidden="true"
                  xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
                  <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z" />
                </svg>
              </div>
              <input v-model="keyword" type="search"
                class="block w-full border border-gray-300 rounded-lg bg-gray-50 p-2.5 pl-10 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500 dark:focus:ring-blue-500 dark:placeholder-gray-400"
                placeholder="Search">
            </div> -->
            <label class="ml-2 inline-flex shrink-0 cursor-pointer items-center">
              <input v-model="isTrainingModel" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-300">练习模式</span>
            </label>
            <label class="ml-2 inline-flex shrink-0 cursor-pointer items-center">
              <input v-model="isOnlyShowUnknown" type="checkbox" class="peer sr-only">
              <div
                class="peer relative h-6 w-11 rounded-full bg-gray-200 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:border after:border-gray-300 dark:border-gray-600 after:rounded-full after:bg-white dark:bg-gray-700 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white dark:peer-focus:ring-blue-800 rtl:peer-checked:after:-translate-x-full"
              />
              <span class="ms-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-300">只看未认识</span>
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
      <!-- 学习总览：全部词库统计，点击行切换词库 -->
      <div class="mt-2 border border-gray-200 rounded-lg p-3 dark:border-gray-700">
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
              导出记录
            </button>
            <button
              type="button"
              class="ml-2 inline-block border border-gray-300 rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-gray-700 dark:border-gray-600 dark:bg-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-600"
              @click="fileInput?.click()"
            >
              导入记录
            </button>
            <input ref="fileInput" type="file" accept="application/json,.json" class="hidden" @change="onImportFile">
          </span>
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
          <span class="w-44 shrink-0 text-xs text-gray-500 dark:text-gray-400">
            已学 {{ row.learned }} / {{ row.total }} 词
          </span>
          <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
            <div class="h-full bg-green-500" :style="{ width: `${row.pct}%` }" />
          </div>
          <span class="ml-3 w-12 shrink-0 text-right text-xs text-gray-500 dark:text-gray-400">{{ row.pct }}%</span>
        </div>
      </div>
      <!-- Table -->
      <div class="mt-6 flex flex-col">
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
                  <tr class="bg-hex-f3f3f3">
                    <td
                      colspan="7"
                      class="px-4 py-6 text-sm font-normal text-gray-900 dark:bg-gray-500 dark:text-white"
                    >
                      <div class="flex flex-row">
                        <div class="flex flex-1 items-center">
                          <span class="text-lg">{{ category }}</span>
                          （ {{ refVocabulary[category].groupCount }} 组 {{ refVocabulary[category].wordCount }} 个词 ）
                          <span class="ml-4 text-sm">
                            已认识 <b class="text-green-500">{{ progress.known }}</b> ·
                            模糊 <b class="text-yellow-500">{{ progress.fuzzy }}</b> ·
                            未学 <b>{{ progress.unknown }}</b>
                          </span>
                        </div>
                        <div v-if="refVocabulary[category].audio" class="justify-items-end">
                          <audio controls class="chapter">
                            <source :src="`vocabulary/audio/${refVocabulary[category].audio}`" type="audio/mpeg">
                          </audio>
                        </div>
                      </div>
                      <div class="mt-3 h-1.5 w-full flex overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
                        <div class="bg-green-500" :style="{ width: progress.knownPct }" />
                        <div class="bg-yellow-400" :style="{ width: progress.fuzzyPct }" />
                      </div>
                    </td>
                  </tr>
                  <template v-for="(wordGroup, i) of refVocabulary[category].words" :key="wordGroup.label">
                    <tr
                      v-for="item of wordGroup"
                      v-show="(!isOnlyShowUnknown || getWordStatus(item.word[0]) !== 'known') && ((isTrainingModel && (isOnlyShowErrors ? item.spellError : true)) || !isTrainingModel)" :id="`tr_${item.id}`"
                      :key="item.id"
                      :class="{ 'bg-gray-50 dark:bg-gray-700': item.id % 2 === 0, [`group-color-${i % 15}`]: true }" class="text-sm text-gray-900 dark:text-white"
                    >
                      <td class="p-4">
                        {{ item.id }}
                      </td>
                      <td>
                        <i
                          class="i-ph-speaker-simple-high-bold inline-block cursor-pointer"
                          @click="play(wordAudioUrl(item.word[0]))"
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
                      <td class="group relative whitespace-nowrap p-4">
                        <div v-if="!isTrainingModel || item.showSource || (isTrainingModel && isOnlyShowErrors && item.spellError) || isShowSource">
                          <p v-for="w in item.word" :key="w">
                            <a
                              class="hover:underline" :title="`在剑桥词典中查询 ${w}`" target="_blank"
                              :href="`https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${w}`"
                            >{{ w }}</a>
                          </p>
                          <p v-if="item.phonetic" class="text-sm">
                            {{ item.phonetic }}
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
                      <td class="p-4">
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
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
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
  </div>
</template>
