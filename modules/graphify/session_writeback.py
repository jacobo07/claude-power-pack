#!/usr/bin/env python3
"""
GK-08 Session Writeback — enrich the knowledge graph at session close.

A Stop hook. At session end it re-indexes the CURRENT repo into the central
store (global_store) so any knowledge file created or changed this session
becomes navigable in the NEXT session — this closes the WRITE -> READ -> ACT
loop: session_writeback WRITES the graph, the GK-12 Graph-First gate READS it,
navigation ACTS on it. A writer with no reader is documentation; here the
reader is the gate, so the cycle is whole.

Honest + bounded (GK-08's registered residual is "a silently-closed session"):
  - Fail-open ABSOLUTE: it NEVER blocks Stop. Any error -> a logged note and
    exit 0. A hook that stalls session close is worse than a stale graph.
  - Bounded: a full re-index hashes + parses every markdown node. For a
    29k-node repo that is far too slow for a Stop hook, so a repo with more than
    MAX_MD_FILES markdown files is SKIPPED with a logged "deferred" verdict
    (those refresh via the scheduled `indexer --all`). The skip is recorded,
    never silent — the residual is measured, per GK-12.
  - Cheap pre-check: counts markdown files with an early bail at the cap, so a
    huge repo costs a bounded directory walk, not a full parse.

Reads {cwd, session_id} from the Stop JSON on stdin. Also callable as
writeback(cwd) for tests.
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import global_store as gs  # noqa: E402
# graphify_knowledge is importable because global_store put tools/ on sys.path.
import graphify_knowledge as gk  # noqa: E402

MAX_MD_FILES = 4000  # above this a Stop-time full re-index is too slow -> defer

# --- Stop-budget guards (2026-09-15) ---------------------------------------
# The dispatcher gives this member 8000 ms and KILLS it at the budget. A killed
# child never reaches _log, so the only runs visible in writeback.log are the
# ones that FINISHED -- which means a repo that sits under MAX_MD_FILES and is
# still too slow retried, died, and wrote nothing, once per turn, forever, with
# no trace anywhere that it was happening.
#
# The existing cap is the right idea measured in the wrong unit: MAX_MD_FILES
# bounds FILE COUNT, and what the chain enforces is TIME. They are not the same
# quantity and nothing converts between them. Measured on this host, a repo of
# 2906 nodes sits comfortably under the cap and takes about 180 seconds.
STOP_BUDGET_MS = 8000       # mirrors the dispatcher's timeoutMs for this member
THROTTLE_SEC = 900          # re-index any one repo at most this often
INFLIGHT_STALE_SEC = 60     # an older in-flight marker means the run was killed
COST_RECHECK_SEC = 86400    # re-probe a cost-deferred repo about once a day


def _log(payload: dict) -> None:
    """Append a one-line writeback receipt to the state dir. Best-effort."""
    try:
        d = gs.state_dir()
        d.mkdir(parents=True, exist_ok=True)
        payload["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(d / "writeback.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass  # logging must never break Stop


def _log_skip(payload: dict) -> None:
    """A run that did nothing gets its own log, NOT writeback.log.

    `indexer.deferred_repos` takes the LAST row per repo from writeback.log
    whatever its verdict ("append-only: last write wins"), so a throttle
    receipt written there would supersede a pending "deferred" and silently
    retire real debt. The residual is still measured, per GK-12 -- just not in
    the file that decides the debt set.
    """
    try:
        d = gs.state_dir()
        d.mkdir(parents=True, exist_ok=True)
        payload["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(d / "writeback_skips.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass


def _state_path():
    return gs.state_dir() / "writeback_state.json"


def _load_state() -> dict:
    try:
        with open(_state_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    try:
        p = _state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, p)
    except OSError:
        pass  # state is an optimisation, never a requirement


def _guard(rec: dict, now: float):
    """Decide whether this turn should attempt an index at all.

    Returns None to proceed, or (verdict, reason). The first branch is the
    load-bearing one: a run killed at the budget leaves no receipt, so the
    receipt it never wrote cannot be read -- but the in-flight marker it wrote
    BEFORE dying can. That marker is how an invisible failure becomes visible.
    """
    inflight = rec.get("inflight_at")
    if inflight:
        try:
            age = now - float(inflight)
        except (TypeError, ValueError):
            return None
        if age > INFLIGHT_STALE_SEC:
            return ("deferred",
                    "a previous attempt was killed before it could finish")
        return ("skip", "another writeback for this repo is in flight")

    cost_at = rec.get("cost_deferred_at")
    if cost_at:
        try:
            if now - float(cost_at) < COST_RECHECK_SEC:
                return ("deferred",
                        f"this repo does not fit the {STOP_BUDGET_MS} ms Stop budget")
        except (TypeError, ValueError):
            pass

    last_ok = rec.get("last_ok_at")
    if last_ok:
        try:
            age = now - float(last_ok)
            if age < THROTTLE_SEC:
                return ("throttled",
                        f"indexed {int(age)}s ago; interval is {THROTTLE_SEC}s")
        except (TypeError, ValueError):
            pass

    return None


def _md_count_capped(root: Path, cap: int) -> int:
    """Count markdown files under root (skipping generated/vendored dirs), with
    an early bail once the count passes cap — bounded cost on a huge repo."""
    n = 0
    for dpath, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in gk.SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                n += 1
                if n > cap:
                    return n
    return n


def writeback(cwd, quiet: bool = True, force: bool = False) -> dict:
    """Re-index cwd into the central store if it is within the size and time
    bounds. Returns a verdict dict; never raises. `force` skips the guards and
    is for tests and for the out-of-band repairer, never for the Stop path."""
    try:
        rp = Path(cwd)
        if not rp.is_dir():
            return {"verdict": "skip", "reason": "cwd not a dir", "repo": str(cwd)}

        key = str(rp.resolve())
        state = _load_state()
        rec = state.get(key) or {}
        now = time.time()

        guard = None if force else _guard(rec, now)
        if guard is not None:
            verdict, reason = guard
            if verdict != "deferred":
                _log_skip({"verdict": verdict, "reason": reason, "repo": key})
                return {"verdict": verdict, "reason": reason, "repo": key,
                        "_suppress_log": True}

            # A cost deferral is real debt and belongs in the log the repairer
            # discovers from -- but only ONCE. Re-appending it every turn would
            # grow that log without adding a fact, and the row is already the
            # latest for this repo, so the debt stays visible either way.
            rec.pop("inflight_at", None)
            rec.pop("inflight_pid", None)
            rec.setdefault("cost_deferred_at", now)
            already = rec.get("cost_logged")
            rec["cost_logged"] = True
            state[key] = rec
            _save_state(state)
            out = {"verdict": "deferred", "reason": reason, "repo": key,
                   "hint": "refresh via 'indexer --deferred --repair'"}
            if already:
                _log_skip(dict(out, verdict="deferred-repeat"))
                out["_suppress_log"] = True
            return out

        md = _md_count_capped(rp, MAX_MD_FILES)
        if md > MAX_MD_FILES:
            # The hint must name a refresher that actually comes back for this
            # repo. It used to say `indexer --all`, which discovers from
            # terminal_slots.json inside a 7-day window and was never
            # scheduled -- so "deferred" was terminal, not temporary.
            # `--deferred` reads THIS log, so every skip here is recoverable.
            return {"verdict": "deferred", "reason": f"{md}+ md files > {MAX_MD_FILES} cap",
                    "repo": str(rp),
                    "hint": "refresh via 'indexer --deferred --repair'"}

        # Plant the marker BEFORE the slow part. If the chain kills us during
        # index_repo we write no receipt at all, and this marker is the only
        # evidence that survives to tell the NEXT turn what happened here.
        rec["inflight_at"] = now
        rec["inflight_pid"] = os.getpid()
        state[key] = rec
        _save_state(state)

        t0 = time.time()
        res = gs.index_repo(rp, quiet=quiet)
        elapsed_ms = int((time.time() - t0) * 1000)

        # Re-read before writing: a concurrent session may have recorded other
        # repos meanwhile, and this member must not roll their entries back.
        state = _load_state()
        rec = state.get(key) or {}
        rec.pop("inflight_at", None)
        rec.pop("inflight_pid", None)
        rec["last_ok_at"] = time.time()
        rec["last_ms"] = elapsed_ms
        # It finished only because nothing killed it -- `force` and the repairer
        # both run without a budget. If it spent most of one, it will not
        # survive the Stop path, so hand this repo to the out-of-band repairer
        # rather than paying the budget for it once per turn forever.
        if elapsed_ms > STOP_BUDGET_MS * 0.75:
            rec.setdefault("cost_deferred_at", time.time())
        else:
            rec.pop("cost_deferred_at", None)
            rec.pop("cost_logged", None)
        state[key] = rec
        _save_state(state)

        return {"verdict": "indexed" if res.get("ok") else "error",
                "repo": res.get("repo", str(rp)),
                "nodes": res.get("nodes"), "promoted": res.get("promoted"),
                "elapsed_ms": elapsed_ms,
                "error": res.get("error")}
    except Exception as e:  # fail-open absolute
        return {"verdict": "error", "reason": str(e), "repo": str(cwd)}


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
    except OSError:
        raw = ""
    data = {}
    try:
        data = json.loads(raw or "{}")
    except (json.JSONDecodeError, ValueError):
        data = {}

    cwd = data.get("cwd") or os.getcwd()
    verdict = writeback(cwd)
    # A run that did nothing must not append to writeback.log. The repairer
    # discovers debt by taking the LAST row per repo from that file whatever
    # its verdict, so a throttle row would supersede a pending deferral and
    # retire real debt silently. Those rows went to writeback_skips.log inside
    # writeback(); this flag is how it says so.
    suppress = verdict.pop("_suppress_log", False)
    verdict["session_id"] = data.get("session_id", "")
    if not suppress:
        _log(verdict)
    # Stop hooks emit optional JSON; we never block, so an empty object is fine.
    try:
        sys.stdout.write("{}")
    except OSError:
        pass  # a closed stdout must never break session close
    return 0  # ALWAYS exit 0 — GK-08 never blocks session close


if __name__ == "__main__":
    sys.exit(main())
