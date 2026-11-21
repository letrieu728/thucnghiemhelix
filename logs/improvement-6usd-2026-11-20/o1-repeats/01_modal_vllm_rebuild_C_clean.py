"""
01_modal_vllm_rebuild_C.py - Rebuild Step 1, variant C (15/11/2026)
=====================================================================
Based on closed-loop/scripts/01_modal_vllm.py (working copy, thucnghiemhelix)
+ the 2 parser flags from the 12/11 smoke copy (01_modal_vllm_smoke.py).

Variant C changes vs the smoke copy (proxy fix + tool-call shim):
  1. /v1/chat/completions is no longer proxied by buffering the raw vLLM
     response and copying ALL of its headers back (that copied hop-by-hop
     headers such as transfer-encoding, which broke SSE framing at Modal's
     edge proxy: server 200 -> CLI 502 empty, 3/3 on 12/11).
     Instead the proxy calls vLLM with stream=false internally, then:
       - if the client asked stream=true: re-emits a well-formed SSE stream
         (correct content-type, no hop-by-hop headers) built from the
         complete response;
       - if the client asked stream=false: returns the JSON body.
  2. All other paths forward with hop-by-hop headers filtered out.
  3. ENABLE_TOOLCALL_SHIM = True in this variant: the tool-call shim in
     section 2 is ENABLED. Variant C differs from variant A ONLY by this
     flag (plus this docstring).

Serves: base Qwen/Qwen2.5-Coder-7B-Instruct + LoRA alias "helix-lora"
from volume helix-adapters/helix-lora-final (round-2 adapter, verified).

O2-CLEAN COPY (2026-11-20): identical to the REBUILD-fix copy EXCEPT the
serving list gains one more adapter: also serves LoRA alias
"helix-lora-clean" from volume helix-adapters/helix-lora-clean (trained
20/11 from lcb_*-only subset of fix data). --max-loras raised 2 -> 3 so
all three adapters load. Proxy, shim, flags, and base model unchanged.
The REBUILD-fix file is untouched; this copy deploys under the same
app name (helix-vllm-engine) and endpoint.
"""

import json
import os
import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

import modal

# =============================================================================
# 1. Configuration
# =============================================================================
MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"
VLLM_PORT = 8000

ADAPTERS_VOLUME_NAME = "helix-adapters"
ADAPTERS_MOUNT_PATH = "/adapters"
LORA_ADAPTER_SUBDIR = "helix-lora-final"  # round-2 adapter (verified 15/11)
LORA_ADAPTER_NAME = "helix-lora"
# REBUILD-FIX: new adapter trained from real-harness traces (18/11)
REALTOOL_ADAPTER_SUBDIR = "helix-lora-realtool"
REALTOOL_ADAPTER_NAME = "helix-lora-realtool"
# O2-CLEAN: clean adapter trained from lcb_*-only subset of fix data (20/11)
CLEAN_ADAPTER_SUBDIR = "helix-lora-clean"
CLEAN_ADAPTER_NAME = "helix-lora-clean"

# Variant flag: False = proxy fix only (variant A). True = + tool-call shim
# (variant C). The ONLY intended difference between variants A and C.
ENABLE_TOOLCALL_SHIM = True

# =============================================================================
# 2. Tool-call shim (pure functions; also unit-tested offline)
# =============================================================================
# The group shim: translates XML <function_call> / <tool_call> markup that
# Qwen2.5-Coder-7B emits as plain text into OpenAI-style tool_calls.
# This is the GROUP's shim, not upstream/vLLM behaviour. It only runs when
# ENABLE_TOOLCALL_SHIM is True, only when the request declared tools, only
# when vLLM itself returned no tool_calls, and only for tool names declared
# in the request. Anything it cannot parse is left untouched as text.

