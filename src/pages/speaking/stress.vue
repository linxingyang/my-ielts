<script setup lang="ts">
import { STRESS_GROUPS } from '~/data/stress'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

const { playWord } = usePhonemeAudio()

// ---- 分组浏览 ----
const activeId = ref(STRESS_GROUPS[0].key)
const activeGroup = computed(() =>
  STRESS_GROUPS.find(g => g.key === activeId.value) || STRESS_GROUPS[0])

const playingWord = ref('')
function play(word: string) {
  playingWord.value = word
  playWord(word)
  setTimeout(() => {
    if (playingWord.value === word)
      playingWord.value = ''
  }, 1200)
}

// ---- 听音判断重音位置练习 ----
interface Round {
  word: string
  syllables: string[]
  stress: number
  note?: string
}

function buildRounds(): Round[] {
  return [...activeGroup.value.words].sort(() => Math.random() - 0.5)
}

const rounds = ref<Round[]>([])
const index = ref(0)
const chosen = ref<number | null>(null)
const correctCount = ref(0)
const wrongCount = ref(0)
const isFinished = computed(() => rounds.value.length > 0 && index.value >= rounds.value.length)
const current = computed(() => rounds.value[index.value])

function playCurrent() {
  if (current.value)
    playWord(current.value.word)
}

function start(playFirst = true) {
  rounds.value = buildRounds()
  index.value = 0
  chosen.value = null
  correctCount.value = 0
  wrongCount.value = 0
  // 仅在用户主动点击「重新开始 / 再来一轮」时自动播放；进入页面与切换分组不自动发声
  if (playFirst)
    setTimeout(playCurrent, 300)
}

function choose(i: number) {
  if (chosen.value !== null || !current.value)
    return
  chosen.value = i
  if (i === current.value.stress)
    correctCount.value += 1
  else
    wrongCount.value += 1
}

function next() {
  chosen.value = null
  index.value += 1
  setTimeout(playCurrent, 300)
}

const accuracy = computed(() => {
  const total = correctCount.value + wrongCount.value
  return total === 0 ? 100 : Math.round(correctCount.value / total * 100)
})

watch(activeId, () => start(false))
onMounted(() => start(false))
</script>

<template>
  <div class="px-4 pt-6 text-gray-500 2xl:px-0 dark:text-gray-400">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 class="text-xl font-semibold text-black dark:text-white">
          单词重音
        </h3>
        <p class="mt-1 text-sm">
          重音读错是"听得出发音不对"的最大原因。点击单词听重音；方块图展示音节与重音位置（实心为重音）
        </p>
      </div>
      <AccentToggle />
    </div>

    <!-- 分组选择器 -->
    <div class="mb-5 flex flex-wrap gap-2">
      <button
        v-for="g in STRESS_GROUPS"
        :key="g.key"
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="activeId === g.key
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="activeId = g.key"
      >
        {{ g.label }}
      </button>
    </div>

    <!-- 音节可视化浏览 -->
    <div class="mb-8 border border-gray-200 rounded-xl bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <p class="mb-4 text-sm leading-6">
        {{ activeGroup.desc }}
      </p>
      <div class="grid gap-3 lg:grid-cols-2 md:grid-cols-2 sm:grid-cols-1">
        <div
          v-for="w in activeGroup.words"
          :key="w.word"
          class="flex items-center justify-between border border-gray-100 rounded-xl bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-700/40"
        >
          <div>
            <button
              class="flex cursor-pointer items-center gap-2 text-lg font-bold text-gray-700 transition-colors dark:text-gray-200 hover:text-primary-500 dark:hover:text-primary-400"
              @click="play(w.word)"
            >
              <div class="i-carbon-volume-down" />
              {{ w.word }}
            </button>
            <p v-if="w.note" class="mt-0.5 text-xs text-gray-400">
              {{ w.note }}
            </p>
          </div>
          <!-- 音节方块：重音实心、非重音描边 -->
          <div class="flex items-center gap-1.5">
            <span
              v-for="(syl, i) in w.syllables"
              :key="i"
              class="rounded-md px-2 py-1.5 text-xs font-bold transition-all duration-150"
              :class="i === w.stress
                ? 'bg-primary-500 text-white shadow'
                : 'border border-gray-300 text-gray-400 dark:border-gray-600'"
            >
              {{ syl }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 听音判断重音位置练习 -->
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h4 class="text-lg font-semibold text-black dark:text-white">
        小练习：听音判断重音
      </h4>
      <button
        class="cursor-pointer rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-500 transition-colors dark:bg-gray-800 hover:bg-primary-100 dark:text-gray-400 hover:text-primary-600 dark:hover:bg-gray-700"
        @click="start"
      >
        重新开始
      </button>
    </div>

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
        @click="playCurrent"
      >
        <div class="i-carbon-volume-up" />
      </button>

      <p class="mb-3 text-sm">
        重音在第几个音节？
      </p>
      <div class="grid gap-3" :class="current.syllables.length >= 3 ? 'sm:grid-cols-3' : 'sm:grid-cols-2'">
        <button
          v-for="(syl, i) in current.syllables"
          :key="i"
          class="cursor-pointer border-2 rounded-xl px-4 py-4 transition-all duration-200 active:scale-95"
          :class="chosen === null
            ? 'border-gray-200 text-gray-700 hover:border-primary-400 hover:bg-primary-50 hover:text-primary-600 dark:border-gray-600 dark:text-gray-200 dark:hover:border-primary-500 dark:hover:bg-primary-500/10'
            : i === current.stress
              ? 'border-green-500 bg-green-50 text-green-600 dark:bg-green-500/10 dark:text-green-400'
              : i === chosen
                ? 'border-red-500 bg-red-50 text-red-500 dark:bg-red-500/10'
                : 'border-gray-200 opacity-50 dark:border-gray-600'"
          :disabled="chosen !== null"
          @click="choose(i)"
        >
          <span class="mr-1.5 text-xs text-gray-400">第 {{ i + 1 }} 音节</span>
          <span v-show="chosen !== null" class="text-lg font-bold">{{ syl }}</span>
        </button>
      </div>

      <div class="mt-4 min-h-14">
        <template v-if="chosen !== null">
          <p
            class="text-sm font-medium"
            :class="chosen === current.stress ? 'text-green-600 dark:text-green-400' : 'text-red-500'"
          >
            {{ chosen === current.stress ? '✓ 回答正确！' : `✗ 重音在第 ${current.stress + 1} 音节` }}
            <span class="ml-1 text-gray-400">{{ current.note || current.word }}</span>
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

    <div class="mt-6 flex flex-wrap gap-6 text-sm">
      <RouterLink to="/speaking/clusters" class="text-primary-500 hover:underline">
        ← 辅音连缀
      </RouterLink>
      <RouterLink to="/speaking/practice" class="text-primary-500 hover:underline">
        综合检验：听音辨词练习 →
      </RouterLink>
    </div>
  </div>
</template>
