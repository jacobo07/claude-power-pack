#!/usr/bin/env python3
"""Mission execution binding (AMCR, plan vault/plans/amcr-mission-continuity-20261015.md).

Execution location is mission state. A mission record carries ``binding``: the git worktree its
worker actually writes, with a generation that grows on every rebind. Every observer -- the cost
breaker, the relay, AMR recovery, the card -- asks ``execution_root`` instead of deriving
``work_dir or cwd`` on its own.

Why (measured 2026-10-15, m-4e31db7aca3f, Credit Score Engine): Claude Code's background-session
isolation refused edits in the shared checkout, the worker made ``Credit Score Engine-wt`` with
``git worktree add`` and moved there with Set-Location (its transcript ``cwd`` never changed), committed,
and launched a researcher. The breaker fingerprinted the untouched main checkout and stopped a working
mission at "5,051,831 processed since the work tree last changed". Third instance of the class in five
days (m-4a0f39b59a60 add_dirs, m-07a78fbae3c7 excluded .planning).

Kill switch: CPP_MISSION_CONTINUITY=off restores the old ``work_dir or cwd`` observers.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

CHILD_RECENT_S = 600            # a child whose transcript moved within this window is working
CHILD_EXTRA_STALL_BUDGETS = 1   # a working child earns at most this many extra stall budgets
UNKNOWN_INCIDENT_STREAK = 3     # consecutive unmeasurable trips before a surfaced incident

# Progress Reconciliation Gate outcomes.
GOOD = "GOOD_PROGRESS"
TOPOLOGY_CHANGED = "TOPOLOGY_CHANGED"
CHILD_ACTIVE = "CHILD_ACTIVE"
PROGRESS_UNKNOWN = "PROGRESS_UNKNOWN"
STALE_GENERATION = "STALE_GENERATION"
ZERO_CONFIRMED = "ZERO_PROGRESS_CONFIRMED"
NO_TRIP = "NO_TRIP"

# Child obligation states (the obligation outlives the executor).
OUTSTANDING_CHILD_STATES = ("KILLED_WITH_PARENT", "LOST", "RETRYABLE")
CHILD_STATES = OUTSTANDING_CHILD_STATES + ("COMPLETED", "SUPERSEDED", "CANCELLED")

# A known GSD child type and the artifact whose existence completes its obligation.
GSD_CHILD_ARTIFACT = {"gsd-phase-researcher": "-RESEARCH.md", "gsd-planner": "-PLAN.md",
                      "gsd-pattern-mapper": "-PATTERNS.md", "gsd-verifier": "-VERIFICATION.md"}


class BindError(Exception):
    pass


def enabled() -> bool:
    return os.environ.get("CPP_MISSION_CONTINUITY", "on").strip().lower() not in ("off", "0", "false", "no")


def _norm(p: str) -> str:
    return os.path.normcase(str(Path(p).resolve()))


def _git(wd: str, *args: str, timeout: int = 30) -> str | None:
    from gsd_mission import resolve_exe
    g = resolve_exe("git") or "git"
    try:
        r = subprocess.run([g, "-C", wd, *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001 -- unanswered is None, never ""
        return None
    return r.stdout if r.returncode == 0 else None


# ----------------------------------------------------------------------------- the resolver
def binding(rec: dict) -> dict | None:
    b = rec.get("binding")
    return b if isinstance(b, dict) and b.get("root") else None


def generation(rec: dict) -> int:
    return int((binding(rec) or {}).get("gen") or 0)


def legacy_root(rec: dict) -> str:
    """The pre-AMCR derivation, used ONLY behind the kill switch."""
    return rec.get("work_dir") or rec["cwd"]


def execution_root(rec: dict) -> str:
    """THE answer to "where does this mission's work live". A bound root that has disappeared is still
    returned: measuring a missing tree yields None (unmeasured), measuring the main checkout instead
    would be a confident answer about the wrong reality."""
    b = binding(rec) if enabled() else None
    if b:
        return b["root"]
    return legacy_root(rec)


def describe(path: str, cwd: str) -> dict:
    """Facts of a candidate execution root, or BindError: it must be the top of a worktree of the SAME
    repository as the mission's cwd (one git common dir)."""
    from gsd_mission import _git_toplevel_and_common
    if not Path(path).is_dir():
        raise BindError(f"not a directory: {path}")
    here, base = _git_toplevel_and_common(path), _git_toplevel_and_common(cwd)
    if not here or not base:
        raise BindError(f"git could not read {path} or {cwd}")
    if here[1] != base[1]:
        raise BindError(f"{path} is not a worktree of the repository at {cwd}")
    if here[0] != _norm(path):
        raise BindError(f"{path} is inside a worktree, not its top ({here[0]})")
    head = (_git(path, "rev-parse", "HEAD") or "").strip() or None
    branch = (_git(path, "rev-parse", "--abbrev-ref", "HEAD") or "").strip() or None
    cwd_head = (_git(cwd, "rev-parse", "HEAD") or "").strip()
    base_rev = (_git(path, "merge-base", "HEAD", cwd_head) or "").strip() if head and cwd_head else ""
    return {"root": str(Path(path).resolve()), "common": here[1], "branch": branch, "head": head,
            "base": base_rev or None}


