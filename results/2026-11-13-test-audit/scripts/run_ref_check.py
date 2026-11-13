import json, subprocess, sys
sys.path.insert(0, "/tmp")
from refs import REFS

allp = json.load(open("/tmp/all35.json"))
print(f"problems={len(allp)} refs={len(REFS)}")
missing = [p["id"] for p in allp if p["id"] not in REFS]
print("missing refs:", missing)

results = {}
for p in allp:
    pid = p["id"]
    code = REFS[pid]
    test_lines = "\n".join(p["test_cases"])
    script = f"{code}\n\n# --- auto-generated test harness ---\n{test_lines}\n"
    try:
        r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=10)
        ok = r.returncode == 0
        err = (r.stderr or r.stdout or "").strip()[:600]
    except subprocess.TimeoutExpired:
        ok, err = False, "TIMEOUT"
    results[pid] = ok
    print(("PASS " if ok else "FAIL ") + pid)
    if not ok:
        print("   ERR:", err.replace("\n", " | ")[:600])

print("----")
print("pass:", sum(results.values()), "/", len(results))
print("fail:", [k for k, v in results.items() if not v])
json.dump(results, open("/tmp/ref_results.json", "w"), indent=2)
