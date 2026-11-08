"""Deterministic independent oracles, witnesses, transport and full-size cases."""
import itertools
import json
import pathlib
import random
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Python/source'))
sys.path.insert(0, str(ROOT / 'tools'))
import algorithms as alg
from public_validate import check

SEED = 41026
rng = random.Random(SEED)
cases = []


def positions(text, pattern):
    return [i for i in range(len(text)-len(pattern)+1)
            if text[i:i+len(pattern)] == pattern]


def subsequences(text):
    return {''.join(text[i] for i in range(len(text)) if mask >> i & 1)
            for mask in range(1 << len(text))}


def all_merges(blocks):
    if len(blocks) < 2:
        return 0
    return min(blocks[i] + blocks[i+1] +
               all_merges(blocks[:i] + [blocks[i]+blocks[i+1]] + blocks[i+2:])
               for i in range(len(blocks)-1))


def oracle(x):
    task = x['task']
    if task == 'lcs':
        return {'length': max(map(len, subsequences(x['a']) & subsequences(x['b'])))}
    if task == 'merge':
        return {'cost': all_merges(x['sizes'])}
    if task == 'tree':
        return {'weight': max(sum(w for i, w in enumerate(x['weights']) if mask >> i & 1)
                              for mask in range(1 << x['n'])
                              if all(not (mask >> u & 1 and mask >> v & 1)
                                     for u, v in x['edges']))}
    if task in ('naive', 'kmp', 'rk'):
        return {'positions': positions(x['text'], x['pattern'])}
    if task == 'suffix':
        text = x['text']
        sa = sorted(range(len(text)), key=lambda i: text[i:])
        lcp = [0] * len(text)
        for j in range(1, len(text)):
            a, b = text[sa[j-1]:], text[sa[j]:]
            for u, v in zip(a, b):
                if u != v:
                    break
                lcp[j] += 1
        best = max(range(len(text)), key=lambda j: lcp[j]) if text else 0
        return {'sa': sa, 'lcp': lcp,
                'repeated': text[sa[best]:sa[best]+lcp[best]] if text else ''}
    return {'counts': [[len(positions(text, p)) for p in x['patterns']]
                       for text in x['texts']]}


def verify(x, expected=None):
    expected = oracle(x) if expected is None else expected
    result = getattr(alg, x['task'])(x)
    assert check(x, result, expected), (x, result, expected)
    cases.append({'input': x, 'output': expected})


def small_tests():
    for a, b in itertools.product(['', 'a', 'aaaa', 'aba', 'abc', 'bac', 'a b!'], repeat=2):
        verify(dict(task='lcs', a=a, b=b))
    for sizes in [[], [0], [10**9], [0, 0, 0], [1, 100, 1], [10**9]*4]:
        verify(dict(task='merge', sizes=sizes))
    for n in range(10):
        for shape in ('chain', 'star'):
            for value in (-3, 0, 2, 10**9):
                verify(dict(task='tree', n=n, weights=[value]*n,
                            edges=[[v-1 if shape == 'chain' else 0, v] for v in range(1, n)]))
    for text, pattern in [('', ''), ('', 'a'), ('abc', ''), ('a', 'aa'),
                          ('aaaaaa', 'aaa'), ('abdj', 'ab'), ('a A!a A!', 'A!'), ('xyz', 'a')]:
        for task in ('naive', 'kmp', 'rk'):
            verify(dict(task=task, text=text, pattern=pattern))
    for text in ['', 'x', 'abcdef', 'aaaaaaaa', 'ababcdcd', 'banana', 'A ! A !']:
        verify(dict(task='suffix', text=text))
    for patterns, texts in [([], []), ([], ['', 'abc']), (['a'], []),
                             (['a', 'aa', 'aaa', 'a'], ['aaaa', '', 'aaaa']),
                             (['he', 'she', 'hers', 'ers', 'he'], ['shershe', '', 'shershe'])]:
        verify(dict(task='aho', patterns=patterns, texts=texts))
    for _ in range(200):
        word = lambda cap: ''.join(rng.choices('ab A!', k=rng.randrange(cap+1)))
        verify(dict(task='lcs', a=word(8), b=word(8)))
        verify(dict(task='merge', sizes=[rng.randrange(8) for _ in range(rng.randrange(7))]))
        n = rng.randrange(11)
        verify(dict(task='tree', n=n, weights=[rng.randrange(-5, 9) for _ in range(n)],
                    edges=[[rng.randrange(v), v] for v in range(1, n)]))
        text, pattern = word(35), word(10)
        for task in ('naive', 'kmp', 'rk'):
            verify(dict(task=task, text=text, pattern=pattern))
        verify(dict(task='suffix', text=word(35)))
        verify(dict(task='aho', patterns=[word(6) or 'a' for _ in range(rng.randrange(9))],
                    texts=[word(35) for _ in range(rng.randrange(5))]))


