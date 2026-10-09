<script setup lang="ts" generic="T extends any, O extends any">
import { RouterLink } from 'vue-router'

defineOptions({
  name: 'IndexPage',
})

interface MenuItem {
  label: string
  icon: string
  link: string
  badge?: string
  desc: string
  tags?: string[]
}

const menus = reactive<MenuItem[]>([
  {
    label: '词汇',
    icon: 'i-carbon-chart-histogram',
    link: '/vocabulary',
    badge: '新增',
    desc: '8 大词库：雅思真经、NGSL、牛津 5000、四六级、AWL、NAWL、OPAL',
    tags: ['学习状态过滤', '学习统计', '单词搜索', '英音美音', '例句翻译'],
  },
  {
    label: '语法',
    icon: 'i-carbon-load-balancer-vpc ',
    link: '/grammar',
    desc: '新东方雅思语法课程，针对雅思考试设计，思维导图',
  },
  {
    label: '听力',
    icon: 'i-carbon-headphones',
    link: '/listening',
    desc: '听力基本概念，179 考点词同义替换和雅思王语料库',
  },
  {
    label: '口语',
    icon: 'i-carbon-microphone',
    link: '/speaking',
    badge: '新增',
    desc: '音标学习、易错音对比、听音辨词',
  },
  {
    label: '阅读',
    icon: 'i-carbon-white-paper',
    link: '/reading',
    desc: '538 考点词同义替换',
  },
  {
    label: '写作',
    icon: 'i-carbon-edit',
    link: '/writing',
    desc: '100 句翻译练习、大小作文',
  },
  {
    label: '单词练习',
    icon: 'i-carbon-keyboard',
    link: '/vocabulary/typing',
    desc: '背景单词跟打练习，提升打字速度与单词读写熟悉度',
  },
])
</script>

<template>
  <div class="px-4 pt-6 2xl:px-0">
    <section class="mb-4 border border-gray-200 rounded-lg bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800 sm:p-6">
      <div class="mx-auto max-w-screen-xl px-4 py-8 lg:px-6 sm:py-16">
        <!--<h1 style="font-family: Charmonman;" class="mb-16 text-center text-6xl text-gray-900 dark:text-white">
          Salvation lies within <span class="font-bold text-#f00">IELTS</span>
        </h1>-->
        <div class="mx-auto mb-8 max-w-screen-md text-center lg:mb-16">
          <!--
          <h2 class="mb-4 text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white">
            我的 IELTS 备考中心
          </h2>-->
          <p class="text-gray-500 sm:text-xl dark:text-gray-400">
            项目从 https://github.com/hefengxian/my-ielts fork 而来，感谢原作者的付出。
          </p>
        </div>
        <div class="mx-auto flex max-w-screen-md flex-col gap-6">
          <RouterLink
            v-for="m in menus"
            :key="m.label"
            :to="m.link"
            class="group flex items-center gap-5 rounded-xl border border-gray-100 bg-gray-50 p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:bg-white hover:shadow-md dark:border-gray-700 dark:bg-gray-700/40 dark:hover:border-primary-700 dark:hover:bg-gray-700/70"
          >
            <div class="h-12 w-12 shrink-0 flex items-center justify-center rounded-full bg-primary-100 transition-colors group-hover:bg-primary-200 lg:h-14 lg:w-14 dark:bg-primary-900 dark:group-hover:bg-primary-800">
              <i class="block h-6 w-6 text-primary-600 lg:h-7 lg:w-7 dark:text-primary-300" :class="m.icon" />
            </div>
            <div class="min-w-0">
              <h3 class="mb-1 flex items-center gap-2 text-xl font-bold transition-colors group-hover:text-primary-600 dark:text-white dark:group-hover:text-primary-300">
                {{ m.label }}
                <span
                  v-if="m.badge"
                  class="rounded-full bg-primary-600 px-2 py-0.5 text-xs font-medium text-white"
                >
                  {{ m.badge }}
                </span>
              </h3>
              <p class="text-gray-500 dark:text-gray-400">
                {{ m.desc }}
              </p>
              <div v-if="m.tags?.length" class="mt-2 flex flex-wrap gap-1.5">
                <span
                  v-for="t in m.tags"
                  :key="t"
                  class="rounded-full bg-primary-100/70 px-2.5 py-0.5 text-xs text-primary-700 dark:bg-primary-900/50 dark:text-primary-300"
                >
                  {{ t }}
                </span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>
