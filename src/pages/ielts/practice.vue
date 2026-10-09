<script setup lang="ts" generic="T extends any, O extends any">
import words from './listening179.json'

const ws = reactive(words.map((v) => {
  const item = {
    ...v,
    form: {
      word: '',
      replaceStr: '',
    },
    result: {
      checked: false,
      errorWords: [],
    },
  }
  return item
}))

function onKeydown(e, word) {
  if (e.key === '`') {
    e.preventDefault()
    play(word)
  }
}

function play(word: string) {
  const audio = document.createElement('audio')
  audio.src = `/179_audios/${word}.mp3`
  audio.play()
}
function next(index: number) {
  const i = index + 1
  if (i >= words.length)
    return

  // 校验结果
  const cw = ws[index]

  // 处理词
  const practiceWord = cw.form.word.trim().toLowerCase()
  const practiceReplace = cw.form.replaceStr.split(/[,，]/).map(v => v.trim().toLowerCase().replace(/\s+/g, ' '))
  // window.console.log(practiceReplace, practiceWord)

  const errorWords = []
  if (practiceWord !== cw.word)
    errorWords.push(cw.word)

  errorWords.push(...cw.replace.filter((w) => {
    return !practiceReplace.includes(w)
  }))
  cw.result.checked = true
  cw.result.errorWords = errorWords

  // window.console.log(cw)

  const nw = words[i]
  play(nw.word)
  // 光标移动到下一个输入框
  document.getElementById(`input_${i + 1}`)?.focus()
}
</script>

<template>
  <div>
    <div class="relative overflow-x-auto">
      <div class="mb-3">
        <button class="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-medium text-white dark:bg-blue-600 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:hover:bg-blue-700 dark:focus:ring-blue-800" @click="() => { play(words[0].word) }">
          开始
        </button>
      </div>
      <table class="w-full text-left text-sm text-gray-500 dark:text-gray-400">
        <thead class="bg-gray-50 text-xs uppercase text-gray-700 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            <th class="w-0 px-3 py-3 sm:px-6">
              #
            </th>

            <th class="w-0 px-3 py-3 sm:px-6">
              词性
            </th>
            <th class="w-20 px-3 py-3 sm:px-6">
              音频
            </th>
            <th class="px-3 py-3 sm:px-6">
              考点词/同义替换
            </th>
            <th class="px-3 py-3 sm:px-6">
              结果
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(w, i) in ws" :key="w.index" class="border-b bg-white dark:border-gray-700 dark:bg-gray-800">
            <td class="px-3 py-4 sm:px-6">
              {{ w.index }}
            </td>
            <td class="px-3 py-4 sm:px-6 italic">
              {{ w.type }}
            </td>
            <td class="px-3 py-4 sm:px-6">
              <button class="i-carbon-volume-up-filled p-2 text-xl" @click="play(w.word)" />
            </td>
            <td
              class="flex flex-col items-start gap-2 px-3 py-4 sm:flex-row sm:items-center sm:gap-0 sm:px-6"
              @keydown="onKeydown($event, w.word)"
            >
              <input
                :id="`input_${w.index}`"
                v-model="w.form.word"
                class="w-full sm:w-[150px]"
                p="x-2 y-1"
                w="150px"
                bg="transparent"
                border="~ rounded gray-200 dark:gray-700"
                outline="none active:none"
                spellcheck="false"
                type="text"
                placeholder="请输入..."
              >
              <div class="px-4">
                {{ w.meaning }}
              </div>
              <input
                v-model="w.form.replaceStr"
                class="w-full sm:w-[300px]"
                p="x-2 y-1"
                w="300px"
                bg="transparent"
                border="~ rounded gray-200 dark:gray-700"
                outline="none active:none"
                type="text"
                spellcheck="false"
                placeholder="请输入..."
                @keydown.enter="next(i)"
              >
            </td>
            <td class="px-3 py-4 sm:px-6">
              <i v-if="w.result.checked && w.result.errorWords.length < 1" class="i-carbon-checkmark block text-green-700" />
              <p v-if="w.result.checked && w.result.errorWords.length > 0">
                {{ w.result.errorWords.join(', ') }}
              </p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
