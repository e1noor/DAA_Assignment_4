"""Assignment algorithms. All request state is local to a call."""
from collections import deque
def lcs(request):
    """Compare two versions of a sequence while preserving the order of shared characters. Implement lcs according to docs/guide/CONTRACTS.md."""
    a, b = request['a'], request['b']
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = (dp[i-1][j-1] + 1 if a[i-1] == b[j-1]
                        else max(dp[i-1][j], dp[i][j-1]))
    i, j, answer = n, m, []
    while i and j:
        if a[i-1] == b[j-1]:
            answer.append(a[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] >= dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    return {'length': dp[n][m], 'sequence': ''.join(reversed(answer))}

def merge(request):
    """Plan the cheapest sequence of adjacent block merges when the original order must be preserved. Implement merge according to docs/guide/CONTRACTS.md."""
    sizes = request['sizes']
    n = len(sizes)
    if n < 2:
        return {'cost': 0, 'plan': []}
    prefix = [0]
    for size in sizes:
        prefix.append(prefix[-1] + size)
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for width in range(2, n + 1):
        for l in range(n - width + 1):
            r = l + width - 1
            best = None
            for k in range(l, r):
                candidate = dp[l][k] + dp[k+1][r]
                if best is None or candidate < best:
                    best, split[l][r] = candidate, k
            dp[l][r] = best + prefix[r+1] - prefix[l]
    plan, stack = [], [(0, n-1, False)]
    while stack:
        l, r, ready = stack.pop()
        if l == r:
            continue
        k = split[l][r]
        if ready:
            plan.append([l, k, r])
        else:
            stack.extend([(l, r, True), (k+1, r, False), (l, k, False)])
    return {'cost': dp[0][n-1], 'plan': plan}

def tree(request):
    """Choose a maximum-value set when neighbouring vertices are incompatible and conflicts form a tree. Implement tree according to docs/guide/CONTRACTS.md."""
    n, weights = request['n'], request['weights']
    if not n:
        return {'weight': 0, 'selected': []}
    adj = [[] for _ in range(n)]
    for u, v in request['edges']:
        adj[u].append(v)
        adj[v].append(u)
    parent, order = [-1] * n, [0]
    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    take, skip = weights.copy(), [0] * n
    for u in reversed(order):
        if parent[u] != -1:
            p = parent[u]
            take[p] += skip[u]
            skip[p] += max(take[u], skip[u])
    selected, chosen = [], [False] * n
    for u in order:
        chosen[u] = (parent[u] == -1 or not chosen[parent[u]]) and take[u] > skip[u]
        if chosen[u]:
            selected.append(u)
    return {'weight': max(take[0], skip[0]), 'selected': selected}

def naive(request):
    """Establish a simple exact-search baseline against which the other two searches can be checked. Implement naive according to docs/guide/CONTRACTS.md."""
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    positions = []
    for start in range(n - m + 1):
        j = 0
        while j < m and text[start+j] == pattern[j]:
            j += 1
        if j == m:
            positions.append(start)
    return {'positions': positions}

def kmp(request):
    """Reuse information about matched prefixes to avoid restarting the search after every mismatch. Implement kmp according to docs/guide/CONTRACTS.md."""
    text, pattern = request['text'], request['pattern']
    m = len(pattern)
    if not m:
        return {'positions': list(range(len(text) + 1))}
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j and pattern[i] != pattern[j]:
            j = pi[j-1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    positions, j = [], 0
    for i, char in enumerate(text):
        while j and char != pattern[j]:
            j = pi[j-1]
        if char == pattern[j]:
            j += 1
        if j == m:
            positions.append(i-m+1)
            j = pi[j-1]
    return {'positions': positions}

def rk(request):
    """Reject windows with unequal fingerprints and verify every equal-hash candidate. Implement rk according to docs/guide/CONTRACTS.md."""
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    if not m:
        return {'positions': list(range(n + 1))}
    if m > n:
        return {'positions': []}
    base, modulus = 31, 101
    high = pow(base, m-1, modulus)
    target = window = 0
    for j in range(m):
        target = (target * base + ord(pattern[j])) % modulus
        window = (window * base + ord(text[j])) % modulus
    positions = []
    for start in range(n-m+1):
        if window == target:
            j = 0
            while j < m and text[start+j] == pattern[j]:
                j += 1
            if j == m:
                positions.append(start)
        if start < n-m:
            window = ((window - ord(text[start]) * high) * base + ord(text[start+m])) % modulus
    return {'positions': positions}

def suffix(request):
    """Order the text suffixes and use adjacent common prefixes to find repeated substrings. Implement suffix according to docs/guide/CONTRACTS.md."""
    text = request['text']
    n = len(text)
    if not n:
        return {'sa': [], 'lcp': [], 'repeated': ''}
    sa, rank, width = list(range(n)), [ord(c) for c in text], 1
    while width < n:
        sa.sort(key=lambda i: (rank[i], rank[i+width] if i+width < n else -1))
        new_rank = [0] * n
        for j in range(1, n):
            a, b = sa[j-1], sa[j]
            different = (rank[a], rank[a+width] if a+width < n else -1) != (rank[b], rank[b+width] if b+width < n else -1)
            new_rank[b] = new_rank[a] + different
        rank = new_rank
        if rank[sa[-1]] == n-1:
            break
        width *= 2
    inverse = [0] * n
    for j, start in enumerate(sa):
        inverse[start] = j
    lcp, h = [0] * n, 0
    for i in range(n):
        j = inverse[i]
        if j == 0:
            h = 0
            continue
        previous = sa[j-1]
        while i+h < n and previous+h < n and text[i+h] == text[previous+h]:
            h += 1
        lcp[j] = h
        h = max(0, h-1)
    best = max(range(n), key=lambda j: lcp[j])
    return {'sa': sa, 'lcp': lcp, 'repeated': text[sa[best]:sa[best]+lcp[best]]}

def aho(request):
    """Build one dictionary automaton and count its patterns in several independent texts. Implement aho according to docs/guide/CONTRACTS.md."""
    edges, failure, terminals = [{}], [0], []
    for pattern in request['patterns']:
        state = 0
        for char in pattern:
            if char not in edges[state]:
                edges[state][char] = len(edges)
                edges.append({})
                failure.append(0)
            state = edges[state][char]
        terminals.append(state)
    # Complete transitions for the pattern alphabet (at most 95 characters).
    alphabet = set(char for row in edges for char in row)
    go = [row.copy() for row in edges]
    queue = deque(edges[0].values())
    order = [0]
    for char in alphabet:
        go[0].setdefault(char, 0)
    while queue:
        state = queue.popleft()
        order.append(state)
        fallback = go[failure[state]]
        for char, child in edges[state].items():
            failure[child] = fallback[char]
            queue.append(child)
        for char in alphabet:
            go[state].setdefault(char, fallback[char])
    counts = []
    for text in request['texts']:
        visits, state = [0] * len(edges), 0
        for char in text:
            state = go[state].get(char, 0)
            visits[state] += 1
        for state in reversed(order[1:]):
            visits[failure[state]] += visits[state]
        counts.append([visits[state] for state in terminals])
    return {'counts': counts}
