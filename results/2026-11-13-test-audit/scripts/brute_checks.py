# Brute-force / independent-method cross-checks of every asserted expected value.
# Each check recomputes the answer WITHOUT reusing the reference implementation's
# algorithm, then compares with the value asserted in the real test_cases.
import itertools, json, re
from collections import deque

fails = []
def chk(name, got, exp):
    ok = got == exp
    print(("OK   " if ok else "MISMATCH ") + f"{name}: got={got!r} expected={exp!r}")
    if not ok:
        fails.append(name)

# ---------- lcb_006: enumerate ALL subarrays ----------
print("== lcb_006 max_subarray: all max-sum slices ==")
for nums, exp in [([-2,1,-3,4,-1,2,1,-5,4], (6,[4,-1,2,1])), ([1], (1,[1])),
                  ([5,4,-1,7,8], (23,[5,4,-1,7,8])), ([-1,-2,-3], (-1,[-1]))]:
    best = None; slices = []
    for i in range(len(nums)):
        s = 0
        for j in range(i, len(nums)):
            s += nums[j]
            if best is None or s > best:
                best = s; slices = [(i, j, nums[i:j+1])]
            elif s == best:
                slices.append((i, j, nums[i:j+1]))
    print(f"  nums={nums} max={best} n_max_slices={len(slices)} slices={slices}")
    chk(f"lcb_006 {nums}", (best, slices[0][2]), exp)
    if len(slices) != 1:
        print("  *** TIE EXISTS: spec has NO tie-break rule -> potential (c) ***")
        fails.append(f"lcb_006 TIE {nums}")

# ---------- lcb_013: enumerate ALL substrings ----------
print("== lcb_013 longest_palindrome: all max-length palindromes ==")
for s, exp in [('babad','bab'),('cbbd','bb'),('',''),('a','a'),('ac','a'),
               ('racecar','racecar'),('abacdfgdcaba','aba'),('forgeeksskeegfor','geeksskeeg')]:
    pals = []
    for i in range(len(s)):
        for j in range(i+1, len(s)+1):
            sub = s[i:j]
            if sub == sub[::-1]:
                pals.append((len(sub), i, sub))
    mx = max([p[0] for p in pals], default=0)
    winners = sorted([p for p in pals if p[0] == mx], key=lambda p: p[1])
    print(f"  {s!r} maxlen={mx} winners={winners}")
    chk(f"lcb_013 {s!r}", winners[0][2] if winners else '', exp)

# ---------- lcb_002: interval/range method (independent of exhaustive ref) ----------
print("== lcb_002 wildcard: range-of-open-counts method (tests use only () and *) ==")
def valid_range(s):
    lo = hi = 0
    for ch in s:
        if ch == '(':
            lo += 1; hi += 1
        elif ch == ')':
            lo -= 1; hi -= 1
        elif ch == '*':
            lo -= 1; hi += 1
        else:
            return None
        if hi < 0:
            return False
        lo = max(lo, 0)
    return lo == 0
for s, exp in [('()',True),('(*)',True),('(*))',True),(')',False),('(*(',False),
               ('(((******))',True),('',True)]:
    chk(f"lcb_002 {s!r}", valid_range(s), exp)

# ---------- held2_002: Python re.fullmatch cross-check ----------
print("== held2_002 regex: DP-ref vs re.fullmatch ==")
for s, p, exp in [('aa','a',False),('aa','a*',True),('ab','.*',True),('aab','c*a*b',True),
                  ('mississippi','mis*is*p*.',False),('','.*',True),('ab','.*c',False),
                  ('aaa','a*a',True),('ab','a*b',True),('a','ab*',True)]:
    chk(f"held2_002 {s!r} {p!r}", re.fullmatch(p, s) is not None, exp)

