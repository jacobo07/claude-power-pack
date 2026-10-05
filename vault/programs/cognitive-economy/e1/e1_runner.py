"""E1 runner, I/O layer: a POSIX port of the P3 runner's judgement path
(.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_runner.py) over the frozen E1 bank.

One counted run = fresh detached worktree at BASE (outside the repo, under the bank's RUNS) -> leak listing ->
jprepare (rule scrub + stub) -> red precondition grade -> run_start record -> one headless `claude -p` session ->
post-session grade -> metrics from the session transcript -> validity from e1_contract -> worktree removed.

The bank's own code (fresh_tree, leak_scan, jprepare, jgrade, drop_tree, tasks, jbase, git) is loaded from the bank
directory by load_bank under one module name, so one process drives exactly one bank dir.

The command-line entry (plan / preflight / run) belongs to plans 02-03 and 02-04; this module only prints this
docstring when run directly.
"""
import sys

sys.dont_write_bytecode = True

import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e1_contract as K  # noqa: E402

REPO = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(HERE), capture_output=True,
                           text=True, check=True).stdout.strip())
CLAUDE = "/home/kobii/.local/bin/claude"
CLI_VERSION = "2.1.289"
MODEL = K.MODEL
PY = sys.executable
PACKET = REPO / "vault/programs/cognitive-economy/post-reset-packet.json"
RESULTS = HERE / "results.jsonl"
BANK_DIR = HERE / "bank"
FROZEN = HERE / "BANK_FROZEN_AT"
PROJECTS = Path.home() / ".claude" / "projects"  # read-only
RULES_ROOT = "/home/kobii/.claude/rules"
SESSION_TIMEOUT = 1500
ALLOWED_TOOLS = "Read,Edit,Write,Grep,Glob,Bash"  # P3 also allowed PowerShell; this host is POSIX
EXCLUDED_BY_R2 = ["rules/technical-failure-to-product-state.md", "rules/scoped-side-effect-authority.md"]

sys.path.insert(0, str(REPO / "tools"))
import tis_observed as tob  # noqa: E402  (read-only import)


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


# ---- bank and packet ---------------------------------------------------------------------------------

def load_bank(bank_dir):
    """Load <bank_dir>/validate_bank.py as module "e1_bank_validate". Its HERE is bank_dir, so every bank
    function used here is the bank's own frozen code. One process loads one bank dir."""
    f = Path(bank_dir) / "validate_bank.py"
    if not f.is_file():
        raise SystemExit(f"no bank validator at {f}")
    spec = importlib.util.spec_from_file_location("e1_bank_validate", f)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e1_bank_validate"] = mod
    spec.loader.exec_module(mod)
    return mod


def packet_rules(packet=PACKET):
    p = json.loads(Path(packet).read_text(encoding="utf-8"))
    out = []
    for c in p["experiments"][0]["candidates"]:
        rel = c["rule"]
        if rel.startswith("~/.claude/"):
            rel = rel[len("~/.claude/"):]
        out.append({"rule": rel, "bytes": c["bytes"], "sha256_lf": c["sha256_lf"]})
    return out


def excludes(packet=PACKET, home=None):
    """Arm B's claudeMdExcludes: all 13 packet rules as absolute posix paths, in packet order."""
    home = Path(home) if home is not None else Path.home()
    rules = packet_rules(packet)
    if len(rules) != 13:
        raise ValueError(f"packet holds {len(rules)} candidates, want 13")
    prefix = (home / ".claude" / "rules").as_posix() + "/"
    out = []
    for r in rules:
        p = (home / ".claude" / r["rule"]).as_posix()
        if not p.startswith(prefix):
            raise ValueError(f"packet rule {r['rule']} is not under {prefix}")
        out.append(p)
    return out


# ---- the session -------------------------------------------------------------------------------------

def child_env():
    return {k: v for k, v in os.environ.items()
            if not (k.startswith("CLAUDECODE") or k.startswith("CLAUDE_CODE_"))}