def new_binding(rec: dict, path: str, cause: str, now: float) -> dict:
    facts = describe(path, rec["cwd"])
    prev = binding(rec)
    return {**facts, "gen": generation(rec) + 1, "bound_at": now, "cause": cause,
            "previous": prev["root"] if prev else None}


# ----------------------------------------------------------------------------- rebind detection
def worktrees(cwd: str) -> list[dict] | None:
    out = _git(cwd, "worktree", "list", "--porcelain")
    if out is None:
        return None
    rows, cur = [], {}
    for line in out.splitlines() + [""]:
        if not line.strip():
            if cur.get("root"):
                rows.append(cur)
            cur = {}
        elif line.startswith("worktree "):
            cur["root"] = str(Path(line[9:].strip()).resolve())
        elif line.startswith("HEAD "):
            cur["head"] = line[5:].strip()
        elif line.startswith("branch "):
            cur["branch"] = line[7:].strip().replace("refs/heads/", "")
    return rows


def created_at(root: str) -> float | None:
    """When a linked worktree was added: its admin dir's `commondir` file is written once, by `add`."""
    dotgit = Path(root) / ".git"
    try:
        if not dotgit.is_file():
            return None
        line = dotgit.read_text(encoding="utf-8", errors="replace").strip()
        admin = Path(line.split(":", 1)[1].strip()) if line.startswith("gitdir:") else None
        if admin and not admin.is_absolute():
            admin = (Path(root) / admin).resolve()
        f = admin / "commondir" if admin else None
        return f.stat().st_mtime if f and f.is_file() else None
    except (OSError, IndexError):
        return None


