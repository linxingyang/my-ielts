<script setup lang="ts">
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

// 通用二选一听辨练习：给定词对分组（易错音/同音词/数字词共用），播放一个词，选出听到的那个
export interface PairGroup {
  id: string
  label: string
  pairs: Array<{ a: string; b: string; meaning: string }>
}

const props = defineProps<{ groups: PairGroup[] }>()

const { playWord } = usePhonemeAudio()

interface Round {
  groupId: string
  groupLabel: string
  word: string
  other: string
  answer: 'a' | 'b'
  meaning: string
}

const groupChoice = useLocalStorage<string>('speaking_pair_quiz_group', 'all')

function buildRounds(): Round[] {
  const filtered = groupChoice.value === 'all'
    ? props.groups
    : props.groups.filter(g => g.id === groupChoice.value)
  // 切换模式后保存的分组可能不存在，回退到全部
  const gs = filtered.length ? filtered : props.groups
  const rounds: Round[] = []
  for (const g of gs) {
    for (const pair of g.pairs) {
      const answer: 'a' | 'b' = Math.random() < 0.5 ? 'a' : 'b'
      rounds.push({
        groupId: g.id,
        groupLabel: g.label,
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
  <div>
    <!-- 分组选择 -->
    <div v-if="groups.length > 1" class="mb-5 flex flex-wrap gap-2">
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
        v-for="g in groups"
        :key="g.id"
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="groupChoice === g.id
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="groupChoice = g.id"
      >
        {{ g.label }}
      </button>
    </div>

    <!-- 题目卡片 -->
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

      <button
        class="mx-auto mb-6 h-20 w-20 flex cursor-pointer items-center justify-center rounded-full bg-primary-500 text-3xl text-white shadow-lg transition-all duration-200 active:scale-95 hover:bg-primary-600"
        title="重新播放"
        @click="play"
      >
        <div class="i-carbon-volume-up" />
      </button>

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

      <div class="mt-4 h-12">
        <template v-if="chosen">
          <p
            class="text-sm font-medium"
            :class="chosen === current.answer ? 'text-green-600 dark:text-green-400' : 'text-red-500'"
          >
            {{ chosen === current.answer ? '✓ 回答正确！' : `✗ 应该是 ${current.word}` }}
            <span class="ml-1 text-gray-400">（{{ current.meaning }} · {{ current.groupLabel }}）</span>
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
  </div>
</template>
