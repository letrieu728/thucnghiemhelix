import json, subprocess, sys

allp = {p["id"]: p for p in json.load(open("/tmp/all35.json"))}

def run(pid, code, extra_tests=None):
    p = allp[pid]
    tests = list(p["test_cases"]) + (extra_tests or [])
    script = f"{code}\n\n# --- probe ---\n" + "\n".join(tests) + "\n"
    r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=10)
    return r.returncode == 0, (r.stderr or "").strip().split("\n")[-1][:160]

def probe(name, pid, code, expect, extra_tests=None):
    ok, err = run(pid, code, extra_tests)
    verdict = "PASS" if ok else "FAIL"
    match = "as-expected" if ok == expect else "*** UNEXPECTED ***"
    print(f"{verdict:4} [{match}] {name} (expected {'PASS' if expect else 'FAIL'})" + ("" if ok else f" :: {err}"))

# --- held2_011: row-only and row+col-only checkers (expect PASS = gap) ---
probe("sudoku ROW-ONLY checker", "held2_011_valid_sudoku", '''
def is_valid_sudoku(board):
    for r in range(9):
        vals = [v for v in board[r] if v != '.']
        if len(vals) != len(set(vals)):
            return False
    return True
''', True)
probe("sudoku ROW+COL checker (no boxes)", "held2_011_valid_sudoku", '''
def is_valid_sudoku(board):
    for r in range(9):
        vals = [v for v in board[r] if v != '.']
        if len(vals) != len(set(vals)):
            return False
    for c in range(9):
        vals = [board[r][c] for r in range(9) if board[r][c] != '.']
        if len(vals) != len(set(vals)):
            return False
    return True
''', True)

# --- lcb_014: >= instead of > (expect PASS = gap) ---
probe("daily_temps with >= (non-strict)", "lcb_014_daily_temperatures", '''
def daily_temperatures(temperatures):
    n = len(temperatures)
    ans = [0]*n
    for i in range(n):
        for j in range(i+1, n):
            if temperatures[j] >= temperatures[i]:
                ans[i] = j - i
                break
    return ans
''', True)

# --- lcb_002: ignore [] and {} entirely (expect PASS = gap) ---
probe("is_valid ()-only, ignores []/{}", "lcb_002_valid_parentheses", '''
def is_valid(s):
    t = ''.join(ch for ch in s if ch in '()*')
    def check(chars):
        bal = 0
        for ch in chars:
            if ch == '(': bal += 1
            elif ch == ')':
                bal -= 1
                if bal < 0: return False
        return bal == 0
    def rec(i, acc):
        if i == len(t):
            return check(acc)
        if t[i] == '*':
            return rec(i+1, acc) or rec(i+1, acc+['(']) or rec(i+1, acc+[')'])
        return rec(i+1, acc+[t[i]])
    return rec(0, [])
''', True)

# --- lcb_010: 8-directional (expect FAIL = discrimination works) ---
probe("islands 8-directional (must FAIL)", "lcb_010_number_of_islands", '''
def num_islands(grid):
    if not grid or not grid[0]:
        return 0
    R, C = len(grid), len(grid[0])
    seen = [[False]*C for _ in range(R)]
    count = 0
    for r in range(R):
        for c in range(C):
            if grid[r][c] == '1' and not seen[r][c]:
                count += 1
                stack = [(r, c)]; seen[r][c] = True
                while stack:
                    x, y = stack.pop()
                    for dx in (-1,0,1):
                        for dy in (-1,0,1):
                            nx, ny = x+dx, y+dy
                            if 0 <= nx < R and 0 <= ny < C and grid[nx][ny] == '1' and not seen[nx][ny]:
                                seen[nx][ny] = True
                                stack.append((nx, ny))
    return count
''', False)

# --- lcb_004: build NEW nodes, not in-place (expect PASS = in-place untested) ---
probe("reverse_list via NEW nodes (not in-place)", "lcb_004_reverse_linked_list", '''
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
def reverse_list(head):
    vals = []
    cur = head
    while cur is not None:
        vals.append(cur.val)
        cur = cur.next
    dummy = ListNode(0)
    cur = dummy
    for v in reversed(vals):
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next
''', True)

# --- lcb_019: encounter order, no sort (expect PASS on real tests; FAIL on unsorted input) ---
probe("permute_unique encounter-order (no sort)", "lcb_019_permutations_unique", '''
import itertools
def permute_unique(nums):
    seen = set()
    out = []
    for p in itertools.permutations(nums):
        if p not in seen:
            seen.add(p)
            out.append(list(p))
    return out
''', True)
probe("permute_unique encounter-order + extra [2,1,1] (must FAIL)",
      "lcb_019_permutations_unique", '''
import itertools
def permute_unique(nums):
    seen = set()
    out = []
    for p in itertools.permutations(nums):
        if p not in seen:
            seen.add(p)
            out.append(list(p))
    return out
''', False, extra_tests=["assert permute_unique([2, 1, 1]) == [[1, 1, 2], [1, 2, 1], [2, 1, 1]]"])

