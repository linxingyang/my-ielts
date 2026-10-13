// 单词重音数据（手工维护，可直接编辑）
// 依据《English Pronunciation in Use - Elementary》Section B Unit 28-32
// （音节、双音节词重音、多音节词重音、复合词重音、名词/动词同形词重音对比）
// 注意：_fetch_audio.py 会从本文件提取全部例词下载音频（us + uk 两套）

/**
 * @type {Array<{
 *   key: string,
 *   label: string,
 *   desc: string,
 *   words: Array<{ word: string, syllables: string[], stress: number, note?: string }>
 * }>
 * syllables 为音节划分数组（小写原样拼写），stress 为重音音节下标（0 开始）
 */
export const STRESS_GROUPS = [
  {
    key: 'two-first',
    label: '双音节词 · 重音在前',
    desc: '名词和形容词通常重音在第一个音节',
    words: [
      { word: 'table', syllables: ['ta', 'ble'], stress: 0 },
      { word: 'window', syllables: ['win', 'dow'], stress: 0 },
      { word: 'mother', syllables: ['mo', 'ther'], stress: 0 },
      { word: 'doctor', syllables: ['doc', 'tor'], stress: 0 },
      { word: 'happy', syllables: ['hap', 'py'], stress: 0 },
      { word: 'clever', syllables: ['cle', 'ver'], stress: 0 },
      { word: 'garden', syllables: ['gar', 'den'], stress: 0 },
      { word: 'money', syllables: ['mo', 'ney'], stress: 0 },
    ],
  },
  {
    key: 'two-last',
    label: '双音节词 · 重音在后',
    desc: '许多动词重音在第二个音节',
    words: [
      { word: 'agree', syllables: ['a', 'gree'], stress: 1 },
      { word: 'forget', syllables: ['for', 'get'], stress: 1 },
      { word: 'enjoy', syllables: ['en', 'joy'], stress: 1 },
      { word: 'decide', syllables: ['de', 'cide'], stress: 1 },
      { word: 'begin', syllables: ['be', 'gin'], stress: 1 },
      { word: 'arrive', syllables: ['ar', 'rive'], stress: 1 },
      { word: 'repair', syllables: ['re', 'pair'], stress: 1 },
      { word: 'prepare', syllables: ['pre', 'pare'], stress: 1 },
    ],
  },
  {
    key: 'two-both',
    label: '同形词 · 名前动后',
    desc: '拼写相同的名词/动词对：名词重音在前，动词重音在后（REcord / reCORD）',
    words: [
      { word: 'record', syllables: ['re', 'cord'], stress: 0, note: '名词：唱片；动词重音在后' },
      { word: 'present', syllables: ['pre', 'sent'], stress: 0, note: '名词：礼物；动词"呈上"重音在后' },
      { word: 'produce', syllables: ['pro', 'duce'], stress: 0, note: '名词：农产品；动词重音在后' },
      { word: 'increase', syllables: ['in', 'crease'], stress: 0, note: '名词：增长；动词重音在后' },
      { word: 'import', syllables: ['im', 'port'], stress: 0, note: '名词：进口货；动词重音在后' },
      { word: 'permit', syllables: ['per', 'mit'], stress: 0, note: '名词：许可证；动词重音在后' },
    ],
  },
  {
    key: 'long',
    label: '多音节词',
    desc: '三个及以上音节，重音位置要逐词记忆',
    words: [
      { word: 'important', syllables: ['im', 'por', 'tant'], stress: 1 },
      { word: 'tomorrow', syllables: ['to', 'mor', 'row'], stress: 1 },
      { word: 'together', syllables: ['to', 'ge', 'ther'], stress: 1 },
      { word: 'remember', syllables: ['re', 'mem', 'ber'], stress: 1 },
      { word: 'September', syllables: ['Sep', 'tem', 'ber'], stress: 1 },
      { word: 'difficult', syllables: ['dif', 'fi', 'cult'], stress: 0 },
      { word: 'interesting', syllables: ['in', 'ter', 'es', 'ting'], stress: 0, note: '口语中常读三音节 IN-trə-sting' },
      { word: 'hospital', syllables: ['hos', 'pi', 'tal'], stress: 0 },
      { word: 'beautiful', syllables: ['beau', 'ti', 'ful'], stress: 0 },
      { word: 'expensive', syllables: ['ex', 'pen', 'sive'], stress: 1 },
      { word: 'banana', syllables: ['ba', 'na', 'na'], stress: 1 },
      { word: 'telephone', syllables: ['te', 'le', 'phone'], stress: 0 },
    ],
  },
  {
    key: 'compound',
    label: '复合词 · 重音在前',
    desc: '复合名词重音几乎总在第一个词：GREENhouse 是"温室"，green HOUSE 是"绿色的房子"',
    words: [
      { word: 'football', syllables: ['foot', 'ball'], stress: 0 },
      { word: 'bedroom', syllables: ['bed', 'room'], stress: 0 },
      { word: 'blackboard', syllables: ['black', 'board'], stress: 0 },
      { word: 'toothbrush', syllables: ['tooth', 'brush'], stress: 0 },
      { word: 'raincoat', syllables: ['rain', 'coat'], stress: 0 },
      { word: 'sunglasses', syllables: ['sun', 'glass', 'es'], stress: 0 },
      { word: 'grandmother', syllables: ['grand', 'mo', 'ther'], stress: 0 },
      { word: 'bus stop', syllables: ['bus', 'stop'], stress: 0, note: '两个独立词构成的复合名词，重音同样在第一个词' },
      { word: 'post office', syllables: ['post', 'of', 'fice'], stress: 0 },
      { word: 'football player', syllables: ['foot', 'ball', 'pla', 'yer'], stress: 0, note: '核心重音在 foot，ball player 次重音递减' },
    ],
  },
]
