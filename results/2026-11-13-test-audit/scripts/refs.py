# Reference solutions, written independently from each problem's SPEC text
# (not copied from traces). Each value is a code string run against the
# problem's real test_cases with the exact run_test_cases semantics.
REFS = {}

REFS["lcb_001_two_sum"] = '''
def two_sum(nums, target):
    seen = {}
    for i, v in enumerate(nums):
        need = target - v
        if need in seen:
            return sorted([seen[need], i])
        seen[v] = i
    return []
'''

REFS["lcb_002_valid_parentheses"] = '''
def is_valid(s):
    # Exhaustive: each '*' is '(', ')' or ''. Other chars must match stack-wise.
    pairs = {')': '(', ']': '[', '}': '{'}
    opens = set('([{')
    def check(chars):
        stack = []
        for ch in chars:
            if ch in opens:
                stack.append(ch)
            elif ch in pairs:
                if not stack or stack[-1] != pairs[ch]:
                    return False
                stack.pop()
            else:
                return False
        return not stack
    def rec(i, acc):
        if i == len(s):
            return check(acc)
        ch = s[i]
        if ch == '*':
            return rec(i+1, acc) or rec(i+1, acc+['(']) or rec(i+1, acc+[')'])
        return rec(i+1, acc+[ch])
    return rec(0, [])
'''

REFS["lcb_003_lru_cache"] = '''
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
            return None
        evicted = None
        if len(self.d) >= self.capacity:
            evicted, _ = self.d.popitem(last=False)
        self.d[key] = value
        return evicted
'''

REFS["lcb_004_reverse_linked_list"] = '''
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
def reverse_list(head):
    prev = None
    cur = head
    while cur is not None:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev
'''

REFS["lcb_005_binary_search"] = '''
def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
'''

REFS["lcb_006_max_subarray"] = '''
def max_sub_array(nums):
    if not nums:
        return (0, [])
    best_sum = nums[0]
    best_l, best_r = 0, 0
    cur_sum = nums[0]
    cur_l = 0
    for i in range(1, len(nums)):
        if cur_sum < 0:
            cur_sum = nums[i]
            cur_l = i
        else:
            cur_sum += nums[i]
        if cur_sum > best_sum:
            best_sum = cur_sum
            best_l, best_r = cur_l, i
    return (best_sum, nums[best_l:best_r+1])
'''

REFS["lcb_007_climbing_stairs"] = '''
def climb_stairs(n):
    if n <= 1:
        return 1
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b
'''

REFS["lcb_008_merge_intervals"] = '''
def merge(intervals):
    if not intervals:
        return []
    ivs = sorted(intervals, key=lambda x: x[0])
    out = []
    cs, ce, cnt = ivs[0][0], ivs[0][1], 1
    for s, e in ivs[1:]:
        if s <= ce:
            ce = max(ce, e)
            cnt += 1
        else:
            out.append({'start': cs, 'end': ce, 'count': cnt})
            cs, ce, cnt = s, e, 1
    out.append({'start': cs, 'end': ce, 'count': cnt})
    return out
'''

REFS["lcb_009_word_break"] = '''
def word_break(s, word_dict):
    words = set(word_dict)
    memo = {}
    def rec(i):
        if i in memo:
            return memo[i]
        if i == len(s):
            return [[]]
        res = []
        for j in range(i + 1, len(s) + 1):
            w = s[i:j]
            if w in words:
                for rest in rec(j):
                    res.append([w] + rest)
        memo[i] = res
        return res
    if s == '':
        return []
    return sorted(' '.join(parts) for parts in rec(0))
'''

REFS["lcb_010_number_of_islands"] = '''
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
                stack = [(r, c)]
                seen[r][c] = True
                while stack:
                    x, y = stack.pop()
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < R and 0 <= ny < C and grid[nx][ny] == '1' and not seen[nx][ny]:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
    return count
'''

REFS["lcb_011_trap_rain_water"] = '''
def trap(height):
    l, r = 0, len(height) - 1
    lm, rm = 0, 0
    ans = 0
    while l < r:
        if height[l] < height[r]:
            lm = max(lm, height[l])
            ans += lm - height[l]
            l += 1
        else:
            rm = max(rm, height[r])
            ans += rm - height[r]
            r -= 1
    return ans
'''

REFS["lcb_012_can_finish_courses"] = '''
from collections import deque
def can_finish(num_courses, prerequisites):
    indeg = [0]*num_courses
    adj = [[] for _ in range(num_courses)]
    for a, b in prerequisites:
        adj[b].append(a)
        indeg[a] += 1
    q = deque([i for i in range(num_courses) if indeg[i] == 0])
    done = 0
    while q:
        u = q.popleft()
        done += 1
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return done == num_courses
'''

