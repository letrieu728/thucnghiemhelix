#!/usr/bin/env python3
"""REBUILD-fix statistics (2026-11-18): read runs/*/*/*/result.json only.

Diff vs step-3 compute_stats.py: paired block compares base vs realtool;
adds a paired comparison of realtool against the RECORDED old-LoRA
per-task outcomes from steps 2-3 (files read, never re-run). Wilson +
McNemar + summarise() verbatim.

Per-harness summaries; NO pooled test across harnesses (each harness is
reported separately; cross-harness comparison is descriptive only).

Wilson + McNemar exact copied VERBATIM from step-2 compute_stats.py
(themselves copied from closed-loop/notebooks/round1_stats.py).
summarise() is also verbatim from step 2. Only the driver-level
aggregation changed: results are keyed by (product, model, task) and
each product gets its own models/paired/flip_table section.
Writes summary.json + summary.md next to this script.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent


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


def load_results():
    out = {}
    for result_path in sorted((LOG_DIR / "runs").glob("*/*/*/result.json")):
        # Skip archived attempts: runs/<product>/<model>/<task>.attemptN/
        if ".attempt" in result_path.parent.name:
            continue
        rec = json.loads(result_path.read_text(encoding="utf-8"))
        out[(rec["product"], rec["model_key"], rec["task_id"])] = rec
    return out


def summarise_product(results, product, task_order, old=None):
    models = sorted({m for (p, m, _t) in results if p == product})
    entry = {"models": {}, "paired": None, "old_lora_paired": None, "flip_table": []}
    for model in models:
        recs = [results[(product, model, t)] for t in task_order
                if (product, model, t) in results]
        m_entry = {"overall": summarise(recs)}
        for task_set in ("train", "heldout2"):
            m_entry[task_set] = summarise([r for r in recs if r["task_set"] == task_set])
        m_entry["loose_test_subset"] = summarise([r for r in recs if r["loose_test"]])
        m_entry["no_tool_mechanism"] = no_tool_stats(recs)
        m_entry["infra_detail"] = [
            {"task_id": r["task_id"], "reason": r["classification_reason"],
             "exit_code": r["cli"]["exit_code"], "timed_out": r["cli"]["timed_out"],
             "finish": r["harness"]["finish"],
             "harness_error": r["harness"]["error"],
             "stderr_tail": r["cli"]["stderr_tail"][-300:]}
            for r in recs if r["classification"] == "INFRA"]
        m_entry["per_task"] = [
            {"task_id": r["task_id"], "task_set": r["task_set"],
             "loose_test": r["loose_test"],
             "classification": r["classification"],
             "reason": r["classification_reason"],
             "steps": r["harness"]["steps"], "finish": r["harness"]["finish"],
             "n_tool_calls": r["harness"]["n_tool_calls"],
             "latency_sec": r["cli"]["latency_sec"],
             "scoring_error": r["scoring"]["error"]}
            for r in recs]
        entry["models"][model] = m_entry

    if "base" in models and "realtool" in models:
        pairs = []
        excluded = []
        for task_id in task_order:
            b = results.get((product, "base", task_id))
            l = results.get((product, "realtool", task_id))
            if b is None or l is None:
                excluded.append({"task_id": task_id, "reason": "missing_run",
                                 "base": b["classification"] if b else None,
                                 "realtool": l["classification"] if l else None})
                continue
            if b["classification"] == "INFRA" or l["classification"] == "INFRA":
                excluded.append({"task_id": task_id, "reason": "infra_on_at_least_one_side",
                                 "base": b["classification"],
                                 "realtool": l["classification"]})
                continue
            pairs.append((task_id, b["classification"] == "PASS",
                          l["classification"] == "PASS"))
        gains = sum(1 for _t, b, l in pairs if not b and l)
        losses = sum(1 for _t, b, l in pairs if b and not l)
        same_pass = sum(1 for _t, b, l in pairs if b and l)
        same_fail = sum(1 for _t, b, l in pairs if not b and not l)
        disc = gains + losses
        entry["paired"] = {
            "paired_tasks": len(pairs),
            "excluded_pairs": excluded,
            "gains_fail_to_pass": gains,
            "losses_pass_to_fail": losses,
            "same_pass": same_pass,
            "same_fail": same_fail,
            "exact_p_two_sided": round(mcnemar_exact(gains, losses), 4),
            "chi2_continuity_corrected": round((abs(gains - losses) - 1) ** 2 / disc, 3) if disc else 0.0,
            "flips": [{"task_id": t, "base_pass": b, "realtool_pass": l}
                      for (t, b, l) in pairs if b != l],
        }
    entry["flip_table"] = [
        {"task_id": t,
         "base": results[(product, "base", t)]["classification"] if (product, "base", t) in results else None,
         "realtool": results[(product, "realtool", t)]["classification"] if (product, "realtool", t) in results else None}
        for t in task_order]
    if old is not None and "realtool" in models:
        entry["old_lora_paired"] = paired_vs_old(results, old, product, task_order)
    return entry


def load_old_lora():
    """Recorded old-LoRA per-task outcomes from steps 2-3 (READ ONLY, never
    re-run). Returns {(product, task_id): result-record}."""
    out = {}
    step2 = LOG_DIR.parent / "rebuild-driver-2026-11-15" / "runs" / "lora"
    for result_path in sorted(step2.glob("*/result.json")):
        rec = json.loads(result_path.read_text(encoding="utf-8"))
        out[("pi-mono", rec["task_id"])] = rec
    step3 = LOG_DIR.parent / "rebuild-driver-multiharness-2026-11-16" / "runs"
    for result_path in sorted(step3.glob("*/*/*/result.json")):
        if result_path.parent.parent.name != "lora":
            continue
        rec = json.loads(result_path.read_text(encoding="utf-8"))
        out[(result_path.parent.parent.parent.name, rec["task_id"])] = rec
    return out


def paired_vs_old(results, old, product, task_order):
    """Paired McNemar: new LoRA (realtool) vs recorded old LoRA, same
    tasks, same protocol. Gains = old FAIL -> new PASS."""
    pairs, excluded = [], []
    for task_id in task_order:
        new = results.get((product, "realtool", task_id))
        o = old.get((product, task_id))
        if new is None or o is None:
            excluded.append({"task_id": task_id, "reason": "missing_run",
                             "realtool": new["classification"] if new else None,
                             "old_lora": o["classification"] if o else None})
            continue
        if new["classification"] == "INFRA" or o["classification"] == "INFRA":
            excluded.append({"task_id": task_id, "reason": "infra_on_at_least_one_side",
                             "realtool": new["classification"],
                             "old_lora": o["classification"]})
            continue
        pairs.append((task_id, o["classification"] == "PASS",
                      new["classification"] == "PASS"))
    gains = sum(1 for _t, o, n in pairs if not o and n)
    losses = sum(1 for _t, o, n in pairs if o and not n)
    disc = gains + losses
    old_recs = [old[(product, t)] for t in task_order if (product, t) in old]
    return {
        "paired_tasks": len(pairs),
        "excluded_pairs": excluded,
        "gains_fail_to_pass": gains,
        "losses_pass_to_fail": losses,
        "same_pass": sum(1 for _t, o, n in pairs if o and n),
        "same_fail": sum(1 for _t, o, n in pairs if not o and not n),
        "exact_p_two_sided": round(mcnemar_exact(gains, losses), 4),
        "chi2_continuity_corrected": round((abs(gains - losses) - 1) ** 2 / disc, 3) if disc else 0.0,
        "flips": [{"task_id": t, "old_lora_pass": o, "realtool_pass": n}
                  for (t, o, n) in pairs if o != n],
        "old_lora_no_tool": no_tool_stats(old_recs),
        "old_lora_overall": summarise(old_recs),
    }


# Step-2 pi-mono numbers, quoted as REFERENCE ONLY (from the step-2
# summary.md, verified 2026-11-15). Never pooled with step-3 numbers.
STEP2_PI_MONO_REFERENCE = {
    "source": "rebuild-driver-2026-11-15/summary.md (verified)",
    "base": "25/35 PASS (rate 0.7143, Wilson 95% [0.5495, 0.8367]; INFRA 0/35)",
    "lora": "15/35 PASS (rate 0.4286, Wilson 95% [0.2798, 0.5914]; INFRA 0/35)",
    "mcnemar": "35 pairs, gains 1, losses 11, same_pass 14, same_fail 9, p exact two-sided = 0.0063",
    "no_tool_calls": "base 4/35, lora 14/35",
}


def main():
    results = load_results()
    old = load_old_lora()
    products = sorted({p for (p, _m, _t) in results})
    task_order = [p["id"] for p in
                  json.loads((LOG_DIR / "tasks.json").read_text(encoding="utf-8"))]

    summary = {
        "products": {p: summarise_product(results, p, task_order, old) for p in products},
        "step2_pi_mono_reference": STEP2_PI_MONO_REFERENCE,
        "pooling_note": (
            "NO POOLED TEST: each harness is reported separately with its "
            "own McNemar. Cross-harness comparison is descriptive only "
            "(same protocol, different harness products; each cell is a "
            "single run with the harness default sampling)."),
    }
    (LOG_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["# REBUILD-fix — Thống kê tổng hợp (từng harness riêng)", ""]
    for product in products:
        entry = summary["products"][product]
        lines.append(f"# Harness: {product}")
        lines.append("")
        for model in sorted(entry["models"]):
            e = entry["models"][model]
            o = e["overall"]
            lines.append(f"## {model}: {o['n_pass']}/{o['n_scored']} PASS "
                         f"(rate {o['pass_rate']:.4f}, Wilson 95% "
                         f"[{o['wilson95'][0]:.4f}, {o['wilson95'][1]:.4f}]; "
                         f"INFRA {o['n_infra']}/{o['n_total']})")
            for key in ("train", "heldout2", "loose_test_subset"):
                s = e[key]
                lines.append(f"- {key}: {s['n_pass']}/{s['n_scored']} "
                             f"(Wilson [{s['wilson95'][0]:.4f}, {s['wilson95'][1]:.4f}], "
                             f"INFRA {s['n_infra']})")
            nt = e["no_tool_mechanism"]
            lines.append(f"- no-tool-call runs: {nt['n_no_tool_calls']}/{nt['n_scored']} "
                         f"({nt['n_no_tool_calls_pass']} PASS); wrote file: "
                         f"{nt['n_wrote_file_pass']}/{nt['n_wrote_file']} PASS")
            lines.append(f"- avg latency (scored): {o['avg_latency_sec_scored']}s; "
                         f"avg steps: {o['avg_steps_scored']}; "
                         f"tool calls: {o['tool_call_totals']}")
            lines.append("")
        if entry["paired"]:
            p = entry["paired"]
            lines.append(f"## McNemar base vs LoRA-mới ({product}): {p['paired_tasks']} cặp, "
                         f"gains {p['gains_fail_to_pass']}, losses {p['losses_pass_to_fail']}, "
                         f"same_pass {p['same_pass']}, same_fail {p['same_fail']}, "
                         f"p (exact, 2 phía) = {p['exact_p_two_sided']}")
            lines.append(f"Cặp loại khỏi phép thử (INFRA/thiếu): {len(p['excluded_pairs'])}")
            lines.append("")
        else:
            lines.append("## McNemar: không tính được (thiếu một phía base/LoRA).")
            lines.append("")
        lines.append(f"## Bảng flip theo bài ({product}, base → LoRA-mới)")
        lines.append("")
        lines.append("| task_id | base | realtool |")
        lines.append("|---|---|---|")
        for row in entry["flip_table"]:
            lines.append(f"| {row['task_id']} | {row['base']} | {row['realtool']} |")
        lines.append("")
        if entry["old_lora_paired"]:
            q = entry["old_lora_paired"]
            lines.append(f"## McNemar LoRA-mới vs LoRA-cũ đã ghi ({product}): {q['paired_tasks']} cặp, "
                         f"gains {q['gains_fail_to_pass']}, losses {q['losses_pass_to_fail']}, "
                         f"same_pass {q['same_pass']}, same_fail {q['same_fail']}, "
                         f"p (exact, 2 phía) = {q['exact_p_two_sided']}")
            lines.append(f"Cặp loại khỏi phép thử (INFRA/thiếu): {len(q['excluded_pairs'])}")
            lines.append("")
    lines.append("## Tham chiếu bước 2 — pi-mono (KHÔNG gộp số)")
    lines.append("")
    ref = STEP2_PI_MONO_REFERENCE
    lines.append(f"- Nguồn: {ref['source']}")
    lines.append(f"- base: {ref['base']}")
    lines.append(f"- lora: {ref['lora']}")
    lines.append(f"- McNemar: {ref['mcnemar']}")
    lines.append(f"- no-tool-call: {ref['no_tool_calls']}")
    lines.append("")
    lines.append(summary["pooling_note"])
    lines.append("")
    (LOG_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    for product in products:
        print(product, {m: summary["products"][product]["models"][m]["overall"]
                        for m in summary["products"][product]["models"]},
              "paired:", summary["products"][product]["paired"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
