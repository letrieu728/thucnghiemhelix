#!/usr/bin/env python3
"""O5 statistics (2026-11-20): read runs/pi-mono/<variant>/*/*/result.json only.

Adapted from step-5 compute_stats.py: wilson + mcnemar_exact + summarise() +
mechanism_summary() copied VERBATIM; aggregation keyed by (variant, model);
engagement (PRIMARY, DESIGN §4) added per (variant, model); paired McNemar
computed WITHIN each variant only. No comparison across task sets."""


from __future__ import annotations

import json
import math
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


def mechanism_summary(records):
    scored = [r for r in records if r["classification"] in ("PASS", "FAIL")]
    n = len(scored)
    def cnt(key):
        return sum(1 for r in scored if r["mechanism"][key])
    text_only = sum(1 for r in scored if r["harness"]["n_tool_calls"] == 0)
    lo, hi = wilson(text_only, n)
    return {
        "n_scored": n,
        "text_only": text_only,
        "text_only_wilson95": [round(lo, 4), round(hi, 4)],
        "read_solution": cnt("read_solution"),
        "edited_solution": cnt("edited_solution"),
        "ran_test_command": cnt("ran_test_command"),
        "marker_seen_in_bash_result": cnt("marker_seen_in_bash_result"),
        "solution_changed": sum(1 for r in scored if r["scoring"]["solution_changed"]),
        "verifier_modified": sum(1 for r in scored if r.get("verifier_modified")),
    }



def engagement_summary(records):
    """PRIMARY metric (DESIGN §4): runs with >=1 tool call reading OR
    editing solution.py OR running the test (bash test_solution.py)."""
    scored = [r for r in records if r["classification"] in ("PASS", "FAIL")]
    n = len(scored)
    k = sum(1 for r in scored
            if r["mechanism"]["read_solution"] or r["mechanism"]["edited_solution"]
            or r["mechanism"]["ran_test_command"])
    lo, hi = wilson(k, n)
    return {"n_scored": n, "engaged": k, "engaged_rate": round(k / n, 4) if n else 0.0,
            "engagement_wilson95": [round(lo, 4), round(hi, 4)]}


