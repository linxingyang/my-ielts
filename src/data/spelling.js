// 拼读规则数据（手工维护，可直接编辑）
// 依据《English Pronunciation in Use - Elementary》Unit 1 与附录 E4（spelling-to-sound）
// 同一个字母/字母组合在不同单词里可能读不同音，按"拼写 → 多种读音"组织
// 注意：_fetch_audio.py 会从本文件提取全部例词下载音频（us + uk 两套）

/**
 * @type {Array<{
 *   key: string,
 *   label: string,
 *   desc: string,
 *   rules: Array<{ letters: string, sound: string, tip: string, examples: Array<{ word: string, part: string }> }>
 * }>
 * rules[].examples[].part 为 word 中发该音的字母（用于页面高亮），必须是 word 的子串
 */
export const SPELLING_GROUPS = [
  {
    key: 'ea',
    label: '元音组合 ea',
    desc: '同样的字母组合，读音可能完全不同——背单词时要连发音一起记',
    rules: [
      {
        letters: 'ea',
        sound: '/iː/',
        tip: '最常见的读法，长音 /iː/',
        examples: [{ word: 'meat', part: 'ea' }, { word: 'sea', part: 'ea' }, { word: 'teach', part: 'ea' }, { word: 'dream', part: 'ea' }, { word: 'cheap', part: 'ea' }],
      },
      {
        letters: 'ea',
        sound: '/e/',
        tip: '少数常用词读短音 /e/，极易读错',
        examples: [{ word: 'bread', part: 'ea' }, { word: 'head', part: 'ea' }, { word: 'ready', part: 'ea' }, { word: 'weather', part: 'ea' }, { word: 'heavy', part: 'ea' }],
      },
      {
        letters: 'ea',
        sound: '/eɪ/',
        tip: '极少数词读双元音 /eɪ/',
        examples: [{ word: 'great', part: 'ea' }, { word: 'break', part: 'ea' }],
      },
    ],
  },
  {
    key: 'oo',
    label: '元音组合 oo',
    desc: 'oo 有长短两种读法，book 和 food 不押韵',
    rules: [
      {
        letters: 'oo',
        sound: '/uː/',
        tip: '长音 /uː/，双唇收圆前突',
        examples: [{ word: 'food', part: 'oo' }, { word: 'moon', part: 'oo' }, { word: 'school', part: 'oo' }, { word: 'room', part: 'oo' }, { word: 'soon', part: 'oo' }],
      },
      {
        letters: 'oo',
        sound: '/ʊ/',
        tip: '短促放松的 /ʊ/，k/d 前常见',
        examples: [{ word: 'book', part: 'oo' }, { word: 'good', part: 'oo' }, { word: 'look', part: 'oo' }, { word: 'foot', part: 'oo' }, { word: 'wood', part: 'oo' }],
      },
    ],
  },
  {
    key: 'ou',
    label: '元音组合 ou',
    desc: 'ou 是读音最不规律的组合之一，重点记例外词',
    rules: [
      {
        letters: 'ou',
        sound: '/aʊ/',
        tip: '最常见的读法，由 /a/ 滑向 /ʊ/',
        examples: [{ word: 'house', part: 'ou' }, { word: 'out', part: 'ou' }, { word: 'about', part: 'ou' }, { word: 'mouth', part: 'ou' }, { word: 'cloud', part: 'ou' }],
      },
      {
        letters: 'ou',
        sound: '/ʌ/',
        tip: '高频例外词，读短音 /ʌ/',
        examples: [{ word: 'young', part: 'ou' }, { word: 'country', part: 'ou' }, { word: 'double', part: 'ou' }, { word: 'touch', part: 'ou' }, { word: 'enough', part: 'ou' }],
      },
      {
        letters: 'ou',
        sound: '/uː/',
        tip: '少数词读长音 /uː/',
        examples: [{ word: 'group', part: 'ou' }, { word: 'soup', part: 'ou' }, { word: 'you', part: 'ou' }],
      },
    ],
  },
  {
    key: 'magic-e',
    label: 'magic e（不发音的 e）',
    desc: '词尾不发音的 e 让前面的元音"念字母本音"：hop → hope',
    rules: [
      {
        letters: 'a_e',
        sound: '/eɪ/',
        tip: '有 magic e 时 a 读字母本音 /eɪ/',
        examples: [{ word: 'name', part: 'a' }, { word: 'cake', part: 'a' }, { word: 'date', part: 'a' }, { word: 'plane', part: 'a' }],
      },
      {
        letters: 'i_e',
        sound: '/aɪ/',
        tip: '有 magic e 时 i 读 /aɪ/，对比 sit / site',
        examples: [{ word: 'time', part: 'i' }, { word: 'five', part: 'i' }, { word: 'like', part: 'i' }, { word: 'white', part: 'i' }],
      },
      {
        letters: 'o_e',
        sound: '/əʊ/',
        tip: '有 magic e 时 o 读 /əʊ/，对比 hop / hope',
        examples: [{ word: 'home', part: 'o' }, { word: 'nose', part: 'o' }, { word: 'phone', part: 'o' }, { word: 'rose', part: 'o' }],
      },
    ],
  },
  {
    key: 'c-g',
    label: '辅音字母 c 与 g',
    desc: 'c 和 g 后面跟不同元音时读音会变"软"',
    rules: [
      {
        letters: 'c',
        sound: '/k/',
        tip: 'a/o/u 前读 /k/',
        examples: [{ word: 'cat', part: 'c' }, { word: 'come', part: 'c' }, { word: 'cup', part: 'c' }, { word: 'clock', part: 'c' }],
      },
      {
        letters: 'c',
        sound: '/s/',
        tip: 'e/i/y 前读 /s/（软音）',
        examples: [{ word: 'city', part: 'c' }, { word: 'nice', part: 'c' }, { word: 'cycle', part: 'c' }, { word: 'face', part: 'c' }],
      },
      {
        letters: 'g',
        sound: '/g/',
        tip: 'a/o/u 前通常读 /g/',
        examples: [{ word: 'go', part: 'g' }, { word: 'game', part: 'g' }, { word: 'big', part: 'g' }, { word: 'bag', part: 'g' }],
      },
      {
        letters: 'g',
        sound: '/dʒ/',
        tip: 'e/i/y 前常读 /dʒ/（soft g）',
        examples: [{ word: 'gym', part: 'g' }, { word: 'giant', part: 'g' }, { word: 'orange', part: 'g' }, { word: 'page', part: 'g' }],
      },
    ],
  },
  {
    key: 'ch',
    label: '字母组合 ch',
    desc: 'ch 大多数读 /tʃ/，但来自希腊语和法语的词例外',
    rules: [
      {
        letters: 'ch',
        sound: '/tʃ/',
        tip: '最常见读法',
        examples: [{ word: 'chair', part: 'ch' }, { word: 'much', part: 'ch' }, { word: 'teacher', part: 'ch' }, { word: 'lunch', part: 'ch' }],
      },
      {
        letters: 'ch',
        sound: '/k/',
        tip: '希腊来源词读 /k/',
        examples: [{ word: 'school', part: 'ch' }, { word: 'Christmas', part: 'ch' }, { word: 'chemistry', part: 'ch' }],
      },
    ],
  },
  {
    key: 'r-controlled',
    label: 'ar / or / or 读 /ɜː/',
    desc: 'r 前的元音读音会被 r 影响，注意 w 后的 ar 读 /ɜː/',
    rules: [
      {
        letters: 'ar',
        sound: '/ɑː/',
        tip: '重读音节中 ar 读长音 /ɑː/',
        examples: [{ word: 'car', part: 'ar' }, { word: 'star', part: 'ar' }, { word: 'park', part: 'ar' }, { word: 'farm', part: 'ar' }],
      },
      {
        letters: 'or',
        sound: '/ɔː/',
        tip: '重读音节中 or 读长音 /ɔː/',
        examples: [{ word: 'short', part: 'or' }, { word: 'sport', part: 'or' }, { word: 'morning', part: 'or' }, { word: 'fork', part: 'or' }],
      },
      {
        letters: 'wor',
        sound: '/wɜː/',
        tip: 'w 后的 or 读 /ɜː/，特殊记忆',
        examples: [{ word: 'work', part: 'or' }, { word: 'word', part: 'or' }, { word: 'world', part: 'or' }, { word: 'worse', part: 'or' }],
      },
    ],
  },
]
