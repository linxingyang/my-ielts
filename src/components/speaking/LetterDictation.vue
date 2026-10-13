<script setup lang="ts">
import { ALPHABET } from '~/data/numbers'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

// 字母听写：连播一串字母，输入所听序列（雅思听力地名人名拼写高频场景）
const { playSequence } = usePhonemeAudio()

const LENGTH_KEY = 'speaking_letter_length'
const lengthOptions = [3, 4, 5, 6] as const
const seqLength = useLocalStorage<number>(LENGTH_KEY, 4)

interface Round {
  letters: string[]
}

const round = ref<Round | null>(null)
const input = ref('')
const submitted = ref(false)
const correctCount = ref(0)
const wrongCount = ref(0)
const wasCorrect = computed(() =>
  round.value && input.value.trim().toLowerCase() === round.value.letters.join(''))

function newRound(play = true) {
  const letters = Array.from({ length: seqLength.value }, () =>
    ALPHABET[Math.floor(Math.random() * ALPHABET.length)]!)
  round.value = { letters }
  input.value = ''
  submitted.value = false
  if (play)
    setTimeout(playLetters, 300)
}

function playLetters() {
  if (round.value)
    playSequence(round.value.letters, 900)
}

function submit() {
  if (!round.value || submitted.value || !input.value.trim())
    return
  submitted.value = true
  if (wasCorrect.value)
    correctCount.value += 1
  else
    wrongCount.value += 1
}

watch(seqLength, () => newRound(false))
onMounted(() => newRound(false))
</script>

<template>
  <div class="mx-auto max-w-xl border border-gray-200 rounded-xl bg-white p-6 text-center dark:border-gray-700 dark:bg-gray-800">
    <!-- 计分 -->
    <div class="mb-6 flex items-center justify-between text-sm">
      <span>累计</span>
      <span>
        <span class="text-green-600 dark:text-green-400">✓ {{ correctCount }}</span>
        <span class="mx-1 text-red-500">✗ {{ wrongCount }}</span>
        <span>正确率 {{ correctCount + wrongCount === 0 ? 100 : Math.round(correctCount / (correctCount + wrongCount) * 100) }}%</span>
      </span>
    </div>

    <!-- 字母数量选择 -->
    <div class="mb-6 flex items-center justify-center gap-2 text-sm">
      <span class="text-gray-400">字母数量</span>
      <button
        v-for="n in lengthOptions"
        :key="n"
        class="cursor-pointer rounded-full px-3 py-1 text-xs transition-all duration-200"
        :class="seqLength === n
          ? 'bg-primary-100 text-primary-600 font-medium dark:bg-primary-500/20 dark:text-primary-400'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600'"
        @click="seqLength = n"
      >
        {{ n }}
      </button>
    </div>

    <!-- 播放 -->
    <button
      class="mx-auto mb-6 h-20 w-20 flex cursor-pointer items-center justify-center rounded-full bg-primary-500 text-3xl text-white shadow-lg transition-all duration-200 active:scale-95 hover:bg-primary-600"
      title="播放字母序列"
      @click="playLetters"
    >
      <div class="i-carbon-volume-up" />
    </button>

    <!-- 输入 -->
    <input
      v-model="input"
      type="text"
      placeholder="输入你听到的字母，如 abcd"
      class="mx-auto block w-64 border-2 rounded-xl px-4 py-3 text-center text-xl font-bold tracking-[0.3em] uppercase outline-none transition-colors focus:border-primary-400 dark:bg-gray-700 dark:text-white"
      :disabled="submitted"
      @keydown.enter="submit"
    >

    <div class="mt-4 min-h-12">
      <template v-if="submitted">
        <p
          class="text-sm font-medium"
          :class="wasCorrect ? 'text-green-600 dark:text-green-400' : 'text-red-500'"
        >
          {{ wasCorrect
            ? '✓ 全对！'
            : `✗ 正确答案是 ${round?.letters.join(' ').toUpperCase()}` }}
        </p>
      </template>
      <button
        class="mt-2 cursor-pointer rounded-lg bg-primary-500 px-6 py-2 text-sm text-white transition-colors hover:bg-primary-600"
        @click="submitted ? newRound() : submit()"
      >
        {{ submitted ? '下一题' : '提交' }}
      </button>
    </div>
  </div>
</template>