def session_cmd(prompt, arm, excl):
    cmd = [CLAUDE, "-p", prompt, "--model", MODEL, "--output-format", "json", "--max-turns", "40",
           "--permission-mode", "acceptEdits", "--allowedTools", ALLOWED_TOOLS]
    if arm == "B":
        return cmd + ["--settings", json.dumps({"claudeMdExcludes": list(excl)})]
    if arm == "A":
        return cmd
    raise ValueError(f"arm {arm!r} is neither A nor B")


def session(wt, prompt, arm, rec, excl, exec_fn=None):
    """One headless session in wt; records launch/rc/wall/turns on rec and returns the session id ("" if none)."""
    cmd = session_cmd(prompt, arm, excl)
    run = exec_fn if exec_fn is not None else subprocess.run  # looked up at call time (test guard)
    t0 = time.time()
    raw = ""
    rec["session_launched"] = True
    try:
        r = run(cmd, cwd=str(wt), capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=SESSION_TIMEOUT, env=child_env())
        rec["claude_rc"], raw = r.returncode, (r.stdout or "")
    except subprocess.TimeoutExpired:
        rec["claude_rc"], raw = "timeout", ""
    except OSError:
        rec["session_launched"], rec["claude_rc"] = False, "exec-error"
    rec["wall_s"] = round(time.time() - t0, 1)
    sid = ""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    try:
        j = json.loads(lines[-1])
        if not isinstance(j, dict):
            raise ValueError("not an object")
        sid = j.get("session_id") or ""
        rec["num_turns"], rec["is_error"] = j.get("num_turns"), j.get("is_error")
        rec["subtype"] = j.get("subtype")
        res = j.get("result")
        rec["result_head"] = res[:200] if isinstance(res, str) else None
    except (IndexError, ValueError):
        rec["stdout_tail"] = raw[-300:]
    rec["session_id"] = sid
    return sid


# ---- transcript and metrics --------------------------------------------------------------------------

def _norm(s):
    return re.sub(r"[^A-Za-z0-9]", "-", str(s))


def find_transcript(sid, wt, started_epoch, projects=PROJECTS):
    """-> (path or None, reason). By session id first, else by the run tree's project dir with an mtime floor.
    Ambiguity is never resolved by guessing. Read-only."""
    projects = Path(projects)
    if sid:
        hits = sorted(projects.glob(f"*/{sid}.jsonl"))
        if len(hits) == 1:
            return hits[0], "by session id"
        if len(hits) > 1:
            return None, f"ambiguous: {len(hits)} transcripts for session id"
    want = _norm(wt)
    found = []
    if projects.is_dir():
        for d in sorted(projects.iterdir()):
            if not d.is_dir() or _norm(d.name) != want:
                continue
            for f in sorted(d.glob("*.jsonl")):
                try:
                    if f.stat().st_mtime >= started_epoch - 2:
                        found.append(f)
                except OSError:
                    continue
    if len(found) == 1:
        return found[0], "by run tree"
    if not found:
        return None, "no transcript for run tree"
    return None, f"ambiguous: {len(found)} transcripts for run tree"


def _ctx(u):
    return (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
            + u.get("cache_creation_input_tokens", 0))


def metrics(sid, wt, started_epoch, projects=PROJECTS):
    p, reason = find_transcript(sid, wt, started_epoch, projects)
    if p is None:
        return {"state": "UNMEASURED", "reason": reason}
    calls, _usage_lines, _synthetic, _bad = tob._calls_in(p)
    if not calls:
        return {"state": "NO_CALLS", "reason": reason, "transcript": str(p), "calls": 0, "total_context": 0,
                "first_call_context": None, "output_tokens": 0, "models": [], "entrypoint": None}
    return {"state": "MEASURED", "reason": reason, "transcript": str(p), "entrypoint": calls[0].get("entrypoint"),
            "calls": len(calls), "first_call_context": _ctx(calls[0]["usage"]),
            "total_context": sum(_ctx(c["usage"]) for c in calls),
            "output_tokens": sum(c["usage"].get("output_tokens", 0) for c in calls),
            "models": sorted({c["model"] for c in calls})}


