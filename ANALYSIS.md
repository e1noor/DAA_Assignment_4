# Assignment 4 — analysis

## Environment and commands

Selected language: Python (`submission.json` already contained `"Python"`). Actual runtime: CPython 3.13.5, MSC v.1943, 64-bit AMD64. OS: Windows 11, build 22631. CPU identifier: Intel64 Family 6 Model 186 Stepping 3, GenuineIntel. RAM capacity was not obtained because the Windows hardware query denied access. No measured peak-memory claim is made. No external Python packages are needed.

Run from the repository root in the PyCharm PowerShell terminal. On this machine `python` resolves to a Microsoft Store alias; the working interpreter is:

```powershell
$py = 'C:/Users/Acer/.local/bin/python3.13.exe'
& $py tools/run.py --setup
& $py tools/run.py --check
& $py tests/student/check_student.py
& $py tests/student/benchmark_search.py
& $py tools/run.py --input examples/lcs.jsonl
```

With Python 3.12+ correctly on PATH, replace `& $py` with `python`. The Python launcher has no compilation step. Setup checks only transport. `Python/source/main.py` reads and answers one JSON object per line and supports mixed consecutive requests. No algorithm writes diagnostic output. State belongs to individual calls. Positions and original vertex/block indices are zero-based; Python integers preserve large totals exactly. Strings are printable ASCII. Official limits are 20 seconds per requirement-group batch and 768 MiB; these local checks do not reproduce the official container or award a grade.

## Algorithm explanations

### lcs

For prefixes of lengths i and j, `dp[i][j]` is the optimum common subsequence length of `a[:i]` and `b[:j]`. Row zero and column zero are zero. If the last characters match, use `dp[i-1][j-1]+1`; otherwise use `max(dp[i-1][j], dp[i][j-1])`. Increasing i and j makes all dependencies ready.

Correctness follows by induction over prefix lengths. Matching last characters can extend an optimum of the shorter prefixes. With unequal last characters, a common subsequence must omit at least one of them; taking the better omission is exhaustive. Trace backwards from (n,m): append an equal character and move diagonally, otherwise move to an optimum predecessor. Ties prefer the upper cell; reverse the collected characters. Each diagonal step decreases the optimum by one and preserves the relative order in both inputs, proving witness validity and optimal length. Empty strings produce zero and an empty witness.

Time and auxiliary memory are O((n+1)(m+1)); reconstruction costs O(n+m), output O(ell+1) for optimum length ell. Inputs occupy O(n+m+1). The implementation stores the complete Python list-of-lists table, not just two rows. Tests enumerate all subsequences on small strings, accept any optimum witness, distinguish subsequence from substring, include ties, and test identical strings of length 1000.

### merge

`dp[l][r]` is the minimum cost of merging the closed original interval [l,r]. Singletons cost zero. Prefix sums give interval weight `prefix[r+1]-prefix[l]` in O(1). For each increasing interval width:

`dp[l][r] = min(dp[l][k] + dp[k+1][r] for l <= k < r) + interval_weight`.

The last merge in any legal plan separates two adjacent original intervals at some k. Its children must themselves be optimally merged, or replacing a child by a cheaper plan would improve the whole plan. Conversely every candidate split combines two legal optimal children. Induction on width proves the recurrence.

Store the first minimizing k. An explicit stack outputs left child, right child, then `[l,k,r]`. Thus both current child blocks exist and are adjacent when their parent step is emitted. This produces exactly n-1 steps and the DP cost. Empty and singleton inputs return cost zero and no steps. Arbitrary smallest-pair merging is illegal: for [1,100,1], the two size-one blocks are separated.

Time O(n^3) and auxiliary memory O(n^2) for n>=1; input and plan each O(n+1); empty input O(1). No advanced optimization is needed at n<=200. Small tests enumerate every chronological adjacent merge choice; the validator simulates returned plans. Zero/tied blocks, [1,100,1], billion-sized blocks and n=200 are covered. For 200 equal blocks the independent optimum uses leaf depths 7 or 8: total weighted depth is `w*(200*7+2*(200-128))`.

### tree

Root at vertex zero. An iterative parent-before-child traversal builds `parent` and `order`. Reverse order is a valid postorder. `take[u]` is the best weight in u's rooted subtree when u is selected; `skip[u]` is the best when u is omitted:

`take[u] = weights[u] + sum(skip[v])`; `skip[u] = sum(max(take[v], skip[v]))`, over children v.

