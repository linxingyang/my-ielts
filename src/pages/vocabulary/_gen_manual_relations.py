"""生成手工精选关联组 relations.json（初始种子，可随时手工编辑补充）。

内容：常见学术词根族 + 典型同义/反义组。候选词先与词库（vocabulary.txt 全部词形）
求交集，仅保留词库中实际存在的词；剩余不足 2 词的组丢弃。
重复运行幂等（relations.json 为手工维护文件，脚本只在文件不存在时生成，
或配合 --force 重新生成——注意 --force 会覆盖手工编辑的内容）。
"""
import json
import sys
from pathlib import Path

CUR_DIR = Path(__file__).absolute().parent
RELATIONS_PATH = CUR_DIR / 'relations.json'

# 词根/派生族：root 说明 → 候选词（词库中不存在的自动剔除）
ROOT_FAMILIES = {
    'spect / spic（看）': ['inspect', 'respect', 'spectator', 'perspective', 'suspect', 'prospect',
                      'spectacle', 'spectacular', 'spectrum', 'suspicion', 'suspicious', 'suspiciously',
                      'conspicuous', 'retrospect', 'expectation', 'spectacles', 'perspicacious'],
    'dict / dic（说）': ['predict', 'prediction', 'contradict', 'contradiction', 'dictate', 'dictation',
                    'dictionary', 'indicate', 'indication', 'verdict', 'dictator', 'predicate',
                    'dedicate', 'dedication', 'dedicated'],
    'duct / duc（引导）': ['conduct', 'conductor', 'product', 'production', 'reduce', 'reduction',
                     'introduce', 'introduction', 'educate', 'education', 'deduct', 'deduction',
                     'induce', 'semiconductor', 'productive', 'counterpart'],
    'ject（扔）': ['project', 'projection', 'injection', 'inject', 'reject', 'rejection', 'object',
                'objection', 'objective', 'subject', 'subjective', 'eject', 'projectile'],
    'fer（带来）': ['transfer', 'refer', 'reference', 'prefer', 'preference', 'differ', 'difference',
                'different', 'offer', 'conference', 'infer', 'inference', 'fertile', 'fertilizer',
                'interfere', 'interference', 'confer', ' ferry', 'ferry'],
    'pos / pon（放置）': ['position', 'compose', 'composition', 'deposit', 'oppose', 'opposite',
                    'opposition', 'propose', 'proposal', 'suppose', 'supposedly', 'expose',
                    'exposure', 'impose', 'imposition', 'disposal', 'dispose', 'component',
                    'postpone', 'opponent', 'positive', 'positively', 'punctuation'],
    'mit / miss（送）': ['mission', 'missionary', 'admit', 'admission', 'permit', 'submission',
                   'transmit', 'transmission', 'commit', 'commission', 'committee', 'commitment',
                   'dismiss', 'dismissal', 'missile', 'emission', 'omit', 'permission', 'compromise'],
    'press（压）': ['pressure', 'depress', 'depression', 'express', 'expression', 'impress',
                'impression', 'impressive', 'compress', 'compressor', 'compression', 'suppress', 'oppress'],
    'tract（拉）': ['attract', 'attraction', 'attractive', 'contract', 'extraction', 'extract',
               'subtract', 'abstract', 'tractor', 'distract', 'distraction'],
    'vert / vers（转）': ['convert', 'conversion', 'reverse', 'invert', 'divert', 'diversion',
                    'advertisement', 'advertise', 'universe', 'universal', 'anniversary',
                    'controversy', 'controversial', 'versatile', 'versus', 'vertical'],
    'struct（建造）': ['structure', 'structural', 'construct', 'construction', 'instruct',
                 'instruction', 'instructor', 'infrastructure', 'instrument', 'instrumental',
                 'reconstruction', 'restructure'],
    'vid / vis（看）': ['visible', 'visibility', 'vision', 'visual', 'visualize', 'revise',
                  'revision', 'supervise', 'supervision', 'supervisor', 'evident', 'evidence',
                  'provide', 'provision', 'provider', 'review', 'preview', 'television'],
    'aud（听）': ['audio', 'audience', 'auditorium', 'audible'],
    'scrib / script（写）': ['describe', 'description', 'subscribe', 'subscription', 'prescribe',
                      'prescription', 'manuscript', 'script', 'transcript', 'inscription'],
    'graph（写/画）': ['photograph', 'photography', 'photographer', 'autobiography', 'biography',
                  'paragraph', 'geography', 'geographical', 'graphic', 'demography',
                  'demographic', 'telegraph'],
    'log / logy（学说）': ['biology', 'biological', 'psychology', 'psychological', 'psychologist',
                     'technology', 'technological', 'technologist', 'geology', 'ecology',
                     'ecological', 'ideology', 'apologize', 'apology', 'dialogue', 'logic',
                     'logical', 'illogical', 'archaeology', 'archaeologist', 'technology'],
    'port（搬运）': ['transport', 'transportation', 'import', 'importation', 'export', 'exportation',
               'report', 'reporter', 'support', 'supporter', 'portable', 'deport', 'deportation',
               'deportee'],
    'cap / cept / cip（拿取）': ['accept', 'acceptable', 'acceptance', 'concept', 'conception',
                       'conceptional', 'except', 'exception', 'exceptional', 'capture', 'capable',
                       'capacity', 'captive', 'anticipate', 'anticipation', 'participant',
                       'participate', 'participation', 'recipient', 'principal', 'principle'],
    'ceive / cept（拿取）': ['receive', 'reception', 'receptionist', 'perceive', 'perception', 'deceive',
                     'deception', 'conceive', 'concept'],
    'mov / mot（移动）': ['move', 'movement', 'remove', 'removal', 'motive', 'motivate',
                    'motivation', 'motion', 'promote', 'promotion', 'remote', 'emotion',
                    'emotional', 'motor', 'automobile', 'demote'],
    'st / sta / sist（站立）': ['standard', 'standardize', 'status', 'statue', 'stationary', 'station',
                      'stable', 'stabilize', 'stability', 'establish', 'establishment', 'obstacle',
                      'instant', 'instantly', 'constant', 'constantly', 'insist', 'consist',
                      'consistent', 'consistency', 'persist', 'persistence', 'persistent', 'assist',
                      'assistance', 'assistant', 'resist', 'resistance', 'resistant', 'existence',
                      'substance', 'substantial', 'substantially', 'circumstance', 'distance'],
    'tain / ten（握持）': ['contain', 'container', 'obtain', 'maintain', 'maintenance', 'sustain',
                    'sustainable', 'retain', 'entertain', 'entertainment', 'tenant', 'content',
                    'continuous', 'continually', 'continent', 'continental'],
    'ced / cess（走）': ['proceed', 'process', 'procedure', 'succeed', 'success', 'successful',
                   'successfully', 'succession', 'successive', 'access', 'accessible', 'accessory',
                   'exceed', 'exceedingly', 'concede', 'concession', 'recession', 'recess',
                   'precede', 'predecessor', 'unprecedented', 'necessity', 'necessarily'],
    'gress / grad（走/步）': ['progress', 'progressive', 'progressively', 'congress', 'aggressive',
                     'aggression', 'aggressor', 'gradual', 'gradually', 'graduate', 'graduation',
                     'degrade', 'degradation', 'upgrade', 'ingredient'],
    'pel / puls（推）': ['compel', 'compulsory', 'compulsorily', 'impulse', 'pulse', 'expel',
                   'propel', 'repel', 'expulsion', 'compulsion'],
    'flect / flex（弯曲）': ['reflect', 'reflection', 'reflective', 'flexible', 'flexibility',
                     'flexibly', 'deflect'],
    'flict（打击）': ['conflict', 'affliction', 'inflict'],
    'rupt（破裂）': ['rupture', 'interrupt', 'interruption', 'corruption', 'corrupt', 'bankrupt',
                'bankruptcy', 'erupt', 'eruption', 'abrupt', 'abruptly', 'disrupt', 'disruption'],
    'sol（单独）': ['sole', 'solely', 'solo', 'solitary', 'solitude', 'desolate', 'desert',
               'isolate', 'isolated', 'isolation', 'solar'],
    'soc（同伴/社会）': ['society', 'social', 'socially', 'socialise', 'socialize', 'sociology',
                  'associate', 'association', 'sociable'],
    'sens / sent（感觉）': ['sense', 'sensible', 'sensitive', 'sensitivity', 'sensitize', 'sensor',
                     'sensory', 'sentence', 'consent', 'consensus', 'sentiment', 'sentimental',
                     'dissent', 'nonsense', 'sensation', 'sensational'],
    'med / medi（中间）': ['medium', 'media', 'mediate', 'mediation', 'immediate', 'immediately',
                   'intermediate', 'medieval', 'Mediterranean', 'medical', 'medicine',
                   'medication', 'remedy', 'remedial'],
    'ann / enn（年）': ['annual', 'annually', 'anniversary', 'annals'],
    'chron（时间）': ['chronic', 'chronically', 'chronology', 'chronological', 'synchronize'],
    'temp（时间）': ['temporary', 'temporarily', 'contemporary', 'contemporaries', 'tempo'],
    'cred（相信）': ['credit', 'credible', 'incredible', 'incredibly', 'credential', 'credence'],
    'fid（信任）': ['confidence', 'confident', 'confidential', 'confidentiality', 'confide'],
    'cur / curr / cours（跑）': ['current', 'currently', 'currency', 'occur', 'occurrence', 'curriculum',
                      'excursion', 'course', 'discourse'],
    'voc（声音/叫）': ['vocabulary', 'vocal', 'advocate', 'provoke', 'provocative', 'provocation',
                 'vocation', 'vocational', 'invoke', 'irrevocable'],
    'dur（持续）': ['during', 'durable', 'duration', 'endure', 'endurance', 'enduring'],
    'val（价值/强度）': ['value', 'valuable', 'invaluable', 'evaluate', 'evaluation', 'equivalent',
                  'equivalence', 'prevalent', 'prevalence', 'prevail', 'valid', 'validity',
                  'validate', 'invalid'],
    'ver（真实）': ['verify', 'verification', 'verdict', 'veritable'],
    'path（感觉/病）': ['sympathy', 'sympathize', 'sympathetic', 'sympathetically', 'empathy',
                  'empathetic', 'pathetic', 'pathology', 'apathy', 'telepathy'],
    'gen（出生/产生）': ['generate', 'generation', 'generator', 'generative', 'genetic', 'genetics',
                  'gene', 'genius', 'genuine', 'genuinely', 'degenerate', 'regenerate',
                  'indigenous', 'homogeneous', 'hydrogen', 'nitrogen', 'oxygen', 'carbon dioxide'],
    'dem（人民）': ['democracy', 'democrat', 'democratic', 'demography', 'demographic', 'epidemic',
              'endemic', 'pandemic'],
    'mono（单一）': ['monopoly', 'monopolize', 'monotonous', 'monotony', 'monologue', 'monotonously'],
    'ambi（两/周围）': ['ambiguous', 'ambiguity', 'ambition', 'ambitious', 'ambience', 'ambulance'],
    'circum / circ（环绕）': ['circumstance', 'circus', 'circuit', 'circuit', 'circular',
                     'circulate', 'circulation', 'circumference'],
    'tele（远）': ['telephone', 'television', 'telescope', 'telecommunication', 'television'],
    'sub（下/次）': ['subway', 'submarine', 'subtitle', 'substandard', 'submit', 'subordinate',
               'subordination', 'subsequent', 'subsequently', 'subsidiary', 'subsidy',
               'subsidize', 'substitute', 'subterranean', 'suburb', 'suburban'],
    'super / sur（上/超）': ['superior', 'superiority', 'supermarket', 'supervise', 'superb',
                    'superbly', 'superficial', 'superintendent', 'supreme', 'supremacy',
                    'supersonic', 'surplus', 'surpass', 'surreal'],
    'inter（之间）': ['international', 'internationally', 'interact', 'interaction', 'interfere',
               'interference', 'interior', 'internal', 'internalize', 'interpret',
               'interpretation', 'interrupt', 'interruption', 'interval', 'intervene',
               'intervention', 'interview', 'interviewer', 'intermediate', 'interpersonal'],
    'trans（横穿）': ['transfer', 'transport', 'transform', 'transformation', 'transmit', 'transmission',
               'transplant', 'translate', 'translation', 'translator', 'transaction', 'transit',
               'transition', 'transparent', 'transparency'],
    'pre（前）': ['predict', 'prediction', 'precaution', 'precede', 'preceding', 'precise',
             'precision', 'precisely', 'prefer', 'preference', 'prejudice', 'preliminary',
             'premier', 'premises', 'prescribe'],
    'post（后）': ['postpone', 'poster', 'posterior', 'postgraduate', 'postage', 'posterity'],
    'con / com（共同）': ['confirm', 'conform', 'confront', 'confuse', 'confusion', 'connect',
                 'connection', 'conscious', 'consciousness', 'consent', 'conserve', 'conservation',
                 'consider', 'considerable', 'considerate', 'consideration', 'consist'],
    'de（离去/否定）': ['decline', 'decorate', 'decrease', 'dedicate', 'deduce', 'defeat', 'defect',
                'defend', 'deficit', 'define', 'definite', 'definitely', 'definition', 'deform',
                'degenerate', 'degrade'],
    're（回/再）': ['recall', 'receipt', 'receive', 'recession', 'recipe', 'recite', 'reckon',
             'reclaim', 'recognize', 'recommend', 'reconcile', 'recover', 'recruit', 'recycle'],
}