# --- held2_009: mutating variants (expect FAIL = non-mutation tested) ---
probe("next_perm mutates input, returns copy (must FAIL T7)", "held2_009_next_permutation", '''
def next_permutation(nums):
    a = nums  # alias: mutates caller's list
    n = len(a)
    i = n - 2
    while i >= 0 and a[i] >= a[i+1]:
        i -= 1
    if i < 0:
        a.sort()
        return list(a)
    j = n - 1
    while a[j] <= a[i]:
        j -= 1
    a[i], a[j] = a[j], a[i]
    a[i+1:] = sorted(a[i+1:])
    return list(a)
''', False)
probe("next_perm LeetCode in-place, returns None (must FAIL)", "held2_009_next_permutation", '''
def next_permutation(nums):
    n = len(nums)
    i = n - 2
    while i >= 0 and nums[i] >= nums[i+1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    nums[i+1:] = sorted(nums[i+1:])
    return None
''', False)

# --- lcb_013: last-max tie-break (expect FAIL = tie-break tested) ---
probe("longest_palindrome LAST max (must FAIL)", "lcb_013_longest_palindromic_substring", '''
def longest_palindrome(s):
    best = ''
    best_start = -1
    for i in range(len(s)):
        for j in range(i+1, len(s)+1):
            sub = s[i:j]
            if sub == sub[::-1] and (len(sub) > len(best) or (len(sub) == len(best) and i > best_start)):
                best, best_start = sub, i
    return best
''', False)

# --- lcb_015: cell reuse allowed (expect FAIL = ABCB catches) ---
probe("word_search with cell REUSE (must FAIL)", "lcb_015_word_search", '''
def exist(board, word):
    if not board or not board[0]:
        return False
    R, C = len(board), len(board[0])
    def dfs(r, c, k):
        if k == len(word):
            return True
        if not (0 <= r < R and 0 <= c < C) or board[r][c] != word[k]:
            return False
        return (dfs(r+1, c, k+1) or dfs(r-1, c, k+1) or dfs(r, c+1, k+1) or dfs(r, c-1, k+1))
    for r in range(R):
        for c in range(C):
            if dfs(r, c, 0):
                return True
    return False
''', False)

# --- lcb_003: put always returns None (expect FAIL = eviction return tested) ---
probe("LRU put always None (must FAIL)", "lcb_003_lru_cache", '''
from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.d = OrderedDict()
    def get(self, key):
        if key not in self.d:
            return -1
        self.d.move_to_end(key)
        return self.d[key]
    def put(self, key, value):
        if key in self.d:
            self.d[key] = value
            self.d.move_to_end(key)
        else:
            if len(self.d) >= self.capacity:
                self.d.popitem(last=False)
            self.d[key] = value
        return None
''', False)

# --- held2_010: reversed output order (expect FAIL = sorting tested) ---
probe("three_sum reversed order (must FAIL)", "held2_010_three_sum", '''
def three_sum(nums):
    nums = sorted(nums)
    n = len(nums)
    out = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i-1]:
            continue
        l, r = i + 1, n - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s == 0:
                out.append([nums[i], nums[l], nums[r]])
                l += 1; r -= 1
                while l < r and nums[l] == nums[l-1]: l += 1
                while l < r and nums[r] == nums[r+1]: r -= 1
            elif s < 0: l += 1
            else: r -= 1
    return list(reversed(out))
''', False)

# --- lcb_008: count always 1 (expect FAIL) ---
probe("merge count always 1 (must FAIL)", "lcb_008_merge_intervals", '''
def merge(intervals):
    if not intervals:
        return []
    ivs = sorted(intervals, key=lambda x: x[0])
    out = []
    cs, ce = ivs[0][0], ivs[0][1]
    for s, e in ivs[1:]:
        if s <= ce:
            ce = max(ce, e)
        else:
            out.append({'start': cs, 'end': ce, 'count': 1})
            cs, ce = s, e
    out.append({'start': cs, 'end': ce, 'count': 1})
    return out
''', False)

# --- lcb_009: dict-order DFS, no sort (informative) ---
probe("word_break dict-order, NO sort (informative)", "lcb_009_word_break", '''
def word_break(s, word_dict):
    if s == '':
        return []
    out = []
    def rec(i, parts):
        if i == len(s):
            out.append(' '.join(parts))
            return
        for w in word_dict:
            if s.startswith(w, i):
                rec(i + len(w), parts + [w])
    rec(0, [])
    return out
''', False)

# --- held2_007: fixed range order (expect FAIL: cycle + prereq) ---
probe("find_order fixed range (must FAIL)", "held2_007_course_order", '''
def find_order(num_courses, prerequisites):
    return list(range(num_courses))
''', False)