_FUNCTION_CALL_RE = re.compile(
    r"<function_call\s*>(.*?)</function_call\s*>", re.DOTALL | re.IGNORECASE
)
_NAME_RE = re.compile(r"<name\s*>(.*?)</name\s*>", re.DOTALL | re.IGNORECASE)
_ARGS_RE = re.compile(
    r"<arguments\s*>(.*?)</arguments\s*>", re.DOTALL | re.IGNORECASE
)
_TOOL_CALL_RE = re.compile(
    r"<tool_call\s*>(.*?)</tool_call\s*>", re.DOTALL | re.IGNORECASE
)
_FENCE_RE = re.compile(
    r"^\s*```[a-zA-Z]*\s*\n?(.*?)\n?\s*```\s*$", re.DOTALL
)
_RESPONSE_WRAP_RE = re.compile(
    r"^\s*<response\s*>(.*?)</response\s*>\s*$", re.DOTALL | re.IGNORECASE
)

# Bare-string arguments mapping (only used when args parse to a plain string).
_BARE_STRING_KEY = {
    "read": "path",
    "write": "path",
    "edit": "path",
    "ls": "path",
    "find": "path",
    "grep": "query",
    "bash": "command",
}


def _xml_element_to_value(el):
    if len(el) == 0:
        return (el.text or "").strip()
    return {child.tag.strip(): _xml_element_to_value(child) for child in el}


def _parse_args_text(raw, tool_name):
    """Parse an <arguments> body into a dict, or return None if unparseable."""
    text = (raw or "").strip()
    if not text:
        return {}
    # 1. JSON object / JSON value.
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, str):
        key = _BARE_STRING_KEY.get(tool_name)
        return {key: parsed} if key else None
    if parsed is not None:
        return None
    # 2. Nested XML elements: <path>buggy.py</path><a>1</a>
    if "<" in text and ">" in text:
        try:
            root = ET.fromstring("<args>%s</args>" % text)
        except ET.ParseError:
            return None
        out = {}
        for child in root:
            out[child.tag.strip()] = _xml_element_to_value(child)
        return out
    # 3. Bare string.
    key = _BARE_STRING_KEY.get(tool_name)
    return {key: text} if key else None


_FENCE_BLOCK_RE = re.compile(
    r"```[a-zA-Z]*\s*\n?(.*?)\n?\s*```", re.DOTALL
)


def _json_call_from_value(value, known_tools):
    """Return list of {name, arguments} if value looks like (a) tool call(s)."""
    out = []
    items = value if isinstance(value, list) else [value]
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if name not in known_tools or "arguments" not in item:
            continue
        args = item.get("arguments")
        if isinstance(args, str):
            parsed = _parse_args_text(args, name)
            if parsed is None:
                continue
            args = parsed
        if not isinstance(args, dict):
            continue
        out.append({"name": name, "arguments": args})
    return out


def _collect_json_calls(text, known_tools):
    """Find fenced/bare JSON tool-call objects in text.

    Returns (calls, spans): calls in order of appearance, spans are the
    (start, end) ranges of the matched JSON (including fences) to remove.
    Only accepts objects whose "name" is a declared tool and that carry
    "arguments" — plain JSON prose is left untouched.
    """
    decoder = json.JSONDecoder()
    found = []  # (start, end, [calls])

    def _try_parse(s, start, end):
        try:
            value, _ = decoder.raw_decode(s.strip())
        except (json.JSONDecodeError, ValueError):
            return
        calls = _json_call_from_value(value, known_tools)
        if calls:
            found.append((start, end, calls))

    # 1. Whole text (possibly fence-wrapped).
    stripped = text.strip()
    fence = _FENCE_RE.match(stripped)
    if fence:
        _try_parse(fence.group(1), 0, len(text))
    else:
        _try_parse(stripped, 0, len(text))
    # 2. Fenced blocks anywhere in the text.
    for m in _FENCE_BLOCK_RE.finditer(text):
        _try_parse(m.group(1), m.start(), m.end())
    # 3. Brace scan for embedded JSON objects.
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            value, end = decoder.raw_decode(text[i:])
        except (json.JSONDecodeError, ValueError):
            continue
        calls = _json_call_from_value(value, known_tools)
        if calls:
            found.append((i, i + end, calls))
    if not found:
        return [], []
    # Greedily accept non-overlapping spans, earliest first; prefer the
    # longest span when starts tie (whole-text match wins over inner match).
    found.sort(key=lambda f: (f[0], -(f[1] - f[0])))
    calls, spans, taken_until = [], [], -1
    for start, end, cs in found:
        if start < taken_until:
            continue
        calls.extend(cs)
        spans.append((start, end))
        taken_until = end
    return calls, spans