# ---------- held2_004: enumerate ALL subsequences ----------
print("== held2_004 number_of_lis: brute-force subsequence enumeration ==")
for nums, exp in [([1,3,5,4,7],2),([2,2,2],3),([1,2,4,3,5,4,7,2],3),([],0),
                  ([1],1),([1,2,3],1),([3,2,1],3)]:
    best, cnt = 0, 0
    for r in range(len(nums)+1):
        for idxs in itertools.combinations(range(len(nums)), r):
            seq = [nums[i] for i in idxs]
            if all(seq[k] < seq[k+1] for k in range(len(seq)-1)):
                if len(seq) > best:
                    best, cnt = len(seq), 1
                elif len(seq) == best and len(seq) > 0:
                    cnt += 1
    if not nums:
        cnt = 0
    chk(f"held2_004 {nums}", cnt, exp)

# ---------- held2_010: brute-force index triples ----------
print("== held2_010 three_sum: brute-force triples ==")
for nums, exp in [([-1,0,1,2,-1,-4],[[-1,-1,2],[-1,0,1]]),([0,0,0],[[0,0,0]]),
                  ([],[ ]),([0,1,1],[]),([-2,0,1,1,2],[[-2,0,2],[-2,1,1]]),
                  ([-1,0,1,0],[[-1,0,1]])]:
    found = set()
    for trip in itertools.combinations(range(len(nums)), 3):
        vals = tuple(sorted(nums[i] for i in trip))
        if sum(vals) == 0:
            found.add(vals)
    chk(f"held2_010 {nums}", sorted([list(v) for v in found]), exp)

# ---------- held2_012: simulate every start ----------
print("== held2_012 gas_station: simulate every start ==")
for gas, cost, exp in [([1,2,3,4,5],[3,4,5,1,2],3),([2,3,4],[3,4,3],-1),
                       ([5],[4],0),([4],[5],-1),([3,1,1],[1,2,2],0),([1,2],[2,1],1)]:
    good = []
    n = len(gas)
    for st in range(n):
        tank, ok = 0, True
        for k in range(n):
            i = (st + k) % n
            tank += gas[i] - cost[i]
            if tank < 0:
                ok = False; break
        if ok:
            good.append(st)
    print(f"  gas={gas} cost={cost} feasible_starts={good}")
    chk(f"held2_012 {gas}", good[0] if good else -1, exp)
    if len(good) > 1:
        print("  *** MULTIPLE feasible starts: spec claims uniqueness ***")

# ---------- held2_009: via sorted unique permutations ----------
print("== held2_009 next_permutation: via itertools.permutations ==")
for nums, exp in [([1,2,3],[1,3,2]),([3,2,1],[1,2,3]),([1,1,5],[1,5,1]),
                  ([1],[1]),([],[]),([1,3,2],[2,1,3]),([2,1,3],[2,3,1])]:
    perms = sorted(set(itertools.permutations(nums)))
    t = tuple(nums)
    nxt = None
    for p in perms:
        if p > t:
            nxt = list(p); break
    if nxt is None:
        nxt = list(perms[0]) if perms else []
    chk(f"held2_009 {nums}", nxt, exp)

# ---------- held2_001: full-matrix DP ----------
print("== held2_001 edit_distance: full-matrix DP ==")
def lev(a, b):
    m, n = len(a), len(b)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j
    for i in range(1, m+1):
        for j in range(1, n+1):
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1] + (0 if a[i-1]==b[j-1] else 1))
    return dp[m][n]
for a, b, exp in [('horse','ros',3),('intention','execution',5),('','abc',3),
                  ('abc','',3),('','',0),('a','a',0),('kitten','sitting',3),('flaw','lawn',2)]:
    chk(f"held2_001 {a!r}->{b!r}", lev(a, b), exp)

# ---------- held2_013: recursion + memo ----------
print("== held2_013 decode_ways: recursion+memo ==")
from functools import lru_cache
def dec(s):
    @lru_cache(maxsize=None)
    def f(i):
        if i == len(s): return 1
        if s[i] == '0': return 0
        tot = f(i+1)
        if i+1 < len(s) and 10 <= int(s[i:i+2]) <= 26: tot += f(i+2)
        return tot
    return f(0) if s else 0
for s, exp in [('12',2),('226',3),('06',0),('0',0),('10',1),('11106',2),
               ('27',1),('101',1),('100',0),('110',1)]:
    chk(f"held2_013 {s!r}", dec(s), exp)

