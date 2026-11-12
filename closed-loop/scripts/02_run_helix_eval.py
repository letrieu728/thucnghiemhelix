"""
02_run_helix_eval.py - HELIX Harness Evaluation Runner
=======================================================
Drives 4 harnesses (minimal, pi-mono, hermes-agent, opencode) across a built-in
benchmark of 10 algorithmic programming problems and persists per-run trace files
that are 100% compatible with the schema expected by 03_extract_pairs.py.

Two execution modes
-------------------
  live      Call the Modal vLLM endpoint via an OpenAI-compatible client,
            emulating each harness's system prompt / loop depth.
            Requires: HELIX_LIVE_BASE_URL (or --base-url) to be set.

  dry-run   Generate plausible, deterministic mock solutions entirely on-machine
            (no GPU, no Modal, no network).  Useful for validating the full
            pipeline and the output JSON schema on any developer laptop.
            Dry-run traces are labelled "mode": "dry-run" and are REJECTED by
            03_extract_pairs.py unless --allow-dry-run is passed explicitly,
            so mock solutions can never silently enter training data.

  Two problem sets (--problem-set):
  train     The 10 original problems (lcb_001..lcb_010). Training data may
            only be extracted from live BUILD traces on this set.
  train20   The 10 original problems plus 10 extra training problems
            (lcb_011..lcb_020) in closed-loop/data/train_extra_problems.json.
            Round 2 training set (20 tasks). Never includes held-out IDs.
  heldout   10 fresh problems (held_001..held_010) in
            closed-loop/data/heldout_problems.json, never used for training.
            Run with --phase heldout and an explicit --model (base or
            helix-lora) to measure generalisation. Held-out traces are never
            read by 03_extract_pairs.py (it only reads phase == "build").
  heldout2  15 harder fresh problems (held2_001..held2_015) in
            closed-loop/data/heldout2_problems.json, never used for
            training. Round 2 discriminating held-out set (v1 saturated).

  Round tagging (--run-tag): Round 2 traces carry a run tag (e.g. "build2",
  "rebuild2", "heldout2") that becomes the filename prefix and is recorded
  in the trace JSON, so Round 2 runs never overwrite Round 1 files and the
  extractor can select one round at a time. Untagged runs keep the
  historical filenames. --skip-existing resumes an interrupted run by
  reusing complete live trace files already on disk.

  Sampling (--temperature, --n-samples): defaults temperature=0.0, n=1,
  which reproduces the Round 1 protocol exactly. With n>1 each cell runs
  n times; filenames gain a _s0/_s1/... suffix and traces record
  temperature, sample_index and seed. Sampling runs exist only to create
  sibling contrast for training; baseline comparisons use temp 0.0, n=1.

  Prompt guard: multi-turn transcripts are truncated (oldest middle turns
  dropped, system + original prompt + latest turns kept) before any API
  call whose estimated prompt would exceed the context budget, so a
  growing transcript can no longer overflow the server context window
  (the Round 1 held_006 HTTP 400). Truncations are counted in the trace
  ("prompt_truncations"); normal runs trigger zero truncations.

Output
------
  closed-loop/data/raw_traces/{phase}_{task_id}_{harness_id}.json

  Each file conforms to the schema consumed by 03_extract_pairs.py:
    phase, task_id, task_title, difficulty, prompt, harness_id,
    harness_category, model, provider, mode, steps, latency_sec,
    assistant_solution, passed, test_result, raw_helix_transcript,
    error, timestamp

  "mode" is "live" or "dry-run". Traces written before this field existed
  (the 40 BUILD traces committed 2026-10-28/29) have no mode; see
  closed-loop/PROVENANCE_AUDIT.md — 31 of those 40 are dry-run traces.

Usage
-----
  # Offline validation (no GPU needed):
  python closed-loop/scripts/02_run_helix_eval.py --phase build --mode dry-run --limit 3

  # Live evaluation against Modal vLLM:
  python closed-loop/scripts/02_run_helix_eval.py --phase build --mode live

  # REBUILD phase (uses LoRA adapter alias served by 01_modal_vllm.py):
  python closed-loop/scripts/02_run_helix_eval.py --phase rebuild --mode live

  # HELD-OUT evaluation (never trained on; explicit model required):
  python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout --model Qwen/Qwen2.5-Coder-7B-Instruct
  python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout --model helix-lora
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import re
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
CLOSED_LOOP_ROOT = SCRIPT_DIR.parent
RAW_TRACES_DIR = CLOSED_LOOP_ROOT / "data" / "raw_traces"
CONFIGS_DIR = CLOSED_LOOP_ROOT / "configs"

# ---------------------------------------------------------------------------
# Constants that must stay in sync with 01_modal_vllm.py
# ---------------------------------------------------------------------------
BASE_MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_ADAPTER_NAME = "helix-lora"          # alias registered in vLLM multi-LoRA
DEFAULT_PROVIDER = "openai-compatible"

# ---------------------------------------------------------------------------
# Sandbox execution constants
# ---------------------------------------------------------------------------
SANDBOX_TIMEOUT_SEC = 5         # max wall-clock seconds per test_cases run
CODE_EXTRACTION_PATTERNS = [
    re.compile(r"```python\s*\n(.*?)```", re.DOTALL | re.IGNORECASE),
    re.compile(r"```\s*\n(.*?)```", re.DOTALL),
]

# ---------------------------------------------------------------------------
# Prompt / context budget (Round 2 guard)
# ---------------------------------------------------------------------------
# Server context window is 8192 tokens (01_modal_vllm.py); each call
# requests up to 1024 output tokens. Keep estimated input tokens below
# 8192 - 1024 - 256 (safety margin) by truncating old middle turns.
MAX_INPUT_TOKENS_EST = 8192 - 1024 - 256
MAX_OUTPUT_TOKENS = 1024
# Rough token estimate: ~4 characters per token for code-heavy English
# text. Deliberately conservative: it over-truncates rather than
# under-truncates, and truncation is recorded in the trace.
_CHARS_PER_TOKEN_EST = 4.0
SAMPLING_SEED_BASE = 42000

# Maximum feedback-loop steps for advanced harnesses (Round 2 cap).
# Evidence from the 160 Round 1 traces: all 105 passing advanced cells
# finished within 3 steps, and every longer loop ended in an HTTP 400
# context error at the old 4096-token window — no Round 1 pass ever
# needed a 4th+ retry. The recipe configs still say 8/12/15, but with
# the window raised to 8192 + truncation, failing cells would otherwise
# burn 8–15 generations (~230–400 s) each without changing the outcome
# (observed on lcb_002 in the first Round 2 attempt: 8/12/15 steps, all
# FAIL). The cap of 4 (3 observed + 1 spare retry) preserves all
# observed passing behaviour, bounds retry cost inside the $6 Round 2
# budget, and applies uniformly to both models and all phases, so
# within-Round-2 comparisons stay fair. Minimal stays at 1 step.
MAX_ADVANCED_STEPS = 4

# =============================================================================
# 1. Built-in Benchmark Problems
# =============================================================================
# 10 algorithmic problems (Easy -> Medium), each with:
#   id, title, difficulty, prompt, test_cases (list of Python assert strings)
# The test_cases are evaluated in a subprocess sandbox after code extraction.

BENCHMARK_PROBLEMS: List[Dict[str, Any]] = [
    {
        "id": "lcb_001_two_sum",
        "title": "Two Sum with Indices",
        "difficulty": "easy",
        "prompt": (
            "Write a Python function `two_sum(nums: list[int], target: int) -> list[int]` "
            "that returns the indices of the two numbers in `nums` that add up to `target`. "
            "You may assume each input has exactly one solution and you may not use the same "
            "element twice. Return indices in ascending order."
        ),
        "test_cases": [
            "assert two_sum([2, 7, 11, 15], 9) == [0, 1]",
            "assert two_sum([3, 2, 4], 6) == [1, 2]",
            "assert two_sum([3, 3], 6) == [0, 1]",
        ],
    },
    {
        "id": "lcb_002_valid_parentheses",
        "title": "Valid Parentheses String with Wildcard",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `is_valid(s: str) -> bool` that checks if brackets are valid. "
            "The string can contain `()`, `[]`, `{}`, AND the wildcard character `'*'` which can "
            "be treated as a single `'('`, `')'`, or an empty string `\"\"`."
        ),
        "test_cases": [
            "assert is_valid('()') == True",
            "assert is_valid('(*)') == True",
            "assert is_valid('(*))') == True",
            "assert is_valid(')') == False",
            "assert is_valid('(*(') == False",
            "assert is_valid('(((******))') == True",
            "assert is_valid('') == True",
        ],
    },
    {
        "id": "lcb_003_lru_cache",
        "title": "LRU Cache Implementation with Eviction Return",
        "difficulty": "medium",
        "prompt": (
            "Implement an LRU (Least Recently Used) cache class `LRUCache(capacity: int)` in Python "
            "with O(1) average-time `get(key)` and `put(key, value)` operations. "
            "`get` returns -1 if key does not exist. `put` inserts or updates the key; if inserting a new key "
            "causes capacity to be exceeded, evict the least recently used item AND return the evicted key. "
            "If no eviction occurred, `put` must return None."
        ),
        "test_cases": [
            "cache = LRUCache(2)",
            "assert cache.put(1, 1) is None",
            "assert cache.put(2, 2) is None",
            "assert cache.get(1) == 1",
            "assert cache.put(3, 3) == 2",
            "assert cache.get(2) == -1",
            "assert cache.put(1, 10) is None",
            "assert cache.get(1) == 10",
            "assert cache.put(4, 4) == 3",
            "assert cache.get(3) == -1",
            "assert cache.get(4) == 4",
        ],
    },
    {
        "id": "lcb_004_reverse_linked_list",
        "title": "Reverse a Linked List",
        "difficulty": "easy",
        "prompt": (
            "Define a `ListNode` class with `val` and `next` attributes. "
            "Write a Python function `reverse_list(head: ListNode | None) -> ListNode | None` "
            "that reverses a singly linked list in-place and returns the new head."
        ),
        "test_cases": [
            "class ListNode:",
            "    def __init__(self, val=0, next=None): self.val=val; self.next=next",
            "def to_list(node):",
            "    r=[]",
            "    while node: r.append(node.val); node=node.next",
            "    return r",
            "def make_list(vals):",
            "    if not vals: return None",
            "    h=ListNode(vals[0])",
            "    c=h",
            "    for v in vals[1:]: c.next=ListNode(v); c=c.next",
            "    return h",
            "assert to_list(reverse_list(make_list([1,2,3,4,5]))) == [5,4,3,2,1]",
            "assert to_list(reverse_list(make_list([1,2]))) == [2,1]",
            "assert reverse_list(None) is None",
        ],
    },
    {
        "id": "lcb_005_binary_search",
        "title": "Binary Search",
        "difficulty": "easy",
        "prompt": (
            "Write a Python function `search(nums: list[int], target: int) -> int` that "
            "performs binary search on a sorted list `nums` and returns the index of `target`, "
            "or -1 if it is not found. Must run in O(log n) time."
        ),
        "test_cases": [
            "assert search([-1, 0, 3, 5, 9, 12], 9) == 4",
            "assert search([-1, 0, 3, 5, 9, 12], 2) == -1",
            "assert search([5], 5) == 0",
            "assert search([5], 3) == -1",
            "assert search([], 1) == -1",
        ],
    },
    {
        "id": "lcb_006_max_subarray",
        "title": "Maximum Subarray Sum and Slice",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `max_sub_array(nums: list[int]) -> tuple[int, list[int]]` that finds "
            "the contiguous subarray with the largest sum and returns a tuple `(max_sum, subarray)`. "
            "If `nums` is empty, return `(0, [])`."
        ),
        "test_cases": [
            "assert max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == (6, [4, -1, 2, 1])",
            "assert max_sub_array([1]) == (1, [1])",
            "assert max_sub_array([5, 4, -1, 7, 8]) == (23, [5, 4, -1, 7, 8])",
            "assert max_sub_array([-1, -2, -3]) == (-1, [-1])",
            "assert max_sub_array([]) == (0, [])",
        ],
    },
    {
        "id": "lcb_007_climbing_stairs",
        "title": "Climbing Stairs (DP)",
        "difficulty": "easy",
        "prompt": (
            "Write a Python function `climb_stairs(n: int) -> int` that returns the number "
            "of distinct ways to climb `n` stairs if you can take 1 or 2 steps at a time."
        ),
        "test_cases": [
            "assert climb_stairs(1) == 1",
            "assert climb_stairs(2) == 2",
            "assert climb_stairs(3) == 3",
            "assert climb_stairs(5) == 8",
            "assert climb_stairs(10) == 89",
        ],
    },
    {
        "id": "lcb_008_merge_intervals",
        "title": "Merge Overlapping Intervals with Count",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `merge(intervals: list[list[int]]) -> list[dict]` that "
            "merges all overlapping or touching intervals (e.g. `[1, 4]` and `[4, 5]` merge into `[1, 5]`). "
            "Return each merged interval as a dictionary `{'start': int, 'end': int, 'count': int}` where `'count'` "
            "is the count of original intervals that were merged into it. The result list must be sorted by `'start'`."
        ),
        "test_cases": [
            "assert merge([[1,3],[2,6],[8,10],[15,18]]) == [{'start': 1, 'end': 6, 'count': 2}, {'start': 8, 'end': 10, 'count': 1}, {'start': 15, 'end': 18, 'count': 1}]",
            "assert merge([[2,6],[1,3],[15,18],[8,10]]) == [{'start': 1, 'end': 6, 'count': 2}, {'start': 8, 'end': 10, 'count': 1}, {'start': 15, 'end': 18, 'count': 1}]",
            "assert merge([[1,4],[4,5]]) == [{'start': 1, 'end': 5, 'count': 2}]",
            "assert merge([]) == []",
        ],
    },
    {
        "id": "lcb_009_word_break",
        "title": "Word Break Sentences (DP/Backtracking)",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `word_break(s: str, word_dict: list[str]) -> list[str]` that "
            "segments `s` into all possible valid space-separated sentences using words from `word_dict`. "
            "Return the list of sentences sorted in lexicographical order. If no valid sentence can be formed, return `[]`."
        ),
        "test_cases": [
            "assert word_break('catsanddog', ['cat', 'cats', 'and', 'sand', 'dog']) == ['cat sand dog', 'cats and dog']",
            "assert word_break('pineapplepenapple', ['apple', 'pen', 'applepen', 'pine', 'pineapple']) == ['pine apple pen apple', 'pine applepen apple', 'pineapple pen apple']",
            "assert word_break('catsandog', ['cats', 'dog', 'sand', 'and', 'cat']) == []",
            "assert word_break('', ['a']) == []",
        ],
    },
    {
        "id": "lcb_010_number_of_islands",
        "title": "Number of Islands (BFS/DFS)",
        "difficulty": "medium",
        "prompt": (
            "Write a Python function `num_islands(grid: list[list[str]]) -> int` that "
            "counts the number of islands in a 2D binary grid. An island is a group of "
            "adjacent '1's (land) surrounded by '0's (water). Connections are 4-directional."
        ),
        "test_cases": [
            "g1=[['1','1','1','1','0'],['1','1','0','1','0'],['1','1','0','0','0'],['0','0','0','0','0']]",
            "assert num_islands(g1) == 1",
            "g2=[['1','1','0','0','0'],['1','1','0','0','0'],['0','0','1','0','0'],['0','0','0','1','1']]",
            "assert num_islands(g2) == 3",
            "assert num_islands([]) == 0",
            "assert num_islands([['0','0'],['0','0']]) == 0",
        ],
    },
]

# =============================================================================
# 2. Harness System Prompt Templates
# =============================================================================
# Each harness uses a different system prompt depth — mirroring the scaffolding
# differences in the actual HELIX recipe configs.

# =============================================================================
# 1b. Held-Out Problem Set (never used for training)
# =============================================================================
# Fresh problems live in closed-loop/data/heldout_problems.json so the eval
# set can grow without editing this runner. IDs must not collide with
# BENCHMARK_PROBLEMS: any overlap would silently re-test training tasks.

HELDOUT_PROBLEMS_PATH = CLOSED_LOOP_ROOT / "data" / "heldout_problems.json"
TRAIN_EXTRA_PROBLEMS_PATH = CLOSED_LOOP_ROOT / "data" / "train_extra_problems.json"
HELDOUT2_PROBLEMS_PATH = CLOSED_LOOP_ROOT / "data" / "heldout2_problems.json"


def _load_problems_json(path: Path, label: str) -> List[Dict[str, Any]]:
    """Load and validate a JSON problem set (list of problem dicts)."""
    if not path.exists():
        raise SystemExit(f"{label} problem file not found: {path}")
    with open(path, encoding="utf-8") as f:
        problems = json.load(f)
    if not isinstance(problems, list) or not problems:
        raise SystemExit(f"{label} problem file must contain a non-empty JSON list")
    seen = set()
    for problem in problems:
        for field in ("id", "title", "difficulty", "prompt", "test_cases"):
            if field not in problem:
                raise SystemExit(f"{label} problem missing field {field!r}: {problem}")
        if not isinstance(problem["test_cases"], list) or not problem["test_cases"]:
            raise SystemExit(f"{label} problem {problem['id']} has no test cases")
        if problem["id"] in seen:
            raise SystemExit(f"Duplicate {label} problem id: {problem['id']!r}")
        seen.add(problem["id"])
    return problems


def _check_disjoint(*sets: Tuple[str, List[Dict[str, Any]]]) -> None:
    """Fail if any problem id appears in more than one named set."""
    seen: Dict[str, str] = {}
    for label, problems in sets:
        for problem in problems:
            owner = seen.get(problem["id"])
            if owner is not None:
                raise SystemExit(
                    f"Problem id {problem['id']!r} appears in both {owner} and {label}; "
                    "training and held-out sets must be disjoint."
                )
            seen[problem["id"]] = label


def _load_heldout_problems() -> List[Dict[str, Any]]:
    """Load and validate the held-out problem set from JSON."""
    problems = _load_problems_json(HELDOUT_PROBLEMS_PATH, "heldout")
    _check_disjoint(("train", BENCHMARK_PROBLEMS), ("heldout", problems))
    return problems


def _load_train_extra_problems() -> List[Dict[str, Any]]:
    """Load the Round 2 extra training problems (lcb_011..lcb_020)."""
    problems = _load_problems_json(TRAIN_EXTRA_PROBLEMS_PATH, "train-extra")
    _check_disjoint(("train", BENCHMARK_PROBLEMS), ("train-extra", problems))
    return problems


def _load_heldout2_problems() -> List[Dict[str, Any]]:
    """Load the Round 2 harder held-out set (held2_001..held2_015)."""
    problems = _load_problems_json(HELDOUT2_PROBLEMS_PATH, "heldout2")
    sets: List[Tuple[str, List[Dict[str, Any]]]] = [
        ("train", BENCHMARK_PROBLEMS),
        ("heldout2", problems),
    ]
    if TRAIN_EXTRA_PROBLEMS_PATH.exists():
        sets.append(("train-extra", _load_problems_json(TRAIN_EXTRA_PROBLEMS_PATH, "train-extra")))
    if HELDOUT_PROBLEMS_PATH.exists():
        sets.append(("heldout", _load_problems_json(HELDOUT_PROBLEMS_PATH, "heldout")))
    _check_disjoint(*sets)
    return problems


def get_problems(problem_set: str) -> List[Dict[str, Any]]:
    """Return the problem list for a --problem-set value."""
    if problem_set == "train":
        return list(BENCHMARK_PROBLEMS)
    if problem_set == "train20":
        return list(BENCHMARK_PROBLEMS) + _load_train_extra_problems()
    if problem_set == "heldout":
        return _load_heldout_problems()
    if problem_set == "heldout2":
        return _load_heldout2_problems()
    raise SystemExit(f"Unknown problem set: {problem_set!r}")


def _build_system_prompt(harness_id: str) -> str:
    """Return the system prompt that characterises each harness's scaffolding level."""
    if harness_id == "minimal":
        # Bare minimum — reflects allow-echo-only / minimal-transcript recipe
        return "You are a helpful coding assistant. Provide a complete Python solution."

    elif harness_id == "pi-mono":
        # Structured but single-agent — mirrors pi-active-leaf-context
        return textwrap.dedent("""\
            You are an expert Python software engineer.
            Think step-by-step before writing code.
            Provide a complete, correct, and efficient Python implementation.
            Wrap your final solution in a ```python ... ``` code block.""")

    elif harness_id == "hermes-agent":
        # Session-oriented, stable context — mirrors hermes-stable-context-prompt-builder
        return textwrap.dedent("""\
            <|im_start|>system
            You are an expert autonomous software engineer with deep knowledge of algorithms,
            data structures, and Python best practices.
            - Reason through the problem carefully before writing code.
            - Write concise, optimised, and well-commented Python code.
            - Validate your solution mentally against edge cases.
            - Return ONLY the final implementation wrapped in ```python ... ```.
            <|im_end|>""")

    elif harness_id == "opencode":
        # Feature-rich, detailed prompt — mirrors opencode-prompt-context
        return textwrap.dedent("""\
            You are OpenCode, an elite autonomous coding agent specialising in competitive
            programming and production-grade Python.

            Workflow:
            1. ANALYSE the problem statement and constraints.
            2. PLAN the algorithm (time/space complexity).
            3. IMPLEMENT a clean, optimal Python solution.
            4. VERIFY mentally by tracing through the provided examples.

            Rules:
            - Return ONLY the final Python implementation.
            - Use type hints.
            - Do NOT include test code, print statements, or explanatory prose outside comments.
            - Wrap code in ```python ... ```.""")

    return "You are a helpful coding assistant."