def extract_function_calls(content, known_tools):
    """Return (calls, remaining_text).

    calls: list of {"name": str, "arguments": dict} in order of appearance.
    remaining_text: content with the parsed call markup removed.
    Only calls whose name is in known_tools are extracted.
    """
    if not content or not known_tools:
        return [], content or ""
    text = content
    calls = []
    spans = []  # (start, end) spans to remove from text

    def _collect(pattern, kind):
        for m in pattern.finditer(text):
            body = m.group(1)
            if kind == "function_call":
                nm = _NAME_RE.search(body)
                ag = _ARGS_RE.search(body)
                if not nm:
                    continue
                name = nm.group(1).strip()
                args_raw = ag.group(1) if ag else ""
            else:  # tool_call with JSON body
                try:
                    payload = json.loads(body.strip())
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(payload, dict):
                    continue
                name = str(payload.get("name", "")).strip()
                args_raw = payload.get("arguments", {})
                if isinstance(args_raw, dict):
                    args = args_raw
                    if name in known_tools:
                        calls.append(
                            {"name": name, "arguments": args, "_span": m.span()}
                        )
                    continue
                args_raw = args_raw if isinstance(args_raw, str) else json.dumps(args_raw)
            if name not in known_tools:
                continue
            args = _parse_args_text(args_raw, name)
            if args is None:
                continue
            calls.append({"name": name, "arguments": args, "_span": m.span()})

    _collect(_FUNCTION_CALL_RE, "function_call")
    _collect(_TOOL_CALL_RE, "tool_call")
    calls.sort(key=lambda c: c["_span"][0])
    spans = [c["_span"] for c in calls]
    # Rebuild remaining text without the removed spans.
    remaining_parts = []
    pos = 0
    for start, end in spans:
        remaining_parts.append(text[pos:start])
        pos = end
    remaining_parts.append(text[pos:])
    remaining = "".join(remaining_parts)
    # JSON-object calls (fenced ```json {"name":..,"arguments":..} or bare)
    # in whatever text is left after XML extraction.
    json_calls, json_spans = _collect_json_calls(remaining, known_tools)
    if json_calls:
        calls.extend(json_calls)
        parts = []
        pos = 0
        for start, end in sorted(json_spans):
            parts.append(remaining[pos:start])
            pos = end
        parts.append(remaining[pos:])
        remaining = "".join(parts)
    if not calls:
        return [], content
    # Drop a lone <response> wrapper / lone code fence left behind.
    stripped = remaining.strip()
    fence = _FENCE_RE.match(stripped)
    if fence:
        stripped = fence.group(1).strip()
    wrap = _RESPONSE_WRAP_RE.match(stripped)
    if wrap:
        stripped = wrap.group(1).strip()
    for c in calls:
        c.pop("_span", None)
    return calls, stripped


