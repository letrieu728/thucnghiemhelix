#!/usr/bin/env python3
"""O1 two-run analysis (2026-11-20): compare the O2 run with the O1 repeat,
cell by cell, per the pre-registered analysis in O1/DESIGN.md section 3.

  - Per-cell agreement (same PASS/FAIL in both runs) per arm and per cohort.
  - Pooled 2-run Pass@1 per arm x cohort (k/30 per 15-task cohort, k/60 for
    the 30-task primary, k/90 for the 45-task table) + Wilson 95% CI.
    This is a DESCRIPTIVE 2-run rate, never a new independent estimate.
  - Primary comparison (clean vs base, 30 unseen tasks): McNemar computed
    SEPARATELY for the O2 run and the O1 run. NEVER pool p-values across runs.
  - Base-drift check within-program: base O2 run vs base O1 run on the same
    45 tasks. If base shifts >= 4 tasks, record the drift sentence for O6.
  - Re-read of the O2 verdict under the O1 light (written to RESULTS.md of O1).

SCOPE NOTE (billing trim, DESIGN.md section 5 step 1): the realtool arm was
cut from O1 by the billing forecast (see RUN_LOG.md). The 2-run analysis
therefore covers base + clean only (90 cells x 2 runs). Realtool numbers
stay O2-only (1 run/cell) and are NOT repeated here.

Reads O2 runs read-only from ../o2-clean-retrain/runs/ and O1 runs from
runs-repeat/ in this directory. Writes o1_2run_summary.json + o1_2run_summary.md.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
O2_DIR = LOG_DIR.parent / "o2-clean-retrain"

COHORTS = ("held2", "held3", "held4")
PRIMARY_COHORTS = ("held3", "held4")
MODELS = ("base", "clean")  # realtool trimmed from O1 (billing rule, DESIGN §5)


def wilson(k: int, n: int, z: float = 1.959964):
    """Wilson 95% score interval (copied verbatim from O2 compute_stats.py)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(gains: int, losses: int) -> float:
    """Two-sided exact McNemar p-value (copied verbatim from O2 compute_stats.py)."""
    n = gains + losses
    if n == 0:
        return 1.0
    m = min(gains, losses)
    tail = sum(math.comb(n, i) for i in range(m + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def load_run(run_dir: Path):
    out = {}
    for p in sorted((run_dir / "pi-mono").glob("*/*/result.json")):
        if ".attempt" in p.parent.name:
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        out[(rec["model_key"], rec["task_id"])] = rec
    return out


def paired_mcnemar(results, model_a, model_b, task_ids):
    pairs = []
    for t in task_ids:
        a = results.get((model_a, t))
        b = results.get((model_b, t))
        assert a is not None and b is not None, f"missing run {model_a}/{model_b} {t}"
        assert a["classification"] in ("PASS", "FAIL"), f"INFRA left in {model_a} {t}"
        assert b["classification"] in ("PASS", "FAIL"), f"INFRA left in {model_b} {t}"
        pairs.append((t, a["classification"] == "PASS", b["classification"] == "PASS"))
    gains = sum(1 for _t, a, b in pairs if not a and b)
    losses = sum(1 for _t, a, b in pairs if a and not b)
    return {
        "model_a": model_a, "model_b": model_b,
        "paired_tasks": len(pairs),
        "gains_fail_to_pass": gains, "losses_pass_to_fail": losses,
        "same_pass": sum(1 for _t, a, b in pairs if a and b),
        "same_fail": sum(1 for _t, a, b in pairs if not a and not b),
        "exact_p_two_sided": round(mcnemar_exact(gains, losses), 4),
        "flips": [{"task_id": t, f"{model_a}_pass": a, f"{model_b}_pass": b}
                  for (t, a, b) in pairs if a != b],
    }


def main():
    task_order = [p["id"] for p in
                  json.loads((LOG_DIR / "tasks.json").read_text(encoding="utf-8"))]
    assert len(task_order) == 45
    by_cohort = {c: [t for t in task_order if t.startswith(c + "_")] for c in COHORTS}
    primary_tasks = [t for c in PRIMARY_COHORTS for t in by_cohort[c]]
    assert len(primary_tasks) == 30

    o2 = load_run(O2_DIR / "runs")
    o1 = load_run(LOG_DIR / "runs-repeat")
    for model in MODELS:
        for t in task_order:
            assert (model, t) in o2, f"O2 missing {model} {t}"
            assert (model, t) in o1, f"O1 missing {model} {t}"

    def is_pass(rec):
        return rec["classification"] == "PASS"

    def no_tool(rec):
        return rec["harness"]["n_tool_calls"] == 0

    summary = {
        "experiment": "O1-repeat (2026-11-20): 2-run analysis of O2 cells",
        "design": "O1/DESIGN.md section 3 (pre-registered)",
        "scope": ("base + clean only (90 cells x 2 runs). Realtool arm trimmed "
                  "from O1 by the billing forecast (DESIGN.md section 5 step 1); "
                  "its O2 numbers stay 1 run/cell."),
        "runs": {"o2": "O2 run (1st)", "o1": "O1 repeat (2nd)"},
        "agreement": {},
        "pooled_2run": {},
        "mcnemar_per_run": {},
        "base_drift": {},
        "verdict_reread": {},
    }

    # --- Per-cell agreement (same PASS/FAIL both runs) per arm and cohort.
    for model in MODELS:
        overall_tasks = task_order
        agree = sum(1 for t in overall_tasks
                    if is_pass(o2[(model, t)]) == is_pass(o1[(model, t)]))
        flips = [{"task_id": t, "o2": o2[(model, t)]["classification"],
                  "o1": o1[(model, t)]["classification"]}
                 for t in overall_tasks
                 if is_pass(o2[(model, t)]) != is_pass(o1[(model, t)])]
        overall = {"n_cells": len(overall_tasks), "n_agree": agree,
                   "agreement_rate": round(agree / len(overall_tasks), 4),
                   "n_flips": len(flips), "flips": flips}
        cohorts = {}
        for cohort in COHORTS:
            tasks = by_cohort[cohort]
            a = sum(1 for t in tasks
                    if is_pass(o2[(model, t)]) == is_pass(o1[(model, t)]))
            fl = [{"task_id": t, "o2": o2[(model, t)]["classification"],
                   "o1": o1[(model, t)]["classification"]}
                  for t in tasks
                  if is_pass(o2[(model, t)]) != is_pass(o1[(model, t)])]
            cohorts[cohort] = {"n_cells": len(tasks), "n_agree": a,
                               "agreement_rate": round(a / len(tasks), 4),
                               "n_flips": len(fl), "flips": fl}
        summary["agreement"][model] = {"overall": overall, "cohorts": cohorts}

    # --- Pooled 2-run Pass@1 per arm x cohort + primary + full (descriptive).
    for model in MODELS:
        entry = {"cohorts": {}, "primary_held3_held4": {}, "full_45": {}}
        for cohort in COHORTS:
            tasks = by_cohort[cohort]
            k = sum(is_pass(o2[(model, t)]) + is_pass(o1[(model, t)]) for t in tasks)
            lo, hi = wilson(k, 30)
            entry["cohorts"][cohort] = {
                "k": k, "n": 30, "rate": round(k / 30, 4),
                "wilson95": [round(lo, 4), round(hi, 4)],
                "o2_pass": sum(is_pass(o2[(model, t)]) for t in tasks),
                "o1_pass": sum(is_pass(o1[(model, t)]) for t in tasks),
            }
        k = sum(is_pass(o2[(model, t)]) + is_pass(o1[(model, t)])
                for t in primary_tasks)
        lo, hi = wilson(k, 60)
        entry["primary_held3_held4"] = {
            "k": k, "n": 60, "rate": round(k / 60, 4),
            "wilson95": [round(lo, 4), round(hi, 4)],
            "o2_pass": sum(is_pass(o2[(model, t)]) for t in primary_tasks),
            "o1_pass": sum(is_pass(o1[(model, t)]) for t in primary_tasks),
        }
        k = sum(is_pass(o2[(model, t)]) + is_pass(o1[(model, t)])
                for t in task_order)
        lo, hi = wilson(k, 90)
        entry["full_45"] = {
            "k": k, "n": 90, "rate": round(k / 90, 4),
            "wilson95": [round(lo, 4), round(hi, 4)],
            "o2_pass": sum(is_pass(o2[(model, t)]) for t in task_order),
            "o1_pass": sum(is_pass(o1[(model, t)]) for t in task_order),
        }
        summary["pooled_2run"][model] = entry

    # --- Text-only per run (for the C1 re-read).
    text_only = {}
    for model in MODELS:
        text_only[model] = {}
        for run_name, run in [("o2", o2), ("o1", o1)]:
            text_only[model][run_name] = {
                "primary_30": sum(no_tool(run[(model, t)]) for t in primary_tasks),
                "full_45": sum(no_tool(run[(model, t)]) for t in task_order),
                "cohorts": {c: sum(no_tool(run[(model, t)]) for t in by_cohort[c])
                            for c in COHORTS},
            }
    summary["text_only_per_run"] = text_only

    # --- McNemar clean vs base, primary 30, SEPARATELY per run.
    for run_name, run in [("o2", o2), ("o1", o1)]:
        summary["mcnemar_per_run"][run_name] = {
            "primary_30": paired_mcnemar(run, "base", "clean", primary_tasks),
            "full_45": paired_mcnemar(run, "base", "clean", task_order),
        }

    # --- Base drift within-program: base O2 vs base O1, same 45 tasks.
    drift_flips = [{"task_id": t, "o2": o2[("base", t)]["classification"],
                    "o1": o1[("base", t)]["classification"]}
                   for t in task_order
                   if is_pass(o2[("base", t)]) != is_pass(o1[("base", t)])]
    n_shift = len(drift_flips)
    summary["base_drift"] = {
        "n_tasks_compared": 45,
        "n_cells_differing": n_shift,
        "o2_pass_45": sum(is_pass(o2[("base", t)]) for t in task_order),
        "o1_pass_45": sum(is_pass(o1[("base", t)]) for t in task_order),
        "o2_pass_primary_30": sum(is_pass(o2[("base", t)]) for t in primary_tasks),
        "o1_pass_primary_30": sum(is_pass(o1[("base", t)]) for t in primary_tasks),
        "drift_ge_4": n_shift >= 4,
        "drift_sentence_for_o6": (
            "drift trong-chương-trình ≥ 4 bài — mọi so sánh một-lần-chạy "
            "đều hạ xuống mức mô tả" if n_shift >= 4 else None),
        "flips": drift_flips,
    }

    # --- Re-read of the O2 verdict (C1/C2) in each run.
    def verdict_for(run):
        c1 = sum(no_tool(run[("clean", t)]) for t in primary_tasks)
        c2_clean = sum(is_pass(run[("clean", t)]) for t in primary_tasks)
        c2_base = sum(is_pass(run[("base", t)]) for t in primary_tasks)
        return {
            "c1_text_only_clean_30": c1, "c1_met": c1 <= 1,
            "c2_clean_pass_30": c2_clean, "c2_base_pass_30": c2_base,
            "c2_diff": c2_clean - c2_base, "c2_met": (c2_clean - c2_base) >= 0,
        }
    v_o2 = verdict_for(o2)
    v_o1 = verdict_for(o1)
    both = v_o2["c1_met"] and v_o2["c2_met"] and v_o1["c1_met"] and v_o1["c2_met"]
    summary["verdict_reread"] = {
        "o2_run": v_o2,
        "o1_run": v_o1,
        "c1_c2_hold_in_both_runs": both,
        "reread": ("phán quyết O2 ổn định qua 2 lượt" if both else
                   "phán quyết O2 KHÔNG ổn định — báo cáo cả hai lượt, "
                   "không chọn lượt đẹp"),
    }

    (LOG_DIR / "o1_2run_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Markdown.
    L = []
    L.append("# O1 — Phân tích 2 lượt (lượt O2 + lượt lặp O1, pi-mono)")
    L.append("")
    L.append("Phạm vi: base + clean (90 ô × 2 lượt). Nhánh realtool bị cắt khỏi "
             "O1 theo quy tắc billing DESIGN §5 bước 1 — số realtool của O2 "
             "ở lại mức 1 lượt/ô, không có trong phân tích 2 lượt này.")
    L.append("")
    L.append("Tỉ lệ gộp 2 lượt là **tỉ lệ mô tả trên 2 lượt**, không phải một "
             "ước lượng độc lập mới. McNemar tính RIÊNG từng lượt, không gộp "
             "p-value qua hai lượt.")
    L.append("")
    L.append("## 1. Tỉ lệ ô đồng thuận (cùng PASS/FAIL ở cả hai lượt)")
    L.append("")
    L.append("| model | tổng thể | held2 | held3 | held4 |")
    L.append("|---|---|---|---|---|")
    for model in MODELS:
        a = summary["agreement"][model]
        row = [f"| {model} |"]
        for key in ["overall", "held2", "held3", "held4"]:
            e = a["overall"] if key == "overall" else a["cohorts"][key]
            row.append(f" {e['n_agree']}/{e['n_cells']} ({e['agreement_rate']:.2f}) |")
        L.append("".join(row))
    L.append("")
    for model in MODELS:
        a = summary["agreement"][model]
        flips = a["overall"]["flips"]
        if flips:
            L.append(f"Ô đổi kết quả giữa hai lượt — {model} "
                     f"({len(flips)} ô): " +
                     ", ".join(f"{f['task_id']} ({f['o2']}→{f['o1']})"
                               for f in flips))
    L.append("")
    L.append("## 2. Pass@1 gộp 2 lượt (mô tả) + Wilson 95% CI")
    L.append("")
    L.append("| model | held2 (k/30) | held3 (k/30) | held4 (k/30) | chính 30 bài (k/60) | đủ 45 bài (k/90) |")
    L.append("|---|---|---|---|---|---|")
    for model in MODELS:
        p = summary["pooled_2run"][model]
        def cell(e):
            return f"{e['k']}/{e['n']} [{e['wilson95'][0]:.4f}, {e['wilson95'][1]:.4f}]"
        L.append(f"| {model} | {cell(p['cohorts']['held2'])} | "
                 f"{cell(p['cohorts']['held3'])} | {cell(p['cohorts']['held4'])} | "
                 f"{cell(p['primary_held3_held4'])} | {cell(p['full_45'])} |")
    L.append("")
    L.append("Chia nhỏ theo lượt (để đọc khoảng đo được):")
    L.append("")
    for model in MODELS:
        p = summary["pooled_2run"][model]
        pr = p["primary_held3_held4"]
        L.append(f"- {model} chính 30 bài: lượt O2 {pr['o2_pass']}/30, "
                 f"lượt O1 {pr['o1_pass']}/30 → gộp {pr['k']}/60.")
        fu = p["full_45"]
        L.append(f"- {model} đủ 45 bài: lượt O2 {fu['o2_pass']}/45, "
                 f"lượt O1 {fu['o1_pass']}/45 → gộp {fu['k']}/90.")
    L.append("")
    L.append("## 3. So sánh chính clean vs base, 30 bài chưa thấy — McNemar RIÊNG từng lượt")
    L.append("")
    L.append("| lượt | clean | base | chênh | gains | losses | same_pass | same_fail | p (exact, 2 phía) |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for run_name in ["o2", "o1"]:
        m = summary["mcnemar_per_run"][run_name]["primary_30"]
        v = summary["verdict_reread"][f"{run_name}_run"]
        L.append(f"| {run_name.upper()} | {v['c2_clean_pass_30']}/30 | "
                 f"{v['c2_base_pass_30']}/30 | {v['c2_diff']:+d} | "
                 f"{m['gains_fail_to_pass']} | {m['losses_pass_to_fail']} | "
                 f"{m['same_pass']} | {m['same_fail']} | {m['exact_p_two_sided']} |")
    L.append("")
    L.append("Text-only (C1) từng lượt, 30 bài chính: clean lượt O2 "
             f"{summary['text_only_per_run']['clean']['o2']['primary_30']}/30, "
             f"lượt O1 {summary['text_only_per_run']['clean']['o1']['primary_30']}/30 "
             f"(ngưỡng ≤ 1/30); base lượt O2 "
             f"{summary['text_only_per_run']['base']['o2']['primary_30']}/30, "
             f"lượt O1 {summary['text_only_per_run']['base']['o1']['primary_30']}/30.")
    L.append("")
    L.append("## 4. Kiểm tra base drift trong chương trình (base lượt O2 vs lượt O1, 45 bài)")
    L.append("")
    d = summary["base_drift"]
    L.append(f"- Base lượt O2: {d['o2_pass_45']}/45; lượt O1: {d['o1_pass_45']}/45; "
             f"số ô đổi kết quả: **{d['n_cells_differing']}/45**.")
    if d["flips"]:
        L.append("- Ô base đổi kết quả: " +
                 ", ".join(f"{f['task_id']} ({f['o2']}→{f['o1']})" for f in d["flips"]))
    if d["drift_sentence_for_o6"]:
        L.append(f"- **{d['drift_sentence_for_o6']}**")
    else:
        L.append("- Drift < 4 bài — không kích hoạt câu ghi chú drift cho O6.")
    L.append("")
    L.append("## 5. Đọc lại phán quyết O2 dưới ánh sáng O1")
    L.append("")
    v = summary["verdict_reread"]
    L.append(f"- Lượt O2: C1 {'ĐẠT' if v['o2_run']['c1_met'] else 'KHÔNG ĐẠT'} "
             f"(text-only {v['o2_run']['c1_text_only_clean_30']}/30), C2 "
             f"{'ĐẠT' if v['o2_run']['c2_met'] else 'KHÔNG ĐẠT'} "
             f"(clean {v['o2_run']['c2_clean_pass_30']}/30 vs base "
             f"{v['o2_run']['c2_base_pass_30']}/30, chênh {v['o2_run']['c2_diff']:+d}).")
    L.append(f"- Lượt O1: C1 {'ĐẠT' if v['o1_run']['c1_met'] else 'KHÔNG ĐẠT'} "
             f"(text-only {v['o1_run']['c1_text_only_clean_30']}/30), C2 "
             f"{'ĐẠT' if v['o1_run']['c2_met'] else 'KHÔNG ĐẠT'} "
             f"(clean {v['o1_run']['c2_clean_pass_30']}/30 vs base "
             f"{v['o1_run']['c2_base_pass_30']}/30, chênh {v['o1_run']['c2_diff']:+d}).")
    L.append(f"- **{v['reread']}**")
    L.append("")
    (LOG_DIR / "o1_2run_summary.md").write_text("\n".join(L), encoding="utf-8")

    print(json.dumps(summary["agreement"], indent=2, ensure_ascii=False))
    print("pooled:", json.dumps(summary["pooled_2run"], indent=2, ensure_ascii=False))
    print("mcnemar:", json.dumps(summary["mcnemar_per_run"], indent=2, ensure_ascii=False))
    print("drift:", json.dumps(summary["base_drift"], ensure_ascii=False))
    print("verdict:", summary["verdict_reread"]["reread"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
