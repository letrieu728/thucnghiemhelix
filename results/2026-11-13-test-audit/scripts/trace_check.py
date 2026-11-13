import json, glob, os

base = "/home/hatch/workspace/helix-eval/thucnghiemhelix/closed-loop/data/raw_traces"
# 1) held2_009 traces: passed + error + solution head
print("== held2_009_next_permutation traces ==")
for f in sorted(glob.glob(base + "/*held2_009_next_permutation*.json")):
    t = json.load(open(f))
    sol = (t.get("assistant_solution") or "")[:400].replace("\n", " | ")
    print(os.path.basename(f))
    print("   phase:", t.get("phase"), "| model:", t.get("model"), "| mode:", t.get("mode"),
          "| passed:", t.get("passed"), "| test_result:", str(t.get("test_result"))[:200],
          "| error:", str(t.get("error"))[:200])
    print("   solution head:", sol[:300])

# 2) prompt consistency: trace prompt vs local problem prompt
allp = {p["id"]: p for p in json.load(open("/tmp/all35.json"))}
# also load heldout v1 for completeness of the mapping check
held1 = json.load(open("/home/hatch/workspace/helix-eval/thucnghiemhelix/closed-loop/data/heldout_problems.json"))
for p in held1:
    allp[p["id"]] = p
mismatch, checked, unknown = 0, 0, []
for f in sorted(glob.glob(base + "/*.json")):
    t = json.load(open(f))
    tid = t.get("task_id")
    if tid in allp:
        checked += 1
        if t.get("prompt") != allp[tid]["prompt"]:
            mismatch += 1
            print("PROMPT MISMATCH:", os.path.basename(f), tid)
    else:
        unknown.append((os.path.basename(f), tid))
print(f"prompt check: {checked} traces matched to known problems, {mismatch} mismatches, {len(unknown)} unknown task_ids")
for u in unknown[:10]:
    print("  unknown:", u)
# trace keys sample
t0 = json.load(open(sorted(glob.glob(base + "/*.json"))[0]))
print("trace keys:", sorted(t0.keys()))
print("trace has test_cases field?", "test_cases" in t0)