# Argument-key aliases. The harness sends tools WITHOUT a JSON parameter
# schema (parameters: {type: "object", additionalProperties: true}), so the
# model invents key names. Its own normalizers already accept several
# aliases (path/file_path, oldText/old_text, ...); the shim extends that
# same idea to the aliases the model actually emits (observed 15/11:
# search_text/replace_text for edit). Only fills in a canonical key when
# it is ABSENT; never overwrites a key the model provided, never touches
# values.
_ARG_ALIASES = {
    "read": {"path": ["file_path", "file", "filename", "filepath"]},
    "write": {
        "path": ["file_path", "file", "filename", "filepath"],
        "content": ["text", "file_content", "data", "file_text"],
    },
    "edit": {
        "path": ["file_path", "file", "filename", "filepath"],
        "old_text": [
            "oldText", "old", "search_text", "search", "find",
            "original_text", "old_string", "oldTextContent", "target",
        ],
        "new_text": [
            "newText", "new", "replace_text", "replace", "replacement",
            "new_string", "replacement_text", "newTextContent",
        ],
    },
    "bash": {"command": ["command_line", "cmd", "shell_command", "script"]},
    "ls": {"path": ["file_path", "file", "filename", "filepath"]},
    "find": {
        "path": ["file_path", "file", "filename", "filepath"],
        "query": ["pattern", "search", "text"],
    },
    "grep": {
        "path": ["file_path", "file", "filename", "filepath"],
        "query": ["pattern", "search", "text"],
    },
}


def _normalize_tool_args(tool_name, args):
    """Rename alias keys to canonical keys. Returns (new_args, n_renamed)."""
    mapping = _ARG_ALIASES.get(tool_name)
    if not mapping or not isinstance(args, dict):
        return args, 0
    out = dict(args)
    renamed = 0
    for canonical, aliases in mapping.items():
        if canonical in out:
            continue
        for alias in aliases:
            if alias in out:
                out[canonical] = out.pop(alias)
                renamed += 1
                break
    return out, renamed


def _normalize_existing_tool_calls(message, known_tools):
    """Normalize argument keys of tool_calls vLLM parsed natively."""
    renamed_total = 0
    for tc in message.get("tool_calls") or []:
        fn = tc.get("function") or {}
        name = fn.get("name")
        if name not in known_tools:
            continue
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except (json.JSONDecodeError, ValueError):
            continue
        new_args, renamed = _normalize_tool_args(name, args)
        if renamed:
            fn["arguments"] = json.dumps(new_args)
            renamed_total += renamed
    return renamed_total


def transform_chat_completion(body, known_tools):
    """Rewrite a vLLM chat.completion body: XML/JSON text calls -> tool_calls.

    Returns (new_body, n_calls, n_normalized). n_calls counts tool calls the
    shim created from text; n_normalized counts argument keys renamed to the
    canonical names the harness accepts. If vLLM already parsed tool_calls,
    only key normalization applies (values untouched).
    """
    try:
        choices = body.get("choices") or []
        if not choices:
            return body, 0, 0
        message = choices[0].get("message") or {}
        if message.get("tool_calls"):
            n_norm = _normalize_existing_tool_calls(message, known_tools)
            return body, 0, n_norm
        content = message.get("content") or ""
        calls, remaining = extract_function_calls(content, known_tools)
        if not calls:
            return body, 0, 0
        tool_calls = []
        n_norm = 0
        for call in calls:
            args, renamed = _normalize_tool_args(call["name"], call["arguments"])
            n_norm += renamed
            tool_calls.append(
                {
                    "id": "call_shim_%s" % uuid.uuid4().hex[:12],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(args),
                    },
                }
            )
        message["content"] = remaining if remaining else None
        message["tool_calls"] = tool_calls
        choices[0]["finish_reason"] = "tool_calls"
        return body, len(tool_calls), n_norm
    except Exception:
        return body, 0, 0