# --- held2_008: int median when whole (informative: == is lenient) ---
probe("MedianFinder int-when-whole (informative)", "held2_008_median_finder", '''
import bisect
class MedianFinder:
    def __init__(self):
        self.data = []
    def add_num(self, num):
        bisect.insort(self.data, num)
    def find_median(self):
        n = len(self.data)
        if n % 2 == 1:
            return self.data[n // 2]
        m = (self.data[n // 2 - 1] + self.data[n // 2]) / 2
        return int(m) if m == int(m) else m
''', True)

print()
print("== extra structural checks ==")
# lcb_002: do any test string literals contain [] or {} ?
import ast
p = allp["lcb_002_valid_parentheses"]
src = "\n".join(p["test_cases"])
lits = [n.value for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
print("lcb_002 string literals in tests:", lits)
print("lcb_002 any literal contains [ ] { } ?", any(any(ch in lit for ch in "[]{}") for lit in lits))
# lcb_019: are all test inputs pre-sorted?
p = allp["lcb_019_permutations_unique"]
print("lcb_019 test inputs: all sorted?", "see dump: [1,1,2],[1,2,3],[1],[],[2,2,2] - all non-decreasing: True")
# lcb_014: any equal adjacent temps in tests?
p = allp["lcb_014_daily_temperatures"]
src = "\n".join(p["test_cases"])
for n in ast.walk(ast.parse(src)):
    pass
print("lcb_014 inputs: [73,74,75,71,69,72,76,73],[30,40,50,60],[30,60,90],[90,80,70],[],[50] - no equal adjacent pair: True")
# held2_007 _valid helper: feed invalid orders directly
helper = "\n".join(allp["held2_007_course_order"]["test_cases"][:4])
ns = {}
exec(helper, ns)
V = ns["_valid"]
print("_valid([1,0],2,[[1,0]]) =", V([1, 0], 2, [[1, 0]]), "(expect False: prereq violated)")
print("_valid([0],2,[[1,0]]) =", V([0], 2, [[1, 0]]), "(expect False: missing course)")
print("_valid([0,0],2,[[1,0]]) =", V([0, 0], 2, [[1, 0]]), "(expect False: duplicate)")
print("_valid([0,1],2,[[1,0]]) =", V([0, 1], 2, [[1, 0]]), "(expect True)")
# held2_008 medians via statistics
import statistics
for data, exp in [([1,2],1.5),([1,2,3],2.0),([-1,-2],-1.5),([1,2,3,4,5],3.0),([5],5.0),([5,5],5.0),([10,0,5,5],5.0)]:
    print(f"statistics.median({data}) = {statistics.median(data)} expected {exp} -> {statistics.median(data)==exp}")
# lcb_005: unique occurrences via linear scan
for nums, t, exp in [([-1,0,3,5,9,12],9,4),([-1,0,3,5,9,12],2,-1),([5],5,0),([5],3,-1),([],1,-1)]:
    idxs = [i for i,v in enumerate(nums) if v==t]
    got = idxs[0] if idxs else -1
    print(f"lcb_005 linear scan {nums} t={t}: occurrences={idxs} got={got} expected={exp} -> {got==exp}")
# lcb_003: independent recency-list simulation of the exact test sequence
print("lcb_003 independent trace: capacity=2, order list = LRU->MRU")
class LRU2:
    def __init__(self, cap): self.cap=cap; self.d={}; self.order=[]
    def get(self,k):
        if k not in self.d: return -1
        self.order.remove(k); self.order.append(k); return self.d[k]
    def put(self,k,v):
        if k in self.d:
            self.d[k]=v; self.order.remove(k); self.order.append(k); return None
        ev=None
        if len(self.d)>=self.cap:
            ev=self.order.pop(0); del self.d[ev]
        self.d[k]=v; self.order.append(k); return ev
c=LRU2(2)
seq=[("put",1,1,None),("put",2,2,None),("get",1,None,1),("put",3,3,2),("get",2,None,-1),
     ("put",1,10,None),("get",1,None,10),("put",4,4,3),("get",3,None,-1),("get",4,None,4)]
for op,a,b,exp in seq:
    got = c.get(a) if op=="get" else c.put(a,b)
    print(f"  {op}({a}{','+str(b) if op=='put' else ''}) = {got!r} expected {exp!r} -> {got==exp} order={c.order}")
# lcb_015: path-enumeration cross-check for classic boards
board=[['A','B','C','E'],['S','F','C','S'],['A','D','E','E']]
def exist_enum(board, word):
    R,C=len(board),len(board[0])
    def paths(r,c,k,used):
        if k==len(word): return True
        if not (0<=r<R and 0<=c<C) or (r,c) in used or board[r][c]!=word[k]: return False
        used=used|{(r,c)}
        return any(paths(r+dr,c+dc,k+1,used) for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)))
    return any(paths(r,c,0,set()) for r in range(R) for c in range(C))
for w,exp in [('ABCCED',True),('SEE',True),('ABCB',False)]:
    print(f"lcb_015 enum {w}: {exist_enum(board,w)} expected {exp}")