def _flat(value) -> str:
    if isinstance(value, dict):
        return " ".join(_flat(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_flat(v) for v in value)
    return str(value) if value is not None else ""


def _canon(text: str) -> str:
    return text.replace("\\", "/").lower()


def tool_text_since(transcript: Path | None, since: float) -> str | None:
    """Everything the worker put in its own tool inputs since `since`, canonical slashes, lower case.
    None = no transcript (unknown, never "mentions nothing")."""
    if not transcript or not Path(transcript).is_file():
        return None
    out = []
    try:
        with open(transcript, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"tool_use"' not in line or '"assistant"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                ts = row.get("timestamp")
                try:
                    from datetime import datetime
                    t = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp() if ts else None
                except ValueError:
                    t = None
                if t is not None and t < since:
                    continue
                for b in (row.get("message") or {}).get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        out.append(_flat(b.get("input")))
    except OSError:
        return None
    return _canon("\n".join(out))


def mentions(text: str, root: str) -> bool:
    """`root` named as a whole path: `.../r8-wt` must not match inside `.../r8-wt2` (measured in V-AMCR-R8)."""
    import re
    forms = {_canon(str(Path(root).resolve())), _canon(root)}
    forms |= {"/" + f[0] + f[2:] for f in list(forms) if len(f) > 2 and f[1] == ":"}   # Git-Bash /c/... form
    for form in forms:
        if re.search(re.escape(form) + r"(?![\w.-])", text):
            return True
    return False


def is_agent_worktree(root: str) -> bool:
    """A harness subagent isolation worktree (`<repo>/.claude/worktrees/agent-*`): a child's scratch, never the
    mission's work root."""
    parts = _canon(str(root)).rstrip("/").split("/")
    return len(parts) >= 3 and parts[-3:-1] == [".claude", "worktrees"] and parts[-1].startswith("agent-")


def worker_cwd(transcript: Path | None, tail_bytes: int = 512 * 1024) -> str | None:
    """The worker's own working directory as its transcript last records it (main thread rows only)."""
    if not transcript or not Path(transcript).is_file():
        return None
    try:
        with open(transcript, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - tail_bytes))
            lines = fh.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        if '"cwd"' not in line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue   # the first line of the tail may be cut
        if isinstance(row, dict) and row.get("cwd") and not row.get("isSidechain"):
            return str(row["cwd"])
    return None


def detect_rebind(rec: dict, transcript: Path | None) -> dict | None:
    """Worktrees of the mission's repository that the worker made its own since the current binding:
    added after `bound_at` (or mission start) AND named in the worker's own tool inputs. Both, because a
    worktree another session added is not this mission's, and a path merely read is not a move.
    T1 F4: harness `agent-*` isolation worktrees satisfy both and are excluded. Measured 2026-10-23
    (m-260aa89142c8, 07:59Z): the auto-rebind chose subagent worktree agent-a33215aa. When the worker's own
    last cwd lies in one candidate, that candidate alone is returned.
    None = could not be judged (git or transcript unreadable)."""
    b = binding(rec)
    since = float((b or {}).get("bound_at") or rec.get("created_at") or 0)
    rows = worktrees(rec["cwd"])
    text = tool_text_since(transcript, since - 5)
    if rows is None or text is None:
        return None
    current = _norm(execution_root(rec))
    cands, excluded = [], []
    for w in rows:
        root = w["root"]
        if _norm(root) in (current, _norm(rec["cwd"])):
            continue
        made = created_at(root)
        if made is None or made < since - 5:
            continue
        if mentions(text, root):
            (excluded if is_agent_worktree(root) else cands).append(root)
    wcwd = worker_cwd(transcript)
    if wcwd and len(cands) > 1:
        n = _norm(wcwd)
        hit = [c for c in cands if n == _norm(c) or n.startswith(_norm(c) + os.sep)]
        if len(hit) == 1:
            cands = hit
    return {"candidates": cands, "excluded_agent_worktrees": excluded, "worker_cwd": wcwd}


# ----------------------------------------------------------------------------- children
def subagent_activity(transcript: Path | None) -> float | None:
    """Last write to any subagent transcript of this worker, or None."""
    if not transcript:
        return None
    d = Path(transcript).parent / Path(transcript).stem / "subagents"
    try:
        times = [p.stat().st_mtime for p in d.glob("*.jsonl")]
    except OSError:
        return None
    return max(times) if times else None


def child_active(kids: dict, transcript: Path | None, now: float) -> bool:
    """A pending background child that is demonstrably working: its own transcript moved recently,
    or it was launched recently. A pending child with neither is not evidence of progress."""
    if (kids or {}).get("verdict") != "HOLD" or not kids.get("pending"):
        return False
    last = subagent_activity(transcript)
    young = kids.get("youngest_age_s")
    return bool((last is not None and now - last < CHILD_RECENT_S)
                or (young is not None and young < CHILD_RECENT_S))


def tool_input(transcript: Path | None, tool_use_id: str) -> dict | None:
    if not transcript or not Path(transcript).is_file():
        return None
    try:
        with open(transcript, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if tool_use_id not in line or '"tool_use"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                for b in (row.get("message") or {}).get("content") or []:
                    if isinstance(b, dict) and b.get("id") == tool_use_id:
                        return b.get("input") if isinstance(b.get("input"), dict) else {}
    except OSError:
        return None
    return None


def capture_obligations(rec: dict, kids: dict, transcript: Path | None, state: str, now: float,
                        store: Path) -> list[dict]:
    """Every pending child becomes (or stays) a durable obligation. The prompt is saved under the state
    dir so a successor can run exactly the residual without the dead worker's transcript."""
    have = {o.get("id"): dict(o) for o in rec.get("obligations") or [] if o.get("id")}
    for p in (kids or {}).get("pending") or []:
        oid = p.get("tool_use_id")
        if not oid:
            continue
        o = have.get(oid) or {"id": oid, "created_at": now}
        if o.get("state") and o["state"] not in OUTSTANDING_CHILD_STATES:
            continue                   # closed (COMPLETED/SUPERSEDED/CANCELLED) is never reopened
        inp = tool_input(transcript, oid) or {}
        kind = inp.get("subagent_type") or p.get("tool")
        prompt = inp.get("prompt") or inp.get("command") or ""
        ref = None
        if prompt:
            try:
                store.mkdir(parents=True, exist_ok=True)
                ref = store / f"{oid}.md"
                ref.write_text(f"# Child obligation {oid} ({kind})\n\n{p.get('what') or ''}\n\n{prompt}\n",
                               encoding="utf-8")
            except OSError:
                ref = None             # the obligation is kept without its prompt; the trip is not lost
        o.update({"kind": kind, "what": p.get("what"), "launched_at": p.get("at"), "state": state,
                  "prompt_ref": str(ref) if ref else o.get("prompt_ref"), "updated_at": now,
                  "expect": GSD_CHILD_ARTIFACT.get(str(kind)) or o.get("expect")})
        have[oid] = o
    return list(have.values())


def settle_obligations(rec: dict, root: str, now: float) -> list[dict] | None:
    """Close obligations whose artifact now exists in the bound tree. None = nothing changed."""
    obs = rec.get("obligations") or []
    changed = False
    out = []
    for o in obs:
        o = dict(o)
        exp = o.get("expect")
        if o.get("state") in OUTSTANDING_CHILD_STATES and exp:
            hits = [p for p in (Path(root) / ".planning").rglob(f"*{exp}")
                    if p.stat().st_mtime >= float(o.get("created_at") or 0) - 3600] \
                if (Path(root) / ".planning").is_dir() else []
            if hits:
                o.update(state="COMPLETED", evidence=str(hits[0]), updated_at=now)
                changed = True
        out.append(o)
    return out if changed else None


def outstanding(rec: dict) -> list[dict]:
    return [o for o in rec.get("obligations") or [] if o.get("state") in OUTSTANDING_CHILD_STATES]


def card_lines(rec: dict) -> list[str]:
    """What the successor must know about the execution root and unfinished child work."""
    lines = []
    if enabled():
        lines.append(f"EXECUTION BINDING: gen {generation(rec)}, root {execution_root(rec)}. If you must move the work "
                     f"to another git worktree, declare it right after creating it: python "
                     f"~/.claude/skills/claude-power-pack/tools/gsd_mission.py bind --mission {rec['mission_id']} "
                     f"--path <worktree>  (the supervisor measures progress only where the mission is bound).")
    obs = outstanding(rec)
    if obs:
        lines.append("OUTSTANDING CHILD WORK (its executor died; the obligation did not):")
        for o in obs[:5]:
            lines.append(f"  - {o.get('kind')}: {o.get('what')} [{o.get('state')}] prompt: {o.get('prompt_ref')}")
        lines.append("  Run only what is still missing. When one is done or no longer needed: gsd_mission.py "
                     "obligation --mission <id> --id <obligation id> --state COMPLETED|SUPERSEDED")
    return lines


def false_stall(rec: dict, hold: dict, mark_at: float | None = None) -> dict | None:
    """Did the stall hold judge a tree that was not the mission's, while the mission's own tree changed?

    Both halves are required (review HIGH-1, 2026-10-15). (a) The trip measured another root: a hold the
    reconciled breaker wrote carries `measured` {gen, root}; equal to the current binding means it judged
    this very tree and nothing is reconciled. A legacy hold (no `measured`) measured the cwd. (b) The bound
    root's CONTENT moved inside the window [last mark, trip]: HEAD's tree at the trip differs from the tree
    before the mark -- an empty commit, an amend or a revert pair is not progress. `mark_at` is the mark's
    time from the ledger when the mark itself carries none; with neither there is no window (never "since
    the mission started")."""
    if not enabled() or "since the work tree last changed" not in str(hold.get("reason") or ""):
        return None
    root = execution_root(rec)
    measured = hold.get("measured") or {}
    if measured:
        if _norm(str(measured.get("root") or "")) == _norm(root) and int(measured.get("gen") or 0) == generation(rec):
            return None
    elif _norm(root) == _norm(rec["cwd"]):
        return None
    start = (rec.get("cost_mark") or {}).get("at") or mark_at
    if start is None:
        return None
    start, end = float(start), float(hold.get("set_at") or time.time())
    base = (binding(rec) or {}).get("base")
    out = _git(root, "log", "--format=%H %ct %T", "-n", "200", f"{base}..HEAD" if base else "HEAD")
    if out is None:
        return None
    rows = [ln.split() for ln in out.splitlines() if len(ln.split()) == 3]          # newest first
    inside = [r[0] for r in rows if start <= int(r[1]) <= end + 1]
    if not inside:
        return None
    tree_end = next((r[2] for r in rows if int(r[1]) <= end + 1), None)
    tree_start = next((r[2] for r in rows if int(r[1]) < start), None)
    if tree_start is None:
        tree_start = (_git(root, "rev-parse", f"{base}^{{tree}}") or "").strip() if base else None
    if not tree_end or tree_end == tree_start:
        return None
    return {"root": root, "commits": inside, "tree_start": tree_start, "tree_end": tree_end}