# =============================================================================
# 3. Code Extraction & Sandbox Verification
# =============================================================================

def extract_python_code(response_text: str) -> Optional[str]:
    """
    Extract a Python code block from an LLM response.
    Tries fenced code blocks first, falls back to raw indented blocks.
    """
    for pattern in CODE_EXTRACTION_PATTERNS:
        match = pattern.search(response_text)
        if match:
            return match.group(1).strip()

    # Heuristic fallback: look for lines starting with 'def ' or 'class '
    lines = response_text.splitlines()
    code_lines: List[str] = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if not in_code and (stripped.startswith("def ") or stripped.startswith("class ")):
            in_code = True
        if in_code:
            code_lines.append(line)
    return "\n".join(code_lines).strip() if code_lines else None


def run_test_cases(
    code: str, test_cases: List[str], timeout: int = SANDBOX_TIMEOUT_SEC
) -> Tuple[bool, Optional[str]]:
    """
    Execute `code` + `test_cases` in a child Python process with a hard timeout.

    Returns:
        (passed: bool, error_message: str | None)
    """
    # Build a self-contained script: inject code then assertions
    test_lines = "\n".join(test_cases)
    script = f"{code}\n\n# --- auto-generated test harness ---\n{test_lines}\n"

    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, None
        err = (result.stderr or result.stdout or "").strip()
        return False, err[:500]  # cap error length for JSON cleanliness
    except subprocess.TimeoutExpired:
        return False, f"TimeoutError: execution exceeded {timeout}s"
    except Exception as exc:
        return False, f"SubprocessError: {exc}"