REFS["lcb_013_longest_palindromic_substring"] = '''
def longest_palindrome(s):
    # Brute force: max length, smallest start index (exactly the spec tie-break).
    n = len(s)
    best = ''
    best_start = 0
    for i in range(n):
        for j in range(i + 1, n + 1):
            sub = s[i:j]
            if sub == sub[::-1] and len(sub) > len(best):
                best = sub
                best_start = i
    return best
'''

REFS["lcb_014_daily_temperatures"] = '''
def daily_temperatures(temperatures):
    n = len(temperatures)
    ans = [0]*n
    stack = []
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            ans[j] = i - j
        stack.append(i)
    return ans
'''

REFS["lcb_015_word_search"] = '''
def exist(board, word):
    if not board or not board[0]:
        return False
    R, C = len(board), len(board[0])
    def dfs(r, c, k):
        if k == len(word):
            return True
        if not (0 <= r < R and 0 <= c < C) or board[r][c] != word[k]:
            return False
        tmp = board[r][c]
        board[r][c] = '#'
        ok = (dfs(r+1, c, k+1) or dfs(r-1, c, k+1) or dfs(r, c+1, k+1) or dfs(r, c-1, k+1))
        board[r][c] = tmp
        return ok
    for r in range(R):
        for c in range(C):
            if dfs(r, c, 0):
                return True
    return False
'''

REFS["lcb_016_partition_equal_subset"] = '''
def can_partition(nums):
    if not nums:
        return True
    total = sum(nums)
    if total % 2 != 0:
        return False
    target = total // 2
    reach = {0}
    for v in nums:
        reach = reach | {x + v for x in list(reach) if x + v <= target}
        if target in reach:
            return True
    return target in reach
'''

REFS["lcb_017_merge_k_sorted_lists"] = '''
import heapq
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
def merge_k_lists(lists):
    heap = []
    for idx, node in enumerate(lists):
        if node is not None:
            heapq.heappush(heap, (node.val, idx, node))
    if not heap:
        return None
    dummy = ListNode(0)
    cur = dummy
    while heap:
        _, idx, node = heapq.heappop(heap)
        cur.next = node
        cur = cur.next
        if node.next is not None:
            heapq.heappush(heap, (node.next.val, idx, node.next))
    return dummy.next
'''

REFS["lcb_018_decode_string"] = '''
def decode_string(s):
    stack = []
    cur = ''
    num = 0
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch == '[':
            stack.append((cur, num))
            cur = ''
            num = 0
        elif ch == ']':
            prev, k = stack.pop()
            cur = prev + cur * k
        else:
            cur += ch
    return cur
'''

REFS["lcb_019_permutations_unique"] = '''
import itertools
def permute_unique(nums):
    return sorted([list(p) for p in set(itertools.permutations(nums))])
'''

REFS["lcb_020_min_jumps"] = '''
from collections import deque
def jump(nums):
    n = len(nums)
    if n <= 1:
        return 0
    seen = [False]*n
    q = deque([(0, 0)])
    seen[0] = True
    while q:
        i, d = q.popleft()
        reach = min(n - 1, i + nums[i])
        for j in range(i + 1, reach + 1):
            if j == n - 1:
                return d + 1
            if not seen[j]:
                seen[j] = True
                q.append((j, d + 1))
    return -1
'''

REFS["held2_001_edit_distance"] = '''
def min_distance(word1, word2):
    m, n = len(word1), len(word2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            tmp = dp[j]
            cost = 0 if word1[i-1] == word2[j-1] else 1
            dp[j] = min(dp[j] + 1, dp[j-1] + 1, prev + cost)
            prev = tmp
    return dp[n]
'''

REFS["held2_002_regex_match"] = '''
def is_match(s, p):
    from functools import lru_cache
    @lru_cache(maxsize=None)
    def dp(i, j):
        if j == len(p):
            return i == len(s)
        first = i < len(s) and (p[j] == s[i] or p[j] == '.')
        if j + 1 < len(p) and p[j+1] == '*':
            return dp(i, j+2) or (first and dp(i+1, j))
        return first and dp(i+1, j+1)
    return dp(0, 0)
'''

REFS["held2_003_n_queens_count"] = '''
def total_n_queens(n):
    count = 0
    cols, d1, d2 = set(), set(), set()
    def backtrack(r):
        nonlocal count
        if r == n:
            count += 1
            return
        for c in range(n):
            if c in cols or (r - c) in d1 or (r + c) in d2:
                continue
            cols.add(c); d1.add(r - c); d2.add(r + c)
            backtrack(r + 1)
            cols.discard(c); d1.discard(r - c); d2.discard(r + c)
    backtrack(0)
    return count
'''

REFS["held2_004_number_of_lis"] = '''
def find_number_of_lis(nums):
    n = len(nums)
    if n == 0:
        return 0
    lengths = [1]*n
    counts = [1]*n
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                if lengths[j] + 1 > lengths[i]:
                    lengths[i] = lengths[j] + 1
                    counts[i] = counts[j]
                elif lengths[j] + 1 == lengths[i]:
                    counts[i] += counts[j]
    mx = max(lengths)
    return sum(c for l, c in zip(lengths, counts) if l == mx)
'''

