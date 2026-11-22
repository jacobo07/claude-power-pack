#!/usr/bin/env python3
"""self_improve_unattended.py -- the autonomous self-improve loop (FIXED CORE, hash-pinned).

Spec: vault/specs/self-improve-unattended.md. Owner, 2026-11-22: "deberia ser 100% autonomo y rectificar si hay
alguna que ha aceptado y ha sido contraproducente y mejorarse a si mismo".

Daily: observe -> rectify what was applied before -> tune itself -> apply at most one new change -> report.
Ranking, trend, prompt, tuning and report live in tools/self_improve_policy.py, which the loop may improve.
MEASUREMENT (candidate keys, snapshots, rates) lives HERE, in the pinned core: a loop that could edit how its own
changes are judged could make every change look validated.

The agent runs in claude's --restricted mode (no code-running tools, settings ignored, file tools confined to the
worktree). Its test and code are still EXECUTED by the driver's gates, so the diff may not add dangerous constructs,
and the core, its pin and the Owner's settings are fingerprinted around every agent run and every gate run: a change
there stops the loop and writes its OFF switch.

Git discipline (shared checkout, other panes live): built and tested in a worktree, the MERGED tree tested again,
landed by `checkout <new> -- <paths>` on paths whose content equals the expected blob, plus a compare-and-swap of a
landing branch. Never push, reset, rebase or force. A revert is a forward commit built the same way.

  python tools/self_improve_unattended.py --once        # one daily cycle now
  python tools/self_improve_unattended.py --dry-run     # observe + decide: no agent, no gates, no git writes
  python tools/self_improve_unattended.py --status      # last report
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import self_improve_guard as guard  # noqa: E402

_HOME = Path.home()
GIT = r"C:\Program Files\Git\cmd\git.exe" if os.name == "nt" else "git"
CLAUDE = str(_HOME / ".local" / "bin" / ("claude.exe" if os.name == "nt" else "claude"))
AGENT_MODEL = "sonnet"
LOCK_STALE_S = 3 * 60 * 60          # > the scheduled task's 2 h limit, and the lock is heartbeaten
TEST_RE = re.compile(r"^(tools/test_[\w-]+\.py|hooks/(_?tests)/test-[\w-]+\.js)$")
RETRYABLE = ("PENDING_MERGE", "GREEN_BRANCH")
OPEN = ("APPLIED", "PENDING_MERGE", "GREEN_BRANCH", "STARTED")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Tampered(RuntimeError):
    pass


class GitRefused(RuntimeError):
    pass


class Ctx:
    """Everything the loop touches in the world. Tests replace the callables."""

    def __init__(self, repo: Path = guard.REPO, state: Path | None = None, today: str | None = None):
        self.repo = Path(repo)
        self.claude_state = _HOME / ".claude" / "state"
        self.state = Path(state) if state else self.claude_state / "self-improve"
        self.pin_path = self.repo / "vault" / "self_improve" / "guard.sha256"
        self.seed_params = self.repo / "vault" / "self_improve" / "params.json"
        self.today = today or date.today().isoformat()
        self.regression = list(guard.REGRESSION_BLOCK)
        self.watched = list(guard.WATCHED_OUTSIDE)
        self.python = sys.executable
        self.node = "node"
        self.dry_run = False
        self.baseline_fp: dict | None = None

    def agent_cmd(self, prompt: str) -> list:
        return [CLAUDE, "-p", prompt, "--model", AGENT_MODEL, *guard.AGENT_FLAGS]

    # -- replaceable effects
    def analyze(self) -> dict:
        cmd = [self.python, str(self.repo / "tools" / "analyze_transcripts.py"), "--all-projects", "--days", "1",
               "--json", "--max-files", "800", "--max-seconds", "900"]
        res = subprocess.run(cmd, cwd=str(self.repo), capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=1200)
        if res.returncode == 3:
            return {"status": "EMPTY", "candidates": [], "coverage": {}}
        if res.returncode != 0:
            raise RuntimeError(f"analyze rc={res.returncode}: {(res.stderr or '')[-300:]}")
        return json.loads(res.stdout)

    def run_agent(self, prompt: str, cwd: Path) -> tuple:
        try:
            res = subprocess.run(self.agent_cmd(prompt), cwd=str(cwd), capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=guard.AGENT_TIMEOUT_S)
            return res.returncode, res.stdout or ""
        except subprocess.TimeoutExpired:
            return "timeout", ""

    def spend_refusal(self) -> str | None:
        import model_spend_gate
        return model_spend_gate.refusal("self_improve_unattended")

    def ram(self) -> float | None:
        return guard.free_ram_pct()

    def publish(self, claim: str) -> None:
        try:
            sys.path.insert(0, str(self.repo / "modules" / "parallel_mesh"))
            import pm_03_bus
            pm_03_bus.publish_session_findings(str(self.repo), [{
                "topic": "self-improve daily", "claim": claim,
                "evidence": str(self.state / "STATUS.md")}], sid="self-improve")
        except Exception:  # noqa: BLE001 -- reporting is fail-open
            pass


# ---------------------------------------------------------------- small io
def _load(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _persist(ctx: Ctx, ledger: dict) -> None:
    """Saved right after every landing or revert, so a hard kill cannot lose the safety net's record."""
    if not ctx.dry_run:
        _save(ctx.state / "ledger.json", ledger)