Leaf states are weight and zero. Child subtrees have no edges between them, so their compatible optimum contributions can be added independently. A chosen parent forbids taking a child; an omitted parent allows either state. These exhaustive cases and induction prove correctness. The root optimum is `max(take[0],skip[0])`.

Reconstruct in forward order: choose u only if its parent was omitted and `take[u]>skip[u]`. On ties omit u; both states have the same optimum. This preserves independent-set feasibility and attains the DP value. Empty selection is allowed: all-negative inputs yield zero. Empty tree returns zero and []. No recursive calls occur, including on a 100000-vertex chain.

Time and auxiliary memory O(n+1), including adjacency lists, traversal arrays and reconstruction; input O(n+1), selected output O(n+1). Tests enumerate every subset for small trees and check uniqueness, independence and witness weight. Chains, stars, zero/negative weights, ties and large sums are included; full-size chain and star use weights 10^9.

### naive

For every possible start 0 through n-m inclusive, compare characters from j=0 until the first mismatch or j=m. Before each comparison the preceding j characters agree. Thus only complete matches are emitted, and every possible start is examined once, in increasing order. Incrementing the start by one preserves overlaps. With m=0 the loop has n+1 starts and each matches immediately; with m>n the range is empty.

Time O(n*m+n+1) including output, auxiliary memory O(1), output O(z+1), input O(n+m+1). Tests compare against independently written slicing comparisons, including empty strings, case, punctuation, no matches and overlaps. The n=3000 repeated-input test checks the full output rather than only completion.

### kmp

`pi[i]` is the length of the longest proper prefix of the pattern that is also a suffix of its prefix ending at i. Build pi from left to right. If the next character mismatches, replace j by `pi[j-1]` until a possible border remains; on equality increment j.

During text scanning j is the length of the pattern prefix matching the current text suffix. Failure fallback considers successive borders and skips only lengths that cannot match, so no occurrence is lost. On reaching m, report `i-m+1` and set j to `pi[m-1]` to preserve overlaps. Empty pattern is handled before indexing the pattern and returns every boundary.

Each increment of j is charged to a processed character; fallback strictly decreases j, giving O(n+m+z+1) total time. Auxiliary memory O(m+1), output O(z+1), input O(n+m+1). Tests include random agreement with an independent oracle, repeated prefixes and overlapping matches, plus n=200000 and m=100000.

### rk

Use ASCII character codes, base B=31 and modulus M=101. A window hash is the polynomial with highest power on its left. Compute the initial hashes in O(m), and let `high=B^(m-1) mod M`. Roll by:

`next = ((current - ord(outgoing)*high)*B + ord(incoming)) mod M`.

Python's modulo with positive M normalizes negative intermediate values. The update algebraically removes the left term, shifts the remaining powers and appends the new character, preserving the hash invariant. Different hashes exclude a match. Every equal-hash window is checked character by character; therefore collisions never create false positives. Starts are scanned in order, including overlaps. Handle m=0 and m>n before hashing.

For 1<=m<=n, time O(n+m+c*m), where c is the number of equal-hash candidate windows; exact verification can be quadratic. A bound over all input branches is O(n*m+n+m+1). Auxiliary memory O(1), output O(z+1), input O(n+m+1). No sliced window is allocated by the algorithm. Tests include the ab/dj collision (both hash to 75), randomized oracle comparisons, repetitive windows and n=10000,m=2000 (product 20000000).

### suffix

Prefix doubling starts with character-code ranks and sorts suffix starts by `(rank[i], rank[i+width])`, using -1 beyond the end. Python's comparison sort is allowed; full suffix strings are never materialized. Assign compressed new ranks, then double width. Initially ranks describe length-one prefixes. Assuming ranks correctly order width-character prefixes, the pair orders prefixes twice as long, including shorter suffixes. Induction gives complete suffix order when all ranks are distinct or the width covers the text. The n=1 case already has the correct singleton order. Empty input returns three empty results.

Kasai builds the inverse suffix ranks. For each original start i, compare with the preceding suffix in SA, beginning from the reusable lower bound h. Store the length in `lcp[inverse[i]]`, then decrement h by at most one. Removing the first character of a common prefix leaves a common prefix one shorter; the preceding suffix at the next position cannot force a smaller lower bound. Rank zero resets h and has LCP zero. The carried bound increases at most O(n) overall, so Kasai is O(n).

`lcp` has exactly n entries and compares `sa[j-1]` with `sa[j]`; no sentinel or empty suffix is returned. Suffixes sharing any prefix occupy a consecutive SA range, so a maximum adjacent LCP is the length of a longest repeat. Slice one witness from its SA position; choose the first maximum on ties. Overlaps are permitted.