# 典型同义组
SYNONYM_GROUPS = [
    ['disaster', 'catastrophe', 'calamity', 'mishap'],
    ['important', 'significant', 'crucial', 'vital', 'essential', 'critical'],
    ['enormous', 'immense', 'vast', 'huge', 'massive', 'tremendous', 'gigantic'],
    ['tiny', 'minute', 'miniature', 'minimal'],
    ['demonstrate', 'illustrate', 'reveal', 'exhibit', 'display', 'indicate'],
    ['consider', 'contemplate', 'ponder', 'deliberate', 'meditate'],
    ['decrease', 'diminish', 'lessen', 'dwindle', 'abate', 'subside'],
    ['increase', 'surge', 'soar', 'rocket', 'escalate', 'inflate'],
    ['famous', 'renowned', 'celebrated', 'eminent', 'prominent', 'notable', 'distinguished'],
    ['idle', 'indolent', 'lazy'],
    ['brave', 'courageous', 'valiant', 'bold', 'daring', 'fearless', 'heroic'],
    ['furious', 'irritated', 'indignant', 'outraged', 'annoyed'],
    ['delighted', 'cheerful', 'content', 'joyful', 'elated', 'ecstatic', 'pleased'],
    ['miserable', 'depressed', 'gloomy', 'sorrowful', 'melancholy'],
    ['wealthy', 'affluent', 'prosperous', 'rich', 'well-off'],
    ['impoverished', 'needy', 'destitute', 'poor'],
    ['intelligent', 'bright', 'brilliant', 'clever', 'smart', 'ingenious', 'shrewd', 'astute', 'wise'],
    ['foolish', 'silly', 'absurd', 'ridiculous'],
    ['exhausted', 'fatigued', 'weary', 'tired'],
    ['strange', 'odd', 'bizarre', 'weird', 'peculiar', 'eccentric'],
    ['sufficient', 'adequate', 'ample'],
    ['scarce', 'rare', 'sparse', 'scant', 'meager'],
    ['accurate', 'precise', 'exact'],
    ['vague', 'ambiguous', 'obscure'],
    ['destroy', 'demolish', 'ruin', 'devastate', 'wreck', 'annihilate'],
    ['commence', 'initiate', 'originate', 'launch', 'begin'],
    ['terminate', 'conclude', 'cease', 'finish'],
    ['assist', 'aid', 'facilitate', 'help'],
    ['damage', 'hurt', 'injure', 'impair', 'undermine', 'harm'],
    ['preserve', 'conserve', 'retain', 'maintain', 'keep'],
    ['safeguard', 'shield', 'defend', 'guard', 'protect'],
    ['cheat', 'defraud', 'swindle', 'deceive'],
    ['detest', 'loathe', 'abhor', 'resent', 'hate'],
    ['compliment', 'applaud', 'commend', 'praise'],
    ['condemn', 'denounce', 'blame', 'reproach', 'criticize'],
    ['substitute', 'replace', 'displace'],
    ['merge', 'integrate', 'incorporate', 'blend'],
    ['divide', 'split', 'segregate', 'detach', 'separate'],
    ['assemble', 'collect', 'accumulate', 'gather'],
    ['scatter', 'disperse', 'diffuse', 'disseminate', 'spread'],
    ['puzzle', 'bewilder', 'perplex', 'baffle', 'confuse'],
    ['astonish', 'amaze', 'astound', 'startle', 'stun', 'surprise'],
    ['dull', 'tedious', 'monotonous', 'tiresome', 'boring'],
    ['arduous', 'demanding', 'laborious', 'tough', 'difficult'],
    ['straightforward', 'effortless', 'simple', 'easy'],
    ['rapid', 'swift', 'speedy', 'prompt', 'hasty', 'quick'],
    ['sluggish', 'gradual', 'leisurely', 'slow'],
    ['region', 'district', 'zone', 'territory', 'area'],
    ['occupation', 'profession', 'career', 'vocation', 'employment', 'job'],
    ['disease', 'sickness', 'disorder', 'ailment', 'illness'],
    ['medication', 'drug', 'remedy', 'therapy', 'medicine'],
    ['physician', 'surgeon', 'doctor'],
    ['instructor', 'tutor', 'educator', 'lecturer', 'teacher'],
    ['pupil', 'learner', 'student'],
    ['academy', 'college', 'university', 'institution', 'school'],
    ['terminology', 'jargon', 'vocabulary'],
    ['conversation', 'dialogue', 'chat', 'gossip', 'discussion'],
    ['conference', 'assembly', 'gathering', 'congress', 'summit', 'convention', 'meeting'],
    ['funds', 'capital', 'finance', 'cash', 'currency', 'money'],
    ['fee', 'salary', 'wage', 'income', 'allowance', 'pension', 'payment'],
    ['inexpensive', 'economical', 'affordable', 'cheap'],
    ['costly', 'expensive', 'pricey'],
    ['administration', 'authority', 'regime', 'government'],
    ['legislation', 'statute', 'regulation', 'legislate', 'law'],
    ['offence', 'offense', 'guilt', 'crime'],
    ['penalty', 'sanction', 'punishment'],
    ['warfare', 'battle', 'combat', 'conflict', 'clash', 'war'],
    ['faith', 'conviction', 'creed', 'belief'],
    ['suspicion', 'skepticism', 'scepticism', 'doubt'],
    ['concept', 'notion', 'conception', 'idea'],
    ['scheme', 'proposal', 'blueprint', 'plan'],
    ['approach', 'technique', 'manner', 'method', 'means'],
    ['issue', 'trouble', 'dilemma', 'predicament', 'problem'],
    ['remedy', 'resolution', 'solution'],
    ['consequence', 'outcome', 'effect', 'aftermath', 'result'],
    ['cause', 'factor', 'rationale', 'reason'],
    ['aim', 'goal', 'objective', 'target', 'intention', 'purpose'],
    ['attribute', 'property', 'characteristic', 'trait', 'feature', 'quality'],
    ['quantity', 'volume', 'amount'],
    ['category', 'species', 'breed', 'variety', 'sort', 'type', 'kind'],
    ['component', 'element', 'constituent', 'segment', 'portion', 'fraction', 'part'],
    ['entire', 'total', 'complete', 'intact', 'whole'],
    ['vacant', 'hollow', 'void', 'blank', 'empty'],
    ['packed', 'crowded', 'crammed', 'full'],
    ['powerful', 'mighty', 'robust', 'sturdy', 'strong'],
    ['feeble', 'fragile', 'frail', 'vulnerable', 'weak'],
    ['firm', 'rigid', 'stiff', 'solid'],
    ['gentle', 'mild', 'tender', 'delicate', 'soft'],
    ['coarse', 'uneven', 'rugged', 'harsh', 'rough'],
    ['silent', 'hushed', 'noiseless', 'quiet'],
    ['pure', 'spotless', 'immaculate', 'sterile', 'clean'],
    ['filthy', 'foul', 'contaminated', 'polluted', 'dirty'],
    ['damp', 'humid', 'moist', 'wet', 'humid'],
    ['arid', 'parched', 'dry'],
    ['boiling', 'scorching', 'hot'],
    ['chilly', 'freezing', 'icy', 'frigid', 'cold'],
    ['brilliant', 'radiant', 'luminous', 'bright'],
    ['dim', 'gloomy', 'dusky', 'murky', 'dark'],
    ['adjacent', 'neighboring', 'nearby', 'near', 'close'],
    ['distant', 'remote', 'far'],
]

