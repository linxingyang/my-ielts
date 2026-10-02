import type { RemovableRef } from '@vueuse/core'
import { useLocalStorage } from '@vueuse/core'

export type WordStatus = 'known' | 'fuzzy' | 'unknown'

const STATUS_KEY = 'vocabulary_word_status'
const CORRECT_KEY = 'vocabulary_word_correct'

// key 为单词本身（word[0]），与 vocabulary.js 的数字 id 解耦，避免数据重排丢失状态
const wordStatusMap: RemovableRef<Record<string, WordStatus>> = useLocalStorage(STATUS_KEY, {})
const wordCorrectMap: RemovableRef<Record<string, number>> = useLocalStorage(CORRECT_KEY, {})

const STATUS_ORDER: WordStatus[] = ['unknown', 'fuzzy', 'known']

export function getWordStatus(word: string): WordStatus {
  return wordStatusMap.value[word] || 'unknown'
}

export function setWordStatus(word: string, status: WordStatus) {
  wordStatusMap.value = { ...wordStatusMap.value, [word]: status }
}

export function cycleWordStatus(word: string) {
  const current = getWordStatus(word)
  const next = STATUS_ORDER[(STATUS_ORDER.indexOf(current) + 1) % STATUS_ORDER.length]
  setWordStatus(word, next)
}

// 打字练习答对后调用：unknown -> fuzzy，累计答对 2 次升级为 known
// 返回升级后的状态
export function recordCorrectTyping(word: string): WordStatus {
  const count = (wordCorrectMap.value[word] || 0) + 1
  wordCorrectMap.value = { ...wordCorrectMap.value, [word]: count }

  const current = getWordStatus(word)
  if (count >= 2 && current !== 'known') {
    setWordStatus(word, 'known')
    return 'known'
  }
  if (current === 'unknown') {
    setWordStatus(word, 'fuzzy')
    return 'fuzzy'
  }
  return current
}

export function chapterProgress(words: { word: string[] }[]) {
  const progress = { known: 0, fuzzy: 0, unknown: 0 }
  for (const item of words)
    progress[getWordStatus(item.word[0])]++
  return progress
}

export function exportWordStatus(): string {
  return JSON.stringify({
    version: 1,
    exportedAt: new Date().toISOString(),
    status: wordStatusMap.value,
    correct: wordCorrectMap.value,
  }, null, 2)
}

export function importWordStatus(json: string): boolean {
  try {
    const data = JSON.parse(json)
    if (typeof data !== 'object' || data === null)
      return false
    if (typeof data.status !== 'object' || data.status === null)
      return false
    wordStatusMap.value = data.status
    if (typeof data.correct === 'object' && data.correct !== null)
      wordCorrectMap.value = data.correct
    return true
  }
  catch {
    return false
  }
}