Doubling takes O(n log^2(n+1)) worst-case time with Python comparison sorting; Kasai and witness extraction take O(n). Auxiliary memory O(n+1), including sort keys/workspace, ranks and inverse ranks; output O(n+1), input O(n+1). Tests compare the entire SA and LCP with direct small suffix sorting/prefix comparison, cover distinct/repeated/tied cases, and check all 50000 equal-character suffixes against a closed-form result.

### aho

Insert patterns into a trie with dictionary edges. Record a terminal state for each original dictionary position; duplicates share a terminal. Build failure links in BFS depth order, completing transitions for the pattern alphabet (A<=95). Root missing transitions go to root; a child reached by character c has failure `go[failure[parent]][c]`. A missing transition at a non-root state follows the already-completed failure-state transition. Failure depth is strictly smaller, so all needed rows are ready. Text characters outside the pattern alphabet go directly to root.

After each text character, the current state represents the longest suffix of the consumed text that is a trie prefix. Count visits to this state. In reverse BFS order, add each visit count into its failure parent. A terminal matches precisely when it lies on the failure chain of the current state; reverse propagation aggregates every such visit exactly once. This counts overlaps and suffix patterns without enumerating every individual match. Reading the shared terminal count at each original dictionary position preserves duplicate columns. All state is new per request; each text starts at root with fresh visits. Empty dictionary yields an empty row per text; empty texts array yields []; empty text yields a zero row. Empty patterns are outside the contract.

Let L be total pattern length including duplicates, p the number of patterns, S the number of states and q the number of texts. Expected dictionary operations are O(1). Construction is O(L+A*S+p), with O(A*S+S+p) auxiliary storage (including sparse edges and completed Python dictionaries). Per text O(|text|+S+p), hence total O(L+A*S+sum|text|+q*(S+p)); fixed alphabet makes A<=95. Input O(L+sum|text|+p+q+1), retained output O(q*(p+1)+1). No inherited output lists are copied. Tests use independent per-pattern slicing, duplicates, suffixes, repeated texts and requests. Scale tests include 10000 duplicate patterns with 100 dense texts, and a single length-100000 pattern containing all 95 ASCII symbols (100001 trie states), queried twice. Peak memory and official-container timing remain unmeasured.

## Own tests

`tests/student/check_student.py` uses seed 41026 and the unmodified public witness/schema validator. Its independent optimum oracles enumerate subsequences, adjacent-merge histories and vertex subsets; searches use direct slices; suffixes use explicit sorting only for tiny inputs. It generates `tests/student/cases.json` as supported input/output fixtures. Alternative optimal witnesses are accepted by semantic validation. Large cases have independent closed-form expected outputs and are generated in memory rather than committed as enormous fixtures.

|Command|Input or fixture path|Expected result|Actual result / log|What it checks|
|---|---|---|---|---|
|lcs|cases.json; small exhaustive subsequences|Exact optimum and any valid subsequence|PASS, results.json|Empty, ties, order, gaps|
|merge|cases.json; all adjacent histories|Minimum cost, valid chronological plan|PASS, results.json|Adjacency, postorder, zeros, large totals|
|tree|cases.json; all vertex masks|Maximum weight and independent witness|PASS, results.json|Negative/zero values, chains, stars, ties|
|naive/kmp/rk|cases.json; slice oracle|All starts, including overlaps|PASS, results.json|Empty patterns, punctuation, no match, longer pattern|
|rk|text abdj, pattern ab|[0], never collision start 2|PASS|Exact verification after equal hashes|
|suffix|cases.json; direct small suffix sorting|Exact SA/LCP, optimal repeat|PASS, results.json|No sentinel, overlaps, ties, LCP convention|
|aho|cases.json; independent per-pattern counts|Rows and duplicate columns agree|PASS, results.json|Failure suffixes, resets, empty dictionary/texts|
|all|1771 cases, shuffled and repeated in one process|3542 valid JSON answers|PASS, results.json|Transport, response count, state isolation|
|scale|large_tests in check_student.py|14 closed-form checks|PASS, results.json|Published maximum dimensions and large values|

Actual execution: setup PASS; all 44 public cases PASS; the public repeated mixed batch PASS. Own tests: 1771 small cases, 3542 mixed JSONL responses and 14 large cases PASS, recorded elapsed time 3.1105601 seconds (whole test script, including fixture writing and validation; not an algorithm benchmark). These checks do not establish every hidden case. No tests, expected public answers or checker code were modified to accommodate the solution. GitHub Actions and Moodle submission have not been performed. No commit or push was made.

