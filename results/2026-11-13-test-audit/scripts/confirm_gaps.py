# Confirm each suspected (b) gap with a concrete spec-valid input where a
# test-passing implementation gives a spec-violating answer.
import subprocess, sys, json

# --- lcb_009: dict-order DFS (passes all real tests) vs shuffled dict order ---
code = '''
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
print(word_break('catsanddog', ['cat', 'cats', 'and', 'sand', 'dog']))
print(word_break('catsanddog', ['dog', 'sand', 'and', 'cats', 'cat']))
'''
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
print("lcb_009 dict-order DFS, original dict order:", r.stdout.strip().split("\n")[0])
print("lcb_009 dict-order DFS, shuffled dict order:", r.stdout.strip().split("\n")[1])
print("  -> shuffled order output is NOT sorted => gap confirmed (spec demands sorted regardless of dict order)")

# --- lcb_014: >= variant on equal temperatures ---
code = '''
def dt_ge(t):
    ans = [0]*len(t)
    for i in range(len(t)):
        for j in range(i+1, len(t)):
            if t[j] >= t[i]:
                ans[i] = j - i
                break
    return ans
def dt_gt(t):
    ans = [0]*len(t)
    for i in range(len(t)):
        for j in range(i+1, len(t)):
            if t[j] > t[i]:
                ans[i] = j - i
                break
    return ans
print(">= :", dt_ge([70, 70, 71]))
print(">  :", dt_gt([70, 70, 71]))
'''
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
print("lcb_014 equal-temp input [70,70,71]:\n" + r.stdout)

# --- lcb_002: ()-only variant on bracket-mixing inputs ---
code = '''
def is_valid_parenonly(s):
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
        if i == len(t): return check(acc)
        if t[i] == '*':
            return rec(i+1, acc) or rec(i+1, acc+['(']) or rec(i+1, acc+[')'])
        return rec(i+1, acc+[t[i]])
    return rec(0, [])
def is_valid_full(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    def check(chars):
        stack = []
        for ch in chars:
            if ch in '([{': stack.append(ch)
            elif ch in pairs:
                if not stack or stack[-1] != pairs[ch]: return False
                stack.pop()
        return not stack
    def rec(i, acc):
        if i == len(s): return check(acc)
        if s[i] == '*':
            return rec(i+1, acc) or rec(i+1, acc+['(']) or rec(i+1, acc+[')'])
        return rec(i+1, acc+[s[i]])
    return rec(0, [])
for s in ['([)]', '(]', '[(])', '[]', '{}', '([{}])']:
    print(repr(s), "paren-only:", is_valid_parenonly(s), " full-spec:", is_valid_full(s))
'''
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
print("lcb_002 bracket-mixing inputs:\n" + r.stdout)

# --- held2_011: column-only violation board ---
code = '''
def row_only(board):
    for r in range(9):
        vals = [v for v in board[r] if v != '.']
        if len(vals) != len(set(vals)): return False
    return True
def full(board):
    rows=[set() for _ in range(9)]; cols=[set() for _ in range(9)]; boxes=[set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v=board[r][c]
            if v=='.': continue
            b=(r//3)*3+(c//3)
            if v in rows[r] or v in cols[c] or v in boxes[b]: return False
            rows[r].add(v); cols[c].add(v); boxes[b].add(v)
    return True
b=[['.']*9 for _ in range(9)]; b[0][0]='5'; b[3][0]='5'
print("column-only violation board: row-only:", row_only(b), " full:", full(b))
b2=[['.']*9 for _ in range(9)]; b2[0][0]='5'; b2[1][1]='5'
print("box-only violation board: row-only:", row_only(b2), " full:", full(b2))
b3=[['.']*9 for _ in range(9)]; b3[0][0]='5'; b3[1][1]='5'
def rowcol(board):
    for r in range(9):
        vals=[v for v in board[r] if v!='.']
        if len(vals)!=len(set(vals)): return False
    for c in range(9):
        vals=[board[r][c] for r in range(9) if board[r][c]!='.']
        if len(vals)!=len(set(vals)): return False
    return True
print("box-only violation board: row+col:", rowcol(b3), " full:", full(b3))
'''
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
print("held2_011 isolated-violation boards:\n" + r.stdout)

# --- lcb_004: identity check distinguishes in-place vs new nodes ---
code = '''
class ListNode:
    def __init__(self, val=0, next=None): self.val=val; self.next=next
def reverse_new(head):
    vals=[]; cur=head
    while cur is not None: vals.append(cur.val); cur=cur.next
    dummy=ListNode(0); cur=dummy
    for v in reversed(vals): cur.next=ListNode(v); cur=cur.next
    return dummy.next
def reverse_inplace(head):
    prev=None; cur=head
    while cur is not None:
        nxt=cur.next; cur.next=prev; prev=cur; cur=nxt
    return prev
def nodes(head):
    out=[]; cur=head
    while cur is not None: out.append(id(cur)); cur=cur.next
    return out
for fn in (reverse_new, reverse_inplace):
    a=ListNode(1, ListNode(2, ListNode(3)))
    before=set(nodes(a))
    out=fn(a)
    after=set(nodes(out))
    print(fn.__name__, "same node objects:", before==after)
'''
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
print("lcb_004 identity check:\n" + r.stdout)