def synthesize_sse_chunks(body):
    """Build SSE `data:` lines for a (possibly transformed) completion body."""
    resp_id = body.get("id", "chatcmpl-shim")
    created = body.get("created", int(time.time()))
    model = body.get("model", MODEL_NAME)
    choices = body.get("choices") or [{}]
    choice = choices[0]
    message = choice.get("message") or {}
    finish = choice.get("finish_reason") or "stop"
    content = message.get("content") or ""
    tool_calls = message.get("tool_calls") or []

    def chunk(delta, finish_reason=None):
        payload = {
            "id": resp_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": delta,
                    "finish_reason": finish_reason,
                }
            ],
        }
        return "data: %s\n\n" % json.dumps(payload)

    lines = []
    first_delta = {"role": "assistant"}
    if content:
        first_delta["content"] = content
    lines.append(chunk(first_delta))
    for i, tc in enumerate(tool_calls):
        fn = tc.get("function") or {}
        lines.append(
            chunk(
                {
                    "tool_calls": [
                        {
                            "index": i,
                            "id": tc.get("id"),
                            "type": "function",
                            "function": {"name": fn.get("name"), "arguments": ""},
                        }
                    ]
                }
            )
        )
        lines.append(
            chunk(
                {
                    "tool_calls": [
                        {
                            "index": i,
                            "function": {"arguments": fn.get("arguments", "")},
                        }
                    ]
                }
            )
        )
    final_delta = {}
    usage = body.get("usage")
    final_payload = {
        "id": resp_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": final_delta, "finish_reason": finish}],
    }
    if usage:
        final_payload["usage"] = usage
    lines.append("data: %s\n\n" % json.dumps(final_payload))
    lines.append("data: [DONE]\n\n")
    return "".join(lines)


# =============================================================================
# 3. Container Image
# =============================================================================
vllm_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.0-devel-ubuntu22.04", add_python="3.12"
    )
    .entrypoint([])
    .pip_install(
        "vllm>=0.6.3,<1.0",
        "torch>=2.4.0",
        "transformers>=4.45.0",
        "huggingface_hub",
        "hf-transfer",
        "fastapi[standard]",
        "httpx",
    )
    .env(
        {
            "HF_XET_HIGH_PERFORMANCE": "1",
            "VLLM_ATTENTION_BACKEND": "FLASHINFER",
        }
    )
)

# =============================================================================
# 4. Volumes
# =============================================================================
hf_cache_vol = modal.Volume.from_name("hf-cache-helix", create_if_missing=True)
adapters_vol = modal.Volume.from_name(
    ADAPTERS_VOLUME_NAME, create_if_missing=True
)

# =============================================================================
# 5. Application & Server Class
# =============================================================================
app = modal.App("helix-vllm-engine")

_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "content-length",
}


def _filtered_headers(headers):
    return {k: v for k, v in headers.items() if k.lower() not in _HOP_BY_HOP}


