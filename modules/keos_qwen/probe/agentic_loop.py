#!/usr/bin/env python3
"""Does Qwen3-Coder-30B sustain a MULTI-TURN TOOL LOOP, and for how long?

This is the measurement C1 depends on. Everything proven so far is one turn: a
prompt in, an answer out. An agentic loop is a different regime -- the model
must emit a well-formed tool call, receive a result it did not write, keep track
of what it already learned, and do it again with the context growing every turn.
A model can be excellent at the first and useless at the second.

WHAT THIS MEASURES, AND WHAT IT DOES NOT.

It drives the OpenAI-compatible endpoint DIRECTLY, not through the Elixir
harness. That is deliberate: driving the harness would measure harness+model and
give one number for two subjects, and if it failed there would be no way to say
which one failed. So the claim this file can support is about THE MODEL. Whether
the harness's own agent loop also sustains it is a SECOND question, still open,
and this file must not be read as answering it.

THE FIXTURE MAKES THE TURN COUNT A PROPERTY, NOT A HOPE.

The task is a chain: file 1 names file 2, which names file 3, ... and the last
one holds a random token. The token is generated per run from os.urandom, so it
is not in any training set and cannot be guessed, inferred or recalled -- the
ONLY way to produce it is to actually walk the chain. With a chain of depth D the
model cannot finish in fewer than D reads plus one answer, so "it sustained D
turns" is established by construction rather than by inspecting a transcript.

Each file carries filler so context grows measurably. The point is not to make
it hard; it is to reach the 25k regime that C1 is actually about, and to record
prompt_tokens at every turn so the growth is data rather than an assumption.

THREE OUTCOMES, NEVER TWO. A loop that ran out of turns and a loop whose harness
broke are different evidence, and only one of them is about the model.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import string
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ENDPOINT = "http://127.0.0.1:8081/v1/chat/completions"
MODEL = "qwen3-coder-30b"

# Verdicts about the MODEL
SUSTAINED = "SUSTAINED"        # walked the chain and produced the token
DEGRADED = "DEGRADED"          # reached the turn/context bound without the token
# Verdicts about the RUN (never about the model)
HARNESS_FAILED = "HARNESS_FAILED"
UNAVAILABLE = "UNAVAILABLE"

TOOLS = [
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from the workspace and return its contents.",
        "parameters": {"type": "object",
                       "properties": {"path": {"type": "string",
                                               "description": "File name, e.g. node_03.txt"}},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "list_dir",
        "description": "List the files in the workspace.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "submit_answer",
        "description": "Submit the final SECRET token once you have found it. Call this exactly once.",
        "parameters": {"type": "object",
                       "properties": {"token": {"type": "string"}},
                       "required": ["token"]}}},
]

FILLER_WORDS = ("configuration deployment invariant threshold registry telemetry "
                "checkpoint partition scheduler allocator descriptor boundary "
                "serializer aggregate predicate resolver namespace").split()


def build_fixture(depth: int, filler_words: int, rng: random.Random) -> tuple[dict, str]:
    """A chain of depth `depth`. Returns (files, secret).

    The secret is random per run. A model cannot shortcut to it, so a correct
    answer is proof of traversal and not of recall.
    """
    secret = "KQ-" + "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    files: dict[str, str] = {}
    names = [f"node_{i:02d}.txt" for i in range(1, depth + 1)]
    rng.shuffle(names)  # so lexical order is not the chain order

    for i, name in enumerate(names):
        filler = " ".join(rng.choice(FILLER_WORDS) for _ in range(filler_words))
        if i == len(names) - 1:
            body = (f"# {name}\nThis is the FINAL node of the chain.\n"
                    f"SECRET_TOKEN = {secret}\n\nNotes: {filler}\n")
        else:
            body = (f"# {name}\nThis node does not hold the secret.\n"
                    f"NEXT_NODE = {names[i + 1]}\n\nNotes: {filler}\n")
        files[name] = body

    # A decoy that looks like a terminal node and is not, so "read one file and
    # guess" cannot succeed. Without it, a model that opened a random file and
    # invented a token could not be told apart from one that traversed.
    files["README.txt"] = (
        "# README\nThe chain starts at " + names[0] + ".\n"
        "Follow NEXT_NODE until you reach the node holding SECRET_TOKEN.\n"
        "Do not guess: the token is generated fresh for every run.\n")
    files["decoy.txt"] = ("# decoy\nSECRET_TOKEN = KQ-NOTTHEREALTOKEN\n"
                          "This file is a decoy and its token is wrong.\n")
    return files, secret


SYSTEM = ("You are working in a small file workspace. Use the provided tools to read "
          "files. Follow the chain of NEXT_NODE references starting from README.txt "
          "until you find the node that contains SECRET_TOKEN, then call submit_answer "
          "with exactly that token. Read one file per step. Do not guess the token.")


def post(payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        served_by = resp.headers.get("server", "")
        body = json.loads(resp.read().decode("utf-8"))
    body["__served_by__"] = served_by
    return body


def run(depth: int, max_turns: int, filler_words: int, ctx_ceiling: int,
        timeout: int, seed: int | None) -> dict:
    rng = random.Random(seed)
    files, secret = build_fixture(depth, filler_words, rng)

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Find the secret token and submit it."}]

    turns: list[dict] = []
    submitted = None
    reads: list[str] = []
    verdict = None
    detail = ""

    for turn in range(1, max_turns + 1):
        t0 = time.time()
        try:
            body = post({"model": MODEL, "messages": messages, "tools": TOOLS,
                         "tool_choice": "auto", "max_tokens": 400,
                         "temperature": 0.2}, timeout)
        except urllib.error.HTTPError as exc:
            return finish(UNAVAILABLE, f"HTTP {exc.code} at turn {turn}", turns, secret,
                          submitted, reads, depth)
        except Exception as exc:  # noqa: BLE001
            return finish(UNAVAILABLE, f"{type(exc).__name__} at turn {turn}: {exc}",
                          turns, secret, submitted, reads, depth)

        wall = round(time.time() - t0, 2)
        served = body.get("__served_by__", "")
        # The same egress question as everywhere else. A remote answer is not a
        # better answer; it is a different subject.
        if "llama.cpp" not in served.lower():
            return finish(HARNESS_FAILED,
                          f"response served by {served!r}, not llama.cpp -- this run is "
                          f"not about the local model", turns, secret, submitted, reads, depth)

        usage = body.get("usage", {})
        choice = (body.get("choices") or [{}])[0]
        msg = choice.get("message", {}) or {}
        finish_reason = choice.get("finish_reason")

        rec = {"turn": turn, "wall_s": wall, "finish_reason": finish_reason,
               "prompt_tokens": usage.get("prompt_tokens"),
               "completion_tokens": usage.get("completion_tokens"),
               "total_tokens": usage.get("total_tokens")}

        calls = msg.get("tool_calls") or []
        rec["n_tool_calls"] = len(calls)

        if not calls:
            # No tool call. Either it answered in prose (a failure of the loop
            # contract) or it stopped. Recorded, and the loop continues so a
            # one-off is not read as collapse.
            rec["text"] = (msg.get("content") or "")[:300]
            rec["event"] = "no_tool_call"
            turns.append(rec)
            messages.append({"role": "assistant", "content": msg.get("content") or ""})
            messages.append({"role": "user",
                             "content": "Use a tool. Do not answer in prose."})
            if sum(1 for t in turns if t.get("event") == "no_tool_call") >= 3:
                return finish(DEGRADED, "three turns produced no tool call",
                              turns, secret, submitted, reads, depth)
            continue

        messages.append({"role": "assistant", "content": msg.get("content") or "",
                         "tool_calls": calls})

        rec["calls"] = []
        for call in calls:
            fn = (call.get("function") or {})
            name = fn.get("name")
            raw_args = fn.get("arguments")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                malformed = False
            except (ValueError, TypeError):
                args, malformed = {}, True

            rec["calls"].append({"name": name, "args": args, "malformed": malformed})

            if malformed:
                result = f"ERROR: arguments were not valid JSON: {raw_args!r}"
            elif name == "list_dir":
                result = "\n".join(sorted(files))
            elif name == "read_file":
                p = str(args.get("path", "")).strip().lstrip("./")
                reads.append(p)
                result = files.get(p, f"ERROR: no such file {p!r}. Use list_dir to see the workspace.")
            elif name == "submit_answer":
                submitted = str(args.get("token", "")).strip()
                result = "submitted"
            else:
                result = f"ERROR: unknown tool {name!r}"

            messages.append({"role": "tool", "tool_call_id": call.get("id"),
                             "name": name, "content": result})

        turns.append(rec)

        if submitted is not None:
            verdict = SUSTAINED if submitted == secret else DEGRADED
            detail = ("token matches" if submitted == secret
                      else f"submitted {submitted!r}, expected {secret!r}")
            return finish(verdict, detail, turns, secret, submitted, reads, depth)

        ptok = rec.get("prompt_tokens") or 0
        if ptok > ctx_ceiling:
            return finish(DEGRADED,
                          f"context reached {ptok} tokens (ceiling {ctx_ceiling}) without "
                          f"an answer", turns, secret, submitted, reads, depth)

    return finish(DEGRADED, f"exhausted {max_turns} turns without submitting",
                  turns, secret, submitted, reads, depth)


def finish(verdict, detail, turns, secret, submitted, reads, depth) -> dict:
    peak = max([t.get("prompt_tokens") or 0 for t in turns], default=0)
    malformed = sum(1 for t in turns for c in t.get("calls", []) if c.get("malformed"))
    distinct_reads = len(set(reads))
    repeated = len(reads) - distinct_reads
    return {
        "verdict": verdict,
        "detail": detail,
        "utc": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "chain_depth": depth,
        # The floor is a property of the fixture: depth reads plus one submit.
        "min_possible_turns": depth + 1,
        "turns_taken": len(turns),
        "peak_prompt_tokens": peak,
        "malformed_tool_calls": malformed,
        "distinct_files_read": distinct_reads,
        "repeated_reads": repeated,
        "submitted": submitted,
        "secret_len": len(secret),
        "turn_log": turns,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure Qwen's multi-turn tool loop")
    ap.add_argument("--depth", type=int, default=8)
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--filler-words", type=int, default=400)
    ap.add_argument("--ctx-ceiling", type=int, default=30000)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    runs = []
    for i in range(args.repeats):
        seed = None if args.seed is None else args.seed + i
        r = run(args.depth, args.max_turns, args.filler_words, args.ctx_ceiling,
                args.timeout, seed)
        runs.append(r)
        print(f"run {i + 1}/{args.repeats}: {r['verdict']} -- {r['detail']}")
        print(f"  turns={r['turns_taken']} (floor {r['min_possible_turns']})  "
              f"peak_prompt_tokens={r['peak_prompt_tokens']}  "
              f"malformed={r['malformed_tool_calls']}  "
              f"distinct_reads={r['distinct_files_read']}  repeated={r['repeated_reads']}")
        for t in r["turn_log"]:
            names = ",".join(c["name"] for c in t.get("calls", [])) or t.get("event", "-")
            print(f"    t{t['turn']:>2}  ptok={t['prompt_tokens']:>6}  "
                  f"{t['wall_s']:>6}s  {t['finish_reason']:<12} {names}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(runs, fh, indent=2)
        print(f"\nwrote {args.out}")

    verdicts = [r["verdict"] for r in runs]
    print(f"\nVERDICTS {verdicts}")
    sustained = verdicts.count(SUSTAINED)
    print(f"SUSTAINED {sustained}/{len(runs)}")
    # A run that could not be judged must not be scored as a model result.
    if any(v in (HARNESS_FAILED, UNAVAILABLE) for v in verdicts):
        print("At least one run was UNJUDGEABLE. It measured nothing about the model.")
        return 2
    return 0 if sustained == len(runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