# ---------- held2_003: permutation-based count ----------
print("== held2_003 n_queens: permutation enumeration (n<=5) + known sequence ==")
for n, exp in [(1,1),(2,0),(3,0),(4,2),(5,10)]:
    cnt = 0
    for perm in itertools.permutations(range(n)):
        if all(abs(perm[i]-perm[j]) != abs(i-j) for i in range(n) for j in range(i+1, n)):
            cnt += 1
    chk(f"held2_003 n={n}", cnt, exp)
print("  n=8,9 checked by backtracking reference PASS; known OEIS A000170: 92, 352")

# ---------- held2_005: naive BFS (all-pairs adjacency) ----------
print("== held2_005 word_ladder: naive adjacency BFS ==")
def ladder_naive(begin, end, wl):
    words = set(wl)
    if end not in words: return 0
    q = deque([(begin, 1)]); seen = {begin}
    def adj(a, b): return sum(1 for x, y in zip(a, b) if x != y) == 1
    while q:
        w, d = q.popleft()
        for nb in words:
            if nb not in seen and adj(w, nb):
                if nb == end: return d + 1
                seen.add(nb); q.append((nb, d+1))
    return 0
for b, e, wl, exp in [('hit','cog',['hot','dot','dog','lot','log','cog'],5),
                      ('hit','cog',['hot','dot','dog','lot','log'],0),
                      ('a','c',['a','b','c'],2),
                      ('hot','dog',['hot','dog'],0),
                      ('hot','dog',['hot','dog','dot'],3),
                      ('red','tax',['ted','tex','red','tax','tad','den','rex','pee'],4)]:
    chk(f"held2_005 {b}->{e}", ladder_naive(b, e, wl), exp)

# ---------- lcb_011: naive water computation ----------
print("== lcb_011 trap: naive per-column computation ==")
def trap_naive(h):
    tot = 0
    for i in range(len(h)):
        tot += max(0, min(max(h[:i+1], default=0), max(h[i:], default=0)) - h[i])
    return tot
for h, exp in [([0,1,0,2,1,0,1,3,2,1,2,1],6),([4,2,0,3,2,5],9),([],0),([1],0),
               ([5,4,3,2,1],0),([2,0,2],2),([3,0,0,2,0,4],10)]:
    chk(f"lcb_011 {h}", trap_naive(h), exp)

# ---------- lcb_020: exhaustive DFS min jumps ----------
print("== lcb_020 jump: exhaustive DFS ==")
def jump_dfs(nums):
    n = len(nums)
    if n <= 1: return 0
    best = [float('inf')]
    def dfs(i, d):
        if d >= best[0]: return
        if i == n-1:
            best[0] = d; return
        for j in range(i+1, min(n, i+nums[i]+1)):
            dfs(j, d+1)
    dfs(0, 0)
    return best[0] if best[0] != float('inf') else -1
for nums, exp in [([2,3,1,1,4],2),([2,3,0,1,4],2),([0],0),([],0),
                  ([3,2,1,0,4],-1),([1,1,1,1],3),([1,2,3],2),([0,1],-1)]:
    chk(f"lcb_020 {nums}", jump_dfs(nums), exp)

# ---------- held2_006 / lcb_014: naive scans ----------
print("== held2_006 sliding_window_max / lcb_014 daily_temps: naive ==")
def swm_naive(nums, k):
    if not nums: return []
    return [max(nums[i:i+k]) for i in range(len(nums)-k+1)]
for nums, k, exp in [([1,3,-1,-3,5,3,6,7],3,[3,3,5,5,6,7]),([1],1,[1]),
                     ([1,-1],1,[1,-1]),([9,11],2,[11]),([4,-2],2,[4]),
                     ([1,3,1,2,0,5],3,[3,3,2,5]),([],[1] if False else 1,[]),
                     ([7,2,4],3,[7])]:
    chk(f"held2_006 {nums} k={k}", swm_naive(nums, k), exp)
def dt_naive(t):
    out = []
    for i in range(len(t)):
        d = 0
        for j in range(i+1, len(t)):
            if t[j] > t[i]:
                d = j - i; break
        out.append(d)
    return out
