// 同音词数据（手工维护，可直接编辑）
// 依据《English Pronunciation in Use - Elementary》附录 E8（homophones）
// 同音词发音完全相同，只能靠语境和拼写区分——是"听音辨词"的终极考验
// 注意：_fetch_audio.py 会从本文件提取全部单词下载音频（us + uk 两套）

/**
 * @type {Array<{
 *   id: string,
 *   note: string,
 *   pairs: Array<{ a: string, b: string, meaning: string }>
 * }>
 * 结构与 phonetics.js 的 MINIMAL_PAIR_GROUPS 对齐，便于练习页复用交互
 * meaning 中 "A / B" 分别对应 a / b 的中文意思
 */
export const HOMOPHONE_GROUPS = [
  {
    id: 'basic',
    note: '最常用的同音词对，听音时只能靠上下文判断',
    pairs: [
      { a: 'their', b: 'there', meaning: '他们的 / 那里' },
      { a: 'meat', b: 'meet', meaning: '肉 / 遇见' },
      { a: 'see', b: 'sea', meaning: '看见 / 大海' },
      { a: 'here', b: 'hear', meaning: '这里 / 听见' },
      { a: 'right', b: 'write', meaning: '正确、右边 / 写' },
      { a: 'sun', b: 'son', meaning: '太阳 / 儿子' },
      { a: 'week', b: 'weak', meaning: '星期 / 虚弱的' },
      { a: 'know', b: 'no', meaning: '知道 / 不' },
      { a: 'wear', b: 'where', meaning: '穿 / 哪里' },
      { a: 'hour', b: 'our', meaning: '小时 / 我们的' },
    ],
  },
  {
    id: 'more',
    note: '更多高频同音词，雅思听力填空易混淆',
    pairs: [
      { a: 'pear', b: 'pair', meaning: '梨 / 一对' },
      { a: 'flower', b: 'flour', meaning: '花 / 面粉' },
      { a: 'whole', b: 'hole', meaning: '整个的 / 洞' },
      { a: 'peace', b: 'piece', meaning: '和平 / 一块' },
      { a: 'plain', b: 'plane', meaning: '朴素的、平原 / 飞机' },
      { a: 'one', b: 'won', meaning: '一 / 赢（win 过去式）' },
      { a: 'ate', b: 'eight', meaning: '吃（eat 过去式） / 八' },
      { a: 'blue', b: 'blew', meaning: '蓝色的 / 吹（blow 过去式）' },
      { a: 'buy', b: 'by', meaning: '买 / 通过、被' },
      { a: 'son', b: 'sun', meaning: '儿子 / 太阳' },
    ],
  },
]
