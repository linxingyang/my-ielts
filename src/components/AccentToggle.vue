<script setup lang="ts">
import { usePhonemeAudio } from '~/composables/usePhonemeAudio'

const { accent } = usePhonemeAudio()

const options = [
  { value: 'us', label: '美音' },
  { value: 'uk', label: '英音' },
] as const
</script>

<template>
  <div class="inline-flex items-center rounded-full bg-gray-100 p-1 text-sm dark:bg-gray-800">
    <button
      v-for="op in options"
      :key="op.value"
      class="cursor-pointer rounded-full px-3 py-1 transition-all duration-200"
      :class="accent === op.value
        ? 'bg-primary-500 text-white shadow-sm'
        : 'text-gray-500 hover:text-primary-500 dark:text-gray-400'"
      @click="accent = op.value"
    >
      {{ op.label }}
    </button>
  </div>
</template>
