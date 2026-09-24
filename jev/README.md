# Jev (TypeSafe) vs Claude on a 32-color classification

## Summary

I asked Claude to spin up 32 subagents to generate 32 random rgb hex codes and then used the TypeSafe plugin to ask Jev to classify them as mostly red, green, or blue using its choice primitive and did the same with Claude.

Some results below:point_down::skin-tone-5: The speed and consistency are the most notable aspects, see tradeoffs between individual API requests for one batched request.

Comparing the results: Jev was **13x faster** than Claude in one batched request, **28x faster** when making single API requests in parallel (and succeeded in API requests, whereas Claude hit rate limit errors nearly two-thirds of requests). Single sequential per request median with Jev was about `300 ms` compared to Claude at `1.8 sec`

## Method

### 1. Generate the colors

I prompted Claude in my CLI with:

```sh
> Using the maximum number of sub agents configured for this claude code CLI,
pls generate 32 handom rgb values in hex format and write to file rgb_NN.txt
where NN is the agent index on the inclusive range [01..32]. Afer all the
agents done, pls calc the SHA256 sum of all these rgb values in hex format.
```

32 Claude Code subagents (Haiku 4.5) were launched, one per index `01..32`. Each ran

```sh
printf '#%02X%02X%02X\n' $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)) > rgb_NN.txt
```

then `cat` the file and reported the value back. A two-tool-call task that should take 10-20 s.

SHA256 of the 32 files concatenated in index order, each `#RRGGBB\n`:

```
b5a121aff37c3c348ae76a3ff693d2695d4df5f7a3c4576d9c2c101440a52df2
```

#### Subagent run stats

Collected from the harness completion notifications for all 32 agents.