# 典型反义组（成对）
ANTONYM_GROUPS = [
    ['abundant', 'scarce'],
    ['advantage', 'drawback'],
    ['advantage', 'disadvantage'],
    ['agree', 'disagree'],
    ['expand', 'shrink'],
    ['expand', 'contract'],
    ['support', 'oppose'],
    ['success', 'failure'],
    ['abstract', 'concrete'],
    ['artificial', 'natural'],
    ['urban', 'rural'],
    ['temporary', 'permanent'],
    ['domestic', 'foreign'],
    ['import', 'export'],
    ['include', 'exclude'],
    ['accept', 'reject'],
    ['advance', 'retreat'],
    ['conceal', 'reveal'],
    ['conservative', 'radical'],
    ['conservative', 'liberal'],
    ['diligent', 'lazy'],
    ['encourage', 'discourage'],
    ['generous', 'stingy'],
    ['gentle', 'harsh'],
    ['hope', 'despair'],
    ['humble', 'arrogant'],
    ['inferior', 'superior'],
    ['innocent', 'guilty'],
    ['luxury', 'poverty'],
    ['major', 'minor'],
    ['maximum', 'minimum'],
    ['modern', 'ancient'],
    ['modern', 'traditional'],
    ['optimistic', 'pessimistic'],
    ['optional', 'compulsory'],
    ['optional', 'obligatory'],
    ['praise', 'criticize'],
    ['private', 'public'],
    ['professional', 'amateur'],
    ['prosper', 'decline'],
    ['rare', 'common'],
    ['rational', 'emotional'],
    ['reward', 'punishment'],
    ['rigid', 'flexible'],
    ['safe', 'dangerous'],
    ['simple', 'complicated'],
    ['simple', 'complex'],
    ['sincere', 'hypocritical'],
    ['spacious', 'cramped'],
    ['strengthen', 'weaken'],
    ['supply', 'demand'],
    ['tame', 'wild'],
    ['transparent', 'opaque'],
    ['virtual', 'real'],
    ['voluntary', 'compulsory'],
    ['positive', 'negative'],
    ['superior', 'inferior'],
    ['sufficient', 'inadequate'],
    ['compress', 'stretch'],
]


