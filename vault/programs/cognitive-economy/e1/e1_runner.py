"""E1 runner, I/O layer: a POSIX port of the P3 runner's judgement path
(.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_runner.py) over the frozen E1 bank.

One counted run = fresh detached worktree at BASE (outside the repo, under the bank's RUNS) -> leak listing ->
jprepare (rule scrub + stub) -> red precondition grade -> run_start record -> one headless `claude -p` session ->
post-session grade -> metrics from the session transcript -> validity from e1_contract -> worktree removed.

The bank's own code (fresh_tree, leak_scan, jprepare, jgrade, drop_tree, tasks, jbase, git) is loaded from the bank
directory by load_bank under one module name, so one process drives exactly one bank dir.

Before anything is launched, `preflight` checks that the world is the one ADDENDUM-E1 describes (the CLI path and
version, the packet's own sha256, the 13 LF sha256 pins, the 13 exclude paths, the bank, BANK_FROZEN_AT against
the pinned freeze hash and the bank's bytes against it, the bank's own freeze_check, the BASE, the index order,
the existing results); `per_run_checks` repeats the cheap subset (CLI, packet, pins, freeze hash, bank bytes)
before every counted run, and a check that raises is a refusal. After the post-session grade the bank is checked
again, and the session transcript's own CLI version is recorded: either one off makes the run invalid, and a bank
drift halts the campaign. No check writes anything and none starts a session.

`drive` is the only campaign loop: it replays results.jsonl through e1_contract on every iteration, appends a
`pair` record per terminal task and a `stop` record per terminal state, reconciles a run interrupted mid-session,
runs the per-run checks before every run, and commits results.jsonl alone after every pair, stop and refusal.

    python3 vault/programs/cognitive-economy/e1/e1_runner.py plan [--bank DIR] [--results PATH]
    python3 vault/programs/cognitive-economy/e1/e1_runner.py preflight [--bank DIR]
    python3 vault/programs/cognitive-economy/e1/e1_runner.py run [--max-pairs N] [--no-commit]

plan: the dry view (one TASK line per task in contract order, SPENT, NEXT); no worktree, no session, no write.
preflight: one `CHECK <name> OK|REFUSED <detail>` line per check, then `PREFLIGHT OK` or `PREFLIGHT REFUSED <n>`.
run: the counted campaign over the frozen bank (always vault/programs/cognitive-economy/e1/bank); refuses unless
every preflight check passes.

Exit codes: 0 ALL_DECIDED (or plan / preflight OK), 1 refused / commit failed, 2 usage, 3 contract stop
(HARM_STOP, SPEND_STOP, SPEND_UNMEASURED, POSITIVE_CONTROL_STOP), 4 paused (--max-pairs reached).
"""
import sys

sys.dont_write_bytecode = True

import ctypes  # noqa: E402
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import signal  # noqa: E402
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
CLI_VERSION = K.CLI_VERSION  # "2.1.289"
MODEL = K.MODEL
PY = sys.executable
PACKET = REPO / "vault/programs/cognitive-economy/post-reset-packet.json"
# The pins the packet and the freeze are judged by live here, not in the files they guard (STATE.md, 2026-10-05
# PINNED IDENTITIES): sha256 of the packet bytes as committed, and the full hash BANK_FROZEN_AT must hold.
PACKET_SHA256 = "b6b104bb523d147377d13f752fe7d13b31cc66728164eb6bdf5b6e2c1c5522ba"
BANK_FROZEN_HASH = "d68871742adefe392728370d82b69991a4437f79"
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


def rule_set_problems(rules):
    """-> problems with the packet's rule list as a SET: 13 entries naming 13 distinct paths (a duplicated entry
    would let one rule pass as two and drop another from arm B's excludes)."""
    probs = []
    if len(rules) != 13:
        probs.append(f"packet holds {len(rules)} candidates, want 13")
    paths = [r["rule"] for r in rules]
    dups = sorted({x for x in paths if paths.count(x) > 1})
    if dups:
        probs.append(f"packet names a rule more than once: {dups}")
    return probs


def check_packet(packet=PACKET, want=PACKET_SHA256):
    """-> problems. The packet's own bytes against the runner's pin; read-only."""
    h = hashlib.sha256(Path(packet).read_bytes()).hexdigest()
    return [] if h == want else [f"packet sha256 {h[:12]} != pinned {want[:12]}"]


def check_frozen_pin(frozen=FROZEN, want=BANK_FROZEN_HASH):
    """-> problems. BANK_FROZEN_AT must hold exactly the pinned freeze hash: a re-freeze (an edited bank committed
    and its new hash written into BANK_FROZEN_AT) would otherwise pass bank_drift."""
    got = Path(frozen).read_text(encoding="utf-8").strip()
    return [] if got == want else [f"BANK_FROZEN_AT {got[:12]!r} != pinned freeze {want[:10]}"]


def excludes(packet=PACKET, home=None):
    """Arm B's claudeMdExcludes: all 13 packet rules as absolute posix paths, in packet order."""
    home = Path(home) if home is not None else Path.home()
    rules = packet_rules(packet)
    probs = rule_set_problems(rules)
    if probs:
        raise ValueError("; ".join(probs))
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
    """The parent env minus Claude Code's own session markers, with the auto-updater off (both arms alike): the
    binary that runs must be the one the per-run check read (STATE.md PINNED IDENTITIES)."""
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("CLAUDECODE") or k.startswith("CLAUDE_CODE_"))}
    env["DISABLE_AUTOUPDATER"] = "1"
    return env