def is_clean_artifact(code: str) -> bool:
    """
    Heuristic: returns True when the extracted code has no obvious artefacts
    (stray markdown, debug print-alls, TODO placeholders, empty bodies).
    """
    if not code or len(code.strip()) < 20:
        return False
    dirty_patterns = [
        r"^```",          # leftover fences
        r"TODO|FIXME|pass  # placeholder",
        r"print\(.*debug",
    ]
    for pat in dirty_patterns:
        if re.search(pat, code, re.IGNORECASE | re.MULTILINE):
            return False
    try:
        ast.parse(code)   # syntax check
        return True
    except SyntaxError:
        return False


# =============================================================================
# 4. Dry-Run Mock Solution Generator
# =============================================================================
# Reference solutions for each benchmark problem used in --mode dry-run.
# These are correct implementations so the pipeline produces realistic
# SFT / DPO pairs when run offline.

_DRY_RUN_SOLUTIONS: Dict[str, Dict[str, str]] = {
    # --- lcb_001 ---
    "lcb_001_two_sum": {
        "opencode": textwrap.dedent("""\
            def two_sum(nums: list[int], target: int) -> list[int]:
                seen: dict[int, int] = {}
                for i, num in enumerate(nums):
                    complement = target - num
                    if complement in seen:
                        return sorted([seen[complement], i])
                    seen[num] = i
                return []"""),
        "hermes-agent": textwrap.dedent("""\
            def two_sum(nums: list[int], target: int) -> list[int]:
                lookup = {}
                for i, n in enumerate(nums):
                    if target - n in lookup:
                        return [lookup[target - n], i]
                    lookup[n] = i
                return []"""),
        "pi-mono": textwrap.dedent("""\
            def two_sum(nums, target):
                seen = {}
                for i, v in enumerate(nums):
                    if target - v in seen:
                        return [seen[target - v], i]
                    seen[v] = i"""),
        "minimal": textwrap.dedent("""\
            def two_sum(nums, target):
                for i in range(len(nums))
                    for j in range(i+1, len(nums)):
                        if nums[i]+nums[j]==target: return [i,j]"""),  # syntax error on purpose
    },
    # --- lcb_002 ---
    "lcb_002_valid_parentheses": {
        "opencode": textwrap.dedent("""\
            def is_valid(s: str) -> bool:
                cmin = cmax = 0
                for c in s:
                    if c in '([{':
                        cmin += 1; cmax += 1
                    elif c in ')]}':
                        cmin = max(cmin - 1, 0); cmax -= 1
                    elif c == '*':
                        cmin = max(cmin - 1, 0); cmax += 1
                    if cmax < 0: return False
                return cmin == 0"""),
        "hermes-agent": textwrap.dedent("""\
            def is_valid(s: str) -> bool:
                cmin = cmax = 0
                for c in s:
                    if c in '([{': cmin += 1; cmax += 1
                    elif c in ')]}': cmin = max(cmin - 1, 0); cmax -= 1
                    elif c == '*': cmin = max(cmin - 1, 0); cmax += 1
                    if cmax < 0: return False
                return cmin == 0"""),
        "pi-mono": textwrap.dedent("""\
            def is_valid(s):
                cmin = cmax = 0
                for c in s:
                    if c in '([{': cmin += 1; cmax += 1
                    elif c in ')]}': cmin = max(cmin - 1, 0); cmax -= 1
                    elif c == '*': cmin = max(cmin - 1, 0); cmax += 1
                    if cmax < 0: return False
                return cmin == 0"""),
        "minimal": "def is_valid(s):\n    return '()' in s or '[]' in s",  # fails wildcard
    },
    # --- lcb_003 ---
    "lcb_003_lru_cache": {
        "opencode": textwrap.dedent("""\
            class LRUCache:
                def __init__(self, capacity: int):
                    from collections import OrderedDict
                    self.cap = capacity
                    self.cache = OrderedDict()
                def get(self, key: int) -> int:
                    if key not in self.cache: return -1
                    self.cache.move_to_end(key)
                    return self.cache[key]
                def put(self, key: int, value: int):
                    if key in self.cache:
                        self.cache.move_to_end(key)
                        self.cache[key] = value
                        return None
                    evicted = None
                    if len(self.cache) >= self.cap:
                        evicted, _ = self.cache.popitem(last=False)
                    self.cache[key] = value
                    return evicted"""),
        "hermes-agent": textwrap.dedent("""\
            class LRUCache:
                def __init__(self, capacity):
                    from collections import OrderedDict
                    self.cap = capacity
                    self.cache = OrderedDict()
                def get(self, key):
                    if key not in self.cache: return -1
                    self.cache.move_to_end(key)
                    return self.cache[key]
                def put(self, key, value):
                    if key in self.cache:
                        self.cache.move_to_end(key); self.cache[key] = value
                        return None
                    evicted = None
                    if len(self.cache) >= self.cap:
                        evicted, _ = self.cache.popitem(last=False)
                    self.cache[key] = value
                    return evicted"""),
        "pi-mono": textwrap.dedent("""\
            class LRUCache:
                def __init__(self, capacity):
                    from collections import OrderedDict
                    self.cap = capacity
                    self.cache = OrderedDict()
                def get(self, key):
                    if key not in self.cache: return -1
                    self.cache.move_to_end(key)
                    return self.cache[key]
                def put(self, key, value):
                    if key in self.cache:
                        self.cache.move_to_end(key); self.cache[key] = value
                        return None
                    ev = None
                    if len(self.cache) >= self.cap:
                        ev, _ = self.cache.popitem(last=False)
                    self.cache[key] = value
                    return ev"""),
        "minimal": textwrap.dedent("""\
            class LRUCache:
                def __init__(self, capacity):
                    self.d = {}
                def get(self, key): return self.d.get(key, -1)
                def put(self, key, value): self.d[key] = value; return None"""),  # fails eviction return
    },
    # --- lcb_004 ---
    "lcb_004_reverse_linked_list": {
        "opencode": textwrap.dedent("""\
            class ListNode:
                def __init__(self, val=0, next=None):
                    self.val = val
                    self.next = next
            def reverse_list(head):
                prev = None
                curr = head
                while curr:
                    nxt = curr.next
                    curr.next = prev
                    prev = curr
                    curr = nxt
                return prev"""),
        "hermes-agent": textwrap.dedent("""\
            class ListNode:
                def __init__(self, val=0, next=None):
                    self.val = val; self.next = next
            def reverse_list(head):
                prev, cur = None, head
                while cur:
                    cur.next, prev, cur = prev, cur, cur.next
                return prev"""),
        "pi-mono": textwrap.dedent("""\
            class ListNode:
                def __init__(self, val=0, next=None):
                    self.val = val; self.next = next
            def reverse_list(head):
                p, c = None, head
                while c:
                    n = c.next; c.next = p; p = c; c = n
                return p"""),
        "minimal": textwrap.dedent("""\
            class ListNode:
                def __init__(self, val=0, next=None):
                    self.val = val; self.next = next
            def reverse_list(head):
                return head  # not implemented"""),
    },
    # --- lcb_005 ---
    "lcb_005_binary_search": {
        "opencode": textwrap.dedent("""\
            def search(nums: list[int], target: int) -> int:
                lo, hi = 0, len(nums) - 1
                while lo <= hi:
                    mid = (lo + hi) // 2
                    if nums[mid] == target:
                        return mid
                    elif nums[mid] < target:
                        lo = mid + 1
                    else:
                        hi = mid - 1
                return -1"""),
        "hermes-agent": textwrap.dedent("""\
            def search(nums, target):
                l, r = 0, len(nums)-1
                while l <= r:
                    m = (l+r)//2
                    if nums[m] == target: return m
                    elif nums[m] < target: l = m+1
                    else: r = m-1
                return -1"""),
        "pi-mono": textwrap.dedent("""\
            def search(nums, target):
                lo, hi = 0, len(nums)-1
                while lo <= hi:
                    mid = lo + (hi-lo)//2
                    if nums[mid] == target: return mid
                    if nums[mid] < target: lo = mid+1
                    else: hi = mid-1
                return -1"""),
        "minimal": textwrap.dedent("""\
            def search(nums, target):
                try: return nums.index(target)
                except: return -1"""),  # O(n) — technically correct but wrong complexity
    },
    # --- lcb_006 ---
    "lcb_006_max_subarray": {
        "opencode": textwrap.dedent("""\
            def max_sub_array(nums: list[int]) -> tuple[int, list[int]]:
                if not nums: return (0, [])
                best_sum = cur_sum = nums[0]
                start = best_start = best_end = 0
                for i in range(1, len(nums)):
                    if cur_sum < 0:
                        cur_sum = nums[i]
                        start = i
                    else:
                        cur_sum += nums[i]
                    if cur_sum > best_sum:
                        best_sum = cur_sum
                        best_start = start
                        best_end = i
                return (best_sum, nums[best_start:best_end+1])"""),
        "hermes-agent": textwrap.dedent("""\
            def max_sub_array(nums):
                if not nums: return (0, [])
                best = cur = nums[0]
                s = bs = be = 0
                for i in range(1, len(nums)):
                    if cur < 0: cur, s = nums[i], i
                    else: cur += nums[i]
                    if cur > best: best, bs, be = cur, s, i
                return (best, nums[bs:be+1])"""),
        "pi-mono": textwrap.dedent("""\
            def max_sub_array(nums):
                if not nums: return (0, [])
                best = cur = nums[0]
                s = bs = be = 0
                for i in range(1, len(nums)):
                    if cur < 0: cur, s = nums[i], i
                    else: cur += nums[i]
                    if cur > best: best, bs, be = cur, s, i
                return (best, nums[bs:be+1])"""),
        "minimal": "def max_sub_array(nums):\n    return max(nums) if nums else 0",  # returns int not tuple
    },
    # --- lcb_007 ---
    "lcb_007_climbing_stairs": {
        "opencode": textwrap.dedent("""\
            def climb_stairs(n: int) -> int:
                if n <= 2:
                    return n
                a, b = 1, 2
                for _ in range(3, n + 1):
                    a, b = b, a + b
                return b"""),
        "hermes-agent": textwrap.dedent("""\
            def climb_stairs(n):
                a, b = 1, 1
                for _ in range(n-1):
                    a, b = b, a+b
                return b"""),
        "pi-mono": textwrap.dedent("""\
            def climb_stairs(n):
                dp = [0]*(n+1)
                dp[0] = dp[1] = 1
                for i in range(2, n+1): dp[i] = dp[i-1]+dp[i-2]
                return dp[n]"""),
        "minimal": textwrap.dedent("""\
            def climb_stairs(n):
                from functools import lru_cache
                @lru_cache
                def f(k): return 1 if k<=1 else f(k-1)+f(k-2)
                return f(n)"""),
    },
    # --- lcb_008 ---
    "lcb_008_merge_intervals": {
        "opencode": textwrap.dedent("""\
            def merge(intervals: list[list[int]]) -> list[dict]:
                if not intervals: return []
                intervals = sorted(intervals, key=lambda x: x[0])
                res = [{'start': intervals[0][0], 'end': intervals[0][1], 'count': 1}]
                for s, e in intervals[1:]:
                    if s <= res[-1]['end']:
                        res[-1]['end'] = max(res[-1]['end'], e)
                        res[-1]['count'] += 1
                    else:
                        res.append({'start': s, 'end': e, 'count': 1})
                return res"""),
        "hermes-agent": textwrap.dedent("""\
            def merge(intervals):
                if not intervals: return []
                ivs = sorted(intervals, key=lambda x: x[0])
                out = [{'start': ivs[0][0], 'end': ivs[0][1], 'count': 1}]
                for s, e in ivs[1:]:
                    if s <= out[-1]['end']:
                        out[-1]['end'] = max(out[-1]['end'], e)
                        out[-1]['count'] += 1
                    else:
                        out.append({'start': s, 'end': e, 'count': 1})
                return out"""),
        "pi-mono": textwrap.dedent("""\
            def merge(intervals):
                if not intervals: return []
                ivs = sorted(intervals, key=lambda x: x[0])
                out = [{'start': ivs[0][0], 'end': ivs[0][1], 'count': 1}]
                for s, e in ivs[1:]:
                    if s <= out[-1]['end']:
                        out[-1]['end'] = max(out[-1]['end'], e); out[-1]['count'] += 1
                    else:
                        out.append({'start': s, 'end': e, 'count': 1})
                return out"""),
        "minimal": textwrap.dedent("""\
            def merge(intervals):
                return sorted(intervals)"""),  # fails schema (list of lists, not dicts)
    },
    # --- lcb_009 ---
    "lcb_009_word_break": {
        "opencode": textwrap.dedent("""\
            def word_break(s: str, word_dict: list[str]) -> list[str]:
                if not s: return []
                ws = set(word_dict)
                memo = {}
                def dfs(rem):
                    if not rem: return [""]
                    if rem in memo: return memo[rem]
                    res = []
                    for w in ws:
                        if rem.startswith(w):
                            for t in dfs(rem[len(w):]):
                                res.append(w + (" " + t if t else ""))
                    memo[rem] = res
                    return res
                return sorted(dfs(s))"""),
        "hermes-agent": textwrap.dedent("""\
            def word_break(s, word_dict):
                if not s: return []
                ws, memo = set(word_dict), {}
                def dfs(rem):
                    if not rem: return [""]
                    if rem in memo: return memo[rem]
                    res = []
                    for w in ws:
                        if rem.startswith(w):
                            for t in dfs(rem[len(w):]):
                                res.append(w + (" " + t if t else ""))
                    memo[rem] = res
                    return res
                return sorted(dfs(s))"""),
        "pi-mono": textwrap.dedent("""\
            def word_break(s, word_dict):
                if not s: return []
                ws, memo = set(word_dict), {}
                def dfs(rem):
                    if not rem: return [""]
                    if rem in memo: return memo[rem]
                    res = []
                    for w in ws:
                        if rem.startswith(w):
                            for t in dfs(rem[len(w):]):
                                res.append(w + (" " + t if t else ""))
                    memo[rem] = res
                    return res
                return sorted(dfs(s))"""),
        "minimal": "def word_break(s, word_dict):\n    return any(w in s for w in word_dict)",  # returns bool
    },
    # --- lcb_010 ---
    "lcb_010_number_of_islands": {
        "opencode": textwrap.dedent("""\
            def num_islands(grid: list[list[str]]) -> int:
                if not grid:
                    return 0
                rows, cols = len(grid), len(grid[0])
                count = 0
                def dfs(r: int, c: int) -> None:
                    if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':
                        return
                    grid[r][c] = '0'
                    dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
                for r in range(rows):
                    for c in range(cols):
                        if grid[r][c] == '1':
                            dfs(r, c); count += 1
                return count"""),
        "hermes-agent": textwrap.dedent("""\
            def num_islands(grid):
                if not grid: return 0
                R, C = len(grid), len(grid[0])
                def sink(r, c):
                    if not (0<=r<R and 0<=c<C) or grid[r][c]!='1': return
                    grid[r][c]='0'
                    for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]: sink(r+dr,c+dc)
                cnt = 0
                for r in range(R):
                    for c in range(C):
                        if grid[r][c]=='1': sink(r,c); cnt+=1
                return cnt"""),
        "pi-mono": textwrap.dedent("""\
            def num_islands(grid):
                from collections import deque
                if not grid: return 0
                R, C, count = len(grid), len(grid[0]), 0
                for r in range(R):
                    for c in range(C):
                        if grid[r][c]=='1':
                            count+=1; q=deque([(r,c)]); grid[r][c]='0'
                            while q:
                                row,col=q.popleft()
                                for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                                    nr,nc=row+dr,col+dc
                                    if 0<=nr<R and 0<=nc<C and grid[nr][nc]=='1':
                                        grid[nr][nc]='0'; q.append((nr,nc))
                return count"""),
        "minimal": textwrap.dedent("""\
            def num_islands(grid):
                return sum(grid[r][c]=='1' for r in range(len(grid)) for c in range(len(grid[0])))"""),
    },
}