def collect_words():
    words = set()
    for line in (CUR_DIR / 'vocabulary.txt').read_text(encoding='utf-8').split('\n'):
        line = line.strip()
        if not line or line in ('===', '+++', '---'):
            continue
        word = line.split('|')[0].strip()
        if '|' not in line or not word[:1].isascii() or not word[:1].isalpha():
            continue
        for variant in word.split('/'):
            variant = variant.strip().lower()
            if variant:
                words.add(variant)
    return words


def filter_group(words, vocab):
    kept = [w for w in words if w.strip().lower() in vocab]
    return kept if len(kept) >= 2 else None


if __name__ == '__main__':
    vocab = collect_words()
    groups = []
    for root, words in ROOT_FAMILIES.items():
        kept = filter_group(words, vocab)
        if kept:
            groups.append({'type': 'root', 'root': root, 'words': kept})
        else:
            print(f'[跳过] 词根组 "{root}" 词库中无命中')
    for words in SYNONYM_GROUPS:
        kept = filter_group(words, vocab)
        if kept and len(kept) < len(words):
            print(f'[部分命中] 同义组 {words} -> {kept}')
        if kept:
            groups.append({'type': 'synonym', 'words': kept})
    for words in ANTONYM_GROUPS:
        kept = filter_group(words, vocab)
        if kept and len(kept) < len(words):
            print(f'[部分命中] 反义组 {words} -> {kept}')
        if kept:
            groups.append({'type': 'antonym', 'words': kept})

    if RELATIONS_PATH.exists() and '--force' not in sys.argv:
        print(f'{RELATIONS_PATH.name} 已存在，跳过（使用 --force 覆盖）')
    else:
        RELATIONS_PATH.write_text(json.dumps(groups, ensure_ascii=False, indent=1), encoding='utf-8')
    covered = len({w for g in groups for w in g['words']})
    print(f'手工关联组: {len(groups)} 组（root {sum(1 for g in groups if g["type"] == "root")}'
          f' / syn {sum(1 for g in groups if g["type"] == "synonym")}'
          f' / ant {sum(1 for g in groups if g["type"] == "antonym")}），覆盖 {covered} 词')
