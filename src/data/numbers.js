// 数字词听辨数据（手工维护，可直接编辑）
// 依据《English Pronunciation in Use - Elementary》附录 E6（numbers）
// teens（13-19）与 tens（30-90）的重音不同：thirTEEN vs THIRty，是雅思听力数字题最高频陷阱
// 注意：_fetch_audio.py 会从本文件提取全部单词下载音频（us + uk 两套）

/**
 * 26 个字母（字母名称读音），供字母听写练习与音频提取使用
 * @type {string[]}
 */
export const ALPHABET = [
  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
]

/**
 * @type {Array<{
 *   id: string,
 *   note: string,
 *   pairs: Array<{ a: string, b: string, meaning: string }>
 * }>
 * 结构与 MINIMAL_PAIR_GROUPS / HOMOPHONE_GROUPS 对齐，便于练习页复用交互
 */
export const NUMBER_PAIR_GROUPS = [
  {
    id: 'teens-vs-tens',
    note: '重音区别：thirteen 重音在 TEEN，thirty 重音在 THIR。听力里靠重音判断数字',
    pairs: [
      { a: 'thirteen', b: 'thirty', meaning: '13 / 30' },
      { a: 'fourteen', b: 'forty', meaning: '14 / 40' },
      { a: 'fifteen', b: 'fifty', meaning: '15 / 50' },
      { a: 'sixteen', b: 'sixty', meaning: '16 / 60' },
      { a: 'seventeen', b: 'seventy', meaning: '17 / 70' },
      { a: 'eighteen', b: 'eighty', meaning: '18 / 80' },
      { a: 'nineteen', b: 'ninety', meaning: '19 / 90' },
    ],
  },
  {
    id: 'cardinal-vs-ordinal',
    note: '基数词与序数词：four / fourth，听力填空注意日期用序数词',
    pairs: [
      { a: 'four', b: 'fourth', meaning: '4 / 第 4' },
      { a: 'nine', b: 'ninth', meaning: '9 / 第 9（拼写特殊）' },
      { a: 'five', b: 'fifth', meaning: '5 / 第 5（拼写特殊）' },
      { a: 'twelve', b: 'twelfth', meaning: '12 / 第 12（拼写特殊）' },
      { a: 'twenty', b: 'twentieth', meaning: '20 / 第 20' },
      { a: 'three', b: 'third', meaning: '3 / 第 3' },
      { a: 'sixty', b: 'sixteenth', meaning: '60 / 第 16' },
    ],
  },
]