def large_tests():
    verify(dict(task='lcs', a='ab'*500, b='ab'*500), {'length': 1000})
    verify(dict(task='merge', sizes=[0]*200), {'cost': 0})
    # Equal blocks: optimal leaves have depths floor(log2(n)) or ceil(log2(n)).
    n, w = 200, 10**9
    depth = n.bit_length()-1
    verify(dict(task='merge', sizes=[w]*n), {'cost': w*(n*depth+2*(n-2**depth))})
    n = 100000
    for shape in ('chain', 'star'):
        verify(dict(task='tree', n=n, weights=[10**9]*n,
                    edges=[[v-1 if shape == 'chain' else 0, v] for v in range(1, n)]),
               {'weight': (n//2 if shape == 'chain' else n-1)*10**9})
    for task, n, m in [('naive', 3000, 1500), ('kmp', 200000, 100000), ('rk', 10000, 2000)]:
        verify(dict(task=task, text='a'*n, pattern='a'*m), {'positions': list(range(n-m+1))})
        verify(dict(task=task, text='a'*n, pattern=''), {'positions': list(range(n+1))})
    n = 50000
    verify(dict(task='suffix', text='a'*n),
           {'sa': list(range(n-1, -1, -1)), 'lcp': list(range(n)), 'repeated': 'a'*(n-1)})
    # 10,000 duplicate entries, L=100,000; avoid enumerating billions of matches.
    verify(dict(task='aho', patterns=['a'*10]*10000, texts=['a'*2000]*100),
           {'counts': [[1991]*10000 for _ in range(100)]})
    # 100,001 states and all 95 symbols; near-maximum transition table.
    text = ''.join(chr(32+i % 95) for i in range(100000))
    verify(dict(task='aho', patterns=[text], texts=[text, text]), {'counts': [[1], [1]]})


def main():
    start = time.perf_counter()
    small_tests()
    small_count = len(cases)
    fixture = ROOT / 'tests/student/cases.json'
    fixture.write_text(json.dumps(cases, indent=2), encoding='utf-8')
    # One persistent process, shuffled mixed requests, twice; check every witness.
    mixed = cases.copy()
    rng.shuffle(mixed)
    mixed *= 2
    proc = subprocess.run([sys.executable, str(ROOT / 'Python/source/main.py')],
                          input=''.join(json.dumps(c['input'])+'\n' for c in mixed),
                          text=True, encoding='utf-8', capture_output=True, timeout=20, check=True)
    answers = [json.loads(line) for line in proc.stdout.splitlines()]
    assert len(answers) == len(mixed)
    assert not proc.stderr, proc.stderr
    for case, answer in zip(mixed, answers):
        assert check(case['input'], answer, case['output']), (case, answer)
    large_tests()
    summary = {'seed': SEED, 'small_cases': small_count, 'mixed_jsonl_responses': len(mixed),
               'large_cases': len(cases)-small_count, 'elapsed_seconds': time.perf_counter()-start,
               'result': 'PASS'}
    (ROOT / 'tests/student/results.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
