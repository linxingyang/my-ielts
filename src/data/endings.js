// -s / -ed 结尾读音数据（手工维护，可直接编辑）
// 依据《English Pronunciation in Use - Elementary》Unit 42（-s 结尾）与 Unit 43（-ed 过去式）
// 规则：清辅音后读清音、浊辅音后读浊音、齿擦音后读 /ɪz/ /ɪd/
// 注意：_fetch_audio.py 会从本文件提取全部例词下载音频（us + uk 两套）

/**
 * @type {Array<{
 *   key: string,
 *   label: string,
 *   desc: string,
 *   sounds: Array<{ sound: string, rule: string, words: string[] }>
 * }>
 */
export const ENDING_GROUPS = [
  {
    key: 's',
    label: '名词复数 / 动词三单 -s',
    desc: '词尾 -s 有三种读法，取决于前面的音',
    sounds: [
      { sound: '/s/', rule: '清辅音后读 /s/（p, t, k, f…）', words: ['works', 'stops', 'cats', 'books', 'laughs', 'maps'] },
      { sound: '/z/', rule: '浊辅音和元音后读 /z/（b, d, g, m, n…）', words: ['plays', 'dogs', 'pens', 'rooms', 'words', 'runs'] },
      { sound: '/ɪz/', rule: '咝音后读 /ɪz/，多一个音节（s, z, ʃ, tʃ, dʒ…）', words: ['watches', 'washes', 'passes', 'buses', 'dances', 'uses'] },
    ],
  },
  {
    key: 'ed',
    label: '动词过去式 -ed',
    desc: '规则动词 -ed 同样有三种读法',
    sounds: [
      { sound: '/t/', rule: '清辅音后读 /t/（p, k, ʃ, tʃ, s…）', words: ['worked', 'stopped', 'washed', 'laughed', 'helped', 'asked'] },
      { sound: '/d/', rule: '浊辅音和元音后读 /d/', words: ['played', 'lived', 'loved', 'cleaned', 'answered', 'called'] },
      { sound: '/ɪd/', rule: 't/d 后读 /ɪd/，多一个音节', words: ['wanted', 'needed', 'started', 'visited', 'ended', 'waited'] },
    ],
  },
]