for t, exp in [([73,74,75,71,69,72,76,73],[1,1,4,2,1,1,0,0]),([30,40,50,60],[1,1,1,0]),
               ([30,60,90],[1,1,0]),([90,80,70],[0,0,0]),([],[]),([50],[0])]:
    chk(f"lcb_014 {t}", dt_naive(t), exp)

# ---------- lcb_018: recursive parser ----------
print("== lcb_018 decode_string: recursive parser ==")
def dec_rec(s):
    def parse(i):
        out = ''
        num = 0
        while i < len(s):
            ch = s[i]
            if ch.isdigit():
                num = num*10 + int(ch); i += 1
            elif ch == '[':
                sub, i = parse(i+1)
                out += sub * num; num = 0
            elif ch == ']':
                return out, i+1
            else:
                out += ch; i += 1
        return out, i
    return parse(0)[0]
for s, exp in [('3[a]2[bc]','aaabcbc'),('3[a2[c]]','accaccacc'),
               ('2[abc]3[cd]ef','abcabccdcdcdef'),('',''),('abc','abc'),
               ('10[a]','a'*10),('2[3[a]b]','aaabaaab')]:
    chk(f"lcb_018 {s!r}", dec_rec(s), exp)

# ---------- lcb_009: enumerate segmentations, verify sorted order claims ----------
print("== lcb_009 word_break: enumerate all segmentations ==")
def wb_all(s, wd):
    words = set(wd)
    res = []
    def rec(i, parts):
        if i == len(s):
            res.append(' '.join(parts)); return
        for j in range(i+1, len(s)+1):
            if s[i:j] in words:
                rec(j, parts + [s[i:j]])
    if s == '': return []
    rec(0, [])
    return sorted(res)
for s, wd, exp in [('catsanddog',['cat','cats','and','sand','dog'],['cat sand dog','cats and dog']),
                   ('pineapplepenapple',['apple','pen','applepen','pine','pineapple'],
                    ['pine apple pen apple','pine applepen apple','pineapple pen apple']),
                   ('catsandog',['cats','dog','sand','and','cat'],[]),
                   ('',['a'],[])]:
    chk(f"lcb_009 {s!r}", wb_all(s, wd), exp)

# ---------- lcb_019: backtracking cross-check ----------
print("== lcb_019 permute_unique: backtracking cross-check ==")
def perm_bt(nums):
    nums = sorted(nums)
    used = [False]*len(nums)
    out = []
    def bt(path):
        if len(path) == len(nums):
            out.append(list(path)); return
        for i in range(len(nums)):
            if used[i]: continue
            if i > 0 and nums[i] == nums[i-1] and not used[i-1]: continue
            used[i] = True; path.append(nums[i])
            bt(path)
            path.pop(); used[i] = False
    bt([])
    return out
for nums, exp in [([1,1,2],[[1,1,2],[1,2,1],[2,1,1]]),
                  ([1,2,3],[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]),
                  ([1],[[1]]),([],[[ ]]),([2,2,2],[[2,2,2]])]:
    chk(f"lcb_019 {nums}", perm_bt(nums), exp)

# ---------- lcb_016: brute-force subsets ----------
print("== lcb_016 partition: brute-force subsets ==")
def part_bf(nums):
    if not nums: return True
    total = sum(nums)
    if total % 2: return False
    for r in range(len(nums)+1):
        for c in itertools.combinations(nums, r):
            if sum(c) == total // 2: return True
    return False
for nums, exp in [([1,5,11,5],True),([1,2,3,5],False),([],True),([2],False),
                  ([1,1],True),([3,3,3,4,5],True),([1,2,5],False)]:
    chk(f"lcb_016 {nums}", part_bf(nums), exp)

# ---------- lcb_001 / lcb_007: brute pairs / fib ----------
print("== lcb_001 two_sum / lcb_007 climb: brute ==")
for nums, t, exp in [([2,7,11,15],9,[0,1]),([3,2,4],6,[1,2]),([3,3],6,[0,1])]:
    sols = sorted([[i,j] for i in range(len(nums)) for j in range(i+1,len(nums)) if nums[i]+nums[j]==t])
    chk(f"lcb_001 {nums} t={t} (all solutions)", sols, [exp])
def fib(n):
    a, b = 1, 1
    for _ in range(n): a, b = b, a+b
    return a
