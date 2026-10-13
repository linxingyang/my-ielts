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
    to: '/speaking/spelling',
    icon: 'i-carbon-text-font',
    title: '拼读规则',
    desc: '同样的字母组合读音可能不同：ea 在 meat/bread、oo 在 book/food 中怎么读？附听词选读音小练习',
    tags: ['字母组合', '一形多音', '听音选读音'],
  },
  {
    to: '/speaking/clusters',
    icon: 'i-carbon-group-objects',
    title: '辅音连缀',
    desc: '词首/词中/词尾辅音连缀（tr-、-mpl、-st）：不加元音、不吞音，连缀字母高亮 + 全部连播跟读',
    tags: ['词首/词中/词尾', '连缀高亮', '连播跟读'],
  },
  {
    to: '/speaking/stress',
    icon: 'i-carbon-meter',
    title: '单词重音',
    desc: '音节方块可视化：双音节词、多音节词、复合词重音规律（REcord 名词 / reCORD 动词），附重音听辨练习',
    tags: ['音节可视化', '复合词重音', '重音听辨'],
  },
  {
    to: '/speaking/practice',
    icon: 'i-carbon-headphones',
    title: '听音辨词',
    desc: '五种模式综合检验：易错音二选一、同音词听辨、数字辨析（thirteen/thirty）、-ed/-s 词尾、字母听写',
    tags: ['同音词', '数字辨析', '字母听写', '计分'],
  },
]
</script>

<template>
  <div class="px-4 pt-6 text-gray-500 2xl:px-0 dark:text-gray-400">
    <h3 class="mb-2 text-xl font-semibold text-black dark:text-white">
      口语 · 发音练习
    </h3>
    <p class="mb-6 max-w-3xl text-sm leading-6">
      地道的发音从音标开始。按学习进阶路线练习：先认识 44 个音素、分清易错音，再掌握拼写与读音的对应、
      辅音连缀和单词重音，最后用综合听辨练习检验。所有单词发音默认使用美音，可切换英音。
      内容参考《English Pronunciation in Use - Elementary》。
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