def _dry_run_solution(harness_id: str, problem_id: str) -> Tuple[str, int, float, str]:
    """
    Return (raw_response, steps, latency_sec, error) for dry-run mode.
    Solutions are pre-defined to produce realistic SFT/DPO signal.
    Steps and latency are calibrated to harness complexity.
    """
    step_map = {"opencode": 1, "hermes-agent": 2, "pi-mono": 3, "minimal": 5}
    latency_map = {"opencode": 1.2, "hermes-agent": 2.1, "pi-mono": 3.4, "minimal": 5.8}

    code = _DRY_RUN_SOLUTIONS.get(problem_id, {}).get(
        harness_id,
        f"def placeholder():\n    pass  # TODO: {problem_id}",
    )
    raw_response = f"```python\n{code}\n```"
    return (
        raw_response,
        step_map.get(harness_id, 3),
        latency_map.get(harness_id, 3.0),
        "",
    )


# =============================================================================
# 5. Live Mode: Pre-flight Health Check & OpenAI-Compatible Client Caller
# =============================================================================

def wait_for_server_ready(base_url: str, timeout_sec: int = 180, poll_interval_sec: int = 5) -> bool:
    """
    Pre-flight health check: polls GET {server_root}/health until HTTP 200 or timeout.
    Enforces fail-fast behavior before queuing expensive evaluation runs on Modal vLLM.
    """
    import urllib.request
    import urllib.error

    base_url_clean = base_url.rstrip("/")
    if base_url_clean.endswith("/v1"):
        server_root = base_url_clean[:-3]
    else:
        server_root = base_url_clean
    health_url = f"{server_root}/health"

    print(f"\n[Health Check] Polling server health at: {health_url}")
    start_time = time.monotonic()
    deadline = start_time + timeout_sec

    while time.monotonic() < deadline:
        elapsed = int(time.monotonic() - start_time)
        try:
            req = urllib.request.Request(
                health_url,
                headers={"User-Agent": "HELIX-Preflight/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    try:
                        data = json.loads(resp.read().decode("utf-8"))
                        lora_info = f"lora_enabled={data.get('lora_enabled')}, adapter={data.get('adapter')}"
                    except Exception:
                        lora_info = "standard vLLM"
                    print(f"[Health Check] Server is healthy and ready! [{lora_info}] ({elapsed}s elapsed)\n")
                    return True
                print(f"[Health Check] Received status {resp.status}... ({elapsed}s elapsed)")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"[Health Check] Waiting for Modal vLLM cold-start... ({elapsed}s elapsed) [{e}]")

        time.sleep(poll_interval_sec)

    print(f"\n[ERROR] Health check timed out after {timeout_sec}s. Modal vLLM server is not healthy.")
    return False


def _estimate_input_tokens(messages: List[Dict[str, str]]) -> int:
    """Conservative token estimate for a chat message list (~4 chars/token)."""
    chars = sum(len(m.get("content", "")) for m in messages)
    return math.ceil(chars / _CHARS_PER_TOKEN_EST)


def _truncate_messages(
    messages: List[Dict[str, str]],
    max_input_tokens: int = MAX_INPUT_TOKENS_EST,
) -> Tuple[List[Dict[str, str]], int]:
    """Drop oldest middle turns until the estimated prompt fits the budget.

    Always keeps the system prompt, the original user prompt, and the two
    most recent messages. Returns (kept_messages, dropped_turn_pairs).
    A normal run never exceeds the budget and gets 0 truncations.
    """
    kept = list(messages)
    dropped = 0
    while len(kept) > 4 and _estimate_input_tokens(kept) > max_input_tokens:
        # Drop the oldest assistant reply + the following user feedback
        # (indices 2 and 3), preserving system + original prompt + tail.
        del kept[2:4]
        dropped += 1
    return kept, dropped


def _live_solution(
    harness_id: str,
    problem: Dict[str, Any],
    base_url: str,
    model: str,
    api_key: str,
    temperature: float = 0.0,
    seed: int | None = None,
) -> Tuple[str, int, float, List[Dict[str, Any]], str, int]:
    """
    Call the OpenAI-compatible vLLM endpoint with the harness-appropriate
    system prompt and return (raw_response, steps, latency_sec, transcript,
    error, prompt_truncations).
    """
    try:
        from openai import OpenAI  # type: ignore[import-untyped]
    except ImportError:
        return "", 0, 0.0, [], "ImportError: pip install openai", 0

    # Enforce 90-second timeout on network requests
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=90.0)
    system_prompt = _build_system_prompt(harness_id)
    # Minimal has zero scaffolding, no execution loop (pure 1-shot)
    if harness_id == "minimal":
        max_steps = 1
    else:
        harness_cfg = _load_harness_config(harness_id)
        max_steps = (harness_cfg or {}).get("max_steps", 8)
        # Round 2 cap: see MAX_ADVANCED_STEPS. The config values (8/12/15)
        # describe the recipes; the effective loop is capped so a failing
        # cell cannot burn unbounded GPU retrying a solution that the
        # Round 1 evidence says will not pass on later retries.
        max_steps = min(max_steps, MAX_ADVANCED_STEPS)

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": problem["prompt"]},
    ]
    transcript: List[Dict[str, Any]] = []
    step = 0
    t0 = time.monotonic()
    prompt_truncations = 0

    # Agentic loop: runs up to max_steps with execution feedback for advanced harnesses
    while step < max_steps:
        step += 1
        # Context guard: never send a prompt estimated to overflow the
        # server window. Truncation drops old middle turns only; the
        # transcript still records every assistant reply received.
        send_messages, dropped = _truncate_messages(messages)
        prompt_truncations += dropped
        if dropped:
            messages = send_messages
        try:
            create_kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "timeout": 90.0,
            }
            if seed is not None:
                create_kwargs["seed"] = seed
            response = client.chat.completions.create(**create_kwargs)
        except Exception as exc:
            return "", step, time.monotonic() - t0, transcript, str(exc), prompt_truncations

        reply = response.choices[0].message.content or ""
        transcript.append({
            "step": step,
            "role": "assistant",
            "content": reply,
            "finish_reason": response.choices[0].finish_reason,
        })
        messages.append({"role": "assistant", "content": reply})

        # Check for extracted Python code
        code = extract_python_code(reply)
        if code:
            if harness_id == "minimal":
                # Minimal harness has no execution tool/feedback (1-shot only)
                break

            # Advanced harness: execute in sandbox against test cases
            passed, test_err = run_test_cases(code, problem["test_cases"])
            if passed or step >= max_steps:
                break

            # Multi-turn error feedback for iterative self-correction
            messages.append({
                "role": "user",
                "content": (
                    f"Test execution failed with error:\n```\n{test_err}\n```\n"
                    "Please analyze this failure, fix the issue, and provide a corrected implementation in ```python ... ```."
                ),
            })
            continue

        # If no code block found, prompt for code
        messages.append({
            "role": "user",
            "content": "Please provide your Python implementation wrapped in ```python ... ```.",
        })

    raw_response = transcript[-1]["content"] if transcript else ""
    return raw_response, step, time.monotonic() - t0, transcript, "", prompt_truncations


