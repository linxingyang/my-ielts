<script setup lang="ts">
import { CLUSTER_POSITIONS } from '~/data/clusters'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

const { playWord, playSequence } = usePhonemeAudio()

const activeId = ref(CLUSTER_POSITIONS[0].key)
const activePosition = computed(() =>
  CLUSTER_POSITIONS.find(p => p.key === activeId.value) || CLUSTER_POSITIONS[0])

const playingWord = ref('')
function play(word: string) {
  playingWord.value = word
  playWord(word)
  setTimeout(() => {
    if (playingWord.value === word)
      playingWord.value = ''
  }, 1200)
}

// 拆分单词为 前缀/连缀/后缀 三段用于高亮
function parts(word: string, part: string): string[] {
  const i = word.toLowerCase().indexOf(part.toLowerCase())
  if (i < 0)
    return [word, '', '']
  return [word.slice(0, i), word.slice(i, i + part.length), word.slice(i + part.length)]
}

// ---- 全部顺序播放（当前分类所有例词） ----
const INTERVAL_KEY = 'speaking_play_interval'
const intervalOptions = [
  { label: '快速', ms: 500 },
  { label: '1秒', ms: 1000 },
  { label: '2秒', ms: 2000 },
  { label: '3秒', ms: 3000 },
] as const
const playInterval = useLocalStorage<number>(INTERVAL_KEY, 1000)

const allWords = computed(() =>
  activePosition.value.clusters.flatMap(c => c.examples.map(e => e.word)))

const isPlayingAll = ref(false)
function playAllWords() {
  isPlayingAll.value = true
  playSequence(allWords.value, playInterval.value, (w, i, total) => {
    playingWord.value = w
    if (i === total - 1) {
      setTimeout(() => {
        playingWord.value = ''
        isPlayingAll.value = false
      }, 1500)
    }
  })
}

function stopPlayAll() {
  playSequence([])
  playingWord.value = ''
  isPlayingAll.value = false
}

function togglePlayAll() {
  if (isPlayingAll.value)
    stopPlayAll()
  else
    playAllWords()
}

watch(activeId, () => {
  if (isPlayingAll.value)
    stopPlayAll()
})
</script>

<template>
  <div class="px-4 pt-6 text-gray-500 2xl:px-0 dark:text-gray-400">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 class="text-xl font-semibold text-black dark:text-white">
          辅音连缀
        </h3>
        <p class="mt-1 text-sm">
          两个及以上辅音相连且中间不夹元音（tr- / -mpl / -st）。中文音节少见这种结构，重点是不加元音、不吞音
        </p>
      </div>
      <AccentToggle />
    </div>

    <!-- 位置分类选择器 -->
    <div class="mb-5 flex flex-wrap gap-2">
      <button
        v-for="p in CLUSTER_POSITIONS"
        :key="p.key"
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="activeId === p.key
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="activeId = p.key"
      >
        {{ p.label }}
      </button>
    </div>

    <div class="border border-gray-200 rounded-xl bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <p class="mb-4 text-sm leading-6">
        {{ activePosition.desc }}
      </p>

      <!-- 全部播放工具条 -->
      <div class="mb-4 flex flex-wrap items-center gap-3 border-b border-gray-100 pb-4 dark:border-gray-700">
        <button
          class="flex cursor-pointer items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-white transition-all duration-200 active:scale-95"
          :class="isPlayingAll ? 'bg-red-500 hover:bg-red-600' : 'bg-primary-500 hover:bg-primary-600'"
          @click="togglePlayAll()"
        >
          <div :class="isPlayingAll ? 'i-carbon-stop' : 'i-carbon-play'" />
          {{ isPlayingAll ? '停止' : `全部播放（${allWords.length} 词）` }}
        </button>
        <span class="text-sm text-gray-400">间隔</span>
        <div class="flex gap-1.5">
          <button
            v-for="op in intervalOptions"
            :key="op.ms"
            class="cursor-pointer rounded-full px-3 py-1 text-xs transition-all duration-200"
            :class="playInterval === op.ms
              ? 'bg-primary-100 text-primary-600 font-medium dark:bg-primary-500/20 dark:text-primary-400'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600'"
            @click="playInterval = op.ms"
          >
            {{ op.label }}
          </button>
        </div>
      </div>

      <!-- 连缀卡片列表 -->
      <div class="flex flex-col gap-4">
        <div
          v-for="c in activePosition.clusters"
          :key="c.cluster"
          class="border border-gray-100 rounded-xl bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-700/40"
        >
          <div class="mb-1 flex flex-wrap items-center gap-2">
            <span class="rounded-md bg-primary-600 px-2.5 py-1 text-sm font-bold tracking-wide text-white">{{ c.cluster }}</span>
            <span class="text-base font-bold text-primary-500 dark:text-primary-400">{{ c.sound }}</span>
            <span class="text-xs text-gray-400">{{ c.tip }}</span>
          </div>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="e in c.examples"
              :key="e.word"
              class="cursor-pointer rounded-full bg-white px-2.5 py-1 text-sm font-medium text-gray-600 shadow-sm transition-all duration-150 active:scale-95 dark:bg-gray-800 hover:bg-primary-500 dark:text-gray-300 hover:text-white dark:hover:bg-primary-500 dark:hover:text-white"
              :class="playingWord === e.word && '!bg-primary-500 !text-white'"
              @click="play(e.word)"
            >
              <span>{{ parts(e.word, e.part)[0] }}</span><span class="font-bold text-primary-500 dark:text-primary-300" :class="playingWord === e.word && '!text-white'">{{ parts(e.word, e.part)[1] }}</span><span>{{ parts(e.word, e.part)[2] }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-6 flex flex-wrap gap-6 text-sm">
      <RouterLink to="/speaking/spelling" class="text-primary-500 hover:underline">
        ← 拼读规则
      </RouterLink>
      <RouterLink to="/speaking/stress" class="text-primary-500 hover:underline">
        下一步：单词重音 →
      </RouterLink>
    </div>
  </div>
</template>
