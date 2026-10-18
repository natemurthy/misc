#!/usr/bin/env python3
"""Classify each rgb_NN.txt hex color as mostly red, green, or blue via the
TypeSafe System One API (choice primitive). Writes one JSONL line per color.

Modes (--mode):
  sequential  one request per color, one after another
  threads     one request per color, fanned out across I/O threads
  batch       ONE request: all colors in `state`, one choice question per color

Outputs (same directory as this script):
  rgb_typesafe_requests.jsonl   - request body/bodies sent
  rgb_typesafe_responses.jsonl  - one line per color with answer + timing
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
API_URL = "https://api.typesafe.ai/v1/systemone"
API_KEY = os.environ.get("TYPESAFE_API_KEY")
MODEL = "jev-latest"

CRITERIA = {
    "red": "The red (R) channel is the largest of the three.",
    "green": "The green (G) channel is the largest of the three.",
    "blue": "The blue (B) channel is the largest of the three.",
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


def single_request(c: dict) -> dict:
    return {
        "model": MODEL,
        "state": {"hex": c["hex"], "channels_0_to_255": c["channels"]},
        "questions": {
            "dominant_channel": {
                "type": "choice",
                "instructions": (
                    "Which single color channel dominates this RGB color? "
                    "Judge from `hex` (format #RRGGBB) and the decoded "
                    "`channels_0_to_255` values."
                ),
                "criteria": CRITERIA,
            }
        },
    }


def batch_request(colors: list[dict]) -> dict:
    """All colors in one state object; one choice question per color."""
    state = {
        f"color_{c['index']}": {"hex": c["hex"], "channels_0_to_255": c["channels"]}
        for c in colors
    }
    questions = {
        f"dominant_{c['index']}": {
            "type": "choice",
            "instructions": (
                f"Which single color channel dominates the RGB color in "
                f"`color_{c['index']}`? Judge from its `hex` (format #RRGGBB) "
                f"and decoded `channels_0_to_255`. Ignore the other colors."
            ),
            "criteria": CRITERIA,
        }
        for c in colors
    }
    return {"model": MODEL, "state": state, "questions": questions}


def call_api(body: dict, retries: int = 5) -> tuple[dict, float]:
    """Returns (response_json, elapsed_ms)."""
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    delay = 1.0
    t0 = time.perf_counter()
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read()), (time.perf_counter() - t0) * 1000
        except urllib.error.HTTPError as e:
            if e.code in (429, 529) and attempt < retries - 1:
                time.sleep(delay); delay *= 2; continue
            return ({"error": {"status": e.code, "body": e.read().decode(errors="replace")}},
                    (time.perf_counter() - t0) * 1000)
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(delay); delay *= 2; continue
            return {"error": {"status": None, "body": str(e)}}, (time.perf_counter() - t0) * 1000


def result_line(c: dict, answer: dict, resp: dict, elapsed_ms: float, mode: str, request_ref) -> dict:
    chosen = answer.get("choice")
    expected = code_dominant(c["channels"])
    return {
        **c,
        "mode": mode,
        "code_dominant": expected,
        "request": request_ref,
        "answer": answer,
        "agrees_with_code": (chosen == expected) if chosen else None,
        "error": resp.get("error"),
        "elapsed_ms": round(elapsed_ms, 1),
    }


def run(mode: str, workers: int) -> None:
    colors = load_colors()
    req_out = HERE / "rgb_typesafe_requests.jsonl"
    resp_out = HERE / "rgb_typesafe_responses.jsonl"
    lines: list[dict] = []
    t_start = time.perf_counter()

    if mode == "batch":
        body = batch_request(colors)
        resp, ms = call_api(body)
        answers = resp.get("answers", {})
        for c in colors:
            ans = answers.get(f"dominant_{c['index']}", {})
            lines.append(result_line(c, ans, resp, ms, mode, {"batch_question_id": f"dominant_{c['index']}"}))
        usage = resp.get("usage", {})
        req_records = [{"mode": mode, "request": body, "response_model": resp.get("model"),
                        "usage": usage, "elapsed_ms": round(ms, 1)}]
        per_call = [ms]
    else:
        bodies = [single_request(c) for c in colors]

        def one(i: int):
            resp, ms = call_api(bodies[i])
            return i, resp, ms

        if mode == "threads":
            with ThreadPoolExecutor(max_workers=workers) as ex:
                results = list(ex.map(one, range(len(colors))))
        else:
            results = [one(i) for i in range(len(colors))]

        req_records, per_call, usage = [], [], {"input_tokens": 0, "output_tokens": 0}
        for i, resp, ms in results:
            c = colors[i]
            ans = resp.get("answers", {}).get("dominant_channel", {})
            lines.append(result_line(c, ans, resp, ms, mode, bodies[i]))
            req_records.append({"mode": mode, "index": c["index"], "request": bodies[i],
                                "response_model": resp.get("model"), "usage": resp.get("usage"),
                                "elapsed_ms": round(ms, 1)})
            per_call.append(ms)
            for k in usage:
                usage[k] += (resp.get("usage") or {}).get(k, 0)

    wall_ms = (time.perf_counter() - t_start) * 1000
    with req_out.open("w") as f:
        for r in req_records:
            f.write(json.dumps(r) + "\n")
    with resp_out.open("w") as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")

    agree = sum(1 for l in lines if l["agrees_with_code"])
    errors = sum(1 for l in lines if l["error"])
    srt = sorted(per_call)
    print(f"mode={mode} colors={len(colors)} agree={agree} errors={errors} "
          f"api_calls={len(per_call)} tokens_in={usage.get('input_tokens')} tokens_out={usage.get('output_tokens')}")
    print(f"per-call ms: min={srt[0]:.0f} median={srt[len(srt)//2]:.0f} max={srt[-1]:.0f} "
          f"sum={sum(srt):.0f} | wall={wall_ms:.0f} ms")


if __name__ == "__main__":
    if not API_KEY:
        sys.exit("TYPESAFE_API_KEY is not set")
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["sequential", "threads", "batch"], default="batch")
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    run(a.mode, a.workers)
