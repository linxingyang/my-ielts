import audioIndex from '~/pages/speaking/audioIndex.json'
import { accent, type Accent } from './accent'

export type { Accent }

/** word(小写) → 本地音频相对路径（us/uk 两套） */
const INDEX = audioIndex as Record<string, Partial<Record<Accent, string>>>

// 模块级单例：同一时刻只播放一个音频；序列令牌用于取消未播放的后续单词
let audio: HTMLAudioElement | null = null
let seqToken = 0

// 0.3 秒静音 wav，用于首次用户交互时预热音频输出流
// （Chrome/Edge 页面首次发声时才创建输出流，可能吞掉第一个音频的开头）
const SILENT_WAV = 'data:audio/wav;base64,UklGRuQSAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YcASAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='

let unlockBound = false
function bindAudioUnlock() {
  if (unlockBound || typeof window === 'undefined')
    return
  unlockBound = true
  const prime = () => {
    if (!audio)
      audio = new Audio()
    // 静音预热：提前打开音频输出流，真实播放时不再有启动延迟
    audio.src = SILENT_WAV
    audio.play().catch(() => {})
  }
  window.addEventListener('pointerdown', prime, { once: true, capture: true })
  window.addEventListener('keydown', prime, { once: true, capture: true })
}

export function usePhonemeAudio() {
  bindAudioUnlock()

  /** 单词发音地址：优先本地音频索引，缺失时在线兜底有道 dictvoice */
  function wordAudioUrl(word: string): string {
    const w = word.trim()
    const local = INDEX[w.toLowerCase()]?.[accent.value]
    if (local)
      return `/${local}`
    const type = accent.value === 'uk' ? 1 : 2
    return `https://dict.youdao.com/dictvoice?type=${type}&audio=${encodeURIComponent(w)}`
  }

  /** 播放单词发音（美音/英音跟随当前口音设置），并取消进行中的连播队列 */
  function playWord(word: string) {
    seqToken++
    if (!audio)
      audio = new Audio()
    audio.pause()
    audio.src = wordAudioUrl(word)
    audio.play()
  }

  /**
   * 依次播放多个单词：基于 ended 事件链式衔接，上一个真正播完再停顿 pause 毫秒播下一个；
   * playWord / 新的 playSequence 会通过令牌取消旧队列。
   * onWord(word, index, total) 用于页面同步高亮当前播放的单词。
   */
  function playSequence(words: string[], pause = 500, onWord?: (word: string, index: number, total: number) => void) {
    const token = ++seqToken
    if (!audio)
      audio = new Audio()
    audio.pause()

    const playAt = (i: number) => {
      if (token !== seqToken || !audio || i >= words.length)
        return
      onWord?.(words[i], i, words.length)
      audio.src = wordAudioUrl(words[i])
      audio.play().catch(() => {})
      const onEnded = () => {
        audio?.removeEventListener('ended', onEnded)
        if (token === seqToken && i + 1 < words.length)
          setTimeout(() => playAt(i + 1), pause)
      }
      audio.addEventListener('ended', onEnded)
    }
    playAt(0)
  }

  return { accent, wordAudioUrl, playWord, playSequence }
}