for n, exp in [(1,1),(2,2),(3,3),(5,8),(10,89)]:
    chk(f"lcb_007 n={n}", fib(n), exp)

# ---------- held2_014: minute-by-minute simulation ----------
print("== held2_014 rotten_oranges: minute simulation ==")
def rot_sim(grid):
    g = [row[:] for row in grid]
    R, C = len(g), len(g[0])
    m = 0
    while True:
        fresh = [(r,c) for r in range(R) for c in range(C) if g[r][c]==1]
        if not fresh: return m
        new = []
        for r, c in fresh:
            if any(0<=r+dr<R and 0<=c+dc<C and g[r+dr][c+dc]==2 for dr,dc in ((1,0),(-1,0),(0,1),(0,-1))):
                new.append((r,c))
        if not new: return -1
        for r, c in new: g[r][c] = 2
        m += 1
for g, exp in [([[2,1,1],[1,1,0],[0,1,1]],4),([[2,1,1],[0,1,1],[1,0,1]],-1),
               ([[0,2]],0),([[1]],-1),([[0,0],[0,0]],0),
               ([[2,2],[1,1],[0,0],[2,0]],1)]:
    chk(f"held2_014 {g}", rot_sim(g), exp)

# ---------- held2_015: sort-based ----------
print("== held2_015 longest_consecutive: sort-based ==")
def lc_sort(nums):
    if not nums: return 0
    a = sorted(set(nums))
    best, cur = 1, 1
    for i in range(1, len(a)):
        cur = cur+1 if a[i]==a[i-1]+1 else 1
        best = max(best, cur)
    return best
for nums, exp in [([100,4,200,1,3,2],4),([0,3,7,2,5,8,4,6,0,1],9),([],0),
                  ([1,2,0,1],3),([9,1,4,7,3,-1,0,5,8,-1,6],7),([5],1),([1,1,1],1)]:
    chk(f"held2_015 {nums}", lc_sort(nums), exp)

# ---------- lcb_008: union-find grouping cross-check ----------
print("== lcb_008 merge: union-find grouping ==")
def merge_uf(intervals):
    if not intervals: return []
    n = len(intervals)
    parent = list(range(n))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra!=rb: parent[ra]=rb
    for i in range(n):
        for j in range(i+1,n):
            if intervals[i][0] <= intervals[j][1] and intervals[j][0] <= intervals[i][1]:
                union(i,j)
    groups = {}
    for i in range(n): groups.setdefault(find(i), []).append(intervals[i])
    out = []
    for g in groups.values():
        out.append({'start': min(x[0] for x in g), 'end': max(x[1] for x in g), 'count': len(g)})
    return sorted(out, key=lambda d: d['start'])
for iv, exp in [([[1,3],[2,6],[8,10],[15,18]],[{'start':1,'end':6,'count':2},{'start':8,'end':10,'count':1},{'start':15,'end':18,'count':1}]),
                ([[2,6],[1,3],[15,18],[8,10]],[{'start':1,'end':6,'count':2},{'start':8,'end':10,'count':1},{'start':15,'end':18,'count':1}]),
                ([[1,4],[4,5]],[{'start':1,'end':5,'count':2}]),
                ([],[])]:
    chk(f"lcb_008 {iv}", merge_uf(iv), exp)

# ---------- lcb_010: union-find 4-dir cross-check ----------
print("== lcb_010 islands: union-find 4-dir + 8-dir contrast ==")
def islands(grid, dirs):
    if not grid: return 0
    R, C = len(grid), len(grid[0])
    parent = {}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for r in range(R):
        for c in range(C):
            if grid[r][c]=='1': parent[(r,c)]=(r,c)
    for (r,c) in list(parent):
        for dr,dc in dirs:
            nb=(r+dr,c+dc)
            if nb in parent:
                ra,rb=find((r,c)),find(nb)
                if ra!=rb: parent[ra]=rb
    return len({find(x) for x in parent})
