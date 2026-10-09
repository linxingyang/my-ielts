<script setup lang="ts" generic="T extends any, O extends any">
import words from './listening179.json'

const ws = reactive(words)
function play(word: string) {
  const audio = document.createElement('audio')
  audio.src = `179_audios/${word}.mp3`
  audio.play()
}
</script>

<template>
  <div>
    <div class="relative overflow-x-auto">
      <div class="mb-3">
        <router-link to="/ielts/practice" class="inline-block rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
          练习
        </router-link>
      </div>
      <table class="w-full text-left text-sm text-gray-500 dark:text-gray-400">
        <thead class="bg-gray-50 text-xs uppercase text-gray-700 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            <th class="w-0 px-3 py-3 sm:px-6">
              #
            </th>
            <th class="w-0 px-3 py-3 sm:px-6" />
            <th scope="col" class="w-0 px-3 py-3 sm:px-6">
              考点词
            </th>
            <th scope="col" class="w-0 px-3 py-3 sm:px-6">
              词性
            </th>
            <th scope="col" class="w-80 px-3 py-3 sm:px-6">
              词义
            </th>
            <th scope="col" class="px-3 py-3 sm:px-6">
              同义替换
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in ws" :key="w.index" class="border-b bg-white dark:border-gray-700 dark:bg-gray-800">
            <td class="px-3 py-4 sm:px-6">
              {{ w.index }}
            </td>
            <td class="px-3 py-4 sm:px-6">
              <a href="javascript:;" class="i-carbon-volume-up-filled block p-2 text-xl" @click="play(w.word)" />
            </td>
            <th scope="row" class="whitespace-nowrap px-3 py-4 sm:px-6 font-medium text-gray-900 dark:text-white">
              <a
                :href="`https://dictionary.cambridge.org/dictionary/english-chinese-simplified/${w.word}`"
                target="_blank"
              >{{ w.word }}</a>
            </th>
            <td class="px-3 py-4 sm:px-6 italic">
              {{ w.type }}
            </td>
            <td class="px-3 py-4 sm:px-6">
              {{ w.meaning }}
            </td>
            <td class="px-3 py-4 sm:px-6">
              {{ w.replace.join(', ') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
