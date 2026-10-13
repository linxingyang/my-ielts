<script setup lang="ts">
import { SPELLING_GROUPS } from '~/data/spelling'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

const { playWord } = usePhonemeAudio()

// ---- 分组浏览 ----
const activeId = ref(SPELLING_GROUPS[0].key)
const activeGroup = computed(() =>
  SPELLING_GROUPS.find(g => g.key === activeId.value) || SPELLING_GROUPS[0])

const playingWord = ref('')
function play(word: string) {
  playingWord.value = word
  playWord(word)
  setTimeout(() => {
    if (playingWord.value === word)
      playingWord.value = ''
  }, 1200)
}

// 拆分单词为 前缀/目标字母/后缀 三段用于高亮
function parts(word: string, part: string): string[] {
  const i = word.toLowerCase().indexOf(part.toLowerCase())
  if (i < 0)
    return [word, '', '']
  return [word.slice(0, i), word.slice(i, i + part.length), word.slice(i + part.length)]
}

// ---- 听音选读音练习：播放单词，选出目标字母组合在词中的读音 ----
interface Round {
  word: string
  part: string
  tip: string
  options: string[]
  answer: number
}

function buildRounds(): Round[] {
  const sounds = [...new Set(activeGroup.value.rules.map(r => r.sound))]
  const rounds: Round[] = []
  for (const rule of activeGroup.value.rules) {
    for (const e of rule.examples) {
      const options = [...sounds].sort(() => Math.random() - 0.5)
      rounds.push({
        word: e.word,
        part: e.part,
        tip: rule.tip,
        options,
        answer: options.indexOf(rule.sound),
      })
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
  if (i === current.value.answer)
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
          拼读规则
        </h3>
        <p class="mt-1 text-sm">
          同样的字母组合读音可能不同（meat / bread），点击例词听发音；下方小练习检验听音辨拼写
        </p>
      </div>
      <AccentToggle />
    </div>

    <!-- 分组选择器 -->
    <div class="mb-5 flex flex-wrap gap-2">
      <button
        v-for="g in SPELLING_GROUPS"
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

    <!-- 规则浏览 -->
    <div class="mb-8 border border-gray-200 rounded-xl bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <p class="mb-4 text-sm leading-6">
        {{ activeGroup.desc }}
      </p>
      <div class="grid gap-3 lg:grid-cols-3 md:grid-cols-2 sm:grid-cols-1">
        <div
          v-for="rule in activeGroup.rules"
          :key="rule.sound"
          class="border border-gray-100 rounded-xl bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-700/40"
        >
          <div class="mb-1 flex items-center gap-2">
            <span class="rounded-md bg-primary-600 px-2 py-0.5 text-sm font-bold text-white">{{ rule.letters }}</span>
            <span class="text-xs text-gray-400">读作</span>
            <span class="text-lg font-bold text-primary-500 dark:text-primary-400">{{ rule.sound }}</span>
          </div>
          <p class="mb-2 text-xs text-gray-400">
            {{ rule.tip }}
          </p>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="e in rule.examples"
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

    <!-- 听音选读音练习 -->
    <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h4 class="text-lg font-semibold text-black dark:text-white">
        小练习：听词选读音
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

      <p class="mb-3 text-sm">
        播放的单词中，目标字母组合读哪个音？
      </p>

      <button
        class="mx-auto mb-6 h-20 w-20 flex cursor-pointer items-center justify-center rounded-full bg-primary-500 text-3xl text-white shadow-lg transition-all duration-200 active:scale-95 hover:bg-primary-600"
        title="重新播放"
        @click="playCurrent"
      >
        <div class="i-carbon-volume-up" />
      </button>

      <div class="grid gap-3" :class="current.options.length >= 3 ? 'sm:grid-cols-3' : 'sm:grid-cols-2'">
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

      <div class="mt-4 min-h-14">
        <template v-if="chosen !== null">
          <p
            class="text-sm font-medium"
            :class="chosen === current.answer ? 'text-green-600 dark:text-green-400' : 'text-red-500'"
          >
            {{ chosen === current.answer ? '✓ 回答正确！' : '✗ 再听一遍感受差异' }}
            <span class="ml-1 text-gray-400">
              {{ parts(current.word, current.part)[0] }}<span class="font-bold text-primary-500">{{ parts(current.word, current.part)[1] }}</span>{{ parts(current.word, current.part)[2] }}
              · {{ current.tip }}
            </span>
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
      <RouterLink to="/speaking/phonetics" class="text-primary-500 hover:underline">
        ← 音标学习
      </RouterLink>
      <RouterLink to="/speaking/clusters" class="text-primary-500 hover:underline">
        下一步：辅音连缀 →
      </RouterLink>
    </div>
  </div>
</template>