def _load_harness_config(harness_id: str) -> Optional[Dict[str, Any]]:
    """Load harness metadata from configs/harnesses.json."""
    cfg_path = CONFIGS_DIR / "harnesses.json"
    if not cfg_path.exists():
        return None
    try:
        with open(cfg_path, encoding="utf-8") as f:
            data = json.load(f)
        for h in data.get("harnesses", []):
            if h.get("id") == harness_id:
                return h
    except Exception:
        pass
    return None


# =============================================================================
# 6. Trace Writer
# =============================================================================

def trace_filename(
    phase: str,
    problem_id: str,
    harness_id: str,
    model: str,
    run_tag: str = "",
    sample_index: int = 0,
    n_samples: int = 1,
) -> str:
    """Deterministic trace filename.

    Historical form (no run tag, single sample) is unchanged:
    ``{phase}_{task}_{harness}.json`` (held-out inserts a model slug).
    A run tag replaces the phase prefix (e.g. ``build2_...``), and
    multi-sample runs gain a ``_s{index}`` suffix before ``.json``.
    """
    prefix = run_tag or phase
    if phase == "heldout":
        slug = {"Qwen/Qwen2.5-Coder-7B-Instruct": "base"}.get(model, model)
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", slug).strip("_")
        stem = f"{prefix}_{slug}_{problem_id}_{harness_id}"
    else:
        stem = f"{prefix}_{problem_id}_{harness_id}"
    if n_samples > 1:
        stem += f"_s{sample_index}"
    return stem + ".json"


