<script setup lang="ts">
import { PHONEME_CATEGORIES } from '~/data/phonetics'
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

const { playWord, playSequence } = usePhonemeAudio()

const activeKey = ref(PHONEME_CATEGORIES[0].key)
const activeCategory = computed(() =>
  PHONEME_CATEGORIES.find(c => c.key === activeKey.value) || PHONEME_CATEGORIES[0])

// 正在播放的单词（发声动画用）
const playingWord = ref('')

function play(word: string) {
  playingWord.value = word
  playWord(word)
  setTimeout(() => {
    if (playingWord.value === word)
      playingWord.value = ''
  }, 1200)
}

function playAll(phoneme: typeof PHONEME_CATEGORIES[0]['phonemes'][0]) {
  const list = phoneme.examples
  playSequence(list, 800, (w, i, total) => {
    playingWord.value = w
    // 最后一个单词开始播放后 1.2s 清除高亮
    if (i === total - 1)
      setTimeout(() => { playingWord.value = '' }, 1200)
  })
}
</script>

<template>
  <div class="px-4 pt-6 text-gray-500 2xl:px-0 dark:text-gray-400">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 class="text-xl font-semibold text-black dark:text-white">
          音标学习
        </h3>
        <p class="mt-1 text-sm">
          {{ activeCategory.desc }} · 点击单词听发音，可整组连读
        </p>
      </div>
      <AccentToggle />
    </div>

    <!-- 分类 tab -->
    <div class="mb-5 flex flex-wrap gap-2">
      <button
        v-for="c in PHONEME_CATEGORIES"
        :key="c.key"
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="activeKey === c.key
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="activeKey = c.key"
      >
        {{ c.label }} <span class="opacity-70">{{ c.phonemes.length }}</span>
      </button>
    </div>

    <!-- 音素卡片网格 -->
    <div class="grid gap-4 md:grid-cols-2 sm:grid-cols-1 xl:grid-cols-3">
      <div
        v-for="p in activeCategory.phonemes"
        :key="p.symbol"
        class="border border-gray-200 rounded-xl bg-white p-4 transition-all duration-200 dark:border-gray-700 hover:border-primary-300 dark:bg-gray-800 hover:shadow-md dark:hover:border-primary-500"
      >
        <div class="mb-2 flex items-start justify-between gap-2">
          <div class="flex items-baseline gap-3">
            <span class="text-3xl font-bold text-primary-500">{{ p.symbol }}</span>
            <span class="text-sm text-gray-400">{{ p.name }}</span>
          </div>
          <button
            class="shrink-0 cursor-pointer rounded-full bg-primary-100 px-3 py-1 text-xs text-primary-600 transition-colors dark:bg-primary-500/15 hover:bg-primary-500 dark:text-primary-400 hover:text-white"
            title="整组连读"
            @click="playAll(p)"
          >
            <div class="align-[-2px] i-carbon-play mr-1 inline-block" />
            连读
          </button>
        </div>
        <p class="mb-3 text-sm leading-5.5">
          {{ p.tips }}
        </p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="w in p.examples"
            :key="w"
            class="cursor-pointer border border-gray-200 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 transition-all duration-150 active:scale-95 dark:border-gray-600 hover:border-primary-400 hover:bg-primary-50 dark:text-gray-200 hover:text-primary-600 dark:hover:border-primary-500 dark:hover:bg-primary-500/10 dark:hover:text-primary-400"
            :class="playingWord === w && 'border-primary-500 bg-primary-50 text-primary-600 dark:bg-primary-500/15'"
            @click="play(w)"
          >
            <div
              class="align-[-1px] mr-1 inline-block"
              :class="playingWord === w ? 'i-carbon-volume-up animate-pulse' : 'i-carbon-volume-down'"
            />
            {{ w }}
          </button>
        </div>
      </div>
    </div>

    <div class="mt-6 flex flex-wrap gap-6 text-sm">
      <RouterLink to="/speaking/minimal-pairs" class="text-primary-500 hover:underline">
        下一步：易错音对比 →
      </RouterLink>
      <RouterLink to="/speaking/practice" class="text-primary-500 hover:underline">
        听音辨词练习 →
      </RouterLink>
    </div>
  </div>
</template>
