# Extract the 35 problems from the ORIGINAL sources (read-only) into /tmp/all35.json
# for the other audit scripts. 10 original train problems are read from
# 02_run_helix_eval.py via AST literal evaluation (the script is never imported
# or executed); the other 20 come from the two JSON files.
import ast, json, pathlib

REPO = pathlib.Path.home() / "workspace/helix-eval/thucnghiemhelix/closed-loop"
src = (REPO / "scripts/02_run_helix_eval.py").read_text()
tree = ast.parse(src)
bench = None
for node in tree.body:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "BENCHMARK_PROBLEMS":
        bench = ast.literal_eval(node.value)
assert bench is not None and len(bench) == 10, "BENCHMARK_PROBLEMS not found"
extra = json.loads((REPO / "data/train_extra_problems.json").read_text())
held2 = json.loads((REPO / "data/heldout2_problems.json").read_text())
assert len(extra) == 10 and len(held2) == 15
allp = bench + extra + held2
assert len(allp) == 35
json.dump(allp, open("/tmp/all35.json", "w"), ensure_ascii=False, indent=2)
print(f"wrote /tmp/all35.json with {len(allp)} problems")
for p in allp:
    print(p["id"], len(p["test_cases"]))