# ---- bank-access evidence (VALIDITY READINGS (d): recorded, never a validity clause) -------------------

BANK_COMMIT_PREFIX = "d68871742a"  # BANK_FROZEN_AT's first 10 hex digits; V-E1-BANK-ACCESS pins the match
BANK_ACCESS_CAP = 100


def bank_markers(bank_dir=BANK_DIR):
    """Strings that only the bank (or a path to it) carries: grader output, bank files, task stems, the freeze."""
    stems = [f.stem for f in sorted(Path(bank_dir).glob("task_*.py"))]
    if not stems:
        raise ValueError(f"no task files under {bank_dir}: the marker list would be blind")
    return ["E1J_PASS", "_e1_common", "validate_bank", "e1/bank", *stems, BANK_COMMIT_PREFIX, "BANK_FROZEN_AT"]


def _tool_texts(path):
    """Yield the text of every tool_use input and tool_result content in a transcript (other lines skipped)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            msg = o.get("message") if isinstance(o, dict) else None
            content = msg.get("content") if isinstance(msg, dict) else None
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    yield json.dumps(c.get("input"), ensure_ascii=False)
                elif c.get("type") == "tool_result":
                    rc = c.get("content")
                    if isinstance(rc, list):
                        yield "\n".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in rc)
                    elif rc is not None:
                        yield str(rc)


def bank_access(path, markers):
    """-> [[marker, excerpt], ...]: the first hit of each marker in each tool block, capped at BANK_ACCESS_CAP."""
    out = []
    for text in _tool_texts(path):
        for m in markers:
            i = text.find(m)
            if i >= 0:
                out.append([m, text[max(0, i - 60):i + len(m) + 60]])
                if len(out) >= BANK_ACCESS_CAP:
                    return out
    return out


# ---- grade, snapshots, records -----------------------------------------------------------------------

def grade(bank, wt, t):
    try:
        return bank.jgrade(wt, t)
    except subprocess.TimeoutExpired:
        return {"rc": "timeout", "summary": "grade timeout", "passed": 0, "total": 0, "fails": []}


def tree_snapshot(wt):
    """{relative posix path: (size, mtime_ns)} for every regular file under wt; `.git` at the root skipped,
    symlinks never followed."""
    root = str(wt)
    out = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if dirpath == root and ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            if dirpath == root and name == ".git":
                continue
            p = os.path.join(dirpath, name)
            try:
                st = os.lstat(p)
            except OSError:
                continue
            if stat.S_ISREG(st.st_mode):
                out[os.path.relpath(p, root).replace(os.sep, "/")] = (st.st_size, st.st_mtime_ns)
    return out


def snapshot_diff(before, after):
    out = [f"A {p}" for p in after if p not in before]
    out += [f"D {p}" for p in before if p not in after]
    out += [f"M {p}" for p in after if p in before and after[p] != before[p]]
    return sorted(out)


def append_record(path, rec):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# ---- one counted run ---------------------------------------------------------------------------------

def _red_with_line(g):
    return g.get("rc") != 0 and "E1J_PASS=" in str(g.get("summary") or "")


def _steps(bank, t, arm, attempt, base, rid, rec, box, excl, excluded, cli_version, append, exec_fn):
    """The ordered steps of one run; returns early (no session) at a leak, an empty listing or a precondition
    that is not red with an E1J line. box["wt"] is set as soon as the tree exists, for the caller's cleanup."""
    wt = box["wt"] = bank.fresh_tree(rid, base)
    rec["tree_files"], rec["bank_in_tree"] = bank.leak_scan(wt)
    if rec["bank_in_tree"] or rec["tree_files"] == 0:
        return
    rec["pin_copies_removed"] = bank.jprepare(wt, t)
    pre = grade(bank, wt, t)
    rec["precondition_rc"], rec["precondition_summary"] = pre["rc"], pre["summary"]
    if not _red_with_line(pre):
        return
    before = tree_snapshot(wt)
    append({"kind": "run_start", "run_id": rid, "task": t["id"], "rule": t["rule"], "arm": arm,
            "attempt": attempt, "base": base, "wt": str(wt), "started": rec["started"],
            "started_epoch": rec["started_epoch"], "cli_version": cli_version, "excluded": excluded})
    session(wt, bank.JPROMPT.format(module=t["module"]), arm, rec, excl, exec_fn=exec_fn)
    rec["session_changed_paths"] = snapshot_diff(before, tree_snapshot(wt))
    g = grade(bank, wt, t)
    rec["grade_rc"], rec["grade_summary"] = g["rc"], g["summary"]
    rec["grade_passed"], rec["grade_total"], rec["grade_fails"] = g["passed"], g["total"], g["fails"]


