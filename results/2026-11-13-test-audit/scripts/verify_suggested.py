import json, subprocess, sys
sys.path.insert(0, "/tmp")
from refs import REFS
allp = {p["id"]: p for p in json.load(open("/tmp/all35.json"))}

SUGGESTED = {
    "lcb_002_valid_parentheses": [
        "assert is_valid('([)]') == False",
        "assert is_valid('[]{}') == True",
        "assert is_valid('[*]') == True",
        "assert is_valid('([*])') == True",
        "assert is_valid('(]') == False",
    ],
    "lcb_004_reverse_linked_list": [
        "assert to_list(reverse_list(make_list([1]))) == [1]",
        "_a = make_list([1, 2, 3]); _ids_before = set()",
        "_n = _a\nwhile _n is not None:\n    _ids_before.add(id(_n)); _n = _n.next",
        "_out = reverse_list(_a); _ids_after = set()",
        "_n = _out\nwhile _n is not None:\n    _ids_after.add(id(_n)); _n = _n.next",
        "assert _ids_before == _ids_after",
    ],
    "lcb_009_word_break": [
        "assert word_break('catsanddog', ['dog', 'sand', 'and', 'cats', 'cat']) == ['cat sand dog', 'cats and dog']",
    ],
    "lcb_014_daily_temperatures": [
        "assert daily_temperatures([70, 70, 71]) == [2, 1, 0]",
        "assert daily_temperatures([73, 73, 73]) == [0, 0, 0]",
    ],
    "lcb_019_permutations_unique": [
        "assert permute_unique([2, 1, 1]) == [[1, 1, 2], [1, 2, 1], [2, 1, 1]]",
        "assert permute_unique([3, 1, 2]) == [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]",
    ],
    "held2_011_valid_sudoku": [
        "_cb = [['.'] * 9 for _ in range(9)]; _cb[0][0] = '5'; _cb[3][0] = '5'; assert is_valid_sudoku(_cb) == False",
        "_bb = [['.'] * 9 for _ in range(9)]; _bb[0][0] = '5'; _bb[1][1] = '5'; assert is_valid_sudoku(_bb) == False",
    ],
}
for pid, extra in SUGGESTED.items():
    p = allp[pid]
    script = REFS[pid] + "\n\n# --- suggested ---\n" + "\n".join(p["test_cases"] + extra) + "\n"
    r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=10)
    print(pid, "REF + suggested:", "PASS" if r.returncode == 0 else "FAIL " + (r.stderr or "")[-300:])
