<script setup lang="ts">
import { getWordStatus, recordCorrectTyping } from '~/composables/wordStatus'

const { source, sourceOptions, category: selectedChapter, chapterOptions } = useVocabularyCategory('vocabulary_typing_chapter')

const currentWordIndex = ref(0)
const userInput = ref('')
const startTime = ref<number | null>(null)
const wpm = ref(0)
const accuracy = ref(100)
const isFinished = ref(false)

// 当前章节全量数据（按需加载，未就绪时为 undefined）。数据为普通对象，订阅版本号触发重算
const curChapter = computed(() => {
  touchVocabularyData()
  return getChapterData(selectedChapter.value)
})

const words = computed(() => {
  const chapter = curChapter.value
  if (!chapter)
    return []
  // Flatten groups into a single list of words, skip known words
  return chapter.words.flat().filter((item: any) => getWordStatus(item.word[0]) !== 'known')
})

const hiddenCount = computed(() => {
  const chapter = curChapter.value
  if (!chapter)
    return 0
  const all = chapter.words.flat().length
  return all - words.value.length
})

const currentWordData = computed(() => words.value[currentWordIndex.value])
const currentWord = computed(() => currentWordData.value?.word[0] || '')

watch(selectedChapter, (newVal) => {
  localStorage.setItem('vocabulary_typing_chapter', newVal)
  reset()
})

// 章节数据加载完成（首次进入或切换词库后异步到达）时重置练习
watch(curChapter, chapter => chapter && reset())

function reset() {
  currentWordIndex.value = 0
  userInput.value = ''
  startTime.value = null
  wpm.value = 0
  accuracy.value = 100
  isFinished.value = false
  playAudio()
}

let audio = null as HTMLAudioElement | null
function playAudio() {
  const word = currentWord.value
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }
  audio = document.createElement('audio')
  audio.src = wordAudioUrl(word)
  audio.play()
}

// Normalize whitespace: replace non-breaking spaces and other unicode spaces with regular space
function normalizeInput(s: string) {
  return s.replace(/[\u00A0\u2000-\u200B\u202F\u205F\u3000]/g, ' ')
}

function handleInput(e: Event) {
  if (!startTime.value)
    startTime.value = Date.now()

  const rawInput = (e.target as HTMLInputElement).value
  const input = normalizeInput(rawInput)
  userInput.value = input
  // Sync normalized value back to DOM input
  if (rawInput !== input)
    (e.target as HTMLInputElement).value = input

  // Calculate Accuracy
  let correctChars = 0
  for (let i = 0; i < input.length; i++) {
    if (input[i] === currentWord.value[i])
      correctChars++
  }
  accuracy.value = input.length > 0 ? Math.round((correctChars / input.length) * 100) : 100

  // Calculate WPM (Words Per Minute)
  // Standard: 1 word = 5 characters
  const timeElapsed = (Date.now() - startTime.value) / 1000 / 60 // in minutes
  if (timeElapsed > 0)
    wpm.value = Math.round((input.length / 5) / timeElapsed)

  // Check if finished
  if (input === currentWord.value) {
    // 打对自动升级状态：未学 -> 模糊，累计答对 2 次 -> 已认识
    const status = recordCorrectTyping(currentWord.value)
    // 该词升级为"已认识"后会从列表中移除，索引无需再前进
    setTimeout(() => nextWord(status === 'known'), 200)
  }
}

function nextWord(skipAdvance = false) {
  if (!skipAdvance)
    currentWordIndex.value++
  if (currentWordIndex.value < words.value.length) {
    userInput.value = ''
    startTime.value = null
    playAudio()
  }
  else {
    isFinished.value = true
  }
}

// 词库切换时按需加载该词库数据
watch(source, s => loadVocabularySource(s))

