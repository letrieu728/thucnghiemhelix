#!/usr/bin/env python3
"""Warmup check for REBUILD-fix serving: poll /health until 200 with
shim_enabled=true AND adapters list containing helix-lora-realtool,
then GET /v1/models. Writes warmup_<product>.json + v1_models_<product>.json.
Usage: python3 warmup.py <endpoint-no-v1-suffix> <product>"""
import json
import sys
import time
import urllib.request
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent


def get(url, timeout=10):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode())


def main():
    endpoint = sys.argv[1].rstrip("/")
    product = sys.argv[2]
    t0 = time.monotonic()
    attempts = 0
    last = None
    while time.monotonic() - t0 < 420:
        attempts += 1
        try:
            status, last = get(endpoint + "/health", timeout=5)
            if status == 200 and last.get("shim_enabled") is True and \
                    "helix-lora-realtool" in (last.get("adapters") or []):
                break
        except Exception as e:
            last = {"error": str(e)}
        time.sleep(5)
    else:
        print("WARMUP FAILED", json.dumps(last))
        sys.exit(1)
    elapsed = round(time.monotonic() - t0, 1)
    status, models = get(endpoint + "/v1/models", timeout=15)
    (LOG_DIR / f"warmup_{product}.json").write_text(
        json.dumps({"elapsed_sec": elapsed, "attempts": attempts,
                    "health": last}, indent=2), encoding="utf-8")
    (LOG_DIR / f"v1_models_{product}.json").write_text(
        json.dumps(models, indent=2), encoding="utf-8")
    ids = [m["id"] for m in models.get("data", [])]
    print(f"WARMUP OK in {elapsed}s ({attempts} attempts): health={last}")
    print("models:", ids)
    assert "helix-lora-realtool" in ids, "realtool model id missing from /v1/models"
    assert "Qwen/Qwen2.5-Coder-7B-Instruct" in ids, "base model id missing"


if __name__ == "__main__":
    main()
