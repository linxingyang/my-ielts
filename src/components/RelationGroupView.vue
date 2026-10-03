<script setup lang="ts">
import type { RelationGroupItem, ResolvedRelation } from '~/composables/vocabularyRelation'
import { resolvedRelationGroups } from '~/composables/vocabularyRelation'

// 关联组学习视图：按关联组成组展示（词 + 词性 + 释义对照），支持发音与三态学习状态
const props = defineProps<{
  /** 当前词库 source，仅显示含该词库词条的组 */
  source: string
  /** 播放单词发音（复用父页面播放器逻辑） */
  play: (audioPath: string) => void
}>()

const emit = defineEmits<{
  goto: [relation: ResolvedRelation]
}>()

const typeFilter = ref('')
const typeOptions = computed(() => {
  const types = new Set(resolvedRelationGroups.map(g => g.type))
  return Array.from(types).map(t => ({
    value: t,
    label: RELATION_TYPE_META[t]?.label || t,
  }))
})

// 只保留含当前词库词条（>= 2 个）的组；当前词库词条排前
const groups = computed<RelationGroupItem[]>(() => {
  const match = resolvedRelationGroups.filter(g =>
    typeFilter.value ? g.type === typeFilter.value : true)
    .map(g => ({
      ...g,
      members: [...g.members].sort((a, b) =>
        (a.source === props.source ? 0 : 1) - (b.source === props.source ? 0 : 1)),
    }))
    .filter(g => g.members.filter(m => m.source === props.source).length >= 2)
  return match
})

// 懒加载：数据量大（数百组），先渲染一部分，点击加载更多
const PAGE_SIZE = 50
const visibleCount = ref(PAGE_SIZE)
const visibleGroups = computed(() => groups.value.slice(0, visibleCount.value))
watch([typeFilter, () => props.source], () => {
  visibleCount.value = PAGE_SIZE
})

const typeBadgeClass: Record<string, string> = {
  root: 'bg-blue-100 text-blue-700 border border-blue-300 dark:bg-transparent dark:text-blue-400 dark:border-blue-700',
  syn: 'bg-green-100 text-green-700 border border-green-300 dark:bg-transparent dark:text-green-400 dark:border-green-700',
  ant: 'bg-red-100 text-red-700 border border-red-300 dark:bg-transparent dark:text-red-400 dark:border-red-700',
  der: 'bg-purple-100 text-purple-700 border border-purple-300 dark:bg-transparent dark:text-purple-400 dark:border-purple-700',
  sim: 'bg-orange-100 text-orange-700 border border-orange-300 dark:bg-transparent dark:text-orange-400 dark:border-orange-600',
}

function statusIcon(status: string) {
  return {
    known: 'i-ph-check-circle-bold text-green-500',
    fuzzy: 'i-ph-circle-half-bold text-yellow-500',
    unknown: 'i-ph-circle-dashed text-gray-400 dark:text-gray-500',
  }[status] || ''
}

const statusTitleMap: Record<string, string> = {
  known: '已认识（点击改为未学）',
  fuzzy: '模糊（点击改为已认识）',
  unknown: '未学（点击改为模糊）',
}
</script>

<template>
  <div>
    <!-- 工具条：类型筛选 + 统计 -->
    <div class="mb-3 flex flex-wrap items-center gap-2">
      <select
        v-model="typeFilter"
        class="block w-36 border border-gray-300 rounded-lg bg-gray-50 p-2 text-sm text-gray-900 dark:border-gray-600 focus:border-blue-500 dark:bg-gray-700 dark:text-white focus:ring-blue-500 dark:focus:border-blue-500"
      >
        <option value="">
          全部类型
        </option>
        <option v-for="t in typeOptions" :key="t.value" :value="t.value">
          {{ t.label }}
        </option>
      </select>
      <span class="text-sm text-gray-500 dark:text-gray-400">
        共 <b>{{ groups.length }}</b> 组（当前词库命中 {{ groups.reduce((s, g) => s + g.members.filter(m => m.source === source).length, 0) }} 词）
      </span>
    </div>

    <!-- 关联组卡片流 -->
    <div class="flex flex-col gap-3">
      <div
        v-for="(g, gi) in visibleGroups"
        :key="`${g.type}_${g.root}_${g.members.map(m => m.word).join('_')}`"
        class="border border-gray-200 rounded-lg bg-white p-3 shadow-sm transition-colors dark:border-gray-700 dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50"
      >
        <div class="mb-2 flex items-center gap-2">
          <span :class="typeBadgeClass[g.type]" class="inline-block rounded px-2 py-0.5 text-xs font-medium">
            {{ g.typeLabel }}
          </span>
          <span v-if="g.root" class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ g.root }}</span>
          <span class="ml-auto text-xs text-gray-400">{{ gi + 1 }}</span>
        </div>
        <div
          v-for="m in g.members"
          :key="`${m.source}_${m.id}`"
          class="flex flex-wrap items-center gap-x-3 gap-y-1 rounded px-2 py-1.5"
          :class="m.source === source ? '' : 'opacity-60'"
        >
          <i
            class="i-ph-speaker-simple-high-bold inline-block shrink-0 cursor-pointer text-gray-500 dark:text-gray-400"
            title="播放发音"
            @click="play(wordAudioUrl(m.word))"
          />
          <i
            :class="statusIcon(getWordStatus(m.word))"
            :title="statusTitleMap[getWordStatus(m.word)]"
            class="inline-block shrink-0 cursor-pointer align-middle text-base"
            @click="cycleWordStatus(m.word)"
          />
          <span class="min-w-24 text-base font-bold text-gray-900 dark:text-white">{{ m.word }}</span>
          <span class="shrink-0 text-xs italic text-gray-400">{{ m.pos }}</span>
          <span class="flex-1 text-sm text-gray-600 dark:text-gray-300">{{ m.meaning }}</span>
          <span
            v-if="m.source !== source"
            class="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500 dark:bg-gray-600 dark:text-gray-300"
            :title="`位于 ${m.sourceLabel} · ${m.chapter}`"
          >{{ m.sourceLabel }}</span>
          <i
            class="i-ph-arrow-square-out inline-block shrink-0 cursor-pointer text-gray-400"
            title="跳转到词条"
            @click="emit('goto', m)"
          />
        </div>
      </div>
    </div>

    <!-- 加载更多 -->
    <div v-if="visibleCount < groups.length" class="mt-4 text-center">
      <button
        type="button"
        class="inline-block border border-gray-300 rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-700 dark:border-gray-600 dark:bg-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-600"
        @click="visibleCount += PAGE_SIZE"
      >
        加载更多（{{ groups.length - visibleCount }} 组）
      </button>
    </div>
    <div v-if="!groups.length" class="py-8 text-center text-sm text-gray-400">
      当前词库暂无该类型的关联组
    </div>
  </div>
</template>