REFS["held2_005_word_ladder"] = '''
from collections import deque, defaultdict
def ladder_length(begin_word, end_word, word_list):
    words = set(word_list)
    if end_word not in words:
        return 0
    L = len(begin_word)
    buckets = defaultdict(list)
    for w in words:
        for i in range(L):
            buckets[w[:i] + '*' + w[i+1:]].append(w)
    q = deque([(begin_word, 1)])
    seen = {begin_word}
    while q:
        w, d = q.popleft()
        for i in range(L):
            pat = w[:i] + '*' + w[i+1:]
            for nb in buckets[pat]:
                if nb == end_word:
                    return d + 1
                if nb not in seen:
                    seen.add(nb)
                    q.append((nb, d + 1))
            buckets[pat] = []
    return 0
'''

REFS["held2_006_sliding_window_max"] = '''
from collections import deque
def max_sliding_window(nums, k):
    if not nums:
        return []
    dq = deque()
    out = []
    for i, v in enumerate(nums):
        while dq and dq[0] <= i - k:
            dq.popleft()
        while dq and nums[dq[-1]] < v:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            out.append(nums[dq[0]])
    return out
'''

REFS["held2_007_course_order"] = '''
from collections import deque
def find_order(num_courses, prerequisites):
    indeg = [0]*num_courses
    adj = [[] for _ in range(num_courses)]
    for a, b in prerequisites:
        adj[b].append(a)
        indeg[a] += 1
    q = deque([i for i in range(num_courses) if indeg[i] == 0])
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order if len(order) == num_courses else []
'''

REFS["held2_008_median_finder"] = '''
import bisect
class MedianFinder:
    def __init__(self):
        self.data = []
    def add_num(self, num):
        bisect.insort(self.data, num)
    def find_median(self):
        n = len(self.data)
        if n % 2 == 1:
            return float(self.data[n // 2])
        return (self.data[n // 2 - 1] + self.data[n // 2]) / 2.0
'''

REFS["held2_009_next_permutation"] = '''
def next_permutation(nums):
    a = list(nums)
    n = len(a)
    i = n - 2
    while i >= 0 and a[i] >= a[i+1]:
        i -= 1
    if i < 0:
        a.sort()
        return a
    j = n - 1
    while a[j] <= a[i]:
        j -= 1
    a[i], a[j] = a[j], a[i]
    a[i+1:] = sorted(a[i+1:])
    return a
'''

REFS["held2_010_three_sum"] = '''
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
                l += 1
                r -= 1
                while l < r and nums[l] == nums[l-1]:
                    l += 1
                while l < r and nums[r] == nums[r+1]:
                    r -= 1
            elif s < 0:
                l += 1
            else:
                r -= 1
    return out
'''

REFS["held2_011_valid_sudoku"] = '''
def is_valid_sudoku(board):
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == '.':
                continue
            b = (r // 3) * 3 + (c // 3)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v); cols[c].add(v); boxes[b].add(v)
    return True
'''

REFS["held2_012_gas_station"] = '''
def can_complete_circuit(gas, cost):
    total = 0
    tank = 0
    start = 0
    for i in range(len(gas)):
        diff = gas[i] - cost[i]
        total += diff
        tank += diff
        if tank < 0:
            start = i + 1
            tank = 0
    return start if total >= 0 and start < len(gas) else -1
'''

REFS["held2_013_decode_ways"] = '''
def num_decodings(s):
    n = len(s)
    if n == 0 or s[0] == '0':
        return 0
    prev2, prev1 = 1, 1
    for i in range(1, n):
        cur = 0
        if s[i] != '0':
            cur += prev1
        two = int(s[i-1:i+1])
        if 10 <= two <= 26:
            cur += prev2
        prev2, prev1 = prev1, cur
    return prev1
'''

REFS["held2_014_rotten_oranges"] = '''
from collections import deque
def oranges_rotting(grid):
    R, C = len(grid), len(grid[0]) if grid else 0
    q = deque()
    fresh = 0
    g = [row[:] for row in grid]
    for r in range(R):
        for c in range(C):
            if g[r][c] == 2:
                q.append((r, c, 0))
            elif g[r][c] == 1:
                fresh += 1
    if fresh == 0:
        return 0
    minutes = 0
    while q:
        r, c, m = q.popleft()
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < R and 0 <= nc < C and g[nr][nc] == 1:
                g[nr][nc] = 2
                fresh -= 1
                minutes = m + 1
                q.append((nr, nc, m + 1))
    return minutes if fresh == 0 else -1
'''

REFS["held2_015_longest_consecutive"] = '''
def longest_consecutive(nums):
    s = set(nums)
    best = 0
    for v in s:
        if v - 1 not in s:
            cur = v
            ln = 1
            while cur + 1 in s:
                cur += 1
                ln += 1
            best = max(best, ln)
    return best
'''
