<script setup lang="ts">
import { MINIMAL_PAIR_GROUPS } from '~/data/phonetics'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

const { playWord } = usePhonemeAudio()

interface Round {
  groupId: string
  phonemeA: string
  phonemeB: string
  word: string
  other: string
  answer: 'a' | 'b'
  meaning: string
}

const ACCENT_KEY = 'speaking_practice_group'
const groupChoice = useLocalStorage<string>(ACCENT_KEY, 'all')

// 生成一轮练习题目：从所选对比组随机取词，随机答案侧
function buildRounds(): Round[] {
  const groups = groupChoice.value === 'all'
    ? MINIMAL_PAIR_GROUPS
    : MINIMAL_PAIR_GROUPS.filter(g => g.id === groupChoice.value)
  const rounds: Round[] = []
  for (const g of groups) {
    for (const pair of g.pairs) {
      const answer: 'a' | 'b' = Math.random() < 0.5 ? 'a' : 'b'
      rounds.push({
        groupId: g.id,
        phonemeA: g.phonemeA,
        phonemeB: g.phonemeB,
        word: answer === 'a' ? pair.a : pair.b,
        other: answer === 'a' ? pair.b : pair.a,
        answer,
        meaning: pair.meaning,
      })
    }
  }
  return rounds.sort(() => Math.random() - 0.5)
}

const rounds = ref<Round[]>([])
const index = ref(0)
const chosen = ref<'a' | 'b' | ''>('')
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
  chosen.value = ''
  correctCount.value = 0
  wrongCount.value = 0
  setTimeout(play, 300)
}

function choose(side: 'a' | 'b') {
  if (chosen.value || !current.value)
    return
  chosen.value = side
  if (side === current.value.answer)
    correctCount.value += 1
  else
    wrongCount.value += 1
}

function next() {
  chosen.value = ''
  index.value += 1
  setTimeout(play, 300)
}

const accuracy = computed(() => {
  const total = correctCount.value + wrongCount.value
  return total === 0 ? 100 : Math.round(correctCount.value / total * 100)
})

watch(groupChoice, start)
onMounted(start)
</script>

<template>
  <div class="px-4 pt-6 text-gray-500 2xl:px-0 dark:text-gray-400">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 class="text-xl font-semibold text-black dark:text-white">
          听音辨词练习
        </h3>
        <p class="mt-1 text-sm">
          听发音，选出你听到的单词——检验是否真的能分辨易错音
        </p>
      </div>
      <AccentToggle />
    </div>

    <!-- 对比组选择 -->
    <div class="mb-5 flex flex-wrap gap-2">
      <button
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="groupChoice === 'all'
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="groupChoice = 'all'"
      >
        全部
      </button>
      <button
        v-for="g in MINIMAL_PAIR_GROUPS"
        :key="g.id"
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="groupChoice === g.id
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="groupChoice = g.id"
      >
        {{ g.phonemeA }} vs {{ g.phonemeB }}
      </button>
    </div>

    <div
      v-if="current && !isFinished"
      class="mx-auto max-w-xl border border-gray-200 rounded-xl bg-white p-6 text-center dark:border-gray-700 dark:bg-gray-800"
    >
      <!-- 进度与计分 -->
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

      <!-- 播放按钮 -->
      <button
        class="mx-auto mb-6 h-20 w-20 flex cursor-pointer items-center justify-center rounded-full bg-primary-500 text-3xl text-white shadow-lg transition-all duration-200 active:scale-95 hover:bg-primary-600"
        title="重新播放"
        @click="play"
      >
        <div class="i-carbon-volume-up" />
      </button>

      <!-- 二选一 -->
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="side in ['a', 'b'] as const"
          :key="side"
          class="cursor-pointer border-2 rounded-xl px-4 py-4 text-xl font-bold transition-all duration-200 active:scale-95"
          :class="!chosen
            ? 'border-gray-200 text-gray-700 hover:border-primary-400 hover:bg-primary-50 hover:text-primary-600 dark:border-gray-600 dark:text-gray-200 dark:hover:border-primary-500 dark:hover:bg-primary-500/10'
            : side === current.answer
              ? 'border-green-500 bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400'
              : side === chosen
                ? 'border-red-500 bg-red-50 text-red-500 dark:bg-red-500/10'
                : 'border-gray-200 opacity-50 dark:border-gray-600'"
          :disabled="!!chosen"
          @click="choose(side)"
        >
          {{ side === 'a' ? current.word : current.other }}
        </button>
      </div>

      <!-- 反馈 -->
      <div class="mt-4 h-12">
        <template v-if="chosen">
          <p
            class="text-sm font-medium"
            :class="chosen === current.answer ? 'text-green-600 dark:text-green-400' : 'text-red-500'"
          >
            {{ chosen === current.answer ? '✓ 回答正确！' : `✗ 应该是 ${current.word}` }}
            <span class="ml-1 text-gray-400">（{{ current.meaning }} · {{ current.answer === 'a' ? current.phonemeA : current.phonemeB }}）</span>
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

    <!-- 结束摘要 -->
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

    <div class="mt-6 text-sm">
      <RouterLink to="/speaking/minimal-pairs" class="text-primary-500 hover:underline">
        ← 返回易错音对比
      </RouterLink>
    </div>
  </div>
</template>