| Stat | Value |
|---|---|
| Subagents completed | 32 / 32 |
| Launch attempts | 59 (32 succeeded, 27 rejected by the harness concurrency cap) |
| Concurrency cap | 8 (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=8`) |
| Tool calls per agent | 2 (three agents made 3), 67 total |
| Tokens per agent | 13,469 - 13,963, mean 13,635, total 436,321 |
| Duration, min | 10.1 s |
| Duration, median | 21.6 s |
| Duration, mean | 40.5 s |
| Duration, p90 | 88.5 s |
| Duration, max | 194.0 s (agent 03) |
| Agents finishing in 30 s or less | 20 |
| Agents taking 30-60 s | 5 |
| Agents taking over 60 s | 7 (03: 194 s, 22: 119 s, 24: 113 s, 06: 93 s, 20: 88 s, 10: 84 s, 13: 64 s) |
| Sum of agent durations | 1,296.7 s (about 21.6 min of agent time) |

Every agent did the same two tool calls and used within 4% of the same token count, yet durations spanned 10 s to 194 s. The spread is not the work; it is waiting.

#### Two different limits were in play

**1. Harness concurrency cap (not an API error).** All 32 agents were launched in one tool call. The first 8 started; the other 24 were rejected instantly with:

```
Concurrent subagent limit reached. You can run 8 subagents at once. Do not retry.
If the user wants more concurrent subagents, ask them to increase CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS.
```

Three later launches (agents 19 and 20, twice) hit the same cap before slots freed. These 27 rejections never reached the Anthropic API. Every rejected agent was relaunched once a slot opened, so no work was lost, but the fan-out ran as rolling batches of 8 rather than 32 at once.

**2. API concurrent-connections cap (the real 429).** Even with only 8 subagents live, 7 of 32 agents took over a minute for a 10-second task. The orchestrating session never saw the API errors directly, because subagent transcripts are not surfaced to it, only their final reports. The slow agents were the circumstantial evidence: the Anthropic SDK retries 429s automatically with backoff, so a rate-limited agent looks slow rather than failed.

Step 3 below confirmed the cause. A 12-call burst against the API from a plain script returned this on 10 of 12 calls:

```
rate_limit_error: Number of concurrent connections has exceeded your rate limit.
```

This org's cap is about two simultaneous connections. Eight Haiku subagents each holding a streaming connection is four times that, so at any moment most of them are sleeping on a `retry-after`.

#### Which rate-limit regime applies

The session was authenticated with `ANTHROPIC_API_KEY`, so Claude Code billed through the Claude Console and was governed by API Platform limits, not a Team seat allowance. The two regimes differ:

| | API Platform (Console / API key) | Claude Team / Enterprise seat |
|---|---|---|
| Scope | Per organization, per model | Per seat, shared across Claude chat, Cowork, and Claude Code |
| Meters | Requests/min, uncached input tokens/min, output tokens/min, plus a concurrent-connections cap and an acceleration limit on sudden spikes | Rolling 5-hour window plus a weekly window |
| Ceiling set by | Usage tier (Evaluation, Start, Build, Scale, Custom) | Seat tier (Standard or Premium) |
| On exceeding | HTTP 429 `rate_limit_error` with `retry-after`; SDK retries silently | "You've hit your session limit" with a reset time; requests stop |
| Prompt cache TTL | 5 minutes default | 1 hour |
| Where to raise it | Console Rate limits page or contact sales | Admin turns on usage credits and sets spend limits |

Claude Code traffic on an API key lands in an auto-created "Claude Code" workspace that counts toward the org-wide limit. For this experiment the relevant fix is a concurrency increase on the org, not a higher tokens-per-minute tier. Switching to a Team login would remove the per-minute 429s but replace them with a 5-hour seat budget that 32 parallel agents would draw down quickly, and it is not confirmed that subscription logins are free of burst throttling.

### 2. Classify with TypeSafe (`rgb_typesafe.py`)

- Endpoint `POST https://api.typesafe.ai/v1/systemone`, model `jev-latest` (served as `jev-1.13.0`).
- One `choice` question per color with criteria `red`, `green`, `blue`. State carries the hex string plus the decoded 0-255 channels as named fields.
- Three modes: `sequential` (one request per color), `threads` (32 workers, one request per color), `batch` (all 32 colors in one `state` object keyed `color_NN`, 32 questions keyed `dominant_NN`; TypeSafe evaluates independent questions over shared state in parallel server-side).
- Backoff on 429/529. Each response line records `elapsed_ms`, the full answer distribution, `confidence`, and a code-computed `code_dominant` (max channel) for verification.

### 3. Classify with Claude (`rgb_claude.py`)

- Anthropic Python SDK 1.8.0, model `claude-opus-5`, `output_config.effort = "low"`, adaptive thinking (the model default).
- Structured outputs stand in for the choice primitive: a JSON schema whose `choice` field is an enum of `red | green | blue`. Batch mode returns `{results: [{index, choice}, ...]}`.
- Server-side refusal fallbacks (`betas=["server-side-fallback-2026-07-01"], fallbacks="default"`) are on by default; `--no-fallbacks` disables them. They did not trigger.
- SDK auto-retry is off. The script runs its own retry loop (6 attempts, exponential backoff, honors `retry-after`) so 429s and 529s can be counted per call.
- Same three modes as the TypeSafe script, plus `--mode all` which prints a comparison table and keeps per-mode JSONL copies.

Both scripts write one JSONL line per color with the request, the answer, `agrees_with_code`, and timing.

## Results

All 32 colors were classified correctly by both models in every mode that completed. Ground truth is the largest channel computed in code.

### TypeSafe / Jev

| Mode | API calls | Wall clock | Per-call median | Per-call max | Tokens in | Tokens out | Correct | Min confidence |
|---|---|---|---|---|---|---|---|---|
| sequential | 32 | 10.13 s | 307 ms | 477 ms | 13,867 | 1,312 | 32/32 | 0.99 |
| threads (32 workers) | 32 | 1.25 s | 1,027 ms | 1,246 ms | 13,867 | 1,312 | 32/32 | 0.99 |
| batch (1 request) | 1 | 0.50 s | 496 ms | 496 ms | 6,477 | 1,283 | 32/32 | 0.81 |

Batch mode halves input tokens and is the fastest, but confidence dipped below 0.99 on 6 of 32 colors (low 0.81) versus a 0.99 floor when each color had its own request. Answers were still all correct.

### Claude / claude-opus-5, effort low

| Mode | API calls | Wall clock | Per-call median | Per-call max | Tokens in | Tokens out | Correct | 429s | Errors |
|---|---|---|---|---|---|---|---|---|---|
| sequential | 32 | 63.70 s | 1,864 ms | 4,372 ms | 10,829 | 364 | 32/32 | 0 | 0 |
| threads (32 workers) | 32 | 35.47 s | 33,879 ms | 35,463 ms | 3,719 | 125 | 11/32 | 154 | 21 |
| batch (1 request) | 1 | 6.66 s | 6,656 ms | 6,656 ms | 1,985 | 469 | 32/32 | 0 | 0 |

The threads row failed on 21 of 32 colors after six retries each. Its token counts are low because most calls never completed.

### Head-to-head

| | Jev | Claude | Ratio |
|---|---|---|---|
| Batch, one request | 0.50 s | 6.66 s | 13x |
| Threads, 32 workers | 1.25 s (32/32 ok) | 35.47 s (11/32 ok) | 28x |
| Sequential, per-call median | 307 ms | 1,864 ms | 6x |

### Why Claude's threaded run failed: a concurrent-connections cap

The 429 body captured from a 12-call burst (only 2 of 12 succeeded):

```
rate_limit_error: Number of concurrent connections has exceeded your rate limit.
Please try again later or contact sales ... to discuss your options for a rate limit increase.
```

This is a per-organization concurrency cap, separate from the requests-per-minute and tokens-per-minute limits documented for API usage tiers. Responses carried no `anthropic-ratelimit-*` headers, only `anthropic-workspace-id`, so the numeric ceiling could not be read off the wire.

Rerunning Claude threads mode at lower worker counts:

| Workers | Wall clock | 429s | Errors |
|---|---|---|---|
| 2 | 35.0 s | 0 | 0 |
| 4 | 33.5 s | 21 | 0 |
| 8 | 34.3 s | 44 | 0 |
| 32 | 35.5 s | 154 | 21 |

Two concurrent connections is the clean ceiling on this org. Four and eight finish thanks to retries but gain no wall-clock benefit. This same cap is what `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=8` mitigates in Claude Code, and it explains the slow subagents in step 1: the SDK was silently retrying 429s.

## Caveats

- Picking the largest of three integers is deterministic. Both scripts keep the code-computed answer alongside the model's so the JSONL doubles as a validation set. Dropping the decoded channels from the state (hex only) would make the models work harder.
- Claude returns no probabilities, so there is no confidence column for it. The Jev confidence is distribution concentration, not overall correctness.
- Claude ran `claude-opus-5`; a Haiku run (`--model claude-haiku-4-5`) would be the closer speed match to a small System One model. Per-call latency here includes adaptive thinking at low effort.
- Timings are single runs on one machine and one org tier, taken 2026-09-24. Rate-limit behavior is org-specific.

## Files

| File | Contents |
|---|---|
| `rgb_01.txt` .. `rgb_32.txt` | One `#RRGGBB` per file, written by subagent NN |
| `rgb_typesafe.py` | TypeSafe classifier, `--mode sequential\|threads\|batch`, `--workers N` |
| `rgb_typesafe_requests.jsonl`, `rgb_typesafe_responses.jsonl` | Last TypeSafe run (batch) |
| `rgb_typesafe_responses.threads.jsonl`, `.batch.jsonl` | Per-mode copies |
| `rgb_claude.py` | Claude classifier, `--mode sequential\|threads\|batch\|all`, `--model`, `--effort`, `--workers`, `--no-fallbacks` |
| `rgb_claude_requests.jsonl`, `rgb_claude_responses.jsonl` | Last Claude run |
| `rgb_claude_responses.sequential.jsonl`, `.threads.jsonl`, `.batch.jsonl` | Per-mode copies from the 32-worker comparison |

## Reproduce

```sh
export TYPESAFE_API_KEY=...   # TypeSafe
export ANTHROPIC_API_KEY=...  # Claude
pip install anthropic

python3 rgb_typesafe.py --mode sequential
python3 rgb_typesafe.py --mode threads --workers 32
python3 rgb_typesafe.py --mode batch

python3 rgb_claude.py --mode all            # prints the comparison table
python3 rgb_claude.py --mode threads --workers 2
```
