#!/usr/bin/env python3
"""Classify each rgb_NN.txt hex color as mostly red, green, or blue via the
Claude API, mirroring rgb_typesafe.py. Uses structured outputs (JSON schema
with an enum) as the analog of TypeSafe's choice primitive.

Modes (--mode):
  sequential  one request per color, one after another
  threads     one request per color, fanned out across I/O threads
  batch       ONE request: all colors in the prompt, one JSON array back
  all         run all three and print a comparison table

Outputs (same directory as this script):
  rgb_claude_requests.jsonl          - request body/bodies sent (last mode run)
  rgb_claude_responses.jsonl         - one line per color (last mode run)
  rgb_claude_responses.<mode>.jsonl  - per-mode copies when --mode all
"""
import argparse
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
CHOICES = ["red", "green", "blue"]

SYSTEM = (
    "You classify RGB colors by dominant channel. Answer only with the JSON "
    "requested. The dominant channel is the one with the largest 0-255 value."
)

SINGLE_SCHEMA = {
    "type": "object",
    "properties": {"choice": {"type": "string", "enum": CHOICES}},
    "required": ["choice"],
    "additionalProperties": False,
}

BATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "string"},
                    "choice": {"type": "string", "enum": CHOICES},
                },
                "required": ["index", "choice"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def parse_hex(h: str) -> dict:
    h = h.strip().lstrip("#")
    return {"r": int(h[0:2], 16), "g": int(h[2:4], 16), "b": int(h[4:6], 16)}


def code_dominant(ch: dict) -> str:
    return {"r": "red", "g": "green", "b": "blue"}[max(ch, key=ch.get)]


def load_colors() -> list[dict]:
    out = []
    for f in sorted(HERE.glob("rgb_[0-9][0-9].txt")):
        hex_value = f.read_text().strip()
        out.append({"index": f.stem.split("_")[1], "file": f.name,
                    "hex": hex_value, "channels": parse_hex(hex_value)})
    return out


def base_params(model: str, effort: str, max_tokens: int, fallbacks: bool) -> dict:
    p = {
        "model": model,
        "max_tokens": max_tokens,
        "system": SYSTEM,
        "output_config": {"effort": effort},
    }
    if fallbacks:
        p["betas"] = ["server-side-fallback-2026-07-01"]
        p["fallbacks"] = "default"
    return p


def single_request(c: dict, **kw) -> dict:
    p = base_params(max_tokens=4096, **kw)
    p["output_config"]["format"] = {"type": "json_schema", "schema": SINGLE_SCHEMA}
    p["messages"] = [{"role": "user", "content": json.dumps({
        "hex": c["hex"], "channels_0_to_255": c["channels"],
        "question": "Which single color channel dominates this RGB color: red, green, or blue?",
    })}]
    return p


def batch_request(colors: list[dict], **kw) -> dict:
    p = base_params(max_tokens=16000, **kw)
    p["output_config"]["format"] = {"type": "json_schema", "schema": BATCH_SCHEMA}
    p["messages"] = [{"role": "user", "content": json.dumps({
        "colors": [{"index": c["index"], "hex": c["hex"], "channels_0_to_255": c["channels"]}
                   for c in colors],
        "question": ("For EACH color, which single channel dominates: red, green, or blue? "
                     "Return one result per input index, in input order."),
    })}]
    return p


class Caller:
    """Own retry loop (SDK retries off) so 429s/529s can be counted."""

    def __init__(self, use_beta: bool, retries: int = 6):
        self.client = anthropic.Anthropic(max_retries=0)
        self.use_beta = use_beta
        self.retries = retries

    def __call__(self, params: dict) -> tuple[dict | None, dict]:
        api = self.client.beta.messages if self.use_beta else self.client.messages
        meta = {"rate_limited": 0, "overloaded": 0, "other_retries": 0, "error": None}
        delay = 1.0
        t0 = time.perf_counter()
        for attempt in range(self.retries):
            try:
                resp = api.create(**params)
                meta["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
                return resp, meta
            except anthropic.RateLimitError as e:
                meta["rate_limited"] += 1
                ra = e.response.headers.get("retry-after")
                wait = float(ra) if ra else delay
            except anthropic.APIStatusError as e:
                if e.status_code == 529:
                    meta["overloaded"] += 1
                elif e.status_code >= 500:
                    meta["other_retries"] += 1
                else:
                    meta["error"] = {"status": e.status_code, "message": e.message}
                    break
                wait = delay
            except anthropic.APIConnectionError as e:
                meta["other_retries"] += 1
                meta["error"] = {"status": None, "message": str(e)}
                wait = delay
            if attempt == self.retries - 1:
                break
            time.sleep(wait)
            delay = min(delay * 2, 30)
        meta["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        if meta["error"] is None:
            meta["error"] = {"status": 429, "message": "retries exhausted"}
        return None, meta


def extract_json(resp) -> dict:
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


def resp_summary(resp) -> dict:
    if resp is None:
        return {}
    u = resp.usage
    return {
        "id": resp.id, "model": resp.model, "stop_reason": resp.stop_reason,
        "usage": {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                  "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0),
                  "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0)},
        "thinking_blocks": sum(1 for b in resp.content if b.type == "thinking"),
    }


def run(mode: str, model: str, effort: str, workers: int, fallbacks: bool) -> dict:
    colors = load_colors()
    call = Caller(use_beta=fallbacks)
    kw = {"model": model, "effort": effort, "fallbacks": fallbacks}
    lines, req_records = [], []
    usage = {"input_tokens": 0, "output_tokens": 0}
    rl = {"rate_limited": 0, "overloaded": 0, "other_retries": 0}
    t_start = time.perf_counter()

    def mk_line(c, chosen, resp, meta, request_ref):
        expected = code_dominant(c["channels"])
        return {**c, "mode": mode, "code_dominant": expected, "request": request_ref,
                "answer": {"choice": chosen}, "response": resp_summary(resp),
                "agrees_with_code": (chosen == expected) if chosen else None,
                "error": meta.get("error"), "retries": {k: meta[k] for k in rl},
                "elapsed_ms": meta["elapsed_ms"]}

    if mode == "batch":
        body = batch_request(colors, **kw)
        resp, meta = call(body)
        by_index = {}
        if resp is not None:
            try:
                by_index = {r["index"]: r["choice"] for r in extract_json(resp)["results"]}
            except Exception as e:  # noqa: BLE001
                meta["error"] = {"status": None, "message": f"parse: {e}"}
        for c in colors:
            lines.append(mk_line(c, by_index.get(c["index"]), resp, meta,
                                 {"batch_result_index": c["index"]}))
        if resp is not None:
            usage = {k: getattr(resp.usage, k) for k in usage}
        for k in rl:
            rl[k] += meta[k]
        req_records.append({"mode": mode, "request": body, "response": resp_summary(resp),
                            "retries": {k: meta[k] for k in rl}, "elapsed_ms": meta["elapsed_ms"]})
        per_call = [meta["elapsed_ms"]]
    else:
        bodies = [single_request(c, **kw) for c in colors]

        def one(i):
            resp, meta = call(bodies[i])
            return i, resp, meta

        if mode == "threads":
            with ThreadPoolExecutor(max_workers=workers) as ex:
                results = list(ex.map(one, range(len(colors))))
        else:
            results = [one(i) for i in range(len(colors))]

        per_call = []
        for i, resp, meta in results:
            c = colors[i]
            chosen = None
            if resp is not None:
                try:
                    chosen = extract_json(resp)["choice"]
                except Exception as e:  # noqa: BLE001
                    meta["error"] = {"status": None, "message": f"parse: {e}"}
                for k in usage:
                    usage[k] += getattr(resp.usage, k)
            for k in rl:
                rl[k] += meta[k]
            lines.append(mk_line(c, chosen, resp, meta, bodies[i]))
            req_records.append({"mode": mode, "index": c["index"], "request": bodies[i],
                                "response": resp_summary(resp), "retries": {k: meta[k] for k in rl},
                                "elapsed_ms": meta["elapsed_ms"]})
            per_call.append(meta["elapsed_ms"])

    wall_ms = (time.perf_counter() - t_start) * 1000
    with (HERE / "rgb_claude_requests.jsonl").open("w") as f:
        for r in req_records:
            f.write(json.dumps(r) + "\n")
    with (HERE / "rgb_claude_responses.jsonl").open("w") as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")

    srt = sorted(per_call)
    summary = {
        "mode": mode, "model": lines[0]["response"].get("model") or model, "effort": effort,
        "api_calls": len(per_call), "wall_ms": round(wall_ms),
        "min_ms": round(srt[0]), "median_ms": round(srt[len(srt) // 2]), "max_ms": round(srt[-1]),
        "tokens_in": usage["input_tokens"], "tokens_out": usage["output_tokens"],
        "correct": sum(1 for l in lines if l["agrees_with_code"]),
        "errors": sum(1 for l in lines if l["error"]),
        **{f"{k}_429s" if k == "rate_limited" else k: v for k, v in rl.items()},
    }
    print(json.dumps(summary))
    return summary


def table(rows: list[dict]) -> str:
    hdr = ["Mode", "API calls", "Wall clock", "Per-call median", "Per-call max",
           "Tokens in", "Tokens out", "Correct", "429s", "Errors"]
    out = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in [
            r["mode"], r["api_calls"], f"{r['wall_ms']/1000:.2f} s",
            f"{r['median_ms']} ms", f"{r['max_ms']} ms", f"{r['tokens_in']:,}",
            f"{r['tokens_out']:,}", f"{r['correct']}/32", r["rate_limited_429s"], r["errors"]]) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["sequential", "threads", "batch", "all"], default="all")
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--no-fallbacks", action="store_true",
                    help="disable server-side refusal fallbacks (beta)")
    a = ap.parse_args()
    fb = not a.no_fallbacks
    modes = ["sequential", "threads", "batch"] if a.mode == "all" else [a.mode]
    rows = []
    for m in modes:
        rows.append(run(m, a.model, a.effort, a.workers, fb))
        if a.mode == "all":
            shutil.copy(HERE / "rgb_claude_responses.jsonl", HERE / f"rgb_claude_responses.{m}.jsonl")
    if len(rows) > 1:
        print("\n" + table(rows))
