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
import re
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
def run_card(payload: dict, state_dir: str, mode: str, card: str = CARD, extra_env: dict | None = None) -> dict:
    env = dict(os.environ)
    env.update(extra_env or {})
    env["DOCTRINE_CARDS_STATE_DIR"] = state_dir   # always wins over extra_env
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


def run_suite(script: str) -> tuple:
    """Run one node suite (bounded 300 s). Returns (rc, stdout); a timeout is rc=-1."""
    try:
        r = subprocess.run([NODE, os.path.join(ROOT, "hooks", "tests", script)], capture_output=True, text=True,
                           timeout=300, cwd=ROOT)
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        return -1, ""


def check_suites() -> None:
    rc, out = run_suite("test-doctrine-cards.js")
    last = (out.strip().splitlines() or [""])[-1]
    m = re.fullmatch(r"DOCTRINE_CARDS_PASS=(\d+)/(\d+)", last)
    check("V-SCA-NODE-DOCTRINE-CARDS", rc == 0 and bool(m) and m.group(1) == m.group(2), f"rc={rc} last={last!r}")
    check("V-SCA-ARM-C", "PASS V-DC-JUDGED-COMMIT-NOT-A-WRITE" in out,
          "doctrine-cards output contains PASS V-DC-JUDGED-COMMIT-NOT-A-WRITE" if "PASS V-DC-JUDGED-COMMIT-NOT-A-WRITE" in out
          else "arm C line missing from the doctrine-cards output")
    rc2, out2 = run_suite("test-destructive-doctrine-card.js")
    last2 = (out2.strip().splitlines() or [""])[-1]
    check("V-SCA-NODE-DESTRUCTIVE-CARD", rc2 == 0, f"rc={rc2} last={last2!r}")


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


# --------------------------------------------------------------------------------------
# D-03: the `git exit 128` x6 class. The card records git's stderr CLASS, never the text.
# --------------------------------------------------------------------------------------
G128 = "git exit 128"
CAPSULE_COMMIT = "& 'C:\\Program Files\\Git\\cmd\\git.exe' commit -m x"


def row_fields(last: dict | None) -> str:
    last = last or {}
    return (f"decision={last.get('decision')} reason={last.get('reason')!r} basis={last.get('basis')} "
            f"git_error={last.get('git_error')}")


def check_128_split(pack: dict) -> None:
    rows = [r for r in pack["rows"] if r.get("reason") == G128]
    a = [r for r in rows if r["session"].startswith("abcd1234") and r.get("basis") == "index"]
    f = [r for r in rows if r["session"].startswith("fce2689e") and r.get("basis") == "only-paths"]
    check("V-SCA-128-ROWS-SPLIT", len(rows) == 6 and len(a) == 3 and len(f) == 3,
          f"{len(rows)} = abcd1234 x{len(a)} (index) + fce2689e x{len(f)} (only-paths)")


def check_128_abcd1234() -> None:
    """The capsule-guard e2e payload, verbatim: PowerShell git commit -m x in cwd C:\\proj, no transcript."""
    sd = tempfile.mkdtemp(prefix="sca-128-abcd-")
    try:
        payload = {"tool_name": "PowerShell", "session_id": "abcd1234-ffff-0000", "cwd": "C:\\proj",
                   "hook_event_name": "PreToolUse", "tool_input": {"command": CAPSULE_COMMIT}}
        r = run_card(payload, sd, "deny")
        last = r["last"] or {}
        good = (r["out"].get("continue") is True and not r["denied"] and last.get("decision") == "unknown"
                and last.get("reason") == G128 and last.get("basis") == "index"
                and last.get("git_error") == "cannot_chdir")
        check("V-SCA-128-CANNOT-CHDIR-abcd1234", good, f"denied={r['denied']} {row_fields(last)}")
    finally:
        shutil.rmtree(sd, ignore_errors=True)


def commit_payload(session: str, cwd: str, command: str, transcript: str | None = None) -> dict:
    p = {"tool_name": "PowerShell", "session_id": session, "cwd": cwd, "hook_event_name": "PreToolUse",
         "tool_input": {"command": command}}
    if transcript:
        p["transcript_path"] = transcript
    return p


def init_repo(repo: str) -> None:
    os.makedirs(repo, exist_ok=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@x.invalid")
    git(repo, "config", "user.name", "t")
    git(repo, "config", "core.autocrlf", "false")


def node_classify(stderr: str) -> str:
    """The card's own classifyGitError, called through node (stderr on stdin)."""
    code = ("const {classifyGitError}=require(process.argv[1]);"
            "process.stdout.write(classifyGitError(require('fs').readFileSync(0,'utf8')))")
    r = subprocess.run([NODE, "-e", code, CARD], input=stderr, capture_output=True, text=True, timeout=60)
    return r.stdout.strip() if r.returncode == 0 else f"node-rc={r.returncode}"


def own_edit_transcript(path: str, new_string: str) -> None:
    row = {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Edit", "input": {
        "file_path": "pricing.py", "old_string": "    return amount - pct", "new_string": new_string}}]}}
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, separators=(",", ":")) + "\n")


