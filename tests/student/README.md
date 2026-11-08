# Student tests and search experiment

Run from the repository root with Python 3.12+ (no third-party dependencies):

```powershell
python tests/student/check_student.py
python tests/student/benchmark_search.py
```

On the current Windows machine, use the installed interpreter explicitly:

```powershell
$py = 'C:/Users/Acer/.local/bin/python3.13.exe'
& $py tools/run.py --setup
& $py tools/run.py --check
& $py tests/student/check_student.py
& $py tests/student/benchmark_search.py
```

`check_student.py` uses seed 41026. It generates 1771 small input/output fixtures in `cases.json`, tests each with independent oracles and the unmodified public semantic validator, then shuffles and repeats them in a single JSONL process (3542 responses). Expected optimum-only fields for LCS/merge/tree intentionally allow different valid witnesses. It also generates 14 large closed-form cases in memory. `results.json` records the actual summary; assertions must remain enabled (do not use `-O`).

`benchmark_search.py` uses identical random and repetitive inputs for all three searches, one untimed warm-up, and three measured direct calls. `search_results.json` includes raw milliseconds, medians, correctness checks and environment information. Rerunning replaces these generated result files. The table in ANALYSIS.md describes the recorded run; update it if adopting a later benchmark run for submission.

The public tests/checker remain unchanged. See ANALYSIS.md for correctness arguments, test coverage, limits and measured results; see `docs/DEFENCE_KK.md` for Kazakh study notes.