def session_cmd(prompt, arm, excl):
    cmd = [CLAUDE, "-p", prompt, "--model", MODEL, "--output-format", "json", "--max-turns", "40",
           "--permission-mode", "acceptEdits", "--allowedTools", ALLOWED_TOOLS]
    if arm == "B":
        return cmd + ["--settings", json.dumps({"claudeMdExcludes": list(excl)})]
    if arm == "A":
        return cmd
    raise ValueError(f"arm {arm!r} is neither A nor B")


PR_SET_PDEATHSIG = 1  # <linux/prctl.h>


def proc_start(pid):
    """-> (start time in clock ticks since boot, state letter) of pid from /proc/<pid>/stat, or None when no such
    process is listed. The start time is what tells a recorded child from a later process reusing its pid."""
    try:
        raw = Path(f"/proc/{int(pid)}/stat").read_text(encoding="ascii", errors="replace")
    except (OSError, ValueError, TypeError):
        return None
    rest = raw[raw.rfind(")") + 2:].split()  # comm may hold spaces and parentheses: fields resume after the last ")"
    try:
        return int(rest[19]), rest[0]  # field 22 starttime, field 3 state
    except (IndexError, ValueError):
        return None


def session_alive(pid, start):
    """True while the recorded session process (pid with that start time) exists and is not a zombie. A pid listed
    with an unknown recorded start time is taken as alive (fail closed: it cannot be told from the session)."""
    if pid is None:
        return False
    st = proc_start(pid)
    if st is None or st[1] == "Z":
        return False
    return start is None or st[0] == start


def _pdeathsig_preexec(parent):
    """-> the child-side preexec: SIGKILL this child when the runner dies (PR_SET_PDEATHSIG), and exit at once if
    the runner already died between fork and prctl (the signal would never come). libc is resolved in the parent."""
    prctl = ctypes.CDLL(None, use_errno=True).prctl

    def pre():
        if prctl(PR_SET_PDEATHSIG, signal.SIGKILL, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG) failed")
        if os.getppid() != parent:
            os._exit(1)
    return pre


def _kill_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)  # start_new_session: the child leads its own group (pgid == pid)
    except (ProcessLookupError, PermissionError):
        pass


