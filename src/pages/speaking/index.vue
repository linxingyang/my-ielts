<script setup lang="ts">
const modules = [
  {
    to: '/speaking/phonetics',
    icon: 'i-carbon-translate',
    title: '音标学习',
    desc: '44 个音素分类浏览：单元音、双元音、清辅音、浊辅音，含发音要点（口型/舌位）与例词，点击即听',
    tags: ['44 音素', '发音要点', '例词跟读'],
  },
  {
    to: '/speaking/minimal-pairs',
    icon: 'i-carbon-compare',
    title: '易错音对比',
    desc: '中国人最易读错的音对比组：/e/ vs /æ/、/θ/ vs /s/、/v/ vs /w/ 等，左右单词点击对比听差异',
    tags: ['对比组', '左右听音', '中文大意'],
  },
  {
    to: '/speaking/practice',
    icon: 'i-carbon-headphones',
    title: '听音辨词',
    desc: '播放一个单词发音，从一对近似音单词中选出听到的那个，检验耳朵是否真能分辨易错音',
    tags: ['二选一', '计分', '正确率'],
  },
]
</script>

<template>
  <div class="px-4 pt-6 text-gray-500 2xl:px-0 dark:text-gray-400">
    <h3 class="mb-2 text-xl font-semibold text-black dark:text-white">
      口语 · 发音练习
    </h3>
    <p class="mb-6 max-w-3xl text-sm leading-6">
      地道的发音从音标开始。这里覆盖英语全部 44 个音素，并针对中国学习者最容易读错的音（如 /e/ 与
      /æ/、/θ/ 与 /s/）设计了对比听音和辨词练习。所有单词发音默认使用美音，可切换英音。
    </p>

    <div class="grid gap-4 md:grid-cols-3 sm:grid-cols-1">
      <RouterLink
        v-for="m in modules"
        :key="m.to"
        :to="m.to"
        class="group border border-gray-200 rounded-xl bg-white p-5 transition-all duration-200 dark:border-gray-700 hover:border-primary-400 dark:bg-gray-800 hover:shadow-lg hover:-translate-y-0.5 dark:hover:border-primary-400"
      >
        <div class="mb-3 flex items-center gap-3">
          <div class="h-11 w-11 flex items-center justify-center rounded-lg bg-primary-100 text-2xl text-primary-600 transition-colors dark:bg-primary-500/15 group-hover:bg-primary-500 dark:text-primary-400 group-hover:text-white">
            <div :class="m.icon" />
          </div>
          <div class="text-lg font-semibold text-black transition-colors dark:text-white group-hover:text-primary-500">
            {{ m.title }}
          </div>
        </div>
        <p class="mb-4 text-sm leading-6">
          {{ m.desc }}
        </p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="t in m.tags"
            :key="t"
            class="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs dark:bg-gray-700"
          >{{ t }}</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