def _receipt(ctx: Ctx, payload: dict) -> None:
    try:
        ctx.state.mkdir(parents=True, exist_ok=True)
        with open(ctx.state / "receipts.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": _now_iso(), **payload}, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def _redact(text: str, n: int = 200) -> str:
    try:
        import transcript_events as te
        return te.redact(text or "", n)
    except Exception:  # noqa: BLE001
        return re.sub(r"[A-Za-z0-9_\-]{32,}", "[REDACTED]", (text or ""))[:n]


# ---------------------------------------------------------------- measurement (core: the loop's judge)
def _key(c: dict) -> str:
    """A stable identity across days: kind + subject, never the counts in the title."""
    kind = c.get("kind", "?")
    title = str(c.get("title") or "")
    m = re.match(r"Hook (\S+)", title)
    if kind in ("hook-timeout", "hook-latency") and m:
        return f"{kind}:{m.group(1)}"
    if kind in ("hook-block", "repeated-failure"):
        return f"{kind}:{title.split(' -- ')[0].strip('` ')[:80]}"
    return kind


def _snapshot(result: dict, day: str) -> dict:
    cov = result.get("coverage") or {}
    metrics, cands = {}, []
    for c in result.get("candidates") or []:
        k = _key(c)
        try:
            score = float(c.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        metrics[k] = metrics.get(k, 0.0) + score
        cands.append({"key": k, "kind": c.get("kind"), "score": score,
                      "title": _redact(str(c.get("title") or ""), 160), "owner": _redact(str(c.get("owner") or ""), 160),
                      "change": _redact(str(c.get("change") or ""), 300),
                      "validate": _redact(str(c.get("validate") or ""), 200)})
    return {"date": day, "status": result.get("status"), "sessions": int(cov.get("sessions_with_events") or 0),
            "metrics": metrics, "candidates": cands}


def _rate(snaps: list, key: str) -> tuple:
    tot = sum(float((s.get("metrics") or {}).get(key, 0.0)) for s in snaps)
    ses = sum(int(s.get("sessions") or 0) for s in snaps)
    return ((tot / ses) if ses else 0.0, tot, ses)


# ---------------------------------------------------------------- integrity around executed code
def _check_tamper(ctx: Ctx, where: str) -> None:
    if ctx.baseline_fp is None:
        return
    why = guard.tamper(ctx.baseline_fp, guard.fingerprint(ctx.pin_path, ctx.repo, ctx.watched))
    if why:
        raise Tampered(f"after {where}: {why}")


# ---------------------------------------------------------------- git
def git(ctx: Ctx, args: list, cwd: Path | None = None, check: bool = True):
    why = guard.git_refusal(args)
    if why:
        raise GitRefused(why)
    res = subprocess.run([GIT, *args], cwd=str(cwd or ctx.repo), capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(map(str, args[:3]))} rc={res.returncode}: {res.stderr.strip()[-300:]}")
    return res


def _rev(ctx: Ctx, ref: str, cwd: Path | None = None) -> str:
    return git(ctx, ["rev-parse", ref], cwd=cwd).stdout.strip()


def _branch(ctx: Ctx) -> str:
    return git(ctx, ["symbolic-ref", "-q", "HEAD"], check=False).stdout.strip()


def _changed_paths(ctx: Ctx, a: str, b: str) -> list:
    out = git(ctx, ["diff", "--name-only", "--no-renames", a, b]).stdout
    return [p for p in out.splitlines() if p.strip()]


def _worktree(ctx: Ctx, name: str, commit: str, branch: str | None = None) -> Path:
    path = ctx.repo / ".claude" / "worktrees" / name
    if path.exists():
        _drop_worktree(ctx, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    git(ctx, ["worktree", "add"] + (["-b", branch] if branch else ["--detach"]) + [str(path), commit])
    return path


def _drop_worktree(ctx: Ctx, path: Path) -> None:
    git(ctx, ["worktree", "remove", "--force", str(path)], check=False)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    git(ctx, ["worktree", "prune"], check=False)


def _drop_branch(ctx: Ctx, branch: str) -> None:
    if branch.startswith("si/"):
        git(ctx, ["branch", "-D", branch], check=False)


def _tree_commit(ctx: Ctx, base: str, ours: str, theirs: str, message: str, parents: list) -> str | None:
    """Three-way merge without touching any index or working tree. None on conflict."""
    res = git(ctx, ["merge-tree", "--write-tree", "--merge-base", base, ours, theirs], check=False)
    if res.returncode != 0:
        return None
    args = ["commit-tree", res.stdout.split()[0]]
    for p in parents:
        args += ["-p", p]
    return git(ctx, args + ["-m", message]).stdout.strip()


def _blob(ctx: Ctx, commit: str, path: str) -> str | None:
    res = git(ctx, ["rev-parse", "-q", "--verify", f"{commit}:{path}"], check=False)
    return res.stdout.strip() if res.returncode == 0 else None


def _land(ctx: Ctx, new: str, old: str, paths: list) -> str:
    """Move the checked-out landing branch old -> new touching only `paths`.
    Returns LANDED / DIRTY:<p> / MOVED / WRONG_BRANCH:<ref>."""
    ref = _branch(ctx)
    if ref not in guard.LAND_BRANCHES:
        return f"WRONG_BRANCH:{ref or 'detached'}"
    if _rev(ctx, "HEAD") != old:
        return "MOVED"
    old_blobs = {p: _blob(ctx, old, p) for p in paths}
    new_blobs = {p: _blob(ctx, new, p) for p in paths}
    # Content, not porcelain: each path must hold exactly the old blob (or be absent if it had none), checked
    # immediately before the write so the window in which another pane's save could be overwritten is minimal.
    for p in paths:
        f = ctx.repo / p
        if old_blobs[p] is None:
            if f.exists():
                return f"DIRTY:{p}"
            continue
        if not f.is_file() or git(ctx, ["hash-object", "--", p]).stdout.strip() != old_blobs[p]:
            return f"DIRTY:{p}"
        if git(ctx, ["diff", "--cached", "--quiet", "--", p], check=False).returncode != 0:
            return f"DIRTY:{p}"

    def _sync(commit: str, blobs: dict) -> None:
        keep = [p for p in paths if blobs[p] is not None]
        gone = [p for p in paths if blobs[p] is None and (ctx.repo / p).exists()]
        if keep:
            git(ctx, ["checkout", commit, "--", *keep])
        if gone:
            git(ctx, ["rm", "-q", "--", *gone])

    try:
        _sync(new, new_blobs)
    except Exception:
        _sync(old, old_blobs)
        raise
    cas = git(ctx, ["update-ref", ref, new, old], check=False)
    if cas.returncode != 0:
        _sync(old, old_blobs)     # the branch moved under us: put the files back
        return "MOVED"
    return "LANDED"


# ---------------------------------------------------------------- tests
def _run_test(ctx: Ctx, rel: str, cwd: Path) -> tuple:
    path = Path(cwd) / rel
    if not path.is_file():
        return "missing", f"{rel}: missing"
    exe = ctx.node if rel.endswith(".js") else ctx.python
    try:
        # No bytecode: a __pycache__ written into the agent's worktree would enter its next diff as binary content.
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        res = subprocess.run([exe, str(path)], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=guard.GATE_TIMEOUT_S, env=env)
        return res.returncode, ((res.stdout or "") + (res.stderr or ""))[-800:]
    except subprocess.TimeoutExpired:
        return "timeout", f"{rel}: timeout after {guard.GATE_TIMEOUT_S}s"


def _gate_set(ctx: Ctx, tests: list, touched: list) -> list:
    extra = []
    for p in touched:
        m = re.match(r"tools/([\w-]+)\.py$", p)
        if m and not p.startswith("tools/test_"):
            extra.append(f"tools/test_{m.group(1)}.py")
    out = []
    for t in list(tests) + extra + list(ctx.regression):
        if t not in out:
            out.append(t)
    return out


def _run_gates(ctx: Ctx, gates: list, cwd: Path, required: set) -> dict:
    """{green, red, inconclusive, ran, log}. A red gate is re-run once (red twice = red); a timeout is
    inconclusive, never red. A missing optional gate (an inferred test_<stem>) is skipped."""
    red, inconclusive, ran, log = [], [], [], []
    for g in gates:
        rc, tail = _run_test(ctx, g, cwd)
        if rc == "missing" and g not in required:
            continue
        if rc not in (0, "missing", "timeout"):
            rc, tail = _run_test(ctx, g, cwd)
        ran.append(g)
        log.append(f"{g}: rc={rc}")
        if rc == "timeout":
            inconclusive.append(g)
        elif rc != 0:
            red.append(g)
            log.append(tail[-400:])
    _check_tamper(ctx, f"gates {ran}")
    return {"green": not red and not inconclusive, "red": red, "inconclusive": inconclusive, "ran": ran,
            "log": "\n".join(log)}


# ---------------------------------------------------------------- rectify
def _revert(ctx: Ctx, ch: dict, reason: str) -> str:
    c = ch["landed_commit"]
    parent = _rev(ctx, f"{c}^1")
    head = _rev(ctx, "HEAD")
    msg = (f"revert(self-improve): {ch['key']} -- {reason}\n\nAutomatic rectification of {c[:10]} "
           f"({ch.get('id')}). Spec: vault/specs/self-improve-unattended.md\n")
    new = _tree_commit(ctx, c, head, parent, msg, [head])
    if not new:
        return "REVERT_CONFLICT"
    return _land(ctx, new, head, _changed_paths(ctx, parent, c))


def _gates_attribute(ctx: Ctx, ch: dict) -> tuple:
    """Gates at HEAD; if definitely red, again at HEAD-without-the-change. (verdict, detail)."""
    # The loop's own suite takes minutes; a change can only break it through the policy module, so it is re-run
    # daily only for changes that touched that module (it always ran on the merged tree before landing).
    gates = [g for g in ch["gates"]
             if g != guard.SELF_SUITE or "tools/self_improve_policy.py" in (ch.get("touched") or [])]
    head = _rev(ctx, "HEAD")
    wt = _worktree(ctx, "si-check-head", head)
    try:
        r = _run_gates(ctx, gates, wt, set(gates))
    finally:
        _drop_worktree(ctx, wt)
    if not r["red"]:
        return ("INCONCLUSIVE" if r["inconclusive"] else "GREEN"), r["log"]
    c = ch["landed_commit"]
    without = _tree_commit(ctx, c, head, _rev(ctx, f"{c}^1"), "probe: HEAD without the change", [head])
    if not without:
        return "RED_UNATTRIBUTABLE", r["log"]
    wt2 = _worktree(ctx, "si-check-without", without)
    try:
        r2 = _run_gates(ctx, r["red"], wt2, set(r["red"]))
    finally:
        _drop_worktree(ctx, wt2)
    if r2["inconclusive"]:
        return "INCONCLUSIVE", r["log"]
    return ("RED_BY_CHANGE" if r2["green"] else "RED_NOT_OURS"), r["log"]


def _rectify_one(ctx: Ctx, ledger: dict, cid: str, ch: dict, ratio: float, snaps: list, gate_ok: bool,
                 events: list) -> None:
    if gate_ok and not ctx.dry_run:
        verdict, _ = _gates_attribute(ctx, ch)
        if verdict == "RED_BY_CHANGE":
            _finish_revert(ctx, ledger, cid, ch, "REVERTED_GATE",
                           "its gate is red at HEAD and passes without it (twice each)", events)
            return
        if verdict != "GREEN":
            ch["note"] = f"{verdict}: not reverted on this evidence"
    after = [s for s in snaps if s.get("date", "") > ch.get("applied_day", "")]
    a_rate, a_tot, a_ses = _rate(after, ch["key"])
    b_rate = float(ch.get("base_rate") or 0.0)
    ch["measure"] = {"days": len(after), "sessions": a_ses, "after_rate": round(a_rate, 4),
                     "base_rate": round(b_rate, 4)}
    if len(after) < guard.MEASURE_MIN_DAYS or a_ses < guard.MEASURE_MIN_SESSIONS:
        return
    excess = a_tot - b_rate * a_ses
    if b_rate > 0 and a_rate >= ratio * b_rate and excess >= guard.REVERT_ABS_MIN:
        _finish_revert(ctx, ledger, cid, ch, "REVERTED_COUNTERPRODUCTIVE",
                       f"rate {a_rate:.3f} >= {ratio}x baseline {b_rate:.3f} (+{excess:.1f})", events)
    elif b_rate > 0 and a_rate <= guard.VALIDATE_RATIO * b_rate:
        ch["status"] = "VALIDATED"
        ch["note"] = f"rate {a_rate:.3f} <= {guard.VALIDATE_RATIO}x baseline {b_rate:.3f}"
        events.append(f"VALIDATED {cid}: {ch['note']}")
    elif len(after) >= guard.MEASURE_MAX_DAYS:
        ch["status"] = "NO_EFFECT"
        ch["note"] = f"no clear effect after {len(after)} days (kept)"
        events.append(f"NO_EFFECT {cid}")


def rectify(ctx: Ctx, ledger: dict, params: dict, snaps: list, events: list) -> None:
    ratio = guard.clamp("revert_ratio", float(params.get("revert_ratio", guard.REVERT_RATIO_FLOOR)))
    ram_why = guard.ram_refusal(ctx.ram())
    if ram_why:
        events.append(f"rectify gates skipped today ({ram_why}); measurement still runs")
    for cid, ch in list((ledger.get("changes") or {}).items()):
        if ch.get("status") != "APPLIED":
            continue
        try:
            _rectify_one(ctx, ledger, cid, ch, ratio, snaps, ram_why is None, events)
        except Tampered:
            raise
        except Exception as exc:  # noqa: BLE001 -- one change's failure must not stop the others
            ch["note"] = f"rectify error: {type(exc).__name__}: {str(exc)[:200]}"
            events.append(f"RECTIFY_ERROR {cid}: {type(exc).__name__}")


def _finish_revert(ctx, ledger, cid, ch, status, why, events) -> None:
    if ctx.dry_run:
        events.append(f"(dry-run) would revert {cid}: {why}")
        return
    res = _revert(ctx, ch, why)
    if res == "LANDED":
        ch["status"], ch["note"], ch["reverted_at"] = status, why, _now_iso()
        k = ledger.setdefault("keys", {}).setdefault(ch["key"], {})
        k["reverts"] = int(k.get("reverts", 0)) + 1
        k.setdefault("approaches", []).append(ch.get("summary", "")[:200])
        if k["reverts"] >= guard.RETIRE_AFTER_REVERTS:
            k["retired"] = True
        _cooldown(ledger, ch["key"], ctx.today)
        _persist(ctx, ledger)
        events.append(f"{status} {cid}: {why}" + (" -- key retired" if k.get("retired") else ""))
    else:
        ch["note"] = f"revert wanted ({why}) but {res}; retrying next run"
        events.append(f"REVERT_PENDING {cid}: {res}")


# ---------------------------------------------------------------- apply
def _diff_changes(ctx: Ctx, wt: Path, fork: str) -> list:
    git(ctx, ["add", "-A"], cwd=wt)
    ns = git(ctx, ["diff", "--cached", "--no-renames", "--name-status", fork], cwd=wt).stdout.splitlines()
    nums = {}
    for line in git(ctx, ["diff", "--cached", "--no-renames", "--numstat", fork], cwd=wt).stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            binary = parts[0] == "-" or parts[1] == "-"
            nums[parts[2]] = (0 if binary else int(parts[0]) + int(parts[1]), binary)
    out = []
    for line in ns:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        st, p = parts[0], parts[-1]
        old = git(ctx, ["show", f"{fork}:{p}"], cwd=wt, check=False)
        new_path = wt / p
        lines, binary = nums.get(p, (0, False))
        out.append({"path": p, "status": st, "lines": lines, "binary": binary,
                    "old_text": old.stdout if old.returncode == 0 else None,
                    "new_text": new_path.read_text(encoding="utf-8", errors="replace") if new_path.is_file() else None})
    return out


def _fails_on_old(ctx: Ctx, tests: list, wt: Path, fork: str) -> bool:
    """The new tests must fail against the old code (copied into a pristine worktree at the fork)."""
    base = _worktree(ctx, "si-base", fork)
    try:
        failed = False
        for t in tests:
            dst = base / t
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(wt / t, dst)
            rc, _ = _run_test(ctx, t, base)
            failed = failed or (rc != 0 and rc != "timeout")
        _check_tamper(ctx, "failing-first run")
        return failed
    finally:
        _drop_worktree(ctx, base)


def _new_id(ctx: Ctx, ledger: dict, key: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")[:30] or "x"
    cid, n = f"{ctx.today}-{slug}", 1
    while cid in (ledger.get("changes") or {}) or \
            git(ctx, ["rev-parse", "-q", "--verify", f"refs/heads/si/{cid}"], check=False).returncode == 0:
        n += 1
        cid = f"{ctx.today}-{slug}-{n}"
    return cid


def attempt(ctx: Ctx, cand: dict, ledger: dict, base_rate: float, events: list) -> dict:
    import self_improve_policy as policy
    cid = _new_id(ctx, ledger, cand["key"])
    branch = f"si/{cid}"
    fork = _rev(ctx, "HEAD")
    ch = {"id": cid, "key": cand["key"], "kind": cand["kind"], "branch": branch, "fork": fork,
          "created": _now_iso(), "day": ctx.today, "base_rate": base_rate, "status": "STARTED"}
    ledger.setdefault("changes", {})[cid] = ch
    approaches = (ledger.get("keys", {}).get(cand["key"], {}) or {}).get("approaches", [])
    name = f"si-{cid}"
    wt = None
    try:
        wt = _worktree(ctx, name, fork, branch=branch)
        feedback, changes, tests, summary = "", [], [], ""
        for _round in (1, 2):
            rc, out = ctx.run_agent(policy.agent_prompt(cand, approaches, feedback), wt)
            _check_tamper(ctx, "agent run")
            m = re.search(r"SUMMARY:\s*(.+)", out or "")
            summary = _redact(m.group(1).strip() if m else "", 200)
            changes = _diff_changes(ctx, wt, fork)
            if not changes:
                ch.update(status="NO_CHANGE", note=f"agent rc={rc} made no change")
                break
            why = guard.diff_refusal(changes)
            if why:
                ch.update(status="REFUSED_DIFF", note=why)
                feedback = f"Your diff was refused: {why}. Stay inside the rules."
                _drop_worktree(ctx, wt)
                _drop_branch(ctx, branch)
                wt = _worktree(ctx, name, fork, branch=branch)
                continue
            tests = [c["path"] for c in changes if TEST_RE.match(c["path"])]
            if not tests:
                ch.update(status="RED", note="no test added or changed")
                feedback = "You changed code without adding or changing a test. Add the failing test first."
                continue
            if not _fails_on_old(ctx, tests, wt, fork):
                ch.update(status="RED", note="the new test does not fail on the old code")
                feedback = ("Your test passes on the OLD code too, so it does not detect the finding. Make it fail "
                            "on the old code and pass on the new.")
                continue
            r = _run_gates(ctx, tests, wt, set(tests))
            if not r["green"]:
                ch.update(status="RED", note=f"own test not green: {r['red'] + r['inconclusive']}")
                feedback = r["log"]
                continue
            ch["status"] = "GREEN_BRANCH"
            break
        if ch["status"] != "GREEN_BRANCH":
            events.append(f"{ch['status']} {cid}: {ch.get('note')}")
            _cooldown(ledger, cand["key"], ctx.today)
            _drop_worktree(ctx, wt)
            wt = None
            _drop_branch(ctx, branch)
            return ch
        msg = f"si({cand['kind']}): {summary or cand['key']}\n\nKey: {cand['key']}\nAutonomous self-improve, spec " \
              "vault/specs/self-improve-unattended.md. Tests: " + ", ".join(tests) + "\n"
        git(ctx, ["commit", "-q", "-m", msg], cwd=wt)
        ch.update(tip=_rev(ctx, "HEAD", cwd=wt), tests=tests, summary=summary, touched=[c["path"] for c in changes])
    except Tampered:
        raise
    except Exception as exc:  # noqa: BLE001
        ch.update(status="ERROR", note=f"{type(exc).__name__}: {str(exc)[:200]}")
        events.append(f"ERROR {cid}: {ch['note']}")
        _cooldown(ledger, cand["key"], ctx.today)
        _drop_branch(ctx, branch)
        return ch
    finally:
        if wt is not None:
            _drop_worktree(ctx, wt)
    _persist(ctx, ledger)
    return land_change(ctx, ch, events, ledger)


def land_change(ctx: Ctx, ch: dict, events: list, ledger: dict) -> dict:
    """Merge a green branch: test the MERGED tree, then land it. PENDING_MERGE is retried next run."""
    head = _rev(ctx, "HEAD")
    msg = f"merge(self-improve): {ch['key']} -- {ch.get('summary') or ''}"[:200] + \
          f"\n\nBranch {ch['branch']} ({ch['tip'][:10]}). Gates: {', '.join(ch['tests'])} + regression block.\n"
    merged = _tree_commit(ctx, ch["fork"], head, ch["tip"], msg, [head, ch["tip"]])
    if not merged:
        ch.update(status="MERGE_CONFLICT", note=f"conflicts with {head[:10]}")
        events.append(f"MERGE_CONFLICT {ch['id']}")
        _cooldown(ledger, ch["key"], ctx.today)
        return ch
    gates = _gate_set(ctx, ch["tests"], ch["touched"])
    wt = _worktree(ctx, "si-merged", merged)
    try:
        r = _run_gates(ctx, gates, wt, set(ch["tests"]) | set(ctx.regression))
    finally:
        _drop_worktree(ctx, wt)
    if not r["green"]:
        if r["red"]:
            ch.update(status="RED", note=f"merged tree red: {r['red']}")
            events.append(f"RED {ch['id']}: merged tree red {r['red']}")
            _cooldown(ledger, ch["key"], ctx.today)
        else:
            ch.update(status="PENDING_MERGE", note=f"merged-tree gates inconclusive: {r['inconclusive']}")
            events.append(f"PENDING_MERGE {ch['id']}: gates inconclusive")
        return ch
    ch["gates"] = r["ran"]
    res = _land(ctx, merged, head, _changed_paths(ctx, head, merged))
    if res == "LANDED":
        ch.update(status="APPLIED", applied_at=_now_iso(), applied_day=ctx.today, landed_commit=merged, note="")
        _persist(ctx, ledger)
        events.append(f"APPLIED {ch['id']}: {ch.get('summary') or ch['key']} ({merged[:10]})")
    else:
        ch.update(status="PENDING_MERGE", note=res)
        events.append(f"PENDING_MERGE {ch['id']}: {res}")
    return ch


def _cooldown(ledger: dict, key: str, today: str, days: int = 7) -> None:
    k = ledger.setdefault("keys", {}).setdefault(key, {})
    k["cooldown_until"] = (date.fromisoformat(today) + timedelta(days=days)).isoformat()


def _excluded(ledger: dict, today: str) -> set:
    out = set()
    for key, k in (ledger.get("keys") or {}).items():
        if k.get("retired") or (k.get("cooldown_until") or "") >= today:
            out.add(key)
    for ch in (ledger.get("changes") or {}).values():
        if ch.get("status") in OPEN:
            out.add(ch["key"])
    return out


# ---------------------------------------------------------------- the daily cycle
def _lock(ctx: Ctx) -> bool:
    lock = ctx.state / "run.lock"
    ctx.state.mkdir(parents=True, exist_ok=True)
    try:
        lock.mkdir()
        return True
    except FileExistsError:
        if time.time() - lock.stat().st_mtime > LOCK_STALE_S:
            os.utime(lock)
            return True
        return False


def _beat(ctx: Ctx) -> None:
    try:
        os.utime(ctx.state / "run.lock")
    except OSError:
        pass


def _unlock(ctx: Ctx) -> None:
    try:
        (ctx.state / "run.lock").rmdir()
    except OSError:
        pass


def _snapshots(ctx: Ctx) -> list:
    d = ctx.state / "snapshots"
    out = []
    for p in sorted(d.glob("*.json")) if d.is_dir() else []:
        s = _load(p, None)
        if isinstance(s, dict):
            out.append(s)
    return out


def _cycle(ctx: Ctx, ledger: dict, params: dict, events: list) -> dict:
    import self_improve_policy as policy
    # 1. observe
    result = ctx.analyze()
    today = _snapshot(result, ctx.today)
    _save(ctx.state / "snapshots" / f"{ctx.today}.json", today)
    snaps = _snapshots(ctx)
    history = [s for s in snaps if s.get("date", "") < ctx.today][-int(params["baseline_days"]):]
    events.append(f"observed {len(today['candidates'])} candidate(s) in {today['sessions']} session(s) "
                  f"({today['status']})")
    _beat(ctx)
    # 2. rectify first; retry what is waiting to land
    if not ctx.dry_run:
        for ch in list((ledger.get("changes") or {}).values()):
            if ch.get("status") in RETRYABLE and ch.get("tip"):
                try:
                    land_change(ctx, ch, events, ledger)
                except Tampered:
                    raise
                except Exception as exc:  # noqa: BLE001
                    ch["note"] = f"retry error: {type(exc).__name__}: {str(exc)[:200]}"
                    events.append(f"RETRY_ERROR {ch['id']}")
    rectify(ctx, ledger, params, snaps, events)
    _beat(ctx)
    # 3. tune itself (bounded by the guard)
    new_params, notes = policy.tune(params, ledger, ctx.today, guard.BENCH_DAYS)
    params = guard.clamp_params(new_params)
    events += [f"tuned: {n}" for n in notes]
    # 4. apply at most one
    used = sum(1 for c in ledger["changes"].values() if c.get("day") == ctx.today and c.get("status") != "NO_CHANGE")
    ranked = policy.rank(today, history, params, _excluded(ledger, ctx.today), guard.NEVER_KINDS, ctx.today)
    if used >= guard.MAX_APPLIES_PER_DAY:
        events.append("daily apply budget used")
    elif not ranked:
        events.append("no eligible candidate")
    else:
        why = guard.admission(ctx.spend_refusal(), ctx.ram(), ctx.claude_state)
        if why:
            events.append(f"apply skipped: {why}")
        elif ctx.dry_run:
            events.append(f"(dry-run) would attempt {ranked[0]['key']} (score {ranked[0]['rank_score']})")
        else:
            b_rate, _, _ = _rate(history + [today], ranked[0]["key"])
            attempt(ctx, ranked[0], ledger, b_rate, events)
    return params


def run_daily(ctx: Ctx) -> dict:
    import self_improve_policy as policy
    events: list = []
    stop = guard.killed(ctx.state)
    if stop:
        _receipt(ctx, {"event": "killed", "why": stop})
        return {"ok": True, "stopped": stop}
    bad = guard.integrity(ctx.pin_path, ctx.repo)
    if bad:
        _receipt(ctx, {"event": "integrity_stop", "why": bad})
        ctx.publish(f"self-improve STOPPED: {bad}")
        return {"ok": False, "stopped": bad}
    if not _lock(ctx):
        _receipt(ctx, {"event": "locked"})
        return {"ok": True, "stopped": "another self-improve run holds the lock"}
    ctx.baseline_fp = guard.fingerprint(ctx.pin_path, ctx.repo, ctx.watched)
    ledger = _load(ctx.state / "ledger.json", None)
    if not isinstance(ledger, dict):
        ledger = {"changes": {}, "keys": {}}
    ledger.setdefault("changes", {})
    ledger.setdefault("keys", {})
    params = guard.clamp_params(_load(ctx.state / "params.json", None) or _load(ctx.seed_params, {}))
    try:
        params = _cycle(ctx, ledger, params, events)
        if not ctx.dry_run:
            _save(ctx.state / "params.json", params)
    except Tampered as exc:
        events.append(f"TAMPER STOP: {exc}")
        try:
            (ctx.state / "OFF").write_text(f"{_now_iso()} {exc}\n", encoding="utf-8")
        except OSError:
            pass
        ctx.publish(f"self-improve STOPPED itself (OFF written): {str(exc)[:300]}")
    except GitRefused as exc:
        events.append(f"guard refused a git command: {exc}")
    except Exception as exc:  # noqa: BLE001 -- a failed cycle is a missed day, never a broken session
        events.append(f"cycle error: {type(exc).__name__}: {str(exc)[:300]}")
    finally:
        _persist(ctx, ledger)
        _unlock(ctx)
    text = policy.report(ctx.today, events, ledger, params)
    if not ctx.dry_run:
        (ctx.state / "STATUS.md").write_text(text, encoding="utf-8")
        if not any(e.startswith("TAMPER STOP") for e in events):
            ctx.publish(policy.headline(events))
    _receipt(ctx, {"event": "cycle", "dry_run": ctx.dry_run, "events": events})
    return {"ok": not any(e.startswith(("cycle error", "guard refused", "TAMPER")) for e in events),
            "events": events}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="autonomous self-improve loop")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--status", action="store_true")
    a = ap.parse_args(argv)
    ctx = Ctx()
    if a.status:
        p = ctx.state / "STATUS.md"
        print(p.read_text(encoding="utf-8") if p.exists() else "no run yet")
        return 0
    ctx.dry_run = a.dry_run
    print(json.dumps(run_daily(ctx), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