@app.cls(
    image=vllm_image,
    gpu="A10G",
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        ADAPTERS_MOUNT_PATH: adapters_vol,
    },
    timeout=60 * 60,
    scaledown_window=180,
    max_containers=1,
)
@modal.concurrent(max_inputs=64)
class VLLMServer:
    """Modal class wrapping a vLLM OpenAI-compatible subprocess."""

    @modal.enter()
    def start_engine(self):
        # O2-CLEAN: serve all three adapters. The clean + realtool adapters
        # are REQUIRED (fail loud if missing); the round-2 adapter is
        # included when present so the deployment keeps the full serving list.
        modules = []
        for subdir, name in ((LORA_ADAPTER_SUBDIR, LORA_ADAPTER_NAME),
                             (REALTOOL_ADAPTER_SUBDIR, REALTOOL_ADAPTER_NAME),
                             (CLEAN_ADAPTER_SUBDIR, CLEAN_ADAPTER_NAME)):
            lora_path = os.path.join(ADAPTERS_MOUNT_PATH, subdir)
            if os.path.isfile(os.path.join(lora_path, "adapter_config.json")):
                modules.append((name, lora_path))
        self.served_adapters = [name for name, _ in modules]
        self.lora_enabled = bool(modules)
        if REALTOOL_ADAPTER_NAME not in self.served_adapters:
            raise RuntimeError(
                f"REBUILD-FIX adapter missing: {REALTOOL_ADAPTER_SUBDIR} "
                "not found on the adapters volume; refusing to serve."
            )
        if CLEAN_ADAPTER_NAME not in self.served_adapters:
            raise RuntimeError(
                f"O2-CLEAN adapter missing: {CLEAN_ADAPTER_SUBDIR} "
                "not found on the adapters volume; refusing to serve."
            )

        cmd = [
            "vllm", "serve", MODEL_NAME,
            "--host", "0.0.0.0",
            "--port", str(VLLM_PORT),
            "--tensor-parallel-size", "1",
            "--max-model-len", "8192",
            "--gpu-memory-utilization", "0.90",
            "--enforce-eager",
            "--trust-remote-code",
            "--uvicorn-log-level", "warning",
            # Same parser flags as the 12/11 smoke copy: the harness sends
            # tools with implicit auto tool choice; without these vLLM 400s.
            "--enable-auto-tool-choice",
            "--tool-call-parser", "hermes",
        ]

        if self.lora_enabled:
            print(
                f"[REBUILD] LoRA adapters detected: {modules}. "
                "Enabling multi-LoRA serving."
            )
            cmd += [
                "--enable-lora",
                "--max-loras", "3",
                "--max-lora-rank", "64",
                "--lora-modules",
            ] + [f"{name}={path}" for name, path in modules]
        else:
            print(
                f"[BUILD] No LoRA adapter found under {ADAPTERS_MOUNT_PATH}. "
                f"Serving base model: {MODEL_NAME}"
            )

        print(f"[vLLM] Command: {' '.join(cmd)}")
        self.log_path = "/tmp/vllm.log"
        self.log_file = open(self.log_path, "w", encoding="utf-8")
        self.proc = subprocess.Popen(
            cmd,
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
        )

        import urllib.error
        import urllib.request

        health_url = f"http://localhost:{VLLM_PORT}/health"
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(health_url, timeout=2) as resp:
                    if resp.status == 200:
                        print("[vLLM] Engine ready - accepting requests.")
                        return
            except (urllib.error.URLError, OSError):
                pass
            if self.proc.poll() is not None:
                self.log_file.flush()
                err_output = ""
                try:
                    with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                        err_output = f.read()
                except Exception as read_err:
                    err_output = f"Could not read log file: {read_err}"
                print("=" * 60)
                print(f"[vLLM CRASH LOGS] exit code {self.proc.returncode}:")
                print(err_output)
                print("=" * 60)
                raise RuntimeError(
                    f"vLLM exited prematurely (code {self.proc.returncode}).\n"
                    f"Last log output:\n{err_output[-2000:]}"
                )
            time.sleep(2)
        raise TimeoutError("vLLM did not become healthy within 5 minutes.")

    @modal.asgi_app()
    def serve(self):
        import fastapi
        import httpx

        web_app = fastapi.FastAPI(
            title="HELIX vLLM Gateway (rebuild step 1)",
            description="OpenAI-compatible endpoint for HELIX Closed-Loop",
        )
        target = f"http://localhost:{VLLM_PORT}"

        @web_app.get("/")
        async def root():
            return {
                "status": "ok",
                "model": MODEL_NAME,
                "lora_enabled": self.lora_enabled,
                "adapter": LORA_ADAPTER_NAME if self.lora_enabled else None,
                "adapters": list(getattr(self, "served_adapters", [])),
                "shim_enabled": ENABLE_TOOLCALL_SHIM,
            }

        @web_app.get("/health")
        async def health():
            async with httpx.AsyncClient(base_url=target, timeout=5.0) as client:
                try:
                    resp = await client.get("/health")
                    if resp.status_code == 200:
                        return fastapi.responses.JSONResponse(
                            status_code=200,
                            content={
                                "status": "ok",
                                "lora_enabled": self.lora_enabled,
                                "adapter": LORA_ADAPTER_NAME if self.lora_enabled else None,
                                "adapters": list(getattr(self, "served_adapters", [])),
                                "shim_enabled": ENABLE_TOOLCALL_SHIM,
                            },
                        )
                    return fastapi.responses.Response(
                        content=resp.content,
                        status_code=resp.status_code,
                        headers=_filtered_headers(resp.headers),
                    )
                except Exception as e:
                    return fastapi.responses.JSONResponse(
                        status_code=503,
                        content={"status": "error", "message": str(e)},
                    )

        @web_app.api_route(
            "/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
        )
        async def proxy(path: str, request: fastapi.Request):
            body = await request.body()
            is_chat = path == "v1/chat/completions" and request.method == "POST"
            if is_chat:
                return await self._chat_completions(request, body, target)
            # Generic passthrough with hop-by-hop headers filtered (this is
            # what broke SSE framing on 12/11 when headers were copied raw).
            async with httpx.AsyncClient(base_url=target, timeout=120.0) as client:
                url = httpx.URL(
                    path=f"/{path}",
                    query=request.url.query.encode("utf-8")
                    if request.url.query
                    else None,
                )
                headers = dict(request.headers)
                headers.pop("host", None)
                rp = await client.request(
                    request.method, url, headers=headers, content=body
                )
            return fastapi.responses.Response(
                content=rp.content,
                status_code=rp.status_code,
                headers=_filtered_headers(rp.headers),
            )

        return web_app

    async def _chat_completions(self, request, body, target):
        """Buffered chat-completions path (fixes the 12/11 streaming bug).

        Calls vLLM with stream=false, optionally applies the tool-call shim,
        then answers the client in the shape it asked for (SSE re-emit for
        stream=true, JSON for stream=false) with clean headers.
        """
        import fastapi
        import httpx

        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        want_stream = bool(payload.get("stream"))
        known_tools = []
        for tool in payload.get("tools") or []:
            fn = (tool or {}).get("function") or {}
            if fn.get("name"):
                known_tools.append(fn["name"])
        payload["stream"] = False

        async with httpx.AsyncClient(base_url=target, timeout=300.0) as client:
            rp = await client.post(
                "/v1/chat/completions",
                content=json.dumps(payload).encode("utf-8"),
                headers={"content-type": "application/json"},
            )
        if rp.status_code != 200:
            return fastapi.responses.Response(
                content=rp.content,
                status_code=rp.status_code,
                headers=_filtered_headers(rp.headers),
                media_type="application/json",
            )
        try:
            resp_body = json.loads(rp.content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return fastapi.responses.Response(
                content=rp.content,
                status_code=rp.status_code,
                headers=_filtered_headers(rp.headers),
                media_type="application/json",
            )

        n_calls = 0
        n_norm = 0
        if ENABLE_TOOLCALL_SHIM and known_tools:
            resp_body, n_calls, n_norm = transform_chat_completion(
                resp_body, known_tools
            )
        print(
            "[proxy] chat_completions model=%s tools=%s stream=%s shim_calls=%d normalized_keys=%d"
            % (
                payload.get("model"),
                ",".join(known_tools) or "-",
                want_stream,
                n_calls,
                n_norm,
            ),
            flush=True,
        )
        if n_calls:
            shim_header = "transformed=%d" % n_calls
        elif n_norm:
            shim_header = "normalized=%d" % n_norm
        else:
            shim_header = "passthrough"
        if want_stream:
            sse_text = synthesize_sse_chunks(resp_body)

            async def _gen():
                yield sse_text.encode("utf-8")

            return fastapi.responses.StreamingResponse(
                _gen(),
                status_code=200,
                headers={
                    "content-type": "text/event-stream",
                    "cache-control": "no-cache",
                    "x-accel-buffering": "no",
                    "x-helix-shim": shim_header,
                },
            )
        return fastapi.responses.JSONResponse(
            content=resp_body,
            status_code=200,
            headers={"x-helix-shim": shim_header},
        )

    @modal.exit()
    def stop_engine(self):
        if hasattr(self, "proc") and self.proc.poll() is None:
            print("[vLLM] Sending SIGTERM ...")
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("[vLLM] Force-killing process.")
                self.proc.kill()
        if hasattr(self, "log_file") and not self.log_file.closed:
            self.log_file.close()
        print("[vLLM] Shutdown complete.")


@app.local_entrypoint()
def smoke_test():
    print("Rebuild step 1 variant A. Deploy with:")
    print("  modal deploy <this file>")
    print("Then point the HELIX CLI at the deployment URL + /v1.")
