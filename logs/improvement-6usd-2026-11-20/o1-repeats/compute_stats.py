#!/usr/bin/env python3
"""O1-repeat statistics (2026-11-20): copy of the O2-clean statistics.
O1 DIFFERENCE (only): read runs-repeat/*/*/*/result.json only.

Pre-registered analysis (DESIGN.md section 5):
  PRIMARY: clean vs base on the 30 truly-unseen tasks (held3+held4):
    C1 text-only(clean) <= 1/30; C2 Pass@1(clean) >= Pass@1(base).
    McNemar exact 2-sided reported EXPLORATORY (p<0.05 NOT required).
  SECONDARY: full-45 table (3 arms x Pass@1 + text-only + Wilson 95% CI)
    + per-cohort splits (held2 / held3 / held4).
    Old-arm (realtool) held2 cells are CONTAMINATED (adapter trained on
    held2 traces) and are flagged so in EVERY table; new-vs-old is read
    only on held3+held4, descriptively.
  NO pooled test across cohorts, NO test across harnesses (pi-mono only),
  NO comparison against old-run base numbers (23/30 etc.) — only
  within-this-run comparisons.

Wilson + McNemar exact + summarise() + no_tool_stats() copied VERBATIM
from the REBUILD-fix compute_stats.py (themselves from step-2 / round1).
Writes summary.json + summary.md next to this script.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent

COHORTS = ("held2", "held3", "held4")
PRIMARY_COHORTS = ("held3", "held4")  # 30 truly-unseen tasks
MODELS = ("base", "clean", "realtool")

# --- Copied VERBATIM from step-2 compute_stats.py ---
def wilson(k: int, n: int, z: float = 1.959964):
    """Wilson 95% score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(gains: int, losses: int) -> float:
    """Two-sided exact McNemar p-value (binomial, discordant pairs only)."""
    n = gains + losses
    if n == 0:
        return 1.0
    m = min(gains, losses)
    tail = sum(math.comb(n, i) for i in range(m + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def summarise(records):
    total = len(records)
    infra = [r for r in records if r["classification"] == "INFRA"]
    scored = [r for r in records if r["classification"] in ("PASS", "FAIL")]
    k = sum(1 for r in scored if r["classification"] == "PASS")
    n = len(scored)
    lo, hi = wilson(k, n)
    lat = [r["cli"]["latency_sec"] for r in scored]
    steps = [r["harness"]["steps"] for r in scored
             if isinstance(r["harness"]["steps"], int)]
    tool_totals = Counter()
    for r in records:
        for tool, c in (r["harness"]["tool_call_counts"] or {}).items():
            tool_totals[tool] += c
    return {
        "n_total": total,
        "n_infra": len(infra),
        "n_scored": n,
        "n_pass": k,
        "n_fail": n - k,
        "pass_rate": round(k / n, 4) if n else 0.0,
        "wilson95": [round(lo, 4), round(hi, 4)],
        "avg_latency_sec_scored": round(sum(lat) / len(lat), 2) if lat else 0.0,
        "total_latency_sec_scored": round(sum(lat), 1) if lat else 0.0,
        "avg_steps_scored": round(sum(steps) / len(steps), 2) if steps else 0.0,
        "tool_call_totals": dict(sorted(tool_totals.items())),
        "infra_task_ids": sorted(r["task_id"] for r in infra),
    }


def no_tool_stats(records):
    """Descriptive mechanism stats (NOT a new test): runs with zero tool
    calls, and pass rate among runs that changed solution.py."""
    scored = [r for r in records if r["classification"] in ("PASS", "FAIL")]
    no_tool = [r for r in scored if r["harness"]["n_tool_calls"] == 0]
    wrote = [r for r in scored if r["scoring"]["solution_changed"]]
    wrote_pass = sum(1 for r in wrote if r["classification"] == "PASS")
    return {
        "n_scored": len(scored),
        "n_no_tool_calls": len(no_tool),
        "n_no_tool_calls_pass": sum(1 for r in no_tool if r["classification"] == "PASS"),
        "n_wrote_file": len(wrote),
        "n_wrote_file_pass": wrote_pass,
    }


# --- O2 aggregation ---

def load_results():
    out = {}
    # O1 ONLY DIFFERENCE: read runs-repeat/ (the repeat output dir).
    for result_path in sorted((LOG_DIR / "runs-repeat").glob("*/*/*/result.json")):
        # Skip archived attempts: runs/<product>/<model>/<task>.attemptN/
        if ".attempt" in result_path.parent.name:
            continue
        rec = json.loads(result_path.read_text(encoding="utf-8"))
        out[(rec["product"], rec["model_key"], rec["task_id"])] = rec
    return out


def paired(results, product, model_a, model_b, task_ids):
    """Paired McNemar: model_b vs model_a on the given tasks.
    gains = a FAIL -> b PASS; losses = a PASS -> b FAIL."""
    pairs, excluded = [], []
    for task_id in task_ids:
        a = results.get((product, model_a, task_id))
        b = results.get((product, model_b, task_id))
        if a is None or b is None:
            excluded.append({"task_id": task_id, "reason": "missing_run",
                             model_a: a["classification"] if a else None,
                             model_b: b["classification"] if b else None})
            continue
        if a["classification"] == "INFRA" or b["classification"] == "INFRA":
            excluded.append({"task_id": task_id, "reason": "infra_on_at_least_one_side",
                             model_a: a["classification"],
                             model_b: b["classification"]})
            continue
        pairs.append((task_id, a["classification"] == "PASS",
                      b["classification"] == "PASS"))
    gains = sum(1 for _t, a, b in pairs if not a and b)
    losses = sum(1 for _t, a, b in pairs if a and not b)
    disc = gains + losses
    return {
        "model_a": model_a,
        "model_b": model_b,
        "paired_tasks": len(pairs),
        "excluded_pairs": excluded,
        "gains_fail_to_pass": gains,
        "losses_pass_to_fail": losses,
        "same_pass": sum(1 for _t, a, b in pairs if a and b),
        "same_fail": sum(1 for _t, a, b in pairs if not a and not b),
        "exact_p_two_sided": round(mcnemar_exact(gains, losses), 4),
        "chi2_continuity_corrected": round((abs(gains - losses) - 1) ** 2 / disc, 3) if disc else 0.0,
        "flips": [{"task_id": t, f"{model_a}_pass": a, f"{model_b}_pass": b}
                  for (t, a, b) in pairs if a != b],
    }


def main():
    results = load_results()
    products = sorted({p for (p, _m, _t) in results})
    assert products == ["pi-mono"], f"O2 runs pi-mono only, got {products}"
    task_order = [p["id"] for p in
                  json.loads((LOG_DIR / "tasks.json").read_text(encoding="utf-8"))]
    assert len(task_order) == 45
    by_cohort = {c: [t for t in task_order if t.startswith(c + "_")] for c in COHORTS}
    for c in COHORTS:
        assert len(by_cohort[c]) == 15, f"{c}: expected 15 tasks"
    primary_tasks = [t for c in PRIMARY_COHORTS for t in by_cohort[c]]
    assert len(primary_tasks) == 30

    product = "pi-mono"
    entry = {"models": {}, "paired": {}, "flip_table": []}
    for model in MODELS:
        recs = [results[(product, model, t)] for t in task_order
                if (product, model, t) in results]
        m_entry = {"overall": summarise(recs),
                   "no_tool_overall": no_tool_stats(recs),
                   "cohorts": {},
                   "loose_test_subset": summarise([r for r in recs if r["loose_test"]]),
                   "infra_detail": [
                       {"task_id": r["task_id"], "reason": r["classification_reason"],
                        "exit_code": r["cli"]["exit_code"], "timed_out": r["cli"]["timed_out"],
                        "finish": r["harness"]["finish"],
                        "harness_error": r["harness"]["error"],
                        "stderr_tail": r["cli"]["stderr_tail"][-300:]}
                       for r in recs if r["classification"] == "INFRA"],
                   "per_task": [
                       {"task_id": r["task_id"], "task_set": r["task_set"],
                        "loose_test": r["loose_test"],
                        "classification": r["classification"],
                        "reason": r["classification_reason"],
                        "steps": r["harness"]["steps"], "finish": r["harness"]["finish"],
                        "n_tool_calls": r["harness"]["n_tool_calls"],
                        "latency_sec": r["cli"]["latency_sec"],
                        "scoring_error": r["scoring"]["error"]}
                       for r in recs]}
        for cohort in COHORTS:
            sub = [r for r in recs if r["task_set"] == cohort]
            m_entry["cohorts"][cohort] = {
                "summary": summarise(sub),
                "no_tool": no_tool_stats(sub),
                "contaminated": (model == "realtool" and cohort == "held2"),
            }
        # Primary subset (held3+held4) for clean and base, used by the verdict.
        prim = [r for r in recs if r["task_set"] in PRIMARY_COHORTS]
        m_entry["primary_held3_held4"] = {
            "summary": summarise(prim),
            "no_tool": no_tool_stats(prim),
        }
        entry["models"][model] = m_entry

    # Pre-registered paired comparisons (DESIGN.md section 5).
    entry["paired"]["base_vs_clean_primary_30"] = paired(
        results, product, "base", "clean", primary_tasks)
    entry["paired"]["base_vs_clean_full_45"] = paired(
        results, product, "base", "clean", task_order)
    entry["paired"]["base_vs_realtool_full_45"] = paired(
        results, product, "base", "realtool", task_order)
    entry["paired"]["clean_vs_realtool_primary_30"] = paired(
        results, product, "realtool", "clean", primary_tasks)
    for cohort in COHORTS:
        entry["paired"][f"base_vs_clean_{cohort}"] = paired(
            results, product, "base", "clean", by_cohort[cohort])

    entry["flip_table"] = [
        {"task_id": t,
         "cohort": t.split("_")[0],
         "base": results[(product, "base", t)]["classification"] if (product, "base", t) in results else None,
         "clean": results[(product, "clean", t)]["classification"] if (product, "clean", t) in results else None,
         "realtool": results[(product, "realtool", t)]["classification"] if (product, "realtool", t) in results else None,
         "realtool_contaminated": t.startswith("held2_")}
        for t in task_order]

    # Pre-registered verdict (DESIGN.md section 5.1), computed mechanically.
    clean_prim = entry["models"]["clean"]["primary_held3_held4"]
    base_prim = entry["models"]["base"]["primary_held3_held4"]
    c1_text_only = clean_prim["no_tool"]["n_no_tool_calls"]
    c1 = c1_text_only <= 1
    c2_diff = clean_prim["summary"]["n_pass"] - base_prim["summary"]["n_pass"]
    c2 = c2_diff >= 0
    if c1 and c2:
        verdict = ("C1+C2 DAT: fix sach khai quat hoa — hanh vi da sua tren bai "
                   "chua thay, khong thua base (n=30, 1 luot/o)")
    elif c1 and c2_diff <= -2:
        verdict = ("HON HOP: hanh vi chuyen duoc (C1 dat), ket qua khong "
                   f"(C2 thieu >= 2 bai) — bao cao nhu vay, khong giau")
    elif not c1:
        verdict = ("AM TINH: fix hanh vi khong chuyen sach sang bai chua thay "
                   "(C1 khong dat)")
    else:  # c1 dat, c2 thieu dung 1 bai
        verdict = ("HON HOP (nhe): C1 dat, C2 thieu dung 1 bai — khong thua "
                   "ro rang, bao cao nguyen trang")
    entry["verdict_primary"] = {
        "c1_text_only_clean_30": c1_text_only,
        "c1_threshold": "<= 1/30",
        "c1_met": c1,
        "c2_clean_pass_30": clean_prim["summary"]["n_pass"],
        "c2_base_pass_30": base_prim["summary"]["n_pass"],
        "c2_diff_clean_minus_base": c2_diff,
        "c2_met": c2,
        "mcnemar_primary_p": entry["paired"]["base_vs_clean_primary_30"]["exact_p_two_sided"],
        "mcnemar_note": "exploratory only; p<0.05 NOT required for the verdict",
        "verdict": verdict,
        "clean_beats_base_by_ge_4": c2_diff >= 4,
    }

    summary = {
        "experiment": "O2-clean-retrain (2026-11-20)",
        "design": "DESIGN.md in this directory (pre-registered)",
        "product": product,
        "task_counts": {"held2": 15, "held3": 15, "held4": 15, "total": 45},
        "primary_subset": "held3+held4 (30 tasks, truly unseen for both clean and base)",
        "contamination_note": ("realtool held2 cells are CONTAMINATED: the old adapter "
                               "trained on 16 SFT + 4 DPO from held2. Do not use them "
                               "for any conclusion. New-vs-old is read only on "
                               "held3+held4, descriptively."),
        "products": {product: entry},
        "pooling_note": ("NO POOLED TEST across cohorts; NO test across harnesses "
                         "(pi-mono only); NO comparison against old-run base numbers "
                         "— only within-this-run comparisons."),
    }
    (LOG_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["# O2 — Train lai adapter fix SACH (lcb_* only) + danh gia 45 bai (pi-mono)", ""]
    lines.append("**CANH BAO O NHIEM:** cac o held2 cua `realtool` la O NHIEM "
                 "(adapter cu train tren 16 SFT + 4 DPO thuoc held2) — khong dung "
                 "so held2 cua nhanh cu de ket luan gi. So sanh moi-vs-cu chi doc "
                 "tren held3+held4 (30 bai), dang mo ta.")
    lines.append("")
    v = entry["verdict_primary"]
    lines.append("## Phan quyet chinh (30 bai held3+held4, dang ky truoc)")
    lines.append("")
    lines.append(f"- C1 (hanh vi): text-only clean = {v['c1_text_only_clean_30']}/30 "
                 f"(nguong <= 1/30) → {'DAT' if v['c1_met'] else 'KHONG DAT'}")
    lines.append(f"- C2 (ket qua): Pass@1 clean {v['c2_clean_pass_30']}/30 vs base "
                 f"{v['c2_base_pass_30']}/30 (chenh {v['c2_diff_clean_minus_base']:+d}) → "
                 f"{'DAT' if v['c2_met'] else 'KHONG DAT'}")
    lines.append(f"- McNemar (kham pha): p = {v['mcnemar_primary_p']} "
                 f"(p<0,05 KHONG yeu cau cho phan quyet)")
    lines.append(f"- **{v['verdict']}**")
    if v["clean_beats_base_by_ge_4"]:
        lines.append("- Ghi chu: clean hon base >= 4 bai tren 30 bai — 'lan dau co "
                     "thang sach tren held-out' (khong nang ngon tu phan quyet "
                     "qua 'ung ho khai quat hoa tren bai ham pi-mono').")
    lines.append("")
    lines.append("## Bang du 45 bai (3 nhanh)")
    lines.append("")
    lines.append("| model | Pass@1 /45 | Wilson 95% | text-only /45 | INFRA |")
    lines.append("|---|---|---|---|---|")
    for model in MODELS:
        e = entry["models"][model]
        o, nt = e["overall"], e["no_tool_overall"]
        lines.append(f"| {model} | {o['n_pass']}/{o['n_scored']} | "
                     f"[{o['wilson95'][0]:.4f}, {o['wilson95'][1]:.4f}] | "
                     f"{nt['n_no_tool_calls']}/{nt['n_scored']} | {o['n_infra']} |")
    lines.append("")
    lines.append("## Tach theo cohort (moi cohort 15 bai)")
    lines.append("")
    lines.append("| model | cohort | Pass@1 /15 | Wilson 95% | text-only /15 | ghi chu |")
    lines.append("|---|---|---|---|---|---|")
    for model in MODELS:
        for cohort in COHORTS:
            c = entry["models"][model]["cohorts"][cohort]
            s, nt = c["summary"], c["no_tool"]
            note = "O NHIEM (realtool train tren held2)" if c["contaminated"] else ""
            lines.append(f"| {model} | {cohort} | {s['n_pass']}/{s['n_scored']} | "
                         f"[{s['wilson95'][0]:.4f}, {s['wilson95'][1]:.4f}] | "
                         f"{nt['n_no_tool_calls']}/{nt['n_scored']} | {note} |")
    lines.append("")
    for model in MODELS:
        e = entry["models"][model]
        o = e["overall"]
        lines.append(f"## {model}: {o['n_pass']}/{o['n_scored']} PASS "
                     f"(rate {o['pass_rate']:.4f}, Wilson 95% "
                     f"[{o['wilson95'][0]:.4f}, {o['wilson95'][1]:.4f}]; "
                     f"INFRA {o['n_infra']}/{o['n_total']})")
        nt = e["no_tool_overall"]
        lines.append(f"- no-tool-call runs: {nt['n_no_tool_calls']}/{nt['n_scored']} "
                     f"({nt['n_no_tool_calls_pass']} PASS); wrote file: "
                     f"{nt['n_wrote_file_pass']}/{nt['n_wrote_file']} PASS")
        lines.append(f"- avg latency (scored): {o['avg_latency_sec_scored']}s; "
                     f"avg steps: {o['avg_steps_scored']}; "
                     f"tool calls: {o['tool_call_totals']}")
        lines.append("")
    for key, label in [
            ("base_vs_clean_primary_30", "McNemar base vs clean — CHINH (held3+held4, 30 bai)"),
            ("base_vs_clean_full_45", "McNemar base vs clean — du 45 bai (mo ta)"),
            ("base_vs_realtool_full_45", "McNemar base vs realtool — du 45 bai (mo ta; held2 cua realtool O NHIEM)"),
            ("clean_vs_realtool_primary_30", "McNemar realtool vs clean — held3+held4, 30 bai (mo ta)")]:
        p = entry["paired"][key]
        lines.append(f"## {label}: {p['paired_tasks']} cap, "
                     f"gains {p['gains_fail_to_pass']}, losses {p['losses_pass_to_fail']}, "
                     f"same_pass {p['same_pass']}, same_fail {p['same_fail']}, "
                     f"p (exact, 2 phia) = {p['exact_p_two_sided']}")
        lines.append(f"Cap loai khoi phep thu (INFRA/thieu): {len(p['excluded_pairs'])}")
        lines.append("")
    lines.append("## Bang flip theo bai (base → clean → realtool)")
    lines.append("")
    lines.append("| task_id | base | clean | realtool |")
    lines.append("|---|---|---|---|")
    for row in entry["flip_table"]:
        rt = (row["realtool"] or "") + (" [O NHIEM]" if row["realtool_contaminated"] else "")
        lines.append(f"| {row['task_id']} | {row['base']} | {row['clean']} | {rt} |")
    lines.append("")
    lines.append(summary["pooling_note"])
    lines.append("")
    (LOG_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    for model in MODELS:
        e = entry["models"][model]
        print(model, e["overall"], "no_tool:", e["no_tool_overall"])
    print("verdict:", v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