def _launch(cmd, cwd, env, timeout, on_spawn):
    """The real session process: its own session/group, SIGKILLed with the runner (PR_SET_PDEATHSIG), the whole
    group SIGKILLed on timeout or on any exception while waiting. on_spawn(pid, start) runs after the process
    exists and before the wait (it writes the run_start record). -> (rc, stdout); raises TimeoutExpired."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                            start_new_session=True, preexec_fn=_pdeathsig_preexec(os.getpid()))
    try:
        st = proc_start(proc.pid)
        if on_spawn is not None:
            on_spawn(proc.pid, st[0] if st else None)
        stdout, _ = proc.communicate(timeout=timeout)
        return proc.returncode, stdout or ""
    except BaseException:  # timeout, a failed run_start append, an interrupt: the session never outlives this
        _kill_group(proc)
        try:
            proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            pass  # a grandchild that left the group may hold the pipes; the group itself is dead
        raise


def session(wt, prompt, arm, rec, excl, exec_fn=None, on_spawn=None):
    """One headless session in wt; records launch/rc/wall/turns/pid on rec and returns the session id ("" if none).
    on_spawn(pid, start) is called exactly once before any wait: with the live child's pid and /proc start time,
    or (None, None) when no process was started (exec error) or exec_fn (a run-shaped test seam) is injected."""
    cmd = session_cmd(prompt, arm, excl)
    t0 = time.time()
    raw = ""
    rec["session_launched"] = True
    rec["session_pid"] = rec["session_pid_start"] = None
    spawned = []

    def spawned_cb(pid, start):
        spawned.append(pid)
        rec["session_pid"], rec["session_pid_start"] = pid, start
        if on_spawn is not None:
            on_spawn(pid, start)
    try:
        if exec_fn is not None:
            spawned_cb(None, None)
            r = exec_fn(cmd, cwd=str(wt), capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=SESSION_TIMEOUT, env=child_env())
            rec["claude_rc"], raw = r.returncode, (r.stdout or "")
        else:
            rec["claude_rc"], raw = _launch(cmd, str(wt), child_env(), SESSION_TIMEOUT, spawned_cb)
    except subprocess.TimeoutExpired:
        rec["claude_rc"], raw = "timeout", ""
    except (OSError, subprocess.SubprocessError):  # never started (missing binary, prctl refused in the child)
        if spawned and spawned[0] is not None:
            raise  # a process did start (and was killed): an error after the spawn is never an exec error
        rec["session_launched"], rec["claude_rc"] = False, "exec-error"
        if not spawned:
            spawned_cb(None, None)
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


def transcript_versions(path):
    """-> sorted distinct string `version` values over the transcript's JSON lines (Claude Code stamps its own
    version on every message line). Read-only."""
    seen = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if isinstance(o, dict) and isinstance(o.get("version"), str):
                seen.add(o["version"])
    return sorted(seen)


def _observe_versions(rec):
    tp = (rec.get("metrics") or {}).get("transcript")
    try:
        rec["cli_versions_observed"] = transcript_versions(tp) if tp else None
    except Exception as e:  # unreadable evidence is None (-> invalid), never []
        rec["cli_versions_observed"], rec["cli_versions_error"] = None, f"{type(e).__name__}: {e}"


# ---- bank-access evidence (VALIDITY READINGS (d): recorded, never a validity clause) -------------------

BANK_COMMIT_PREFIX = BANK_FROZEN_HASH[:10]  # "d68871742a"; V-E1-BANK-ACCESS pins the match
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


def torn_tail(path):
    """-> a problem string when results.jsonl is non-empty and its last byte is not a newline (a write cut before
    its "\n", or a hand repair): appending would fuse the next record onto that line. None otherwise."""
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            if fh.tell() == 0:
                return None
            fh.seek(-1, os.SEEK_END)
            last = fh.read(1)
    except FileNotFoundError:
        return None
    return None if last == b"\n" else f"torn tail: {path} does not end in a newline"


def append_record(path, rec):
    """Append one record as one fsynced line; refuses (ContractError, nothing written) onto a torn tail."""
    problem = torn_tail(path)
    if problem:
        raise K.ContractError(problem)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# ---- one counted run ---------------------------------------------------------------------------------

def _red_with_line(g):
    return g.get("rc") != 0 and "E1J_PASS=" in str(g.get("summary") or "")


def _steps(bank, t, arm, attempt, base, rid, rec, box, excl, excluded, cli_version, append, exec_fn, drift_fn):
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

    def started(pid, pid_start):  # the session process exists and nothing has waited on it yet
        append({"kind": "run_start", "run_id": rid, "task": t["id"], "rule": t["rule"], "arm": arm,
                "attempt": attempt, "base": base, "wt": str(wt), "started": rec["started"],
                "started_epoch": rec["started_epoch"], "cli_version": cli_version, "excluded": excluded,
                "session_pid": pid, "session_pid_start": pid_start})
    session(wt, bank.JPROMPT.format(module=t["module"]), arm, rec, excl, exec_fn=exec_fn, on_spawn=started)
    rec["session_changed_paths"] = snapshot_diff(before, tree_snapshot(wt))
    g = grade(bank, wt, t)
    rec["grade_rc"], rec["grade_summary"] = g["rc"], g["summary"]
    rec["grade_passed"], rec["grade_total"], rec["grade_fails"] = g["passed"], g["total"], g["fails"]
    try:  # the bank graded with must still be the frozen bank (a mid-session edit would be graded into this run)
        rec["bank_drift_after"] = list(drift_fn()) if drift_fn is not None else None
    except Exception as e:
        rec["bank_drift_after"] = [f"bank drift unreadable: {_err(e)}"]


def check_arm_excludes(arm, excl):
    """VALIDITY READINGS (c): arm A carries no excludes and arm B all 13; any other pair is refused before launch."""
    excluded = list(excl)
    if (arm, len(excluded)) not in (("A", 0), ("B", 13)):
        raise ValueError(f"arm {arm!r} with {len(excluded)} excludes: want ('A', 0) or ('B', 13)")
    return excluded


def one_run(bank, t, arm, attempt, base, *, excl, cli_version, append, run_id=None, exec_fn=None,
            projects=PROJECTS, drift_fn=None):
    """One counted run -> the run record. Appends only the run_start record; the caller appends the run record.
    drift_fn() -> bank-drift problems, re-run after the post-session grade (None: never re-checked, so a launched
    run is invalid)."""
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
        _steps(bank, t, arm, attempt, base, rid, rec, box, excl, excluded, cli_version, append, exec_fn, drift_fn)
    except Exception as e:  # recorded, never swallowed: the absent fields make the run invalid
        rec["error"] = f"{type(e).__name__}: {e}"
    finally:
        wt = box["wt"]
        if rec.get("session_launched"):
            try:
                rec["metrics"] = metrics(rec.get("session_id", ""), wt, rec["started_epoch"], projects)
            except Exception as e:
                rec["metrics"] = {"state": "UNMEASURED", "reason": f"metrics error {type(e).__name__}: {e}"}
            _observe_versions(rec)
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


# ---- preflight: the world the contract measures (plan 02-03) ----------------------------------------------

def git(*args, cwd=REPO, check=True, input=None):
    """The runner's own git helper (it checks the bank, so it does not borrow the bank's). `input` (str or bytes)
    is passed on stdin."""
    if isinstance(input, bytes):
        input = input.decode("utf-8")
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=child_env(), input=input)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args[:3])} failed: {r.stderr.strip()[:300]}")
    return r


def e1_rules(packet=PACKET):
    """The 11 rules E1 decides: the 13 packet rules minus the two R2 decided (relative to ~/.claude)."""
    return [r["rule"] for r in packet_rules(packet) if r["rule"] not in EXCLUDED_BY_R2]


def ordered_tasks(bank, packet=PACKET):
    """bank.tasks() extended with the packet's rule_bytes, in contract order (e1_contract.contract_order)."""
    pk = {r["rule"]: r for r in packet_rules(packet)}
    out = []
    for t in bank.tasks():
        if t["rule"] not in pk:
            raise K.ContractError(f"task {t['id']}: rule {t['rule']} is not a packet rule")
        out.append(dict(t, rule_bytes=pk[t["rule"]]["bytes"]))
    return K.contract_order(out, e1_rules(packet))


