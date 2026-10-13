#!/usr/bin/env python3
"""proof_digest (CDC C8): a test run returns a digest, not the full output.

    proof_digest.py run [--log F] [--timeout S] [--context N] -- <command> [args...]
    proof_digest.py digest <file> [--context N]
    proof_digest.py replay <transcript.jsonl> [--min-chars 4000] [--out F]

Motif compiled: "proof run -> full output read -> re-fetch the failing part". `run` executes the command (argv list, no
shell), WAITS for it, kills the process tree on timeout, writes the full output to a log file and prints: exit code,
pass/fail counts, every failing line with N lines of context, the last 5 lines, and the log path. The model reads the
digest; the full log stays on disk for the one case that needs it. Kill switch: CPP_PROOF_DIGEST=off prints the raw output.
Fails OPEN: if the digest itself errors, the raw tail is printed.

`replay` takes a historical transcript, finds proof runs whose result was large, and records calls/tokens before
(result as returned + the re-fetch calls that followed within 3 calls) vs after (one call + digest). Token figures are
chars/4 ESTIMATES of what entered context, not provider usage.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FAIL_LINE = re.compile(r"\bFAIL(?:ED)?\b|\bERROR\b|Traceback \(most recent|AssertionError|\bRED\b|\b[1-9]\d* (?:failed|failures?)\b", re.I)
PASS_LINE = re.compile(r"\bPASS(?:ED)?\b|\bOK\b|\b\d+ passed\b", re.I)
SUMMARY = re.compile(r"\b\d+ (?:passed|failed|failures?|errors?|skipped)\b|Ran \d+ tests?|\bOK\b|tests? \d+", re.I)
REFETCH = re.compile(r"Select-String|Get-Content|\btail\b|\bhead\b|\bgrep\b|\bcat\b|-Last\b|-First\b|\.log\b", re.I)
RUNNER = re.compile(r"\bpytest\b|-m unittest|(?:^|[\s;|&(])(?:python[\w.]*|py|node)(?:\.exe)?[\x27\"]?\s+(?:-\S+\s+)*\S*test_\w+\.(?:py|js)|npm (?:run )?test", re.I)   # a real test runner, not a gate word in a printf
TOK = 4  # chars per token estimate


def digest_text(text: str, context: int = 2, max_fail: int = 12) -> dict:
    lines = text.splitlines()
    fails = [i for i, l in enumerate(lines) if FAIL_LINE.search(l)]
    passes = sum(1 for l in lines if PASS_LINE.search(l))
    shown, seen = [], set()
    for i in fails[:max_fail]:
        for j in range(max(0, i - context), min(len(lines), i + context + 1)):
            if j not in seen:
                seen.add(j)
                shown.append(lines[j][:240])
    summary = [l[:200] for l in lines if SUMMARY.search(l)][-3:]
    return {"lines": len(lines), "chars": len(text), "pass_lines": passes, "fail_lines": len(fails),
            "failing": shown, "summary": summary, "tail": [l[:200] for l in lines[-5:]]}


def render(d: dict, rc, log) -> str:
    out = [f"DIGEST rc={rc} lines={d['lines']} pass_lines={d['pass_lines']} fail_lines={d['fail_lines']} log={log}"]
    out += ["summary: " + s for s in d["summary"]]
    if d["failing"]:
        out += ["failing (with context):"] + ["  " + l for l in d["failing"]]
        if d["fail_lines"] > 12:
            out.append(f"  ... {d['fail_lines'] - 12} more failing lines in the log")
    out += ["tail:"] + ["  " + l for l in d["tail"]]
    return "\n".join(out)


def kill_tree(proc) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def run(argv: list, log: Path | None, timeout: float, context: int) -> tuple[int, str]:
    log = log or Path(tempfile.gettempdir()) / f"proof-{int(time.time())}-{os.getpid()}.log"
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    timed_out = False
    try:
        raw, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_tree(proc)
        raw, _ = proc.communicate()
    text = (raw or b"").decode("utf-8", errors="replace")
    log.write_text(text, encoding="utf-8")
    rc = 124 if timed_out else proc.returncode
    if os.environ.get("CPP_PROOF_DIGEST", "").lower() == "off":
        return rc, text
    try:
        body = render(digest_text(text, context), rc, log)
        if timed_out:
            body = f"TIMEOUT after {timeout}s (process tree killed)\n" + body
        return rc, body
    except Exception:   # fail open: raw tail
        return rc, "\n".join(text.splitlines()[-40:])


def _calls(path: Path):
    import session_autopsy as sa
    return sa._scan(path, "main"), sa


def replay(path: Path, min_chars: int = 4000) -> dict:
    items, sa = _calls(path)
    calls = [c for c in items if not c.get("epoch")]
    best = None
    for idx, c in enumerate(calls):
        for uid, name, inp in c["uses"]:
            cmd = inp.get("command", "") if isinstance(inp.get("command"), str) else ""
            res = c["results"].get(uid)
            if name not in ("Bash", "PowerShell") or not RUNNER.search(cmd) or len(cmd) > 400 or not res:
                continue
            text = res["text"]
            if len(text) < min_chars:
                continue
            follow = 0
            for nxt in calls[idx + 1: idx + 4]:
                for _u, n2, i2 in nxt["uses"]:
                    c2 = i2.get("command", "") if isinstance(i2.get("command"), str) else ""
                    if n2 in ("Read", "Grep") or (n2 in ("Bash", "PowerShell") and (REFETCH.search(c2) or sa._PROOF.search(c2))):
                        follow += 1
            d = digest_text(text)
            after_txt = render(d, "?", "<log>")
            row = {"transcript": str(path), "call_index": idx, "command": cmd[:200],
                   "before": {"calls": 1 + follow, "result_chars": len(text), "tokens_est": len(text) // TOK},
                   "after": {"calls": 1, "result_chars": len(after_txt), "tokens_est": len(after_txt) // TOK},
                   "refetch_calls_observed": follow, "fail_lines_kept": d["fail_lines"]}
            if best is None or (follow > 0, len(text)) > (best["refetch_calls_observed"] > 0, best["before"]["result_chars"]):
                best = row
    return best or {"transcript": str(path), "error": "no proof run with result >= min_chars"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--log")
    r.add_argument("--timeout", type=float, default=600)
    r.add_argument("--context", type=int, default=2)
    r.add_argument("argv", nargs=argparse.REMAINDER)
    d = sub.add_parser("digest")
    d.add_argument("file")
    d.add_argument("--context", type=int, default=2)
    p = sub.add_parser("replay")
    p.add_argument("transcript")
    p.add_argument("--min-chars", type=int, default=4000)
    p.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        cmd = [x for x in a.argv if x != "--"] if a.argv and a.argv[0] == "--" else a.argv
        if not cmd:
            print("no command", file=sys.stderr)
            return 2
        rc, body = run(cmd, Path(a.log) if a.log else None, a.timeout, a.context)
        print(body)
        return rc
    if a.cmd == "digest":
        t = Path(a.file).read_text(encoding="utf-8", errors="replace")
        print(render(digest_text(t, a.context), "?", a.file))
        return 0
    res = replay(Path(a.transcript), a.min_chars)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