## Search comparison

`tests/student/benchmark_search.py` records `search_results.json`. Seed 41026, CPython/runtime and machine metadata are stored there. Random texts use `random.Random(seed).choices('abcd')`, continuing the same generator across sizes; each pattern is the text slice starting at n//2, guaranteeing an occurrence. Repetitive texts and patterns contain only 'a'. Sizes are (500,25), (1500,75), (3000,150), all in the common domain. Each algorithm receives identical text/pattern data. An independent slice oracle checks correctness first and after every measured call. One untimed correctness call warms up each algorithm/input. Three direct calls are timed with `perf_counter_ns`, converted to milliseconds; timings include preprocessing and output allocation, excluding JSON, startup, compilation and validation. No explicit JIT configuration is used. The final measurement was run separately from the test suite. OS scheduling and timer noise still affect short calls.

|Case|n|m|Seed/generator|Algorithm|Run 1 (ms)|Run 2 (ms)|Run 3 (ms)|Median (ms)|Correct outputs checked|
|---|---:|---:|---|---|---:|---:|---:|---:|---|
|random|500|25|41026 / abcd|naive|0.0275|0.0266|0.0259|0.0266|Yes|
|random|500|25|41026 / abcd|kmp|0.0247|0.0239|0.0229|0.0239|Yes|
|random|500|25|41026 / abcd|rk|0.0498|0.0491|0.1016|0.0498|Yes|
|random|1500|75|41026 / abcd|naive|0.0855|0.0832|0.0828|0.0832|Yes|
|random|1500|75|41026 / abcd|kmp|0.0739|0.0726|0.0730|0.0730|Yes|
|random|1500|75|41026 / abcd|rk|0.1579|0.1533|0.1468|0.1533|Yes|
|random|3000|150|41026 / abcd|naive|0.2323|0.1936|0.1763|0.1936|Yes|
|random|3000|150|41026 / abcd|kmp|0.1461|0.1453|0.1496|0.1461|Yes|
|random|3000|150|41026 / abcd|rk|0.3047|0.3143|0.3180|0.3143|Yes|
|repetitive|500|25|41026 / all a|naive|0.4842|0.5208|0.4742|0.4842|Yes|
|repetitive|500|25|41026 / all a|kmp|0.0501|0.0481|0.0491|0.0491|Yes|
|repetitive|500|25|41026 / all a|rk|0.4682|0.4509|0.4468|0.4509|Yes|
|repetitive|1500|75|41026 / all a|naive|3.7244|3.5557|3.7013|3.7013|Yes|
|repetitive|1500|75|41026 / all a|kmp|0.1671|0.1692|0.1574|0.1671|Yes|
|repetitive|1500|75|41026 / all a|rk|6.4663|5.2160|4.2815|5.2160|Yes|
|repetitive|3000|150|41026 / all a|naive|17.4773|15.5587|16.5086|16.5086|Yes|
|repetitive|3000|150|41026 / all a|kmp|0.3422|0.3470|0.3386|0.3422|Yes|
|repetitive|3000|150|41026 / all a|rk|15.4171|18.4913|20.2772|18.4913|Yes|

On repetitive inputs every window really matches, so naive and exact RK perform m character comparisons per occurrence, while KMP reuses its borders. RK's hash does not avoid verification of genuine matches. On random inputs naive often fails early; hash arithmetic and prefix preprocessing add constant overhead, so asymptotic bounds do not alone predict these small-input timings. Modulus 101 intentionally permits many collisions, which require verification and may increase runtime. These observations concern this collision-laboratory implementation, not every production hash. Short timings are noisy and medians are measurements, not proofs of asymptotic complexity. The ab/dj collision is tested separately for correctness.

## Sources and AI assistance

Primary sources: the repository [English specification](docs/Assignment_4_EN.md), [contracts](docs/guide/CONTRACTS.md), [rubric](docs/guide/RUBRIC.md), [testing guide](docs/guide/TESTING.md), [submission guide](docs/guide/SUBMISSION.md), README and supplied Python transport/validator. Official template: https://github.com/RZhaniya/daa-assignment-4-archive . The remote specification fetch was unavailable; the local supplied documents were read directly.

OpenAI Codex assisted with explaining algorithm logic and debugging, implementing the eight algorithm bodies, writing independent tests and the reproducible benchmark, and drafting this analysis and study notes. Verification performed in this workspace consists of the actual public checks, brute-force/differential oracles, witness validation, repeated mixed JSONL batches and large closed-form cases reported above. 