def write_unborn_pricing(repo: str) -> None:
    body = ('"""Order pricing."""\n\nTAX_RATE = 0.21\n\n\ndef apply_discount(amount, pct):\n'
            '    return amount * (1 - pct / 100)\n\n\ndef shipping(weight_kg):\n'
            '    return 4.95 if weight_kg <= 2 else 4.95 + 1.1 * (weight_kg - 2)\n')
    with open(os.path.join(repo, "pricing.py"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    git(repo, "add", "pricing.py")


def check_128_classes() -> None:
    root = tempfile.mkdtemp(prefix="sca-128-classes-")
    host = socket.gethostname()
    try:
        ver = git(root, "--version").stdout.strip()
        print(f"INFO git={ver} host={host}")
        # not_a_repo: an empty dir; the ceiling stops git walking into a repo that holds the temp dir
        plain = os.path.join(root, "plain")
        os.makedirs(plain)
        ceil = {"GIT_CEILING_DIRECTORIES": root}
        rows = {}
        for tag, cmd in (("index", "git commit -m x"), ("pathspec", "git commit -m x -- f")):
            sd = os.path.join(root, f"state-nar-{tag}")
            r = run_card(commit_payload("sca-nar", plain, cmd), sd, "deny", extra_env=ceil)
            rows[tag] = r["last"] or {}
        good = all(l.get("git_error") == "not_a_repo" and str(l.get("reason", "")).startswith("git exit ")
                   and l.get("decision") == "unknown" for l in rows.values())
        check("V-SCA-128-NOT-A-REPO", good,
              " | ".join(f"{t}: {row_fields(l)}" for t, l in rows.items())
              + " (observed on this git: outside a repo `git diff` exits 129 via --no-index, not 128)")

        # outside_repo: a repo with one commit, commit pathspec naming a file in a second directory
        repo = os.path.join(root, "withc")
        init_repo(repo)
        with open(os.path.join(repo, "f"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("a\nb\nc\n")
        git(repo, "add", "f")
        git(repo, "commit", "-q", "-m", "i")
        elsewhere = os.path.join(root, "elsewhere")
        os.makedirs(elsewhere)
        outside = os.path.join(elsewhere, "o.txt")
        with open(outside, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("x\n")
        r = run_card(commit_payload("sca-out", repo, f"git commit -m x -- {outside}"),
                     os.path.join(root, "state-out"), "deny")
        l = r["last"] or {}
        check("V-SCA-128-OUTSIDE-REPO", l.get("git_error") == "outside_repo" and l.get("reason") == G128
              and l.get("decision") == "unknown", row_fields(l))

        # unborn HEAD: real stderr captured by the gate, classified by the card's own function through node
        unb = os.path.join(root, "unb")
        init_repo(unb)
        write_unborn_pricing(unb)
        cap = git(unb, "diff", "HEAD", "--", "pricing.py", "-U0", "--no-color", "--no-ext-diff")
        cls = node_classify(cap.stderr)
        check("V-SCA-128-UNBORN-HEAD-CLASSIFIED", cap.returncode == 128 and cls == "unborn_head",
              f"real git rc={cap.returncode} stderr={cap.stderr.strip()!r} -> {cls}")

        # unborn HEAD is judged, not a git-128 unknown: the commit diffs against the empty tree
        tp = os.path.join(root, "unborn-session.jsonl")
        own_edit_transcript(tp, "    return amount * (1 - pct / 100)")
        r = run_card(commit_payload("sca-unb", unb, "git commit -m first -- pricing.py", tp),
                     os.path.join(root, "state-unb"), "deny")
        l = r["last"] or {}
        check("V-SCA-UNBORN-HEAD-JUDGED", r["denied"] and l.get("decision") == "deny-card" and l.get("base") == "empty-tree"
              and l.get("reason") != G128, f"denied={r['denied']} {row_fields(l)} base={l.get('base')}")

        # dubious_ownership: git's test seam. Not honoured, or honoured without the named stderr, is reported as such.
        drepo = os.path.join(root, "dub")
        init_repo(drepo)
        with open(os.path.join(drepo, "f"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("a\n")
        git(drepo, "add", "f")
        git(drepo, "commit", "-q", "-m", "i")
        with open(os.path.join(drepo, "f"), "a", encoding="utf-8", newline="\n") as fh:
            fh.write("b\nc\nd\n")
        git(drepo, "add", "f")
        r = run_card(commit_payload("sca-dub", drepo, "git commit -m x"), os.path.join(root, "state-dub"), "deny",
                     extra_env={"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1"})
        l = r["last"] or {}
        if l.get("git_error") == "dubious_ownership" and str(l.get("reason", "")).startswith("git exit "):
            ok("V-SCA-128-DUBIOUS-OWNERSHIP", row_fields(l))
        else:
            print(f"NOT-REPRODUCED V-SCA-128-DUBIOUS-OWNERSHIP host={host}: {row_fields(l)} "
                  f"(git test seam GIT_TEST_ASSUME_DIFFERENT_OWNER did not produce the dubious-ownership stderr here)")
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------------------
# D-03 abcd1234 root cause: a test that starts the card without a private state dir writes the live ledger.
# The population is DISCOVERED by an independent marker (the file drives the card or a dispatcher AND
# contains a commit command literal), never by searching for the fix.
# --------------------------------------------------------------------------------------
CARD_REF_RE = re.compile(r"doctrine_cards|hook-dispatcher|--e2e")
COMMIT_LITERAL_RE = re.compile(r"""\bgit(?:\.exe)?['"]?\s+(?:-C\s+\S+\s+)?commit\b""")
CAPSULE_TEST = "test-capsule-mutation-guard.js"
CARDS_TEST = "test-doctrine-cards.js"


def sweep_state_dir(texts: dict) -> tuple:
    """(population, offenders): population = files that reference the card or a dispatcher and carry a commit
    command literal; offenders = population members without DOCTRINE_CARDS_STATE_DIR."""
    pop = [n for n in sorted(texts) if CARD_REF_RE.search(texts[n]) and COMMIT_LITERAL_RE.search(texts[n])]
    return pop, [n for n in pop if "DOCTRINE_CARDS_STATE_DIR" not in texts[n]]


def read_hook_tests() -> dict:
    d = os.path.join(ROOT, "hooks", "tests")
    return {n: open(os.path.join(d, n), encoding="utf-8").read() for n in sorted(os.listdir(d)) if n.endswith(".js")}


def check_hermetic_card_tests() -> None:
    rc, out = run_suite(CAPSULE_TEST)
    last = (out.strip().splitlines() or [""])[-1]
    m = re.match(r"CMG_PASS=(\d+)/(\d+)", last)
    check("V-SCA-NODE-CAPSULE-GUARD", rc == 0 and bool(m) and m.group(1) == m.group(2),
          f"rc={rc} last={last!r} (run without --e2e: the dispatcher's card path ../skills/claude-power-pack/hooks/"
          f"doctrine_cards.js is the laptop layout and does not resolve on this host)")
    texts = read_hook_tests()
    pop, off = sweep_state_dir(texts)
    check("V-SCA-STATE-DIR-SWEEP", len(pop) >= 2 and CAPSULE_TEST in pop and CARDS_TEST in pop and not off,
          f"population={pop} without_private_state_dir={off} floor=2")
    # drill: the same sweep over the capsule test with every DOCTRINE_CARDS_STATE_DIR removed must go red,
    # and over the unmodified text must stay green (both poles of the sweep itself)
    stripped = texts[CAPSULE_TEST].replace("DOCTRINE_CARDS_STATE_DIR", "")
    mpop, moff = sweep_state_dir({CAPSULE_TEST: stripped})
    gpop, goff = sweep_state_dir({CAPSULE_TEST: texts[CAPSULE_TEST]})
    check("V-SCA-STATE-DIR-DRILL", stripped != texts[CAPSULE_TEST] and moff == [CAPSULE_TEST] and gpop == [CAPSULE_TEST] and goff == [],
          f"stripped copy flagged={moff} (population {mpop}); unmodified copy flagged={goff}")


def info_fce2689e(pack: dict) -> list:
    """Count the pack's tool calls of the fce2689e session in the 120 s before each of its 128 rows."""
    sess = next(v for k, v in pack["sessions"].items() if k.startswith("fce2689e"))
    starts = [ms_of(c["start"]) for c in sess["tool_calls"]]
    stamps = [r["ts"] for r in pack["rows"] if r.get("reason") == G128 and r["session"].startswith("fce2689e")]
    counts = [sum(1 for s in starts if ms_of(ts) - 120_000 <= s <= ms_of(ts)) for ts in stamps]
    first = min(sess["tool_calls"], key=lambda c: ms_of(c["start"]))["start"]
    last = max(sess["tool_calls"], key=lambda c: ms_of(c["start"]))["start"]
    print(f"INFO fce2689e: pack tool_calls={len(starts)} first_start={first} last_start={last} "
          f"rows={stamps} calls_in_120s_before_row={counts[0]},{counts[1]},{counts[2]} "
          f"(the exact command is not in the pack and cannot be reproduced from it)")
    return counts


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

    fails_before_128 = fails
    check_128_split(pack)
    check_128_abcd1234()
    check_128_classes()
    counts = info_fce2689e(pack)
    if fails == fails_before_128:
        print("D-CARD unknown_git_exit_128=6: abcd1234 x3 -> cannot_chdir (reproduced; capsule-guard e2e ran the card "
              "without a private state dir); fce2689e x3 -> cause not recoverable from the pack (rows carry no stderr; "
              f"calls_in_window={counts[0]},{counts[1]},{counts[2]}); classes now recorded per row: git_error")

    check_suites()
    check_hermetic_card_tests()

    print(f"SCA_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