g1=[['1','1','1','1','0'],['1','1','0','1','0'],['1','1','0','0','0'],['0','0','0','0','0']]
g2=[['1','1','0','0','0'],['1','1','0','0','0'],['0','0','1','0','0'],['0','0','0','1','1']]
chk("lcb_010 g1 4-dir", islands(g1, ((1,0),(-1,0),(0,1),(0,-1))), 1)
chk("lcb_010 g2 4-dir", islands(g2, ((1,0),(-1,0),(0,1),(0,-1))), 3)
print(f"  g2 with 8-dir would give {islands(g2, [(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc)!=(0,0)])} (must differ from 3 to discriminate)")

# ---------- lcb_012 / held2_007: DFS cycle cross-check ----------
print("== lcb_012 can_finish / held2_007 order: DFS cross-check ==")
def has_cycle(n, pre):
    adj=[[] for _ in range(n)]
    for a,b in pre: adj[b].append(a)
    state=[0]*n
    def dfs(u):
        state[u]=1
        for v in adj[u]:
            if state[v]==1: return True
            if state[v]==0 and dfs(v): return True
        state[u]=2
        return False
    return any(state[i]==0 and dfs(i) for i in range(n))
for n, pre, exp in [(2,[[1,0]],True),(2,[[1,0],[0,1]],False),(4,[[1,0],[2,0],[3,1],[3,2]],True),
                    (3,[[0,1],[1,2],[2,0]],False),(1,[],True),(5,[],True),(3,[[1,0],[2,1]],True)]:
    chk(f"lcb_012 n={n} {pre}", not has_cycle(n, pre), exp)
for n, pre, cyclic in [(2,[[1,0]],False),(2,[[1,0],[0,1]],True),(4,[[1,0],[2,0],[3,1],[3,2]],False),
                       (1,[],False),(3,[],False),(3,[[0,1],[1,2],[2,0]],True)]:
    chk(f"held2_007 cycle? n={n} {pre}", has_cycle(n, pre), cyclic)

# ---------- held2_011: violation-type analysis ----------
print("== held2_011 sudoku: violation-type analysis ==")
valid_board = [['5','3','.','.','7','.','.','.','.'],['6','.','.','1','9','5','.','.','.'],
               ['.','9','8','.','.','.','.','6','.'],['8','.','.','.','6','.','.','.','3'],
               ['4','.','.','8','.','3','.','.','1'],['7','.','.','.','2','.','.','.','6'],
               ['.','6','.','.','.','.','2','8','.'],['.','.','.','4','1','9','.','.','5'],
               ['.','.','.','.','8','.','.','7','9']]
def violations(board):
    row_v, col_v, box_v = [], [], []
    for r in range(9):
        vals=[v for v in board[r] if v!='.']
        if len(vals)!=len(set(vals)): row_v.append(r)
    for c in range(9):
        vals=[board[r][c] for r in range(9) if board[r][c]!='.']
        if len(vals)!=len(set(vals)): col_v.append(c)
    for br in range(3):
        for bc in range(3):
            vals=[board[r][c] for r in range(br*3,br*3+3) for c in range(bc*3,bc*3+3) if board[r][c]!='.']
            if len(vals)!=len(set(vals)): box_v.append((br,bc))
    return row_v, col_v, box_v
def show(name, board):
    rv, cv, bv = violations(board)
    print(f"  {name}: row_viol={rv} col_viol={cv} box_viol={bv} -> valid={not (rv or cv or bv)}")
    return not (rv or cv or bv)
chk("held2_011 valid_board", show("valid_board", valid_board), True)
b2=[r[:] for r in valid_board]; b2[0][2]='5'
chk("held2_011 b2", show("b2 [0][2]=5", b2), False)
b3=[r[:] for r in valid_board]; b3[1][0]='5'
chk("held2_011 b3", show("b3 [1][0]=5", b3), False)
b4=[r[:] for r in valid_board]; b4[1][1]='5'
chk("held2_011 b4", show("b4 [1][1]=5", b4), False)
chk("held2_011 empty", show("empty", [['.']*9 for _ in range(9)]), True)
b6=[['.']*9 for _ in range(9)]; b6[0][0]='9'; b6[8][8]='9'
chk("held2_011 b6", show("b6 two 9s", b6), True)

print()
print("TOTAL MISMATCHES:", len(fails))
for f in fails: print(" -", f)