def check_arm_excludes(arm, excl):
    """VALIDITY READINGS (c): arm A carries no excludes and arm B all 13; any other pair is refused before launch."""
    excluded = list(excl)
    if (arm, len(excluded)) not in (("A", 0), ("B", 13)):
        raise ValueError(f"arm {arm!r} with {len(excluded)} excludes: want ('A', 0) or ('B', 13)")
    return excluded


def one_run(bank, t, arm, attempt, base, *, excl, cli_version, append, run_id=None, exec_fn=None,
            projects=PROJECTS):
    """One counted run -> the run record. Appends only the run_start record; the caller appends the run record."""
    rid = run_id or K.run_id(t["id"], arm, attempt)
    excluded = check_arm_excludes(arm, excl)  # raises before any worktree exists
    bank_here = Path(getattr(bank, "HERE", BANK_DIR))
    try:
        bank_dir = bank_here.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        bank_dir = str(bank_here)
    rec = {"kind": "run", "run_id": rid, "task": t["id"], "rule": t["rule"], "arm": arm, "attempt": attempt,
           "base": base, "bank_dir": bank_dir,
           "task_file_sha256": hashlib.sha256(Path(t["file"]).read_bytes()).hexdigest(),
           "cli": CLAUDE, "cli_version": cli_version, "model": MODEL, "excluded": excluded,
           "started": _now(), "started_epoch": time.time(), "session_launched": False}
    box = {"wt": None}
    try:
        _steps(bank, t, arm, attempt, base, rid, rec, box, excl, excluded, cli_version, append, exec_fn)
    except Exception as e:  # recorded, never swallowed: the absent fields make the run invalid
        rec["error"] = f"{type(e).__name__}: {e}"
    finally:
        wt = box["wt"]
        if rec.get("session_launched"):
            try:
                rec["metrics"] = metrics(rec.get("session_id", ""), wt, rec["started_epoch"], projects)
            except Exception as e:
                rec["metrics"] = {"state": "UNMEASURED", "reason": f"metrics error {type(e).__name__}: {e}"}
            tp = (rec.get("metrics") or {}).get("transcript")
            try:
                rec["bank_access"] = bank_access(tp, bank_markers(bank_here)) if tp else None
            except Exception as e:  # evidence that could not be read is recorded as such, never as []
                rec["bank_access"], rec["bank_access_error"] = None, f"{type(e).__name__}: {e}"
        rec["ended"] = _now()
        if wt is not None:
            try:
                rec["worktree_removed"] = bank.drop_tree(wt)
            except Exception as e:
                rec["worktree_removed"] = False
                rec.setdefault("error", f"{type(e).__name__}: {e}")
    rec["valid"], rec["invalid_reasons"] = K.run_valid(rec)
    rec["task_pass"] = K.task_pass(rec)
    rec["spend"] = K.run_spend(rec)
    return rec


if __name__ == "__main__":
    print(__doc__)
    sys.exit(2)
