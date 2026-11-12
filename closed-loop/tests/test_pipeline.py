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


class PipelineTests(unittest.TestCase):
    def test_live_only_guard_on_committed_traces(self):
        # Provenance audit 2026-11-12: 40 committed BUILD traces, but only 9
        # are live (lcb_001 x4, lcb_002 x4, lcb_003 minimal). The default
        # extractor must keep exactly those; --allow-dry-run reproduces the
        # old mixed counts (9 SFT / 8 DPO) for smoke tests only.
        grouped = extract.load_all_traces(ROOT / "data/raw_traces")
        self.assertEqual(sum(map(len, grouped.values())), 9)
        self.assertEqual(set(grouped), {"lcb_001_two_sum", "lcb_002_valid_parentheses", "lcb_003_lru_cache"})
        for traces in grouped.values():
            for trace in traces:
                self.assertTrue(trace["raw_helix_transcript"])
        self.assertEqual([r["task_id"] for r in extract.extract_sft_records(grouped)], ["lcb_001_two_sum"])
        self.assertEqual(extract.extract_dpo_pairs(grouped), [])
        mixed = extract.load_all_traces(ROOT / "data/raw_traces", allow_dry_run=True)
        self.assertEqual(sum(map(len, mixed.values())), 40)
        self.assertEqual(len(extract.extract_sft_records(mixed)), 9)
        self.assertEqual(len(extract.extract_dpo_pairs(mixed)), 8)

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
        # The committed datasets are legacy mixed (live + dry-run) data: the
        # provenance gate blocks them by default and admits them only with
        # the explicit escape hatch.
        with self.assertRaisesRegex(ValueError, "dry-run"):
            train.validate_data(ROOT / "data/processed", "sft_then_dpo")
        self.assertEqual(
            set(train.validate_data(ROOT / "data/processed", "sft_then_dpo", allow_unverified=True)),
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
        # (no hard-coded values in the evaluator itself).
        metrics = evaluate.load_metrics_from_raw_traces()
        all_traces = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "data/raw_traces").glob("*.json")]
        for phase in ("build", "rebuild"):
            traces = [t for t in all_traces if t.get("phase") == phase and t.get("harness_id") == "minimal"]
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


if __name__ == "__main__":
    unittest.main()
