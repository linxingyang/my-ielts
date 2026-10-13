<script setup lang="ts">
import { ENDING_GROUPS } from '~/data/endings'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

// -s / -ed 结尾读音听辨：播放单词，选出词尾 -s / -ed 的实际读音
const { playWord } = usePhonemeAudio()

interface Round {
  word: string
  sound: string
  rule: string
  groupLabel: string
  options: string[]
  answer: number
}

function buildRounds(): Round[] {
  const rounds: Round[] = []
  for (const group of ENDING_GROUPS) {
    for (const s of group.sounds) {
      for (const word of s.words) {
        const options = group.sounds.map(x => x.sound).sort(() => Math.random() - 0.5)
        rounds.push({
          word,
          sound: s.sound,
          rule: s.rule,
          groupLabel: group.label,
          options,
          answer: options.indexOf(s.sound),
        })
      }
    }
  }
  return rounds.sort(() => Math.random() - 0.5)
}

const rounds = ref<Round[]>([])
const index = ref(0)
const chosen = ref<number | null>(null)
const correctCount = ref(0)
const wrongCount = ref(0)
const isFinished = computed(() => rounds.value.length > 0 && index.value >= rounds.value.length)
const current = computed(() => rounds.value[index.value])

function play() {
  if (current.value)
    playWord(current.value.word)
}

function start() {
  rounds.value = buildRounds()
  index.value = 0
  chosen.value = null
  correctCount.value = 0
  wrongCount.value = 0
  setTimeout(play, 300)
}

function choose(i: number) {
  if (chosen.value !== null || !current.value)
    return
  chosen.value = i
  if (i === current.value.answer)
    correctCount.value += 1
  else
    wrongCount.value += 1
}

function next() {
  chosen.value = null
  index.value += 1
  setTimeout(play, 300)
}

const accuracy = computed(() => {
  const total = correctCount.value + wrongCount.value
  return total === 0 ? 100 : Math.round(correctCount.value / total * 100)
})

onMounted(start)
</script>

<template>
  <div
    v-if="current && !isFinished"
    class="mx-auto max-w-xl border border-gray-200 rounded-xl bg-white p-6 text-center dark:border-gray-700 dark:bg-gray-800"
  >
    <div class="mb-6">
      <div class="mb-2 flex items-center justify-between text-sm">
        <span>{{ index + 1 }} / {{ rounds.length }}</span>
        <span>
          <span class="text-green-600 dark:text-green-400">✓ {{ correctCount }}</span>
          <span class="mx-1 text-red-500">✗ {{ wrongCount }}</span>
          <span>正确率 {{ accuracy }}%</span>
        </span>
      </div>
      <div class="h-1.5 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700">
        <div
          class="h-full rounded-full bg-primary-500 transition-all duration-300"
          :style="{ width: `${index / rounds.length * 100}%` }"
        />
      </div>
    </div>

    <p class="mb-3 text-sm">
      播放的单词（{{ current.groupLabel }}）词尾读哪个音？
    </p>

    <button
      class="mx-auto mb-6 h-20 w-20 flex cursor-pointer items-center justify-center rounded-full bg-primary-500 text-3xl text-white shadow-lg transition-all duration-200 active:scale-95 hover:bg-primary-600"
      title="重新播放"
      @click="play"
    >
      <div class="i-carbon-volume-up" />
    </button>

    <div class="grid grid-cols-3 gap-3">
      <button
        v-for="(opt, i) in current.options"
        :key="opt"
        class="cursor-pointer border-2 rounded-xl px-4 py-4 text-xl font-bold transition-all duration-200 active:scale-95"
        :class="chosen === null
          ? 'border-gray-200 text-gray-700 hover:border-primary-400 hover:bg-primary-50 hover:text-primary-600 dark:border-gray-600 dark:text-gray-200 dark:hover:border-primary-500 dark:hover:bg-primary-500/10'
          : i === current.answer
            ? 'border-green-500 bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400'
            : i === chosen
              ? 'border-red-500 bg-red-50 text-red-500 dark:bg-red-500/10'
              : 'border-gray-200 opacity-50 dark:border-gray-600'"
        :disabled="chosen !== null"
        @click="choose(i)"
      >
        {{ opt }}
      </button>
    </div>

    <div class="mt-4 min-h-12">
      <template v-if="chosen !== null">
        <p
          class="text-sm font-medium"
          :class="chosen === current.answer ? 'text-green-600 dark:text-green-400' : 'text-red-500'"
        >
          {{ chosen === current.answer ? '✓ 回答正确！' : `✗ ${current.word} 的词尾读 ${current.sound}` }}
          <span class="ml-1 text-gray-400">{{ current.rule }}</span>
        </p>
        <button
          class="mt-2 cursor-pointer rounded-lg bg-primary-500 px-6 py-2 text-sm text-white transition-colors hover:bg-primary-600"
          @click="next"
        >
          下一题
        </button>
      </template>
    </div>
  </div>

  <div
    v-else-if="isFinished"
    class="mx-auto max-w-xl border border-gray-200 rounded-xl bg-white p-8 text-center dark:border-gray-700 dark:bg-gray-800"
  >
    <div class="mb-2 text-5xl">
      {{ accuracy >= 80 ? '🎉' : accuracy >= 60 ? '👍' : '💪' }}
    </div>
    <h4 class="mb-1 text-lg font-semibold text-black dark:text-white">
      练习完成
    </h4>
    <p class="mb-6 text-sm">
      共 {{ rounds.length }} 题 · 正确 {{ correctCount }} · 正确率
      <span
        class="font-semibold"
        :class="accuracy >= 80 ? 'text-green-600 dark:text-green-400' : accuracy >= 60 ? 'text-orange-500' : 'text-red-500'"
      >{{ accuracy }}%</span>
    </p>
    <button
      class="cursor-pointer rounded-lg bg-primary-500 px-6 py-2.5 text-white transition-colors hover:bg-primary-600"
      @click="start"
    >
      再来一轮
    </button>
  </div>
</template>
