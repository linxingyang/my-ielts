export type Accent = 'us' | 'uk'

// 全局共享口音（美/英）状态：词汇页与口语页共用同一设置，localStorage 持久化，默认美音
export const accent = useLocalStorage<Accent>('speaking_accent', 'us')
