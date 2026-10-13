// 辅音连缀数据（手工维护，可直接编辑）
// 依据《English Pronunciation in Use - Elementary》Unit 24-27（词首/词中/词尾辅音连缀）
// 连缀 = 两个及以上辅音连在一起，中间不夹元音；中文音节少有这种结构，是发音难点
// 注意：_fetch_audio.py 会从本文件提取全部例词下载音频（us + uk 两套）

/**
 * @type {Array<{
 *   key: string,
 *   label: string,
 *   desc: string,
 *   clusters: Array<{ cluster: string, sound: string, tip: string, examples: Array<{ word: string, part: string }> }>
 * }>
 * clusters[].examples[].part 为 word 中的连缀字母（用于页面高亮），必须是 word 的子串
 */
export const CLUSTER_POSITIONS = [
  {
    key: 'initial',
    label: '词首连缀',
    desc: '两个辅音开头，中间不能加多余的元音（不是"特-rain"，是 train）',
    clusters: [
      { cluster: 'tr', sound: '/tr/', tip: 'tr 实际发音接近 /tʃr/，舌位略卷', examples: [{ word: 'train', part: 'tr' }, { word: 'tree', part: 'tr' }, { word: 'try', part: 'tr' }, { word: 'travel', part: 'tr' }] },
      { cluster: 'dr', sound: '/dr/', tip: 'dr 实际发音接近 /dʒr/', examples: [{ word: 'drink', part: 'dr' }, { word: 'dream', part: 'dr' }, { word: 'drive', part: 'dr' }, { word: 'dress', part: 'dr' }] },
      { cluster: 'pl', sound: '/pl/', tip: 'p 要先憋气再爆发，两音一气呵成', examples: [{ word: 'please', part: 'pl' }, { word: 'plane', part: 'pl' }, { word: 'play', part: 'pl' }, { word: 'plate', part: 'pl' }] },
      { cluster: 'pr', sound: '/pr/', tip: '不要读成"扑-r"', examples: [{ word: 'present', part: 'pr' }, { word: 'price', part: 'pr' }, { word: 'problem', part: 'pr' }, { word: 'pretty', part: 'pr' }] },
      { cluster: 'fl', sound: '/fl/', tip: 'f 轻擦后立即过渡到 l', examples: [{ word: 'fly', part: 'fl' }, { word: 'flower', part: 'fl' }, { word: 'floor', part: 'fl' }, { word: 'flat', part: 'fl' }] },
      { cluster: 'fr', sound: '/fr/', tip: '不要读成"夫-r"', examples: [{ word: 'friend', part: 'fr' }, { word: 'free', part: 'fr' }, { word: 'from', part: 'fr' }, { word: 'fresh', part: 'fr' }] },
      { cluster: 'gr', sound: '/gr/', tip: 'g 浊音直接滑向 r', examples: [{ word: 'green', part: 'gr' }, { word: 'great', part: 'gr' }, { word: 'group', part: 'gr' }, { word: 'grow', part: 'gr' }] },
      { cluster: 'st', sound: '/st/', tip: '词首 s 后的 t 清音化读接近 /sd/，但别加元音："sə-top" ✗', examples: [{ word: 'student', part: 'st' }, { word: 'stop', part: 'st' }, { word: 'study', part: 'st' }, { word: 'stay', part: 'st' }] },
      { cluster: 'sp', sound: '/sp/', tip: '同理不要读成"sə-pay"', examples: [{ word: 'speak', part: 'sp' }, { word: 'sport', part: 'sp' }, { word: 'space', part: 'sp' }, { word: 'spend', part: 'sp' }] },
      { cluster: 'sk', sound: '/sk/', tip: '不要读成"sə-cool"', examples: [{ word: 'school', part: 'sk' }, { word: 'sky', part: 'sk' }, { word: 'ski', part: 'sk' }, { word: 'skill', part: 'sk' }] },
    ],
  },
  {
    key: 'middle',
    label: '词中连缀',
    desc: '多音节词中间的三辅音连缀，容易漏读或吞音',
    clusters: [
      { cluster: 'mpl', sound: '/mpl/', tip: 'complete 中间 /mpl/ 三个辅音连读', examples: [{ word: 'complete', part: 'mpl' }, { word: 'example', part: 'mpl' }, { word: 'simple', part: 'mpl' }] },
      { cluster: 'str', sound: '/str/', tip: 'instrument 词中 /str/', examples: [{ word: 'instrument', part: 'str' }, { word: 'industry', part: 'str' }, { word: 'minister', part: 'str' }] },
      { cluster: 'mbr', sound: '/mbr/', tip: 'umbrella 中间 /mbr/', examples: [{ word: 'umbrella', part: 'mbr' }, { word: 'remember', part: 'mb' }, { word: 'November', part: 'mb' }] },
      { cluster: 'nstr', sound: '/nstr/', tip: '四个辅音连缀，先慢速分解再加速', examples: [{ word: 'instrument', part: 'nstr' }, { word: 'unstructured', part: 'nstr' }] },
      { cluster: 'ns', sound: '/ns/', tip: 'n 结束后直接接 s，不加元音', examples: [{ word: 'answer', part: 'ns' }, { word: 'dance', part: 'nc' }, { word: 'accident', part: 'nt' }] },
      { cluster: 'nk', sound: '/ŋk/', tip: 'thank 里的 n 实际读鼻音 /ŋ/', examples: [{ word: 'thank', part: 'nk' }, { word: 'uncle', part: 'nc' }, { word: 'banker', part: 'nk' }] },
    ],
  },
  {
    key: 'final',
    label: '词尾连缀',
    desc: '词尾辅音群最易被吞掉：friend 是 4 个音，别读成"friend 的 frien"',
    clusters: [
      { cluster: 'st', sound: '/-st/', tip: 'last 别吞掉 t', examples: [{ word: 'last', part: 'st' }, { word: 'best', part: 'st' }, { word: 'first', part: 'rst' }, { word: 'next', part: 'xt' }] },
      { cluster: 'sk', sound: '/-sk/', tip: 'desk 别读成"des"', examples: [{ word: 'desk', part: 'sk' }, { word: 'ask', part: 'sk' }, { word: 'task', part: 'sk' }, { word: 'risk', part: 'sk' }] },
      { cluster: 'mp', sound: '/-mp/', tip: 'm 鼻音后接 p 爆破', examples: [{ word: 'jump', part: 'mp' }, { word: 'lamp', part: 'mp' }, { word: 'camp', part: 'mp' }, { word: 'pump', part: 'mp' }] },
      { cluster: 'nd', sound: '/-nd/', tip: 'friend /frend/ 是单音节词', examples: [{ word: 'friend', part: 'nd' }, { word: 'hand', part: 'nd' }, { word: 'wind', part: 'nd' }, { word: 'send', part: 'nd' }] },
      { cluster: 'nt', sound: '/-nt/', tip: 'went 别读成"wen"', examples: [{ word: 'went', part: 'nt' }, { word: 'plant', part: 'nt' }, { word: 'want', part: 'nt' }, { word: 'point', part: 'nt' }] },
      { cluster: 'ft', sound: '/-ft/', tip: 'gift 别吞 t', examples: [{ word: 'gift', part: 'ft' }, { word: 'left', part: 'ft' }, { word: 'soft', part: 'ft' }, { word: 'lift', part: 'ft' }] },
      { cluster: 'pts', sound: '/-pts/', tip: 'accepts?这组试试更简单的 facts：三辅音词尾', examples: [{ word: 'facts', part: 'cts' }, { word: 'objects', part: 'cts' }, { word: 'texts', part: 'xts' }] },
    ],
  },
]
