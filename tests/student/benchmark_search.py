"""Same direct-call timing scope, deterministic inputs, raw milliseconds."""
import json
import os
import pathlib
import platform
import random
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Python/source'))
import algorithms


def main():
    seed = 41026
    rng = random.Random(seed)
    rows = []
    for kind in ('random', 'repetitive'):
        for n, m in ((500, 25), (1500, 75), (3000, 150)):
            text = ''.join(rng.choices('abcd', k=n)) if kind == 'random' else 'a'*n
            pattern = text[n//2:n//2+m] if kind == 'random' else 'a'*m
            x = {'text': text, 'pattern': pattern}
            expected = [i for i in range(n-m+1) if text[i:i+m] == pattern]
            for name in ('naive', 'kmp', 'rk'):
                fn = getattr(algorithms, name)
                assert fn(x)['positions'] == expected  # correctness and one warm-up
                times = []
                for _ in range(3):
                    start = time.perf_counter_ns()
                    result = fn(x)
                    times.append((time.perf_counter_ns()-start)/1e6)
                    assert result['positions'] == expected
                rows.append(dict(case=kind, n=n, m=m, algorithm=name, milliseconds=times,
                                 median_ms=statistics.median(times), correct=True))
    report = dict(seed=seed, python=sys.version, os=platform.platform(),
                  cpu=os.environ.get('PROCESSOR_IDENTIFIER', platform.processor()),
                  ram='Not available: Windows hardware query denied access',
                  scope='Direct function call including preprocessing and output allocation; excludes JSON, startup and validation',
                  warmup='One correctness call per algorithm and input; no explicit JIT configuration', rows=rows)
    (ROOT / 'tests/student/search_results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
