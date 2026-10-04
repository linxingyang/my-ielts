<script setup lang="ts">
import { MINIMAL_PAIR_GROUPS } from '~/data/phonetics'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

const { playWord, playSequence } = usePhonemeAudio()

const activeId = ref(MINIMAL_PAIR_GROUPS[0].id)
const activeGroup = computed(() =>
  MINIMAL_PAIR_GROUPS.find(g => g.id === activeId.value) || MINIMAL_PAIR_GROUPS[0])

const playingWord = ref('')
const isPlayingAll = ref(false)

function play(word: string) {
  isPlayingAll.value = false
  playingWord.value = word
  playWord(word)
  setTimeout(() => {
    if (playingWord.value === word)
      playingWord.value = ''
  }, 1200)
}

// 行内对比：左 → 右连续播放（跟随实际播放进度高亮）
function compareRow(a: string, b: string) {
  isPlayingAll.value = false
  playSequence([a, b], 700, (w, i, total) => {
    playingWord.value = w
    if (i === total - 1)
      setTimeout(() => { playingWord.value = '' }, 1200)
  })
}

// 音标大按钮：播放该音素的代表词
function playPhoneme(phoneme: string, side: 'a' | 'b') {
  isPlayingAll.value = false
  playWord(activeGroup.value.pairs[0][side])
  playingWord.value = activeGroup.value.pairs[0][side]
  setTimeout(() => playingWord.value = '', 1200)
}

// ---- 全部顺序播放（从上到下、从左到右），间隔可选 ----
const INTERVAL_KEY = 'speaking_play_interval'
const intervalOptions = [
  { label: '快速', ms: 500 },
  { label: '1秒', ms: 1000 },
  { label: '2秒', ms: 2000 },
  { label: '3秒', ms: 3000 },
] as const
const playInterval = useLocalStorage<number>(INTERVAL_KEY, 1000)

// 当前组的全部单词：按表格从上到下，每行先左后右
const allWords = computed(() => activeGroup.value.pairs.flatMap(p => [p.a, p.b]))

function playAllWords() {
  isPlayingAll.value = true
  playSequence(allWords.value, playInterval.value, (w, i, total) => {
    playingWord.value = w
    // 最后一个单词开始播放后 1.5s 清除高亮并复位按钮
    if (i === total - 1) {
      setTimeout(() => {
        playingWord.value = ''
        isPlayingAll.value = false
      }, 1500)
    }
  })
}

function stopPlayAll() {
  // 播放空序列：取消队列并停止当前音频
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

// 切换对比组时停止全部播放
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
          易错音对比
        </h3>
        <p class="mt-1 text-sm">
          点击左右单词分别听发音，感受差异；点中间 ⇄ 连续对比播放；或用「全部播放」按顺序通听整组
        </p>
      </div>
      <AccentToggle />
    </div>

    <!-- 对比组选择器 -->
    <div class="mb-5 flex flex-wrap gap-2">
      <button
        v-for="g in MINIMAL_PAIR_GROUPS"
        :key="g.id"
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="activeId === g.id
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="activeId = g.id"
      >
        {{ g.phonemeA }} vs {{ g.phonemeB }}
      </button>
    </div>

    <div class="border border-gray-200 rounded-xl bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <p class="mb-4 text-sm leading-6">
        {{ activeGroup.note }}
      </p>

      <!-- 全部播放工具条：间隔选择 + 播放/停止 -->
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

      <!-- 音标大按钮 -->
      <div class="grid grid-cols-3 mb-4 items-center gap-2 text-center">
        <button
          class="mx-auto flex cursor-pointer items-center gap-2 border-2 border-primary-300 rounded-xl bg-primary-50 px-6 py-3 text-2xl font-bold text-primary-600 transition-all duration-150 active:scale-95 dark:border-primary-500/50 dark:bg-primary-500/10 hover:bg-primary-500 dark:text-primary-400 hover:text-white"
          @click="playPhoneme(activeGroup.phonemeA, 'a')"
        >
          <div class="i-carbon-volume-up" />
          {{ activeGroup.phonemeA }}
        </button>
        <span class="text-lg text-gray-400">VS</span>
        <button
          class="mx-auto flex cursor-pointer items-center gap-2 border-2 border-orange-300 rounded-xl bg-orange-50 px-6 py-3 text-2xl font-bold text-orange-600 transition-all duration-150 active:scale-95 dark:border-orange-500/50 dark:bg-orange-500/10 hover:bg-orange-500 dark:text-orange-400 hover:text-white"
          @click="playPhoneme(activeGroup.phonemeB, 'b')"
        >
          <div class="i-carbon-volume-up" />
          {{ activeGroup.phonemeB }}
        </button>
      </div>

      <!-- 双列对比表 -->
      <table class="w-full text-center text-sm">
        <tbody>
          <tr
            v-for="(pair, i) in activeGroup.pairs"
            :key="`${pair.a}-${pair.b}-${i}`"
            class="border-t border-gray-100 dark:border-gray-700"
          >
            <td class="w-[38%] py-1">
              <button
                class="w-full cursor-pointer rounded-lg py-2.5 text-lg font-bold text-primary-600 transition-all duration-150 active:scale-95 hover:bg-primary-50 dark:text-primary-400 dark:hover:bg-primary-500/10"
                :class="playingWord === pair.a && 'bg-primary-100 dark:bg-primary-500/20'"
                @click="play(pair.a)"
              >
                <div class="align-[-3px] i-carbon-volume-down mr-1.5 inline-block" />
                {{ pair.a }}
              </button>
            </td>
            <td class="w-[24%] py-1 text-xs text-gray-400">
              {{ pair.meaning }}
              <button
                class="ml-1 cursor-pointer rounded-full px-2 py-0.5 text-primary-500 transition-colors hover:bg-primary-100 hover:text-primary-600 dark:hover:bg-primary-500/15"
                title="连续对比播放"
                @click="compareRow(pair.a, pair.b)"
              >
                ⇄
              </button>
            </td>
            <td class="w-[38%] py-1">
              <button
                class="w-full cursor-pointer rounded-lg py-2.5 text-lg font-bold text-orange-600 transition-all duration-150 active:scale-95 hover:bg-orange-50 dark:text-orange-400 dark:hover:bg-orange-500/10"
                :class="playingWord === pair.b && 'bg-orange-100 dark:bg-orange-500/20'"
                @click="play(pair.b)"
              >
                <div class="align-[-3px] i-carbon-volume-down mr-1.5 inline-block" />
                {{ pair.b }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="mt-6 flex flex-wrap gap-6 text-sm">
      <RouterLink to="/speaking/phonetics" class="text-primary-500 hover:underline">
        ← 音标学习
      </RouterLink>
      <RouterLink to="/speaking/practice" class="text-primary-500 hover:underline">
        检验成果：听音辨词练习 →
      </RouterLink>
    </div>
  </div>
</template>
