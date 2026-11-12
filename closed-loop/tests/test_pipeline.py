import ast
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extract = load("extract", "scripts/03_extract_pairs.py")
train = load("train", "scripts/04_train_lora.py")
evaluate = load("evaluate", "notebooks/evaluate_rebuild.py")
runner = load("runner", "scripts/02_run_helix_eval.py")


class PipelineTests(unittest.TestCase):
    def test_live_only_guard_on_committed_traces(self):
        # Live re-run 2026-11-12: all 40 committed BUILD traces are live
        # (verified: mode=live, non-empty transcripts, base model only).
        # The default extractor must keep exactly those; --allow-dry-run
        # changes nothing now that no dry-run traces remain.
        grouped = extract.load_all_traces(ROOT / "data/raw_traces")
        self.assertEqual(sum(map(len, grouped.values())), 40)
        self.assertEqual(len(grouped), 10)
        for traces in grouped.values():
            for trace in traces:
                self.assertTrue(trace["raw_helix_transcript"])
        sft_tasks = {r["task_id"] for r in extract.extract_sft_records(grouped)}
        self.assertEqual(sft_tasks, set(grouped) - {"lcb_002_valid_parentheses", "lcb_003_lru_cache"})
        self.assertEqual(len(extract.extract_dpo_pairs(grouped)), 2)
        mixed = extract.load_all_traces(ROOT / "data/raw_traces", allow_dry_run=True)
        self.assertEqual(sum(map(len, mixed.values())), 40)
        self.assertEqual(len(extract.extract_sft_records(mixed)), 8)
        self.assertEqual(len(extract.extract_dpo_pairs(mixed)), 2)

    def test_dry_run_mode_field_is_skipped(self):
        live = {"task_id": "t1", "phase": "build", "mode": "live", "passed": True,
                "assistant_solution": "code", "raw_helix_transcript": [{"step": 1}]}
        dry = {"task_id": "t1", "phase": "build", "mode": "dry-run", "passed": True,
               "assistant_solution": "code", "raw_helix_transcript": [{"step": 1}]}
        legacy_dry = {"task_id": "t1", "phase": "build", "passed": True,
                      "assistant_solution": "code", "raw_helix_transcript": []}
        legacy_live = {"task_id": "t1", "phase": "build", "passed": True,
                       "assistant_solution": "code", "raw_helix_transcript": [{"step": 1}]}
        self.assertFalse(extract.is_dry_run_trace(live))
        self.assertTrue(extract.is_dry_run_trace(dry))
        self.assertTrue(extract.is_dry_run_trace(legacy_dry))
        self.assertFalse(extract.is_dry_run_trace(legacy_live))
        with tempfile.TemporaryDirectory() as tmp:
            for name, trace in [("live.json", live), ("dry.json", dry),
                                ("legacy_dry.json", legacy_dry), ("legacy_live.json", legacy_live)]:
                (Path(tmp) / name).write_text(json.dumps(trace), encoding="utf-8")
            kept = extract.load_all_traces(Path(tmp))
            self.assertEqual(sum(map(len, kept.values())), 2)
            kept_all = extract.load_all_traces(Path(tmp), allow_dry_run=True)
            self.assertEqual(sum(map(len, kept_all.values())), 4)

    def test_empty_does_not_seed_or_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(extract, "RAW_TRACES_DIR", Path(tmp)), patch.object(extract, "PROCESSED_DIR", Path(tmp)), patch("sys.argv", ["extract"]), patch.object(extract, "seed_demo_traces") as seed:
                with self.assertRaises(SystemExit):
                    extract.main()
                seed.assert_not_called()
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_missing_empty_invalid_training_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                train.validate_data(tmp, "typo")
            with self.assertRaises(FileNotFoundError):
                train.validate_data(tmp, "sft")
            (Path(tmp) / "sft_data.jsonl").write_text("", encoding="utf-8")
            with self.assertRaises(ValueError):
                train.validate_data(tmp, "sft")
        # The committed datasets are now verified live-only (2026-11-12
        # re-run): the provenance gate admits them by default.
        self.assertEqual(
            set(train.validate_data(ROOT / "data/processed", "sft_then_dpo")),
            {"sft", "dpo"},
        )
        # A manifest that admits dry-run data is still blocked by default
        # and admitted only with the explicit escape hatch (synthetic
        # mixed manifest built from the current verified datasets).
        with tempfile.TemporaryDirectory() as tmp:
            src = ROOT / "data/processed"
            for name in ("sft_data.jsonl", "dpo_pairs.jsonl", "provenance.json"):
                shutil.copy(src / name, Path(tmp) / name)
            manifest_path = Path(tmp) / "provenance.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["allow_dry_run"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dry-run"):
                train.validate_data(tmp, "sft_then_dpo")
            self.assertEqual(
                set(train.validate_data(tmp, "sft_then_dpo", allow_unverified=True)),
                {"sft", "dpo"},
            )

    def test_provenance_gate_blocks_tampered_data(self):
        # Counts/hashes that no longer match the manifest always fail, even
        # with the escape hatch: edited-after-extraction data is never OK.
        with tempfile.TemporaryDirectory() as tmp:
            src = ROOT / "data/processed"
            for name in ("sft_data.jsonl", "dpo_pairs.jsonl", "provenance.json"):
                shutil.copy(src / name, Path(tmp) / name)
            with open(Path(tmp) / "sft_data.jsonl", "a", encoding="utf-8") as f:
                f.write("\n")
            with self.assertRaisesRegex(ValueError, "changed after extraction"):
                train.validate_data(tmp, "sft_then_dpo", allow_unverified=True)
        # A missing manifest fails by default and passes only with the flag.
        with tempfile.TemporaryDirectory() as tmp:
            src = ROOT / "data/processed"
            for name in ("sft_data.jsonl", "dpo_pairs.jsonl"):
                shutil.copy(src / name, Path(tmp) / name)
            with self.assertRaisesRegex(ValueError, "provenance.json"):
                train.validate_data(tmp, "sft_then_dpo")
            self.assertEqual(
                set(train.validate_data(tmp, "sft_then_dpo", allow_unverified=True)),
                {"sft", "dpo"},
            )

    def test_config_matches_training_script(self):
        # configs/lora_config.yaml mirrors 04_train_lora.py defaults; drift
        # between the documented config and the effective config must fail.
        # Defaults are read from the AST (not the Modal-decorated function),
        # so this test works with or without Modal installed.
        cfg = yaml.safe_load((ROOT / "configs/lora_config.yaml").read_text(encoding="utf-8"))
        tree = ast.parse((ROOT / "scripts/04_train_lora.py").read_text(encoding="utf-8"))
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "train_lora_pipeline")
        defaults = {
            arg.arg: ast.literal_eval(d)
            for arg, d in zip(fn.args.args[-len(fn.args.defaults):], fn.args.defaults)
        }
        self.assertEqual(cfg["model"]["base_model_name"], train.BASE_MODEL_NAME)
        self.assertEqual(cfg["lora"]["r"], defaults["r"])
        self.assertEqual(cfg["lora"]["lora_alpha"], defaults["lora_alpha"])
        self.assertEqual(cfg["training"]["epochs"], defaults["epochs"])
        self.assertEqual(cfg["training"]["learning_rate"], defaults["lr"])
        self.assertEqual(cfg["dpo"]["learning_rate"], defaults["dpo_lr"])
        self.assertEqual(cfg["dpo"]["epochs"], defaults["epochs"])
        self.assertEqual(cfg["training"]["seed"], defaults["seed"])
        self.assertEqual(cfg["storage"]["modal_volume_name"], train.VOLUME_NAME)
        self.assertEqual(cfg["storage"]["mount_path"], train.MOUNT_PATH)
        peft_call = next(
            n for n in ast.walk(fn)
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "get_peft_model"
        )
        keywords = {kw.arg: ast.literal_eval(kw.value) for kw in peft_call.keywords if isinstance(kw.value, (ast.Constant, ast.List))}
        self.assertEqual(keywords["target_modules"], cfg["lora"]["target_modules"])
        self.assertEqual(keywords["lora_dropout"], cfg["lora"]["lora_dropout"])
        self.assertEqual(keywords["bias"], cfg["lora"]["bias"])
        self.assertIn("helix-lora-final", ast.unparse(tree))

    def test_loss_history_and_no_steps(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(train, "volume"):
            trainer = SimpleNamespace(state=SimpleNamespace(global_step=1, log_history=[{"step": 1, "loss": 0.5}]))
            train.save_history(trainer, "sft", tmp)
            rows = json.loads((Path(tmp) / "sft_loss_history.json").read_text())
            self.assertEqual(rows[0]["stage"], "sft")
            trainer.state.global_step = 0
            with self.assertRaises(RuntimeError):
                train.save_history(trainer, "sft", tmp)
            trainer.state.global_step = 1
            trainer.state.log_history = [{"step": 1, "loss": float("nan")}]
            with self.assertRaises(RuntimeError):
                train.save_history(trainer, "sft", tmp)

    def test_no_hardcoded_metrics(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(evaluate, "RAW_TRACES_DIR", Path(tmp)):
            with self.assertRaises(ValueError):
                evaluate.load_metrics_from_raw_traces()
        # Aggregated rates must equal a fresh count over the committed traces
        # (no hard-coded values in the evaluator itself). The evaluator only
        # counts untagged Round 1 traces, so the fresh count applies the
        # same filter (Round 2 traces carry run_tag build2/rebuild2/heldout2).
        metrics = evaluate.load_metrics_from_raw_traces()
        all_traces = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data/raw_traces").glob("*.json")]
        for phase in ("build", "rebuild"):
            traces = [t for t in all_traces if t.get("phase") == phase and t.get("harness_id") == "minimal" and not t.get("run_tag")]
            expected = round(100.0 * sum(1 for t in traces if t["passed"]) / len(traces), 1)
            self.assertEqual(metrics[phase]["minimal"]["pass_rate"], expected)

    def test_rebuild_cannot_be_selected_for_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = {"task_id": "only_rebuild", "phase": "rebuild", "passed": True, "assistant_solution": "answer"}
            (Path(tmp) / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
            self.assertFalse(extract.load_all_traces(Path(tmp)))

    def test_malformed_and_unpaired_evaluation_fails(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(evaluate, "RAW_TRACES_DIR", Path(tmp)):
            path = Path(tmp) / "trace.json"
            path.write_text("not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate.load_metrics_from_raw_traces()
            path.write_text(json.dumps({"phase": "build", "harness_id": "minimal", "task_id": "one", "passed": True, "steps": 1, "latency_sec": 1}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unpaired"):
                evaluate.load_metrics_from_raw_traces()


class Round2Tests(unittest.TestCase):
    def test_problem_sets_counts_and_disjoint(self):
        train = runner.get_problems("train")
        train20 = runner.get_problems("train20")
        heldout = runner.get_problems("heldout")
        heldout2 = runner.get_problems("heldout2")
        self.assertEqual(len(train), 10)
        self.assertEqual(len(train20), 20)
        self.assertEqual(len(heldout), 10)
        self.assertEqual(len(heldout2), 15)
        self.assertEqual([p["id"] for p in train20[:10]], [p["id"] for p in train])
        all_ids = [p["id"] for p in train20 + heldout + heldout2]
        self.assertEqual(len(all_ids), len(set(all_ids)))
        for problem in train20 + heldout + heldout2:
            self.assertTrue(problem["test_cases"])
            self.assertTrue(problem["prompt"].strip())

    def test_trace_filenames_legacy_and_tagged(self):
        base = runner.BASE_MODEL_NAME
        self.assertEqual(
            runner.trace_filename("build", "lcb_001_two_sum", "minimal", base),
            "build_lcb_001_two_sum_minimal.json",
        )
        self.assertEqual(
            runner.trace_filename("heldout", "held_001_roman_to_int", "minimal", base),
            "heldout_base_held_001_roman_to_int_minimal.json",
        )
        self.assertEqual(
            runner.trace_filename("build", "lcb_011_trap_rain_water", "opencode", base, "build2", 1, 2),
            "build2_lcb_011_trap_rain_water_opencode_s1.json",
        )
        self.assertEqual(
            runner.trace_filename("heldout", "held2_001_edit_distance", "pi-mono", "helix-lora", "heldout2"),
            "heldout2_helix-lora_held2_001_edit_distance_pi-mono.json",
        )
        # Single-sample tagged runs keep no suffix; sampled runs are distinct.
        self.assertEqual(
            runner.trace_filename("build", "t", "minimal", base, "build2", 0, 1),
            "build2_t_minimal.json",
        )
        self.assertNotEqual(
            runner.trace_filename("build", "t", "minimal", base, "build2", 0, 2),
            runner.trace_filename("build", "t", "minimal", base, "build2", 1, 2),
        )

    def test_truncation_guard_keeps_system_prompt_and_tail(self):
        msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "prompt"}]
        for i in range(6):
            msgs.append({"role": "assistant", "content": "x" * 8000})
            msgs.append({"role": "user", "content": f"feedback-{i}"})
        kept, dropped = runner._truncate_messages(msgs)
        self.assertGreater(dropped, 0)
        self.assertLessEqual(runner._estimate_input_tokens(kept), runner.MAX_INPUT_TOKENS_EST)
        self.assertEqual(kept[0]["content"], "sys")
        self.assertEqual(kept[1]["content"], "prompt")
        self.assertEqual(kept[-1]["content"], "feedback-5")
        short = [{"role": "system", "content": "sys"}, {"role": "user", "content": "short"}]
        kept_short, dropped_short = runner._truncate_messages(short)
        self.assertEqual(dropped_short, 0)
        self.assertEqual(kept_short, short)

    def test_extractor_run_tag_filter_and_heldout_never_leaks(self):
        def trace(task, phase, tag, passed=True):
            return {"task_id": task, "phase": phase, "mode": "live", "passed": passed,
                    "assistant_solution": "def f():\n    return 1", "harness_id": "minimal",
                    "steps": 1, "latency_sec": 1.0, "prompt": "p",
                    "raw_helix_transcript": [{"step": 1}], "run_tag": tag}
        with tempfile.TemporaryDirectory() as tmp:
            files = {
                "r1.json": trace("t1", "build", ""),
                "r2.json": trace("t1", "build", "build2"),
                "r2b.json": trace("t2", "build", "build2"),
                "held.json": trace("held2_001_edit_distance", "heldout", "heldout2"),
                "held_build.json": trace("held2_001_edit_distance", "build", "heldout2"),
            }
            # held_build.json is a synthetic mislabel: a held-out task id in a
            # build trace with a held-out tag. The extractor's held-out-ID
            # block must refuse it even when the tag matches.
            for name, content in files.items():
                (Path(tmp) / name).write_text(json.dumps(content), encoding="utf-8")
            default = extract.load_all_traces(Path(tmp))
            self.assertEqual(sum(map(len, default.values())), 1)
            self.assertEqual(set(default), {"t1"})
            round2 = extract.load_all_traces(Path(tmp), run_tags={"build2"})
            self.assertEqual(sum(map(len, round2.values())), 2)
            self.assertEqual(set(round2), {"t1", "t2"})
            held = extract.load_all_traces(Path(tmp), run_tags={"heldout2"})
            # The genuine heldout-phase trace is never loaded, and the
            # mislabelled build-phase held-out trace is blocked by ID.
            self.assertEqual(sum(map(len, held.values())), 0)
            self.assertNotIn("held2_001_edit_distance", set(round2))

    def test_extractor_skips_identical_dpo_pair(self):
        def trace(harness, passed, code):
            return {"task_id": "t1", "phase": "build", "mode": "live", "passed": passed,
                    "assistant_solution": code, "harness_id": harness, "steps": 1,
                    "latency_sec": 1.0, "prompt": "p",
                    "raw_helix_transcript": [{"step": 1}], "run_tag": ""}
        grouped = {"t1": [
            trace("opencode", True, "def f():\n    return 1"),
            trace("minimal", False, "def f():\n    return 1"),
        ]}
        self.assertEqual(extract.extract_dpo_pairs(grouped), [])
        grouped["t1"][1]["assistant_solution"] = "def f():\n    return 2"
        self.assertEqual(len(extract.extract_dpo_pairs(grouped)), 1)

    def test_evaluator_ignores_tagged_traces(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(evaluate, "RAW_TRACES_DIR", Path(tmp)):
            for phase in ("build", "rebuild"):
                for harness in runner.HARNESS_IDS:
                    content = {"phase": phase, "harness_id": harness, "task_id": "one",
                               "passed": True, "steps": 1, "latency_sec": 1.0, "run_tag": ""}
                    (Path(tmp) / f"{phase}_one_{harness}.json").write_text(json.dumps(content), encoding="utf-8")
            # A Round 2 duplicate of one cell must not break pairing.
            dup = {"phase": "build", "harness_id": "minimal", "task_id": "one",
                   "passed": False, "steps": 1, "latency_sec": 1.0, "run_tag": "build2"}
            (Path(tmp) / "build2_one_minimal.json").write_text(json.dumps(dup), encoding="utf-8")
            metrics = evaluate.load_metrics_from_raw_traces()
            self.assertEqual(metrics["build"]["minimal"]["pass_rate"], 100.0)

    def test_advanced_loop_capped_at_four_steps(self):
        # A harness that always fails must stop after MAX_ADVANCED_STEPS
        # generations, not after the config value (8/12/15). Mock the
        # OpenAI client so no network/GPU is involved.
        from unittest.mock import MagicMock, patch

        problem = runner.BENCHMARK_PROBLEMS[0]  # two_sum
        calls = {"n": 0}

        def fake_create(**kwargs):
            calls["n"] += 1
            choice = MagicMock()
            choice.message.content = "```python\ndef two_sum(nums, target):\n    return []\n```"
            choice.finish_reason = "stop"
            response = MagicMock()
            response.choices = [choice]
            return response

        fake_client = MagicMock()
        fake_client.chat.completions.create.side_effect = fake_create
        with patch("openai.OpenAI", return_value=fake_client):
            raw, steps, _lat, transcript, error, trunc = runner._live_solution(
                "opencode", problem, "http://localhost:1/v1", runner.BASE_MODEL_NAME, "key"
            )
        self.assertEqual(calls["n"], runner.MAX_ADVANCED_STEPS)
        self.assertEqual(steps, runner.MAX_ADVANCED_STEPS)
        self.assertEqual(len(transcript), runner.MAX_ADVANCED_STEPS)
        self.assertEqual(error, "")
        # Minimal still makes exactly one call.
        calls["n"] = 0
        with patch("openai.OpenAI", return_value=fake_client):
            _raw, steps_min, _lat, _tr, _err, _tc = runner._live_solution(
                "minimal", problem, "http://localhost:1/v1", runner.BASE_MODEL_NAME, "key"
            )
        self.assertEqual(calls["n"], 1)
        self.assertEqual(steps_min, 1)


if __name__ == "__main__":
    unittest.main()