def save_trace(
    phase: str,
    problem: Dict[str, Any],
    harness_id: str,
    harness_category: str,
    model: str,
    mode: str,
    raw_response: str,
    steps: int,
    latency_sec: float,
    passed: bool,
    raw_helix_transcript: List[Dict[str, Any]],
    error: str,
    output_dir: Path,
    temperature: float = 0.0,
    sample_index: int = 0,
    n_samples: int = 1,
    run_tag: str = "",
    prompt_truncations: int = 0,
    seed: Optional[int] = None,
) -> Path:
    """
    Persist one trace file.  Schema is 100% compatible with 03_extract_pairs.py.
    Round 2 fields (temperature, sample_index, run_tag, prompt_truncations,
    seed) are additive; older readers ignore them.
    """
    assistant_solution = ""
    code = extract_python_code(raw_response)
    if code:
        assistant_solution = f"```python\n{code}\n```"
    elif raw_response.strip():
        assistant_solution = raw_response.strip()

    trace: Dict[str, Any] = {
        "phase": phase,
        "task_id": problem["id"],
        "task_title": problem["title"],
        "difficulty": problem["difficulty"],
        "prompt": problem["prompt"],
        "harness_id": harness_id,
        "harness_category": harness_category,
        "model": model,
        "provider": DEFAULT_PROVIDER,
        "mode": mode,
        "steps": steps,
        "latency_sec": round(latency_sec, 3),
        "assistant_solution": assistant_solution,
        "passed": passed,
        "test_result": {"passed": passed, "error": error},
        "raw_helix_transcript": raw_helix_transcript,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": temperature,
        "sample_index": sample_index,
        "run_tag": run_tag,
        "prompt_truncations": prompt_truncations,
        "seed": seed,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    fname = trace_filename(
        phase, problem["id"], harness_id, model, run_tag, sample_index, n_samples
    )
    out_path = output_dir / fname
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2, ensure_ascii=False)
    return out_path


