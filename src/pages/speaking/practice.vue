<script setup lang="ts">
import { MINIMAL_PAIR_GROUPS } from '~/data/phonetics'
import { HOMOPHONE_GROUPS } from '~/data/homophones'
import { NUMBER_PAIR_GROUPS } from '~/data/numbers'
import type { PairGroup } from '~/components/speaking/PairQuiz.vue'

// 练习模式 tab：易错音（原有）+ 同音词/数字辨析/-ed-s 结尾/字母听写
const MODE_KEY = 'speaking_practice_mode'
const modes = [
  { key: 'pairs', label: '易错音', desc: '听发音，选出你听到的单词——检验是否真的能分辨易错音' },
  { key: 'homophones', label: '同音词', desc: '同音词发音完全相同，只能靠拼写和语境区分——听音选拼写的终极考验' },
  { key: 'numbers', label: '数字辨析', desc: 'thirTEEN 与 THIRty 靠重音区分，序数词拼写多变——雅思听力数字题高频陷阱' },
  { key: 'endings', label: '-ed / -s 结尾', desc: 'works 读 /s/、needed 读 /ɪd/——听单词辨词尾读音' },
  { key: 'letters', label: '字母听写', desc: '连播字母序列后输入所听内容——雅思听力地名人名拼写基本功' },
] as const

type ModeKey = typeof modes[number]['key']
const mode = useLocalStorage<ModeKey>(MODE_KEY, 'pairs')
const modeDesc = computed(() => modes.find(m => m.key === mode.value)?.desc || '')

// PairQuiz 数据源：易错音/同音词/数字词三模式共用同一交互
const pairGroups = computed<PairGroup[]>(() => {
  if (mode.value === 'homophones') {
    return HOMOPHONE_GROUPS.map(g => ({
      id: g.id,
      label: g.id === 'basic' ? '基础' : '进阶',
      pairs: g.pairs,
    }))
  }
  if (mode.value === 'numbers') {
    return NUMBER_PAIR_GROUPS.map(g => ({
      id: g.id,
      label: g.id === 'teens-vs-tens' ? 'teens vs tens' : '基数 vs 序数',
      pairs: g.pairs,
    }))
  }
  return MINIMAL_PAIR_GROUPS.map(g => ({
    id: g.id,
    label: `${g.phonemeA} vs ${g.phonemeB}`,
    pairs: g.pairs,
  }))
})
</script>

<template>
  <div class="px-4 pt-6 text-gray-500 2xl:px-0 dark:text-gray-400">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 class="text-xl font-semibold text-black dark:text-white">
          听音辨词练习
        </h3>
        <p class="mt-1 text-sm">
          {{ modeDesc }}
        </p>
      </div>
      <AccentToggle />
    </div>

    <!-- 模式 tab -->
    <div class="mb-5 flex flex-wrap gap-2 border-b border-gray-100 pb-3 dark:border-gray-700">
      <button
        v-for="m in modes"
        :key="m.key"
        class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200"
        :class="mode === m.key
          ? 'bg-primary-500 text-white shadow'
          : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'"
        @click="mode = m.key"
      >
        {{ m.label }}
      </button>
    </div>

    <PairQuiz v-if="mode === 'pairs' || mode === 'homophones' || mode === 'numbers'" :key="mode" :groups="pairGroups" />
    <EndingQuiz v-else-if="mode === 'endings'" />
    <LetterDictation v-else />

    <div class="mt-6 flex flex-wrap gap-6 text-sm">
      <RouterLink to="/speaking/stress" class="text-primary-500 hover:underline">
        ← 单词重音
      </RouterLink>
      <RouterLink to="/speaking" class="text-primary-500 hover:underline">
        返回口语栏目
      </RouterLink>
    </div>
  </div>
</template>