def _sha256_lf(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def check_pins(packet=PACKET, home=None):
    """-> (ok_count, problems). Reads each of the 13 packet rules under <home>/.claude in binary READ mode only,
    LF-normalises, and compares the sha256 with the packet's sha256_lf; a packet that is not 13 distinct rules is a
    problem too. Its own implementation, so the check does not depend on a bank being loadable."""
    home = Path(home) if home is not None else Path.home()
    rules = packet_rules(packet)
    ok, bad = 0, rule_set_problems(rules)
    for r in rules:
        f = home / ".claude" / r["rule"]
        try:
            with open(f, "rb") as fh:  # read-only; nothing under ~/.claude is ever opened for writing
                data = fh.read()
        except OSError as e:
            bad.append(f"{r['rule']}: unreadable ({type(e).__name__})")
            continue
        h = _sha256_lf(data)
        if h == r["sha256_lf"]:
            ok += 1
        else:
            bad.append(f"{r['rule']}: sha256 {h[:12]} != pinned {str(r['sha256_lf'])[:12]}")
    return ok, bad


def cli_version(path=CLAUDE):
    """`<path> --version`, stripped. Not a model call and not a session. Raises when it prints nothing or fails."""
    r = subprocess.run([path, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=30)  # subprocess.run looked up at call time (test guard)
    out = (r.stdout or "").strip()
    if r.returncode or not out:
        raise RuntimeError(f"rc {r.returncode}, stdout {out[:60]!r}")
    return out


def check_cli(path, version_fn):
    """-> (problems, version). Only CLAUDE at exactly CLI_VERSION (ADDENDUM-E1 Design) is accepted."""
    if path != CLAUDE:
        return [f"CLI path {path} is not {CLAUDE}"], None
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        return [f"CLI {path} is not an executable file"], None
    try:
        v = str(version_fn()).strip()
    except Exception as e:
        return [f"version unreadable: {type(e).__name__}"], None
    tok = v.split()[0] if v.split() else ""
    if tok != CLI_VERSION:
        return [f"CLI version {tok or repr(v)} != {CLI_VERSION} (ADDENDUM-E1 Design)"], v
    return [], v


_HEX40 = re.compile(r"[0-9a-f]{40}\n?")


def bank_drift(repo, bank_rel, frozen_file, info=None):
    """-> problems. Compares every file of the bank at the commit in BANK_FROZEN_AT with the WORKING-TREE bytes the
    runner grades with (jgrade copies working-tree files; a commit-to-commit diff would miss an uncommitted edit).
    __pycache__ directories are skipped; symlinks are never followed. `info` (optional dict) receives files/frozen."""
    repo = Path(repo)
    bank_rel = str(bank_rel).strip("/") if not Path(str(bank_rel)).is_absolute() else str(bank_rel)
    frozen_file = Path(frozen_file)
    if not frozen_file.is_file():
        return [f"BANK_FROZEN_AT missing: {frozen_file}"]
    try:
        raw = frozen_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"BANK_FROZEN_AT unreadable: {type(e).__name__}"]
    if not _HEX40.fullmatch(raw):
        return [f"BANK_FROZEN_AT malformed: {raw[:60]!r}"]
    h = raw.strip()
    if git("cat-file", "-e", h + "^{commit}", cwd=repo, check=False).returncode:
        return [f"frozen commit {h[:10]} not in this repository"]
    listing = git("ls-tree", "-r", "-z", h, "--", bank_rel, cwd=repo).stdout
    frozen = {}
    for entry in listing.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        frozen[path] = meta.split()[2]
    if not frozen:
        return [f"frozen commit {h[:10]} holds no {bank_rel}"]
    problems = []
    present = []
    for path in sorted(frozen):
        f = repo / path
        if f.is_symlink() or not f.is_file():
            problems.append(f"missing since freeze: {path}")
        else:
            present.append(path)
    if present:
        hashes = git("hash-object", "--", *present, cwd=repo).stdout.split()
        if len(hashes) != len(present):
            raise RuntimeError(f"git hash-object returned {len(hashes)} hashes for {len(present)} files")
        for path, got in zip(present, hashes):
            if got != frozen[path]:
                problems.append(f"edited since freeze: {path}")
    root = repo / bank_rel

    def _raise(e):
        raise e
    try:  # a directory the walk cannot list could hide an added file: unreadable, never "nothing added"
        for dirpath, dirnames, filenames in os.walk(root, onerror=_raise, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            links = [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]
            for name in sorted(filenames) + links:
                rel = Path(os.path.join(dirpath, name)).relative_to(repo).as_posix()
                if rel not in frozen:
                    problems.append(f"added since freeze: {rel}")
    except OSError as e:
        problems.append(f"bank unreadable: {e.filename or root} ({type(e).__name__})")
    if info is not None:
        info.update(files=len(frozen), frozen=h)
    return problems


def read_records(path):
    """results.jsonl -> list of dicts. Absent file -> []; blank lines skipped; any other non-object line raises."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with open(p, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except ValueError:
                o = None
            if not isinstance(o, dict):
                raise K.ContractError(f"results line {n} malformed")
            out.append(o)
    return out


def _bank_rel(bank_dir, repo):
    try:
        return Path(bank_dir).resolve().relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        return Path(bank_dir).resolve().as_posix()


def _err(e):
    return f"{type(e).__name__}: {e}" if str(e) else type(e).__name__


def preflight(*, bank_dir=BANK_DIR, bank=None, repo=REPO, frozen=FROZEN, results=RESULTS, packet=PACKET, home=None,
              cli_path=CLAUDE, version_fn=cli_version, drift_fn=bank_drift, packet_sha256=PACKET_SHA256,
              frozen_hash=BANK_FROZEN_HASH):
    """-> [(name, ok, detail)] for cli, packet, pins, excludes, bank, bank_drift, freeze_check, base, index,
    results, in that order (bank_drift also refuses a BANK_FROZEN_AT other than frozen_hash). Every check is evaluated (a failure never hides a later one); no check writes anything and none
    starts a session. cli_path can only make the check stricter: any value but CLAUDE is refused."""
    out = []

    def run(name, fn):
        try:
            ok, detail = fn()
        except (Exception, SystemExit) as e:  # a crashing check is a refusal, never an escape
            ok, detail = False, _err(e)
        out.append((name, bool(ok), str(detail)))
        return ok

    def c_cli():
        probs, v = check_cli(cli_path, version_fn)
        return (not probs, v if not probs else "; ".join(probs))

    def c_packet():
        probs = check_packet(packet, packet_sha256)
        return (not probs, f"sha256 {packet_sha256[:12]}" if not probs else "; ".join(probs))

    def c_pins():
        n, bad = check_pins(packet, home)
        return (n == 13 and not bad, f"{n}/13" if not bad else f"{n}/13 " + "; ".join(bad))

    def c_excludes():
        ex = excludes(packet, home)
        absent = [p for p in ex if not os.path.isfile(p)]
        return (not absent, f"{len(ex)} paths" if not absent else f"not a file: {absent}")

    box = {"bank": bank, "base": None}

    def c_bank():
        if box["bank"] is not None:
            return True, f"given ({Path(getattr(box['bank'], 'HERE', bank_dir))})"
        if not (Path(bank_dir) / "validate_bank.py").is_file():
            return False, f"no validate_bank.py in {bank_dir}"
        try:
            box["bank"] = load_bank(bank_dir)
        except SystemExit as e:
            return False, f"bank not loadable: {e}"
        return True, _bank_rel(bank_dir, repo)

    bank_rel = _bank_rel(bank_dir, repo)

    def c_drift():
        info = {}
        probs = check_frozen_pin(frozen, frozen_hash) + list(drift_fn(repo, bank_rel, frozen, info=info))
        if probs:
            return False, "; ".join(probs)
        h = info.get("frozen") or Path(frozen).read_text(encoding="utf-8").strip()
        return True, f"{info.get('files', '?')} files match {h[:10]}"

    def need():
        if box["bank"] is None:
            raise _NoBank()
        return box["bank"]

    def c_freeze():
        b = need()
        fc = getattr(b, "freeze_check", None)
        if fc is None:
            return False, "bank has no freeze_check (not the plan 01-05 frozen bank)"
        probs = fc(repo, bank_rel, frozen)
        if probs:
            return False, "; ".join(map(str, probs))
        return True, Path(frozen).read_text(encoding="utf-8").strip()[:10]

    def c_base():
        b = need()
        box["base"] = b.jbase()
        return True, box["base"][:10]

    def c_index():
        b = need()
        f = Path(b.HERE) / "index.json"
        if not f.is_file():
            return False, f"no index.json in {b.HERE}"
        idx = json.loads(f.read_text(encoding="utf-8"))
        want = [t["id"] for t in ordered_tasks(b, packet)]
        items = idx.get("tasks") or []
        got = [t.get("id") for t in items]
        probs = []
        if got != want:
            probs.append(f"ids {got} != contract order {want}")
        if len(items) != K.MAX_TASKS:
            probs.append(f"{len(items)} tasks, want {K.MAX_TASKS}")
        if idx.get("missing") != []:
            probs.append(f"missing {idx.get('missing')!r}, want []")
        pk = {r["rule"]: r for r in packet_rules(packet)}
        for t in items:
            r = pk.get(t.get("rule"))
            if r is None or t.get("rule_bytes") != r["bytes"] or t.get("sha256_lf") != r["sha256_lf"]:
                probs.append(f"{t.get('id')}: rule_bytes/sha256_lf differ from the packet")
        note = ""
        if box["base"] is not None:
            if idx.get("base") != box["base"]:
                probs.append(f"index base {str(idx.get('base'))[:10]} != BASE {box['base'][:10]}")
        else:
            note = " (base unchecked: the base check refused)"
        return (not probs, f"{len(items)} tasks{note}" if not probs else "; ".join(probs))

    def c_results():
        b = need()
        recs = read_records(results)
        if not Path(results).exists():
            return True, "absent"
        st = K.replay(ordered_tasks(b, packet), recs)
        if st["stop"]:
            return True, f"{len(recs)} records, stopped {st['stop'].get('condition')}"
        return True, f"{len(recs)} records, open"

    run("cli", c_cli)
    run("packet", c_packet)
    run("pins", c_pins)
    run("excludes", c_excludes)
    run("bank", c_bank)
    run("bank_drift", c_drift)
    for name, fn in (("freeze_check", c_freeze), ("base", c_base), ("index", c_index), ("results", c_results)):
        if box["bank"] is None:
            out.append((name, False, "bank not loaded"))
        else:
            run(name, fn)
    return out


class _NoBank(Exception):
    def __str__(self):
        return "bank not loaded"


def per_run_checks(*, repo=REPO, bank_rel, frozen=FROZEN, packet=PACKET, home=None, cli_path=CLAUDE,
                   version_fn=cli_version, drift_fn=bank_drift, packet_sha256=PACKET_SHA256,
                   frozen_hash=BANK_FROZEN_HASH):
    """The cheap subset run before EVERY counted run (plan 02-04): CLI, packet, pins, freeze hash, bank bytes. A
    rule, the packet or the bank changed mid-campaign voids what follows (packet invalidation list). Every check
    runs; one that raises is a problem, never a pass. -> {"problems": [...], "cli_version": v}."""
    probs, box = [], {"v": None}

    def step(label, fn):
        try:
            probs.extend(fn())
        except Exception as e:
            probs.append(f"{label} unreadable: {_err(e)}")

    def cli():
        p, box["v"] = check_cli(cli_path, version_fn)
        return p

    def pins():
        n, bad = check_pins(packet, home)
        return [] if n == 13 and not bad else [f"pins {n}/13" + (": " + "; ".join(bad) if bad else "")]

    step("cli", cli)
    step("packet", lambda: check_packet(packet, packet_sha256))
    step("pins", pins)
    step("BANK_FROZEN_AT", lambda: check_frozen_pin(frozen, frozen_hash))
    step("bank drift", lambda: drift_fn(repo, bank_rel, frozen))
    return {"problems": probs, "cli_version": box["v"]}


def cmd_preflight(argv, version_fn=cli_version):
    bank_dir = BANK_DIR
    args = list(argv)
    if args[:1] == ["--bank"] and len(args) == 2:
        bank_dir = Path(args[1])
    elif args:
        print("usage: e1_runner.py preflight [--bank DIR]")
        return 2
    checks = preflight(bank_dir=bank_dir, version_fn=version_fn)
    for name, ok, detail in checks:
        print(f"CHECK {name} {'OK' if ok else 'REFUSED'} {detail}")
    bad = [c for c in checks if not c[1]]
    print("PREFLIGHT OK" if not bad else f"PREFLIGHT REFUSED {len(bad)}")
    return 0 if not bad else 1


# ---- the campaign loop (plan 02-04) ---------------------------------------------------------------------

EXIT = {K.ALL_DECIDED: 0, K.HARM_STOP: 3, K.SPEND_STOP: 3, K.SPEND_UNMEASURED: 3, K.POSITIVE_CONTROL_STOP: 3,
        "REFUSED": 1, "COMMIT_FAILED": 1, "PAUSED": 4}
LOOP_BOUND = 4 * K.MAX_TASKS * K.MAX_ATTEMPTS + 10
COAUTHOR = "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
INTERRUPTED = "runner interrupted: run_start without a run record"


class SessionAlive(RuntimeError):
    """reconcile refused: the interrupted run's session process is still running."""


def reconcile(bank, start, *, projects=PROJECTS, alive_fn=session_alive):
    """-> the run record for a run_start that has none (the runner was killed during a session). The session is
    taken as launched; its spend is measured from the attempt-unique run tree's transcript (no session id needed),
    or is None (-> SPEND_UNMEASURED). No grade ran, so the record is invalid and the rerun-once rule applies.
    While the run_start's session process (pid + /proc start time) is still alive it raises SessionAlive before
    measuring or dropping anything: a transcript that is still growing is never measured."""
    pid = start.get("session_pid")
    if pid is not None and alive_fn(pid, start.get("session_pid_start")):
        raise SessionAlive(f"session still alive pid {pid}")
    rec = {k: start.get(k) for k in ("run_id", "task", "rule", "arm", "attempt", "base", "cli_version", "excluded",
                                     "started", "started_epoch")}
    rec.update(kind="run", cli=CLAUDE, model=MODEL, session_launched=True, error=INTERRUPTED)
    wt = Path(str(start.get("wt") or ""))
    try:
        rec["metrics"] = metrics("", wt, float(start.get("started_epoch") or 0), projects)
    except Exception as e:
        rec["metrics"] = {"state": "UNMEASURED", "reason": f"metrics error {_err(e)}"}
    _observe_versions(rec)
    tp = rec["metrics"].get("transcript")
    try:
        rec["bank_access"] = bank_access(tp, bank_markers(getattr(bank, "HERE", BANK_DIR))) if tp else None
    except Exception as e:
        rec["bank_access"], rec["bank_access_error"] = None, _err(e)
    if start.get("wt") and os.path.lexists(str(wt)):
        try:
            rec["worktree_removed"] = bank.drop_tree(wt)
        except Exception as e:
            rec["worktree_removed"], rec["drop_error"] = False, _err(e)
    else:
        rec["worktree_removed"] = True
    rec["ended"] = _now()
    rec["valid"], rec["invalid_reasons"] = K.run_valid(rec)
    rec["task_pass"] = K.task_pass(rec)
    rec["spend"] = K.run_spend(rec)
    return rec


def drive(order, *, results, run_fn, check_fn, reconcile_fn, commit_fn=None, max_pairs=None,
          r2_rules=EXCLUDED_BY_R2, out=print, dirty_fn=None):
    """The campaign loop -> (exit code, condition). State is recomputed from results.jsonl on every iteration
    (e1_contract.replay), so a resume is the same computation as a first start. Before every run check_fn() runs
    (CLI, pins, bank bytes); a problem appends a refusal record and stops before any session. run_fn(task, arm,
    attempt, ctx) returns the run record, which drive appends. commit_fn(subject) commits results.jsonl after every
    pair, stop and refusal record (None: no commit). dirty_fn() -> True when results.jsonl differs from what git
    holds: at the start and on HALTED a dirty file is committed first (a record whose commit was lost to a crash or
    a failed commit), or the drive ends COMMIT_FAILED. A reconcile that raises (SessionAlive: the interrupted
    session still runs) is a refusal with nothing appended."""
    results = Path(results)
    paired_here = 0

    def commit(subject):
        if commit_fn is None:
            return True
        try:
            commit_fn(subject)
            return True
        except Exception as e:
            out(f"E1-RUN COMMIT_FAILED {_err(e)}")
            return False

    def recommit(subject):
        if commit_fn is None or dirty_fn is None:
            return True
        try:
            dirty = dirty_fn()
        except Exception as e:  # an unreadable git status is never "clean"
            out(f"E1-RUN COMMIT_FAILED status unreadable {_err(e)}")
            return False
        return commit(subject) if dirty else True

    if not recommit("data(e1): recommit results left uncommitted"):
        return EXIT["COMMIT_FAILED"], "COMMIT_FAILED"
    for _ in range(LOOP_BOUND):
        try:
            torn = torn_tail(results)
            if torn:
                raise K.ContractError(torn)
            records = read_records(results)
            state = K.replay(order, records)
        except K.ContractError as e:
            out(f"E1-RUN REFUSED {e}")
            return EXIT["REFUSED"], "REFUSED"
        if state["stop"] is None:  # a stopped file is never appended to again
            for t in state["tasks"]:
                if t["status"] in (K.PAIR_VALID, K.NO_INFORMATION) and t["id"] not in state["pairs_recorded"]:
                    append_record(results, dict(K.pair_record(state, t["id"]), at=_now()))
                    paired_here += 1
                    k = len(state["pairs_recorded"]) + 1
                    state["pairs_recorded"].append(t["id"])
                    out(f"PAIR {t['id']} {t['decision']}")
                    if not commit(f"data(e1): pair {k} {t['id']} {t['decision']}"):
                        return EXIT["COMMIT_FAILED"], "COMMIT_FAILED"
        act = K.next_action(state)
        if act[0] == "HALTED":
            if not recommit(f"data(e1): stop {act[1]} (recommit)"):
                return EXIT["COMMIT_FAILED"], "COMMIT_FAILED"
            out(f"E1-RUN HALTED {act[1]}")
            return EXIT.get(act[1], 1), act[1]
        if act[0] == "RECONCILE":
            start = next(r for r in reversed(records) if r.get("kind") == "run_start" and r.get("run_id") == act[1])
            try:
                rec = reconcile_fn(start)
            except Exception as e:  # nothing is measured or appended while the session may still be spending
                out(f"E1-RUN REFUSED reconcile {act[1]}: {_err(e)}")
                return EXIT["REFUSED"], "REFUSED"
            append_record(results, rec)
            out(f"RECONCILED {act[1]} valid={rec.get('valid')} spend={rec.get('spend')} "
                f"reasons={rec.get('invalid_reasons')}")
            continue
        if act[0] == "STOP":
            cond = act[1]
            n = len(state["pairs_recorded"])
            append_record(results, dict(K.stop_record(state, cond, r2_rules), at=_now()))
            if not commit(f"data(e1): stop {cond} after {n} pairs"):
                return EXIT["COMMIT_FAILED"], "COMMIT_FAILED"
            out(f"E1-RUN {cond} pairs={n} spent={state['spent']}")
            return EXIT[cond], cond
        _, task, arm, attempt = act
        rid = K.run_id(task, arm, attempt)
        if max_pairs is not None and paired_here >= max_pairs:
            out("E1-RUN PAUSED")
            return EXIT["PAUSED"], "PAUSED"
        try:  # a check that raises is a refusal, never a pass
            ctx = check_fn()
            if not isinstance(ctx, dict):
                raise TypeError(f"check_fn returned {type(ctx).__name__}, want dict")
        except Exception as e:
            ctx = {"problems": [f"per-run check raised: {_err(e)}"], "cli_version": None}
        if ctx.get("problems"):
            append_record(results, {"kind": "refusal", "before": rid, "problems": list(ctx["problems"]),
                                    "at": _now()})
            if not commit(f"data(e1): refusal before {rid}"):
                return EXIT["COMMIT_FAILED"], "COMMIT_FAILED"
            out(f"E1-RUN REFUSED {'; '.join(map(str, ctx['problems']))}")
            return EXIT["REFUSED"], "REFUSED"
        rec = run_fn(task, arm, attempt, ctx)
        append_record(results, rec)
        m = rec.get("metrics") if isinstance(rec.get("metrics"), dict) else {}
        sp = rec.get("spend")
        total = state["spent"] + sp if isinstance(state["spent"], int) and isinstance(sp, int) else None
        out(f"RUN {rec.get('run_id')} valid={rec.get('valid')} pass={rec.get('task_pass')} "
            f"first_ctx={m.get('first_call_context')} total_ctx={m.get('total_context')} spent={total} "
            f"reasons={rec.get('invalid_reasons')}")
        drift = rec.get("bank_drift_after")
        if drift:  # the bank moved during the run: this run is invalid and nothing after it may be counted
            probs = ["bank drift during run"] + [str(x) for x in drift]
            append_record(results, {"kind": "refusal", "after": rec.get("run_id"), "problems": probs, "at": _now()})
            if not commit(f"data(e1): refusal after {rec.get('run_id')}"):
                return EXIT["COMMIT_FAILED"], "COMMIT_FAILED"
            out(f"E1-RUN REFUSED {'; '.join(probs)}")
            return EXIT["REFUSED"], "REFUSED"
    raise K.ContractError(f"drive: no terminal state within {LOOP_BOUND} iterations (a loop that never ends is a "
                          "defect, never a wait)")


def commit_results(repo, paths, subject, body=""):
    """Commit exactly `paths` (pathspec: other staged work stays staged and out of the commit), then verify
    `git log -1 --format=%s` equals subject. A mismatch raises and leaves the commit as is (never amended, reset or
    rewritten; the operator reconciles). No push, no --no-verify, no --amend, no force. -> the new HEAD hash."""
    paths = [str(p) for p in paths]
    msg = subject + "\n\n" + (body.rstrip("\n") + "\n\n" if body else "") + COAUTHOR + "\n"
    git("add", "--", *paths, cwd=repo)
    git("commit", "-q", "-F", "-", "--", *paths, cwd=repo, input=msg)
    got = git("log", "-1", "--format=%s", cwd=repo).stdout.strip()
    if got != subject:
        raise RuntimeError(f"commit subject {got!r} != written {subject!r} (commit left as is)")
    return git("rev-parse", "HEAD", cwd=repo).stdout.strip()


def results_dirty(repo, path):
    """True when git status lists results.jsonl (modified or untracked). Read-only."""
    return bool(git("status", "--porcelain", "--", str(path), cwd=repo).stdout.strip())


def _opts(argv, flags, valued):
    """-> dict or None (usage). flags: options without a value; valued: {option: converter}."""
    out, args = {}, list(argv)
    while args:
        a = args.pop(0)
        if a in flags:
            out[a] = True
        elif a in valued and args:
            try:
                out[a] = valued[a](args.pop(0))
            except ValueError:
                return None
        else:
            return None
    return out


def _pos(v):
    n = int(v)
    if n < 1:
        raise ValueError(v)
    return n


def cmd_plan(argv):
    """The dry view of the campaign: no worktree, no session, no preflight, no write."""
    o = _opts(argv, (), {"--bank": Path, "--results": Path})
    if o is None:
        print("usage: e1_runner.py plan [--bank DIR] [--results PATH]")
        return 2
    try:
        bank = load_bank(o.get("--bank", BANK_DIR))
        order = ordered_tasks(bank)
        state = K.replay(order, read_records(o.get("--results", RESULTS)))
        act = K.next_action(state)
    except (Exception, SystemExit) as e:  # a missing or bad bank is a refusal, never a fallback
        print(f"PLAN REFUSED {_err(e)}")
        return 1
    for t, st in zip(order, state["tasks"]):
        print(f"TASK {st['position'] + 1} {t['id']} {t['rule']} bytes={t['rule_bytes']} arms={','.join(st['arms'])} "
              f"status={st['status']} decision={st['decision'] or '-'}")
    spent = state["spent"] if state["spent"] is not None else "UNKNOWN"
    print(f"SPENT {spent} CAP {K.CAP} RUNS {state['runs_counted']} VALID_PAIRS {len(state['valid_pairs'])}")
    print("NEXT " + " ".join(str(x) for x in act))
    return 0


def cmd_run(argv, *, frozen=FROZEN, results=RESULTS, version_fn=cli_version):
    """The counted campaign over BANK_DIR. frozen / results / version_fn exist for the refusal gate: they can only
    point the run at a stricter or emptier world, never skip a check."""
    o = _opts(argv, ("--no-commit",), {"--max-pairs": _pos})
    if o is None:
        print("usage: e1_runner.py run [--max-pairs N] [--no-commit]")
        return 2
    checks = preflight(bank_dir=BANK_DIR, frozen=frozen, results=results, version_fn=version_fn)
    bad = [c for c in checks if not c[1]]
    if bad:
        for name, ok, detail in checks:
            print(f"CHECK {name} {'OK' if ok else 'REFUSED'} {detail}")
        print(f"E1-RUN REFUSED {len(bad)}")
        return 1
    bank = load_bank(BANK_DIR)
    order = ordered_tasks(bank)
    by_id = {t["id"]: t for t in order}
    base = bank.jbase()
    excl = excludes()
    bank_rel = _bank_rel(BANK_DIR, REPO)

    def run_fn(task, arm, attempt, ctx):
        return one_run(bank, by_id[task], arm, attempt, base, excl=excl if arm == "B" else [],
                       cli_version=ctx["cli_version"], append=lambda r: append_record(results, r),
                       drift_fn=lambda: check_frozen_pin(frozen) + bank_drift(REPO, bank_rel, frozen))

    def check_fn():
        return per_run_checks(bank_rel=bank_rel, frozen=frozen, version_fn=version_fn)

    commit_fn = None if o.get("--no-commit") else (lambda subject: commit_results(REPO, [results], subject))
    return drive(order, results=results, run_fn=run_fn, check_fn=check_fn,
                 reconcile_fn=lambda start: reconcile(bank, start), commit_fn=commit_fn,
                 max_pairs=o.get("--max-pairs"), dirty_fn=lambda: results_dirty(REPO, results))[0]


def main(argv):
    cmd, rest = (argv[0], argv[1:]) if argv else (None, [])
    if cmd == "plan":
        return cmd_plan(rest)
    if cmd == "preflight":
        return cmd_preflight(rest)
    if cmd == "run":
        return cmd_run(rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