# =============================================================================
# 7. Main Evaluation Loop
# =============================================================================

HARNESS_IDS = ["minimal", "pi-mono", "hermes-agent", "opencode"]


def run_evaluation(args: argparse.Namespace) -> None:
    """Drive the full evaluation loop across all problems and harnesses."""
    # Resolve model name. Held-out runs compare two models on the same fresh
    # tasks, so the model must be named explicitly -- there is no default.
    if args.model:
        model = args.model
    elif args.phase == "rebuild":
        model = LORA_ADAPTER_NAME
    elif args.phase == "heldout":
        print(
            "[ERROR] --phase heldout requires an explicit --model:\n"
            f"        base model:  --model {BASE_MODEL_NAME}\n"
            f"        LoRA model:  --model {LORA_ADAPTER_NAME}"
        )
        sys.exit(1)
    else:
        model = BASE_MODEL_NAME

    # Resolve base URL (live mode only)
    base_url = (args.base_url or os.environ.get("HELIX_LIVE_BASE_URL", "")).strip()
    api_key = os.environ.get("OPENAI_API_KEY", "not-needed")

    if args.mode == "live":
        if not base_url:
            print(
                "[ERROR] --mode live requires --base-url or HELIX_LIVE_BASE_URL to be set.\n"
                "        Example: export HELIX_LIVE_BASE_URL=https://<workspace>--helix-vllm-engine-vllmserver-serve.modal.run/v1"
            )
            sys.exit(1)

        # Pre-flight health check with fail-fast guarantee
        is_ready = wait_for_server_ready(base_url, timeout_sec=180, poll_interval_sec=5)
        if not is_ready:
            print("[FAIL-FAST] Aborting evaluation loop: Modal vLLM server is not reachable or healthy.")
            sys.exit(1)

    all_problems = get_problems(args.problem_set)
    harness_ids = list(getattr(args, "harnesses", None) or HARNESS_IDS)
    for harness_id in harness_ids:
        if harness_id not in HARNESS_IDS:
            print(f"[ERROR] Unknown harness: {harness_id!r} (valid: {', '.join(HARNESS_IDS)})")
            sys.exit(1)
    temperature = float(getattr(args, "temperature", 0.0))
    n_samples = int(getattr(args, "n_samples", 1))
    run_tag = getattr(args, "run_tag", "") or ""
    start_index = int(getattr(args, "start_index", 0) or 0)
    limit = getattr(args, "limit", None)
    if temperature < 0.0 or temperature > 2.0:
        print("[ERROR] --temperature must be between 0.0 and 2.0.")
        sys.exit(1)
    if n_samples < 1:
        print("[ERROR] --n-samples must be >= 1.")
        sys.exit(1)
    if start_index < 0 or start_index >= len(all_problems):
        print(f"[ERROR] --start-index {start_index} out of range for {len(all_problems)} problems.")
        sys.exit(1)
    if limit is None:
        problems = all_problems[start_index:]
    else:
        if limit < 1:
            print("[ERROR] --limit must be >= 1.")
            sys.exit(1)
        problems = all_problems[start_index:start_index + limit]
    skip_existing = bool(getattr(args, "skip_existing", False))
    total = len(problems) * len(harness_ids) * n_samples

    print("=" * 65)
    print("  HELIX Closed-Loop Evaluation Runner")
    print(f"  Phase    : {args.phase.upper()}")
    print(f"  Problems : {args.problem_set} ({len(problems)} tasks, start={start_index}, of {len(all_problems)})")
    print(f"  Mode     : {args.mode}")
    print(f"  Model    : {model}")
    print(f"  Harnesses: {', '.join(harness_ids)}")
    print(f"  Sampling : temperature={temperature}, n_samples={n_samples}, run_tag={run_tag or '(none)'}")
    print(f"  Total    : {total} runs")
    print(f"  Output   : {RAW_TRACES_DIR}")
    print("=" * 65)

    success_count = 0
    skipped_count = 0
    run_index = 0

    for problem in problems:
        print(f"\n[Problem {problem['id']}] {problem['title']} ({problem['difficulty']})")

        for harness_id in harness_ids:
            harness_cfg = _load_harness_config(harness_id) or {}
            harness_category = harness_cfg.get("category", harness_id)

            for sample_index in range(n_samples):
                run_index += 1
                fname = trace_filename(
                    args.phase, problem["id"], harness_id, model,
                    run_tag, sample_index, n_samples,
                )
                label = f"  [{run_index}/{total}] harness={harness_id} sample={sample_index}"
                if skip_existing:
                    existing = RAW_TRACES_DIR / fname
                    if existing.exists():
                        try:
                            prior = json.loads(existing.read_text(encoding="utf-8"))
                        except Exception:
                            prior = None
                        if (
                            prior is not None
                            and prior.get("mode") == args.mode
                            and prior.get("phase") == args.phase
                            and prior.get("task_id") == problem["id"]
                            and prior.get("harness_id") == harness_id
                            and prior.get("model") == model
                            and prior.get("run_tag", "") == run_tag
                            and prior.get("sample_index", 0) == sample_index
                            and type(prior.get("passed")) is bool
                        ):
                            print(f"{label} [SKIP-EXISTING] {'[PASS]' if prior['passed'] else '[FAIL]'} -> {fname}")
                            skipped_count += 1
                            if prior["passed"]:
                                success_count += 1
                            continue
                print(f"{label} ...", end="", flush=True)

                # ---- Generate solution ----
                raw_response = ""
                steps = 0
                latency_sec = 0.0
                transcript: List[Dict[str, Any]] = []
                error = ""
                prompt_truncations = 0
                seed = SAMPLING_SEED_BASE + sample_index

                if args.mode == "dry-run":
                    raw_response, steps, latency_sec, error = _dry_run_solution(
                        harness_id, problem["id"]
                    )
                else:
                    (raw_response, steps, latency_sec, transcript, error,
                     prompt_truncations) = _live_solution(
                        harness_id, problem, base_url, model, api_key,
                        temperature=temperature, seed=seed,
                    )

                # ---- Sandbox verification ----
                code = extract_python_code(raw_response)
                if code and not error:
                    passed, exec_error = run_test_cases(code, problem["test_cases"])
                    if exec_error and not error:
                        error = exec_error
                else:
                    passed = False
                    if not error:
                        error = "No Python code block found in response"

                # ---- Persist trace ----
                out_path = save_trace(
                    phase=args.phase,
                    problem=problem,
                    harness_id=harness_id,
                    harness_category=harness_category,
                    model=model,
                    mode=args.mode,
                    raw_response=raw_response,
                    steps=steps,
                    latency_sec=latency_sec,
                    passed=passed,
                    raw_helix_transcript=transcript,
                    error=error,
                    output_dir=RAW_TRACES_DIR,
                    temperature=temperature,
                    sample_index=sample_index,
                    n_samples=n_samples,
                    run_tag=run_tag,
                    prompt_truncations=prompt_truncations,
                    seed=seed,
                )

                status = "[PASS]" if passed else "[FAIL]"
                print(f" {status} steps={steps} lat={latency_sec:.1f}s trunc={prompt_truncations} -> {out_path.name}")
                if passed:
                    success_count += 1

    print("\n" + "=" * 65)
    print(f"  Evaluation complete: {success_count}/{total} passed ({skipped_count} reused via --skip-existing)")
    print(f"  Traces saved to: {RAW_TRACES_DIR}")
    print("=" * 65)