def main():
    fixtures = {f["id"]: f for f in json.loads((LOG_DIR / "fixtures.json").read_text())}
    records = []
    for result_path in sorted((LOG_DIR / "runs").glob("pi-mono/*/*/*/result.json")):
        if ".attempt" in result_path.parent.name:
            continue
        records.append(json.loads(result_path.read_text()))
    variants = {}
    for variant in ("V1", "V2"):
        vrecs = [r for r in records if r.get("prompt_variant") == variant]
        by_model = {}
        for model in ("base", "realtool"):
            recs = [r for r in vrecs if r["model_key"] == model]
            by_model[model] = {
                "summary": summarise(recs),
                "mechanism": mechanism_summary(recs),
                "engagement": engagement_summary(recs),
            }
        gains = losses = 0
        per_fixture = []
        for fid in fixtures:
            b = next((r for r in vrecs if r["task_id"] == fid and r["model_key"] == "base"), None)
            t = next((r for r in vrecs if r["task_id"] == fid and r["model_key"] == "realtool"), None)
            row = {"fixture_id": fid, "question_id": fixtures[fid]["question_id"],
                   "letter": fixtures[fid]["letter"],
                   "public_test_cases": fixtures[fid]["publicTestCases"]}
            for key, rec in (("base", b), ("realtool", t)):
                if rec is None:
                    row[key] = None
                else:
                    row[key] = {"classification": rec["classification"],
                                "reason": rec["classification_reason"],
                                "n_tool_calls": rec["harness"]["n_tool_calls"],
                                "steps": rec["harness"]["steps"],
                                "mechanism": rec["mechanism"],
                                "engaged": bool(rec["mechanism"]["read_solution"]
                                                or rec["mechanism"]["edited_solution"]
                                                or rec["mechanism"]["ran_test_command"]),
                                "solution_changed": rec["scoring"]["solution_changed"],
                                "verifier_modified": rec.get("verifier_modified"),
                                "latency_sec": rec["cli"]["latency_sec"]}
            per_fixture.append(row)
            if b is not None and t is not None and \
                    b["classification"] in ("PASS", "FAIL") and t["classification"] in ("PASS", "FAIL"):
                if t["classification"] == "PASS" and b["classification"] == "FAIL":
                    gains += 1
                elif t["classification"] == "FAIL" and b["classification"] == "PASS":
                    losses += 1
        paired = {"gains_realtool_over_base": gains, "losses": losses,
                  "mcnemar_exact_p": round(mcnemar_exact(gains, losses), 4)}
        variants[variant] = {"models": by_model, "paired_base_vs_realtool": paired,
                             "per_fixture": per_fixture,
                             "n_cells_completed": len(vrecs)}
    summary = {
        "step": "o5-v6-probe",
        "fixture_label": "group-regenerated (public test cases only)",
        "product": "pi-mono",
        "n_fixtures_planned": 16,
        "n_cells_completed": len(records),
        "variants": variants,
        "baselines_reused_step5": {
            "base": {"pass": "0/16", "text_only": "14/16", "engagement": "2/16"},
            "realtool": {"pass": "1/16", "text_only": "10/16", "engagement": "6/16"},
        },
    }
    (LOG_DIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                          encoding="utf-8")

    lines = ["# O5 summary — group-regenerated v6 fixtures, pi-mono, prompt variants V1/V2",
             "",
             "Fixtures are GROUP-REGENERATED content; grading on PUBLIC test cases only.",
             "PRIMARY metric: engagement (>=1 tool call reading/editing solution.py or "
             "running test_solution.py). Descriptive only; no comparison with the "
             "authors' benchmark.",
             ""]
    for variant in ("V1", "V2"):
        v = variants[variant]
        lines += [f"## Variant {variant} (cells={v['n_cells_completed']})", ""]
        for model in ("base", "realtool"):
            s_ = v["models"][model]["summary"]
            m = v["models"][model]["mechanism"]
            e = v["models"][model]["engagement"]
            lines += [f"### {model}",
                      f"- Pass@1: {s_['n_pass']}/{s_['n_scored']} "
                      f"(Wilson 95% {s_['wilson95'][0]}–{s_['wilson95'][1]}), "
                      f"INFRA {s_['n_infra']}",
                      f"- Engagement (PRIMARY): {e['engaged']}/{e['n_scored']} "
                      f"(Wilson 95% {e['engagement_wilson95'][0]}–{e['engagement_wilson95'][1]})",
                      f"- Text-only: {m['text_only']}/{m['n_scored']} "
                      f"(Wilson 95% {m['text_only_wilson95'][0]}–{m['text_only_wilson95'][1]})",
                      f"- Read solution.py: {m['read_solution']}, edited: {m['edited_solution']}, "
                      f"ran test cmd: {m['ran_test_command']}, marker seen: "
                      f"{m['marker_seen_in_bash_result']}, solution changed: "
                      f"{m['solution_changed']}, verifier modified: {m['verifier_modified']}",
                      f"- Tool totals: {s_['tool_call_totals']}",
                      f"- Avg latency (scored): {s_['avg_latency_sec_scored']}s, "
                      f"avg steps: {s_['avg_steps_scored']}",
                      ""]
        pr = v["paired_base_vs_realtool"]
        lines += [f"Paired (within variant {variant}): realtool gains {pr['gains_realtool_over_base']}, "
                  f"losses {pr['losses']}, McNemar exact p={pr['mcnemar_exact_p']}",
                  "",
                  "Per-fixture:",
                  "",
                  "| Fixture | Letter | Cases | Base | Realtool |",
                  "|---|---|---|---|---|"]
        for row in v["per_fixture"]:
            def cell(rec):
                if rec is None:
                    return "—"
                return f"{rec['classification']} (tools {rec['n_tool_calls']}, engaged={rec['engaged']})"
            lines.append(f"| {row['fixture_id']} | {row['letter']} | {row['public_test_cases']} "
                         f"| {cell(row['base'])} | {cell(row['realtool'])} |")
        lines.append("")
    (LOG_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    for variant in ("V1", "V2"):
        v = variants[variant]
        print(f"{variant}: cells={v['n_cells_completed']} "
              f"base={v['models']['base']['summary']['n_pass']}/{v['models']['base']['summary']['n_scored']} "
              f"eng={v['models']['base']['engagement']['engaged']}/{v['models']['base']['engagement']['n_scored']} "
              f"realtool={v['models']['realtool']['summary']['n_pass']}/{v['models']['realtool']['summary']['n_scored']} "
              f"eng={v['models']['realtool']['engagement']['engaged']}/{v['models']['realtool']['engagement']['n_scored']} "
              f"paired gains={v['paired_base_vs_realtool']['gains_realtool_over_base']} "
              f"losses={v['paired_base_vs_realtool']['losses']} "
              f"p={v['paired_base_vs_realtool']['mcnemar_exact_p']}")


if __name__ == "__main__":
    main()
