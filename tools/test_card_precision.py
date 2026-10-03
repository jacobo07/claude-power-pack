#!/usr/bin/env python3
"""Pillar A gate (skill-capability, SC-A): commit-card precision.

Drives the REAL card (hooks/doctrine_cards.js) as a child process against REAL scratch git
repos and transcripts rebuilt from the real tool-call windows in the laptop evidence pack
(vault/programs/skill-capability/card_evidence_pack.json, content-free, pinned by sha256).

What is real and what is not, stated once:
  * real: file names, session ids, tool-call start/end timestamps, the card, git, the repos.
  * synthetic: the hunks (the pack carries no content), so each replay appends 3 invented lines.
  * mtime: only 3a05f288 has a MEASURED mtime. The other replays use a PLACED mtime
    (inside the writer window identified from the pack's command text); every output line
    and the spec say `placed`, never `measured`.

Stdlib only. Exit 0 only when no check failed. `SCA_VERDICT=COULD_NOT_RUN` (exit 2) when
node or git is missing: a gate that cannot run never prints PASS.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD = os.path.join(ROOT, "hooks", "doctrine_cards.js")
PACK = os.path.join(ROOT, "vault", "programs", "skill-capability", "card_evidence_pack.json")
SPEC = os.path.join(ROOT, "vault", "programs", "skill-capability", "card_replay_spec.json")
PACK_SHA = "dacfdf5aa8afb0a5e6221ebf98fcf1b70866c7de3931083e210e7e948a6c0c05"

NODE = shutil.which("node")
GIT = shutil.which("git")
if not GIT and os.path.exists(r"C:\Program Files\Git\cmd\git.exe"):
    GIT = r"C:\Program Files\Git\cmd\git.exe"

EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")

passes = 0
fails = 0


def ok(name: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"ok   {name}: {evidence}")


def bad(name: str, evidence: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {name}: {evidence}")


def check(name: str, cond: bool, evidence: str) -> bool:
    (ok if cond else bad)(name, evidence)
    return bool(cond)


def ms_of(ts: str) -> float:
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000.0


def git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, "-C", repo, *args], capture_output=True, text=True, timeout=60)


# --------------------------------------------------------------------------------------
# the ONLY way this gate starts the card: private state dir, so the live ledger is never written
# --------------------------------------------------------------------------------------
def run_card(payload: dict, state_dir: str, mode: str, card: str = CARD) -> dict:
    env = dict(os.environ)
    env["DOCTRINE_CARDS_STATE_DIR"] = state_dir
    env["CLAUDE_DOCTRINE_CARDS"] = mode
    r = subprocess.run([NODE, card], input=json.dumps(payload), capture_output=True, text=True,
                       env=env, timeout=60)
    try:
        out = json.loads(r.stdout or "{}")
    except ValueError:
        out = {"raw": r.stdout}
    last = None
    lp = os.path.join(state_dir, "ledger.jsonl")
    if os.path.exists(lp):
        rows = [ln for ln in open(lp, encoding="utf-8").read().splitlines() if ln.strip()]
        if rows:
            last = json.loads(rows[-1])
    denied = (out.get("hookSpecificOutput") or {}).get("permissionDecision") == "deny"
    return {"out": out, "last": last, "denied": denied, "rc": r.returncode, "stderr": r.stderr}


# --------------------------------------------------------------------------------------
# replay builder
# --------------------------------------------------------------------------------------
def build_transcript(path: str, calls: list, deny_ts: str) -> int:
    """Rows from the pack's real tool calls: a tool_use row stamped at start, a tool_result row
    stamped at end only when it ended before the deny (a call still running at the deny has no result)."""
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for c in calls:
            if c["start"] >= deny_ts:
                continue
            tool = c["tool"]
            if tool in SHELL_TOOLS:
                inp = {"command": c.get("command", "")}
            elif tool in EDIT_TOOLS:
                inp = {"file_path": c.get("file_path", "")}
            else:
                inp = {}
            fh.write(json.dumps({"type": "assistant", "timestamp": c["start"], "message": {"content": [
                {"type": "tool_use", "id": c["id"], "name": tool, "input": inp}]}}, separators=(",", ":")) + "\n")
            n += 1
            if c.get("end") and c["end"] <= deny_ts:
                fh.write(json.dumps({"type": "user", "timestamp": c["end"], "message": {"content": [
                    {"type": "tool_result", "tool_use_id": c["id"], "content": "ok"}]}}, separators=(",", ":")) + "\n")
    return n


def replay(rep: dict, pack: dict, mtime_ms: float, mode: str = "deny", card: str = CARD) -> dict:
    """Build a scratch repo + transcript for one replay entry and run the card on its commit."""
    root = tempfile.mkdtemp(prefix=f"sca-{rep['id']}-")
    try:
        repo = os.path.join(root, "repo")
        os.makedirs(repo)
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@x.invalid")
        git(repo, "config", "user.name", "t")
        git(repo, "config", "core.autocrlf", "false")
        for f in rep["files"]:
            p = os.path.join(repo, *f.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("base content line one\nbase content line two\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "init")
        ns = round(mtime_ms * 1_000_000)
        for f in rep["files"]:
            p = os.path.join(repo, *f.split("/"))
            with open(p, "a", encoding="utf-8", newline="\n") as fh:
                for i in (1, 2, 3):
                    fh.write(f"replay foreign line {i} for {rep['id']}\n")
            os.utime(p, ns=(ns, ns))
        sess = pack["sessions"][rep["session"]]
        tp = os.path.join(root, rep["session"] + ".jsonl")
        build_transcript(tp, sess["tool_calls"], rep["deny_ts"])
        payload = {"tool_name": "PowerShell", "session_id": rep["session"], "transcript_path": tp,
                   "cwd": repo, "tool_input": {"command": "git commit -m replay -- " + " ".join(rep["files"])}}
        res = run_card(payload, os.path.join(root, "state"), mode, card)
        res["root"] = root
        return res
    finally:
        shutil.rmtree(root, ignore_errors=True)


def first_call_start_ms(rep: dict, pack: dict) -> float:
    return min(ms_of(c["start"]) for c in pack["sessions"][rep["session"]]["tool_calls"])


def check_replay(rep: dict, pack: dict) -> tuple:
    rid = rep["id"]
    src = rep["mtime_source"]
    r = replay(rep, pack, rep["mtime_ms"], "deny")
    last = r["last"] or {}
    reasons = last.get("unknown_reasons") or {}
    good = (not r["denied"] and last.get("decision") == "unknown"
            and all(reasons.get(f) == "mtime-in-own-shell-window" for f in rep["files"]))
    allowed = check(f"V-SCA-REPLAY-ALLOWED-{rid}", good,
                    f"mtime={src} decision={last.get('decision')} denied={r['denied']} reasons={reasons}")
    pre = replay(rep, pack, first_call_start_ms(rep, pack) - 60_000, "deny")
    plast = pre["last"] or {}
    presession = check(f"V-SCA-PRESESSION-DENIED-{rid}", pre["denied"] and plast.get("decision") == "deny-card",
                       f"mtime=first_tool_call-60s denied={pre['denied']} decision={plast.get('decision')}")
    return allowed, presession


FROZEN_IDS = {"300ac3a1", "5b36b02f-1", "5b36b02f-2", "3a05f288", "4a7ee8bc"}


def make_mutant(dest_dir: str) -> tuple:
    """Copy of the card whose ownShellWindowHit body is `return false` (the window rule removed).
    Returns (path, declaration_count, differs). Never a silent skip: the caller FAILs on any other count."""
    src = open(CARD, encoding="utf-8").read()
    decl = "function ownShellWindowHit("
    n = src.count(decl)
    if n != 1:
        return None, n, False
    at = src.index(decl)
    open_brace = src.index("{", src.index(")", at))
    depth = 0
    end = None
    for i in range(open_brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return None, n, False
    mutated = src[:open_brace + 1] + " return false; " + src[end:]
    path = os.path.join(dest_dir, "doctrine_cards.js")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(mutated)
    return path, n, mutated != src


def check_spec(spec: dict, pack: dict) -> None:
    ids = [r["id"] for r in spec["replays"]]
    check("V-SCA-SPEC-FIVE-FROZEN", len(ids) == 5 and set(ids) == FROZEN_IDS, f"replays={ids}")
    check("V-SCA-SPEC-6TH-BESIDE", [b["id"] for b in spec["beside"]] == ["4615e1d1"] and "4615e1d1" not in ids,
          f"beside={[b['id'] for b in spec['beside']]}")
    measured = sorted(r["id"] for r in spec["replays"] if r["mtime_source"] == "measured")
    placed = sorted(r["id"] for r in spec["replays"] if r["mtime_source"] == "placed")
    check("V-SCA-SPEC-MEASURED-ONLY-3a05f288", measured == ["3a05f288"] and len(placed) == 4,
          f"measured={measured} placed={placed}")
    inside = []
    for r in spec["replays"]:
        lo, hi = ms_of(r["writer_window"][0]), ms_of(r["writer_window"][1])
        inside.append(lo <= r["mtime_ms"] <= hi)
    check("V-SCA-SPEC-MTIME-INSIDE-WRITER-WINDOW", all(inside), f"inside={inside}")
    problems = []
    for r in spec["replays"] + spec["beside"]:
        calls = {c["id"]: c for c in pack["sessions"][r["session"]]["tool_calls"]}
        c = calls.get(r["writer_call_id"])
        if c is None:
            problems.append(f"{r['id']}: writer_call_id absent from pack")
        elif [c["start"], c["end"]] != r["writer_window"]:
            problems.append(f"{r['id']}: window {r['writer_window']} != pack {[c['start'], c['end']]}")
    check("V-SCA-SPEC-WRITER-IDS-REAL", not problems, "; ".join(problems) or "every writer id and window equals the pack's call")


def main() -> int:
    print(f"host={socket.gethostname()}")
    if not NODE or not GIT:
        print(f"SCA_VERDICT=COULD_NOT_RUN node={NODE} git={GIT}")
        return 2
    raw = open(PACK, "rb").read().replace(b"\r\n", b"\n")
    sha = hashlib.sha256(raw).hexdigest()
    if not check("V-SCA-FIXTURE-SHA", sha == PACK_SHA, f"sha256={sha}"):
        print(f"SCA_PASS={passes}/{passes + fails}")
        return 1
    pack = json.loads(raw)
    spec = json.load(open(SPEC, encoding="utf-8"))
    check("V-SCA-SPEC-PACK-PIN", spec.get("pack_sha256") == PACK_SHA, f"spec pins {spec.get('pack_sha256')}")

    check_spec(spec, pack)

    allowed = presession = 0
    for rep in spec["replays"]:
        a, p = check_replay(rep, pack)
        allowed += bool(a)
        presession += bool(p)

    # mutant pole: the window rule removed -> every replay is denied again
    mdir = tempfile.mkdtemp(prefix="sca-mutant-")
    mutant_denied = 0
    try:
        mpath, count, differs = make_mutant(mdir)
        applied = check("V-SCA-MUTANT-APPLIED", count == 1 and differs and mpath is not None,
                        f"declarations={count} differs={differs}")
        for rep in spec["replays"]:
            if not applied:
                bad(f"V-SCA-MUTANT-DENIES-{rep['id']}", "mutant not applied")
                continue
            m = replay(rep, pack, rep["mtime_ms"], "deny", card=mpath)
            ml = m["last"] or {}
            if check(f"V-SCA-MUTANT-DENIES-{rep['id']}", m["denied"] and ml.get("decision") == "deny-card",
                     f"mtime={rep['mtime_source']} denied={m['denied']} decision={ml.get('decision')}"):
                mutant_denied += 1
    finally:
        shutil.rmtree(mdir, ignore_errors=True)

    # 6th deny, reported beside D-CARD and never folded into the /5 counts
    b = spec["beside"][0]
    br = replay(b, pack, b["mtime_ms"], "deny")
    bl = br["last"] or {}
    beside_denied = br["denied"] and bl.get("decision") == "deny-card"
    check(f"V-SCA-6TH-DENY-STAYS-DENIED-{b['id']}", beside_denied and b["class"] == "rollover-predecessor-lines",
          f"mtime={b['mtime_source']} denied={br['denied']} decision={bl.get('decision')} class={b['class']}")

    print(f"D-CARD frozen_denies=5 replayed_allowed={allowed}/5 presession_denied={presession}/5 "
          f"mutant_denied={mutant_denied}/5 | beside: {b['id']} (after freeze) denied={beside_denied} class={b['class']}")

    print(f"SCA_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