# =============================================================================
# 8. CLI Argument Parsing
# =============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HELIX Closed-Loop Evaluation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Offline pipeline validation (no GPU):
              python closed-loop/scripts/02_run_helix_eval.py --phase build --mode dry-run --limit 3

              # Live evaluation against Modal vLLM (BUILD phase, base model):
              python closed-loop/scripts/02_run_helix_eval.py --phase build --mode live

              # Live evaluation (REBUILD phase, LoRA adapter):
              python closed-loop/scripts/02_run_helix_eval.py --phase rebuild --mode live

              # Held-out evaluation (fresh tasks, explicit model required):
              python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout --model Qwen/Qwen2.5-Coder-7B-Instruct
              python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout --model helix-lora

              # Round 2 (tagged, resumable; never overwrites Round 1 files):
              python closed-loop/scripts/02_run_helix_eval.py --phase build --mode live --problem-set train20 --run-tag build2 --skip-existing
              python closed-loop/scripts/02_run_helix_eval.py --phase build --mode live --problem-set train20 --run-tag build2 --temperature 0.7 --n-samples 2 --harnesses minimal,opencode --skip-existing
              python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout2 --run-tag heldout2 --model helix-lora --skip-existing
        """),
    )
    parser.add_argument(
        "--phase",
        choices=["build", "rebuild", "heldout"],
        required=True,
        help="Pipeline phase: 'build' uses the base model; 'rebuild' uses the LoRA adapter; "
        "'heldout' requires an explicit --model and never feeds training extraction.",
    )
    parser.add_argument(
        "--problem-set",
        choices=["train", "train20", "heldout", "heldout2"],
        default="train",
        help="Problem set: 'train' is the 10 original problems (lcb_001..010); "
        "'train20' adds 10 extra training problems (lcb_011..020); 'heldout' loads "
        "the 10 fresh problems from heldout_problems.json (held_*); 'heldout2' loads "
        "15 harder fresh problems from heldout2_problems.json (held2_*). "
        "All sets are disjoint by construction (checked on load).",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Base URL for the OpenAI-compatible vLLM endpoint "
            "(e.g. https://<workspace>--helix-vllm-engine-vllmserver-serve.modal.run/v1). "
            "Defaults to HELIX_LIVE_BASE_URL env var. Not required in dry-run mode."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            f"Model name to pass to the API. "
            f"Defaults to '{BASE_MODEL_NAME}' for --phase build "
            f"or '{LORA_ADAPTER_NAME}' for --phase rebuild."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["live", "dry-run"],
        default="dry-run",
        help=(
            "Execution mode: 'live' calls the real vLLM API; "
            "'dry-run' generates deterministic mock solutions locally (no GPU needed)."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of problems to run from --start-index (default: all remaining).",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="0-based index of the first problem to run (default: 0). Use with --limit to split a run into resumable chunks.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature passed to the model (default: 0.0, the Round 1 protocol). Sampling runs use 0.7.",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=1,
        help="Samples per (problem, harness) cell (default: 1). With n>1, filenames gain _s0/_s1/... suffixes.",
    )
    parser.add_argument(
        "--run-tag",
        default="",
        help="Round tag recorded in traces and used as the filename prefix (e.g. 'build2'). Empty keeps historical filenames.",
    )
    parser.add_argument(
        "--harnesses",
        default=None,
        help="Comma-separated harness subset (default: all 4). Example: --harnesses minimal,opencode",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reuse complete live trace files already on disk instead of re-running those cells (resume after interruption).",
    )
    args = parser.parse_args()
    # Normalise --harnesses to a list (or None for all).
    if args.harnesses:
        args.harnesses = [h.strip() for h in args.harnesses.split(",") if h.strip()]
    else:
        args.harnesses = None
    return args


def main() -> None:
    run_evaluation(parse_args())


if __name__ == "__main__":
    main()
