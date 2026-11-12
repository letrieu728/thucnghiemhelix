# HELIX Closed-Loop: Continuous Model Adaptation via Harness-to-Weight Distillation

> **Working copy (Triệu, 2026-11-12).** This directory is a copy of
> `closed-loop/` from [`Vietng-XPrince7/HELIX`](https://github.com/Vietng-XPrince7/HELIX)
> at commit `cc44b7b`, plus the 2026-11-12 provenance fixes (branch
> `fix/build-provenance-heldout` in the fork, delivered as a patch), plus the
> training improvements listed below, which exist **only in this copy** so far.
> The fork remains the group's canonical pipeline; port improvements back to
> it with a patch rather than editing both copies independently.
>
> **Training improvements in this copy (vs the fork):**
> 1. `03_extract_pairs.py` writes `data/processed/provenance.json` (counts,
>    source traces, SHA-256 of both datasets) with every extraction.
> 2. `04_train_lora.py` refuses to train unless the manifest exists, says the
>    data is live-only, and still matches the dataset files; the committed
>    legacy mixed data is blocked by default (`--allow-unverified-data` is
>    the explicit escape hatch; count/hash mismatches always fail).
> 3. Training runs record a full `metadata.json` (hyperparameters, seed, data
>    hashes, provenance summary, per-stage steps/final loss, library
>    versions) and the local entrypoint downloads `metadata.json` +
>    `versions.json` next to `loss_history.json`.
> 4. `seed` is a parameter (default 42) instead of a hard-coded constant.
> 5. `configs/lora_config.yaml` was reconciled to the script's actual
>    defaults (the old file disagreed on logging, save strategy, DPO epochs
>    and the whole storage section) and a test fails if they drift again.
> 6. `data/rebuild_comparison_plot.png` is not copied (binary); regenerate it
>    with `notebooks/evaluate_rebuild.py`.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Framework: Modal](https://img.shields.io/badge/Compute-Modal.com-green.svg)](https://modal.com)
[![Engine: vLLM](https://img.shields.io/badge/Inference-vLLM-orange.svg)](https://vllm.ai)
[![Tuning: Unsloth](https://img.shields.io/badge/Finetuning-Unsloth%20%2B%20TRL-red.svg)](https://github.com/unslothai/unsloth)

> **Portfolio Showcase**: An end-to-end autonomous adaptation loop extending the **HELIX AI Agent Harness Framework** from passive trace collection (**BUILD**) into iterative self-improvement (**UPDATE**) and differential re-evaluation (**REBUILD**).

> **Provenance note (2026-11-12):** the committed BUILD baseline mixes 9 live traces with 31 dry-run mock traces, and REBUILD re-tests the same 10 training tasks (see [`PROVENANCE_AUDIT.md`](PROVENANCE_AUDIT.md)). Reported gains are therefore training-task observations, not held-out generalisation. The extractor now rejects dry-run traces by default, and a 10-task held-out set is ready in `data/heldout_problems.json` (see [`HELDOUT_RUNBOOK.md`](HELDOUT_RUNBOOK.md)).

---

## 💡 Executive Pitch & Theoretical Motivation

Modern AI coding agents (such as OpenCode, Pi, and Hermes) achieve high accuracy by wrapping foundation models inside complex **agent harnesses**—multi-turn prompt engineering, tool permission layers, retry heuristics, and dynamic context builders. However:

1. **Heavy Scaffolding Overhead**: Complex harnesses consume excessive prompt tokens, incur high inference latency, and introduce brittle software dependencies.
2. **The Open-Loop Bottleneck**: The original HELIX framework disassembles agents into Lego blocks and records execution traces (`BUILD`), but leaves the model weights ($\theta_0$) fixed.

**HELIX Closed-Loop** bridges this gap by introducing **Sibling Trajectory Contrastive Distillation**:
- We execute 4 heterogeneous agent harnesses (from zero-scaffolding Minimal to high-scaffolding OpenCode) on the exact same programming problem.
- By contrasting successful trajectories (from complex harnesses) against failures or inefficiencies (from naive harnesses), we synthesize clean **SFT** and **DPO preference pairs**.
- We fine-tune the model with **LoRA (QLoRA 4-bit via Unsloth + TRL)** on Modal A100 GPUs to produce $\theta_1$.
- In the **REBUILD** phase, we demonstrate that **a minimalist harness running on the adapted model ($\theta_1$) rivals or exceeds the accuracy of a complex harness running on the base model ($\theta_0$)**, eliminating runtime harness complexity by baking it directly into model weights.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph S1 ["1. BUILD Phase (Initial Trajectory Collection)"]
        direction TB
        B_MODEL["Base Model Theta_0<br/>(Qwen2.5-Coder-7B-Instruct)"] --> VLLM_0["vLLM on Modal.com<br/>(OpenAI-Compatible Endpoint)"]
        VLLM_0 --> H1["Minimal Harness<br/>(Zero Scaffolding)"]
        VLLM_0 --> H2["Pi Mono Harness<br/>(Baseline)"]
        VLLM_0 --> H3["Hermes Agent Harness<br/>(Session Hooks)"]
        VLLM_0 --> H4["OpenCode Harness<br/>(Plugin Architecture)"]
        H1 & H2 & H3 & H4 --> TRACES["Raw Trajectory Traces<br/>(data/raw_traces/*.json)"]
    end

    subgraph S2 ["2. DISTILL Phase (Sibling Contrast Filter)"]
        direction TB
        TRACES --> EXTRACT["03_extract_pairs.py<br/>(Sibling Trajectory Matcher)"]
        EXTRACT --> SFT_DATA["Clean SFT Dataset<br/>(Verified, Fewest Steps)"]
        EXTRACT --> DPO_DATA["DPO Preference Pairs<br/>(Chosen: Complex vs Rejected: Minimal)"]
    end

    subgraph S3 ["3. UPDATE Phase (Cloud LoRA Fine-Tuning)"]
        direction TB
        SFT_DATA & DPO_DATA --> TRAIN["04_train_lora.py on Modal A100<br/>(Unsloth + TRL SFTTrainer & DPOTrainer)"]
        TRAIN --> VOL["Modal Persistent Volume<br/>(/vol/checkpoints/helix_lora_final)"]
    end

    subgraph S4 ["4. REBUILD Phase (Differential Adaptation Benchmark)"]
        direction TB
        VOL --> VLLM_1["vLLM Serving Adapter Theta_1<br/>(--enable-lora)"]
        VLLM_1 --> EVAL["02_run_helix_eval.py --phase rebuild"]
        EVAL --> NOTEBOOK["evaluate_rebuild.py<br/>(Visual Delta & Convergence Proof)"]
    end

    S1 --> S2 --> S3 --> S4
```

---

## 📂 Repository Structure

```text
closed-loop/
├── README.md                 # Professional portfolio documentation (Pitch, Architecture, Setup, Guide)
├── PROVENANCE_AUDIT.md       # 2026-11-12 audit: BUILD mixed 9 live + 31 dry-run traces; what still holds
├── HELDOUT_RUNBOOK.md        # Commands to re-run BUILD live, retrain, and evaluate held-out
├── requirements.txt          # Production dependencies (modal, vllm, unsloth, trl, transformers, etc.)
├── .env.template             # Environment template connecting HELIX to Modal vLLM endpoint
├── configs/
│   ├── harnesses.json        # 4 representative configurations (Minimal, Pi Mono, Hermes Agent, OpenCode)
│   └── lora_config.yaml      # LoRA hyperparameters (Qwen2.5-Coder-7B, r=16, alpha=32, target_modules)
├── scripts/
│   ├── 01_modal_vllm.py      # Modal.com script: vLLM OpenAI-compatible server on A100 GPU (Base & LoRA)
│   ├── 02_run_helix_eval.py  # Benchmark runner calling HELIX CLI across 4 harnesses on coding tasks
│   ├── 03_extract_pairs.py   # Sibling Trajectory Filter: extracts Clean SFT data and DPO preference pairs
│   └── 04_train_lora.py      # Modal.com script: Unsloth + TRL (SFT + DPO) training on A100, commits to Volume
├── data/
│   ├── heldout_problems.json # 10 fresh held-out problems (never trained on)
│   ├── raw_traces/           # Storage for raw agent execution trajectory logs (.json)
│   └── processed/            # Cleaned SFT and DPO training sets (.jsonl)
└── notebooks/
    └── evaluate_rebuild.py   # Aggregation & plotting: before vs after LoRA (Theta_0 vs Theta_1) comparison
```

---

## ⚙️ Environment & Prerequisite Setup

### 1. Local Python Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r closed-loop/requirements.txt
```

### 2. Configure Environment Variables
Copy the template and provide your Modal credentials:
```bash
cp closed-loop/.env.template .env
```
Key variables inside `.env`:
```env
HELIX_LIVE_PROVIDER=openai-compatible
HELIX_LIVE_BASE_URL=https://<your-modal-subdomain>--vllm-openai-serve.modal.run/v1
OPENAI_API_KEY=modal-helix-key
HELIX_LIVE_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
```

### 3. Modal.com Setup
Authenticate with your Modal account:
```bash
modal setup
```

---

## 🚀 Step-by-Step Execution Guide

### Step 1: Deploy Inference Engine on Modal GPU (BUILD Phase)
Deploy a high-performance vLLM endpoint on an NVIDIA A100/A10G GPU:
```bash
modal serve closed-loop/scripts/01_modal_vllm.py
```
*Note the generated public URL (e.g., `https://<org>--helix-vllm-engine-serve.modal.run/v1`) and paste it into `HELIX_LIVE_BASE_URL` in your `.env`.*

---

### Step 2: Collect Trajectories across 4 Harnesses (`BUILD`)
Run the benchmark across all 4 representative harnesses on coding tasks:
```bash
python closed-loop/scripts/02_run_helix_eval.py --phase build --limit 5
```
This logs detailed execution traces (prompts, tool calls, steps, latency, pass/fail status) to:
`closed-loop/data/raw_traces/build_<task_id>_<harness_id>.json`.

---

### Step 3: Extract Sibling Trajectories (SFT & DPO)
Run contrastive sibling filtering to distill insights across harnesses on identical problems:
```bash
python closed-loop/scripts/03_extract_pairs.py
```
- **SFT Dataset** (`closed-loop/data/processed/sft_data.jsonl`): Clean, verified solutions taking minimal steps.
- **DPO Preference Pairs** (`closed-loop/data/processed/dpo_pairs.jsonl`): Pairs where `chosen` is from a disciplined harness and `rejected` is from an unadapted/failing harness.

*(Tip: Pass `--seed-demo` to generate synthetic baseline traces immediately for dry-runs).*

---

### Step 4: Fine-tune LoRA via Unsloth & TRL on Modal A100
Launch distributed 4-bit QLoRA fine-tuning on Modal:
```bash
modal run closed-loop/scripts/04_train_lora.py --stage sft_then_dpo --epochs 3
```
- Trains LoRA adapters with rank $r=16, \alpha=32$ on `Qwen/Qwen2.5-Coder-7B-Instruct`.
- Automatically commits trained weights to the persistent Modal Volume at `/vol/checkpoints/helix_lora_final`.

---

### Step 5: Re-evaluate Adapted Model (`REBUILD` Phase)
1. In `01_modal_vllm.py`, vLLM will automatically detect the committed LoRA adapter and enable multi-LoRA serving.
2. Update your `.env` or pass the adapter name to re-evaluate:
```bash
python closed-loop/scripts/02_run_helix_eval.py --phase rebuild --model helix-lora-adapter --limit 5
```
Traces will be stored as `closed-loop/data/raw_traces/rebuild_<task_id>_<harness_id>.json`.

---

### Step 6: Generate Rebuild Report & Visual Analytics
Synthesize performance metrics before ($\theta_0$) and after ($\theta_1$) adaptation:
```bash
python closed-loop/notebooks/evaluate_rebuild.py
```

Actual output from the committed traces (see `REBUILD_REPORT.md` for the full table; the BUILD baseline mixes live and dry-run traces — see `PROVENANCE_AUDIT.md`):
```text
================================================================================
HELIX CLOSED-LOOP PERFORMANCE SUMMARY: BUILD (θ_0) vs REBUILD (θ_1)
================================================================================
Harness                        | Base Pass@1  | LoRA Pass@1  | Accuracy Δ   | Steps Δ
--------------------------------------------------------------------------------
Minimal (Zero-Scaffolding)     |       30.0%  |       60.0%  |      +30.0%  |    -2.80
Pi Mono (Baseline)             |       90.0%  |       70.0%  |      -20.0%  |    -0.90
Hermes Agent (Session)         |       90.0%  |       70.0%  |      -20.0%  |    +0.10
OpenCode (Complex Scaffolding) |       90.0%  |       70.0%  |      -20.0%  |    +2.30
================================================================================
```
A high-resolution figure is saved to `closed-loop/data/rebuild_comparison_plot.png`.

---

## 📊 Key Insights & Research Takeaways

1. **Scaffold-to-Weight Distillation**: Complex scaffolding (system instructions, format parsers, tool guardrails) can be internalized into model weights through sibling preference tuning.
2. **Minimalist Harness, Training Tasks Only**: The Minimal harness rises **+30.0 pp** (30% → 60%) on the same 10 tasks used for training, while the three advanced harnesses each fall 20.0 pp and average latency rises in REBUILD. No token counts were recorded, so no token/latency efficiency claim is made here. Whether the gain generalises is an open question until the held-out evaluation in `HELDOUT_RUNBOOK.md` is run.
3. **True Closed Loop**: Turns static trace collection into an autonomous data-engine flywheel for domain-specific agent evolution.