onMounted(() => {
  loadVocabularySource(source.value)
  reset()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 px-4 py-12 dark:bg-gray-900 lg:px-8 sm:px-6">
    <div class="mx-auto max-w-3xl">
      <!-- Header -->
      <div class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white">
            单词打字练习
          </h1>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
            照着背景单词输入，提升你的速度
          </p>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-500">
            本次练习 {{ words.length }} 词<template v-if="hiddenCount > 0">
              （已隐藏 {{ hiddenCount }} 个已认识词）
            </template>
          </p>
        </div>
        <div class="flex w-full shrink-0 items-center gap-2 sm:w-auto">
          <select
            v-model="source"
            class="block min-w-0 flex-1 border border-gray-300 rounded-lg bg-white p-2.5 text-sm sm:w-36 sm:flex-none dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500"
          >
            <option
              v-for="s in sourceOptions"
              :key="s.key"
              :value="s.key"
            >
              {{ s.label }}
            </option>
          </select>
          <select
            v-model="selectedChapter"
            class="block min-w-0 flex-1 border border-gray-300 rounded-lg bg-white p-2.5 text-sm sm:w-48 sm:flex-none dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-blue-500"
          >
            <option
              v-for="c in chapterOptions"
              :key="c"
              :value="c"
            >
              {{ c }}
            </option>
          </select>
        </div>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-3 mb-8 gap-2 sm:gap-4">
        <div
          class="border border-gray-200 rounded-xl bg-white p-4 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <div class="mb-1 text-xs tracking-wider uppercase text-gray-500">
            准确率
          </div>
          <div
            class="text-xl font-bold sm:text-2xl"
            :class="accuracy < 90 ? 'text-red-500' : 'text-green-500'"
          >
            {{ accuracy }}%
          </div>
        </div>
        <div
          class="border border-gray-200 rounded-xl bg-white p-4 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <div class="mb-1 text-xs tracking-wider uppercase text-gray-500">
            WPM (速度)
          </div>
          <div class="text-xl font-bold text-blue-500 sm:text-2xl">
            {{ wpm }}
          </div>
        </div>
        <div
          class="border border-gray-200 rounded-xl bg-white p-4 text-center shadow-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <div class="mb-1 text-xs tracking-wider uppercase text-gray-500">
            进度
          </div>
          <div class="text-xl font-bold sm:text-2xl dark:text-white">
            {{ currentWordIndex + 1 }} / {{ words.length }}
          </div>
        </div>
      </div>

      <!-- Typing Area -->
      <div
        class="relative min-h-80 flex flex-col items-center justify-center overflow-hidden border border-gray-200 rounded-2xl bg-white p-8 shadow-lg dark:border-gray-700 dark:bg-gray-800"
      >
        <!-- 章节数据未就绪 -->
        <div v-if="!curChapter" class="text-sm text-gray-400">
          章节词条加载中…
        </div>
        <!-- Container for aligned layers -->
        <div
          v-else
          class="relative mb-8 whitespace-pre-wrap break-all text-center text-4xl font-black tracking-tighter font-mono md:text-7xl sm:text-6xl"
        >
          <!-- Background Word (Grey) -->
          <div class="text-gray-100 dark:text-gray-700">
            {{ currentWord }}
          </div>

          <!-- Feedback Layer (Overlay) -->
          <div class="absolute inset-0 flex">
            <span
              v-for="(char, index) in currentWord"
              :key="index"
              class="inline-block"
              :class="{
                'text-green-500': userInput.charAt(Number(index)) === char,
                'text-red-500': userInput.charAt(Number(index)) !== '' && userInput.charAt(Number(index)) !== char,
                'text-transparent': userInput.charAt(Number(index)) === '',
              }"
            >
              {{ char }}
            </span>
          </div>
        </div>

        <!-- Invisible Input covering the whole area -->
        <input
          v-model="userInput"
          type="text"
          class="absolute inset-0 h-full w-full cursor-default caret-transparent opacity-0"
          autofocus
          autocapitalize="off"
          autocorrect="off"
          autocomplete="off"
          spellcheck="false"
          :disabled="isFinished"
          @input="handleInput"
        >

        <!-- Meaning & Example (Hint) -->
        <div class="w-full border-t border-gray-100 pt-6 text-center dark:border-gray-700">
          <div class="mb-2 text-xl font-medium text-gray-800 dark:text-gray-200">
            <span
              style="font-style: italic; font-family: times;"
              class="mr-2 text-sm font-normal tracking-wide text-gray-400"
            >
              {{ currentWordData?.pos }}
            </span>
            <span class="text-sm">{{ currentWordData?.phonetic }}</span>
            {{ currentWordData?.meaning }}
          </div>
          <p class="mx-auto max-w-xl text-sm italic text-gray-500 sm:text-base dark:text-gray-400">
            {{ currentWordData?.example }}
          </p>
          <p v-if="currentWordData?.translation" class="mx-auto mt-2 max-w-xl text-sm text-gray-600 sm:text-base dark:text-gray-300">
            {{ currentWordData?.translation }}
          </p>
        </div>

        <!-- Audio trigger hint -->
        <div class="absolute right-4 top-4">
          <button
            class="p-2 text-gray-400 transition-colors hover:text-blue-500"
            @click="playAudio"
          >
            <i class="i-ph-speaker-high-bold block text-xl" />
          </button>
        </div>
      </div>

      <!-- Finish Overlay -->
      <div
        v-if="isFinished"
        class="mt-8 animate-bounce rounded-2xl bg-blue-600 p-6 text-center text-white shadow-xl"
      >
        <h2 class="mb-2 text-2xl font-bold">
          太棒了！恭喜完成本章练习 🎉
        </h2>
        <button
          class="mt-4 rounded-full bg-white px-6 py-2 font-bold text-blue-600 transition-colors hover:bg-blue-50"
          @click="reset"
        >
          再练一次
        </button>
      </div>

      <!-- Instructions -->
      <div class="mt-8 text-center text-sm text-gray-400">
        提示：直接开始输入即可，输入正确后会自动进入下一个单词。
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Ensure the input always has focus or can be focused easily */
.relative:focus-within {
  @apply ring-4 ring-blue-500/20 border-blue-500;
}
</style>
