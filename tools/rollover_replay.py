#!/usr/bin/env python
"""Replay the existing rollover policy on MEASURED inputs (plan ccp-s16). Read-only.

`tools/rollover.py::decide` is the single rollover policy. This tool never forks it, never clears
anything and never writes the rollover ledger: every verdict below is a call to `decide`. It
measures what `decide` currently assumes, so the assumption can later be replaced by evidence, in
rollover.py, by its owner.

    python tools/rollover_replay.py fresh-cost [--json] [--min-samples N]
    python tools/rollover_replay.py replay <session-id> [--json] [--out FILE]

fresh-cost: what a fresh epoch actually cost, from sessions that took over a sealed capsule and
passed the resume exam. `decide` prices a fresh epoch as floor + capsule chars / 4; a successor
also pays the calls it spends re-orienting before it changes anything. Measured per certified
successor: first-call context, calls and context carried before its first mutation (Write / Edit /
NotebookEdit, or a successful `git commit`). Those calls include genuine work, so as a
rehydration cost they are an UPPER bound.

replay: at every successful commit of one session (a candidate boundary), `decide` is asked with
ONLY what was known at that call (audit vault/audits/ccp-s16-c3-audit.md):
  shipped     decide as shipped: horizon HORIZON_CALLS (a constant ESTIMATE).
  prior       horizon = each value of a remaining-work PRIOR; S = share of values for which decide
              says rollover. WOULD_ROLLOVER if S >= 0.75, CONTINUE if S <= 0.25, else
              INSUFFICIENT_EVIDENCE. The prior is `calls after a commit` in OTHER interactive
              sessions of the usage index whose last call ended before the boundary, excluding the
              root's own capsule chain and sessions that ended in a rollover (censored by the very
              policy under test; their count is reported).
  rehydrated  the same, with the horizon reduced by rehydration C/G (C = context carried before a
              successor's first mutation, in {0, p50}; G = decide's growth above fresh): the same
              inequality as n* + C/G <= h, so decide's own gates stay the only gates. EXPERIMENTAL.
Window size is unknown from a transcript, so used_pct is None: decide's pressure branch is NOT
evaluated, and the output says so. The price book is the one in force at the boundary's month; the
capsule size is the median of ledger capsules sealed BEFORE the boundary.
After the verdicts, a hindsight EVALUATION (never an input): mechanical reread exposure had the
session rolled at T = G x remaining_calls - fresh x (write - read) / read - C, in cache-read-token
equivalents, an interval over C in {0, p50}. Growth is frozen at T, so it is a lower bound of the
reread a fresh epoch would avoid, and NEVER a saving: behaviour after a fresh epoch is unobserved.

Joins and faults (fixtures in test_rollover_replay.py): `resume_certified` rows carry only the
PREDECESSOR; the successor is `successor_claimed.claimant`. Torn ledger rows are counted, never
guessed. A commit counts only when its tool_result came back without error (a hook-denied or
--dry-run commit is not a boundary). Calls by `tis_observed._calls_in`, context by `_context_of`.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import rollover  # noqa: E402  (single owner: policy, ledger location, transcript rows and lookup)
import tis_observed as tis  # noqa: E402  (single owner: call identity and context size)

MIN_SAMPLES = 5
WOULD_AT, CONTINUE_AT = 0.75, 0.25
PRIOR_DAYS = 14
MUTATING_TOOLS = ("Write", "Edit", "NotebookEdit")
# `commit` must be git's subcommand: an executable spelled git / git.exe or a variable holding it,
# then only options (-C path, -c k=v, --flag[=v]) before `commit`.
_COMMIT_RE = re.compile(
    r"""(?:\bgit(?:\.exe)?['"]?|\$\w+)\s+(?:(?:-C|-c)\s+(?:'[^']*'|"[^"]*"|\S+)\s+|--?[\w-]+(?:=\S+)?\s+)*commit\b(?P<rest>[^;|&\n]*)""",
    re.I)


def is_commit_command(command: str) -> bool:
    m = _COMMIT_RE.search(command or "")
    return bool(m) and "--dry-run" not in m.group("rest")


def read_ledger(path: Path) -> tuple[list[dict], int]:
    """(rows, torn): a line that is not a JSON object is torn, counted, never repaired."""
    rows, torn = [], 0
    if not Path(path).is_file():
        return rows, torn
    for line in Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            torn += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            torn += 1
    return rows, torn


def _epoch(ts) -> Optional[float]:
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()   # one UTC clock


def _tool_message_ids(transcript: Path) -> tuple[set, set]:
    """(ids of messages that mutated, ids of messages whose `git commit` came back without error)."""
    muts, commit_uses, failed, answered = set(), {}, set(), set()
    for row in rollover._rows(transcript):
        msg = row.get("message")
        if not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
            continue
        for b in msg["content"]:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_result":
                answered.add(b.get("tool_use_id"))
                if b.get("is_error"):
                    failed.add(b.get("tool_use_id"))
            if b.get("type") != "tool_use":
                continue
            commit = is_commit_command(str((b.get("input") or {}).get("command") or ""))
            if b.get("name") in MUTATING_TOOLS or commit:
                muts.add(msg.get("id"))
            if commit:
                commit_uses[b.get("id")] = msg.get("id")
    commits = {mid for tid, mid in commit_uses.items() if tid in answered and tid not in failed}
    return muts, commits


_TRACES: dict = {}


def session_trace(transcript: Path) -> dict:
    """Per-call context, time and model; the first mutating call; the successful commit calls.
    Memoised on (path, mtime, size): a replay would otherwise re-read each successor per boundary."""
    st = Path(transcript).stat()
    key = (str(transcript), st.st_mtime_ns, st.st_size)
    if key not in _TRACES:
        _TRACES[key] = _trace(Path(transcript))
    return _TRACES[key]


def _trace(transcript: Path) -> dict:
    calls, *_ = tis._calls_in(Path(transcript))
    muts, commits = _tool_message_ids(transcript)
    return {"calls": len(calls), "ctx": [tis._context_of(c["usage"]) for c in calls],
            "ts": [_epoch(c.get("ts")) for c in calls], "model": [c["model"] for c in calls],
            "first_mutation": next((i + 1 for i, c in enumerate(calls) if c["key"][0] in muts), None),
            "commit_calls": [i + 1 for i, c in enumerate(calls) if c["key"][0] in commits]}


def boundaries(trace: dict) -> list[dict]:
    """One row per successful commit call: ONLY what the session had at that call."""
    return [{"call": i, "ts": trace["ts"][i - 1], "model": trace["model"][i - 1],
             "floor": trace["ctx"][0], "resident": trace["ctx"][i - 1],
             "surface_so_far": sum(trace["ctx"][:i])} for i in trace["commit_calls"]]


def _dist(values: list, min_samples: int) -> dict:
    v = sorted(values)
    if len(v) < min_samples:
        return {"n": len(v), "p10": None, "p50": None, "p90": None}
    pick = lambda q: v[min(len(v) - 1, int(q * len(v)))]
    return {"n": len(v), "p10": pick(0.10), "p50": v[len(v) // 2], "p90": pick(0.90)}


def fresh_cost(ledger_path: Optional[Path] = None, find: Optional[Callable] = None,
               min_samples: int = MIN_SAMPLES, before: Optional[float] = None) -> dict:
    """`before`: only resumes certified before that UTC epoch (a replay must not see the future)."""
    ledger_path = Path(ledger_path or rollover.STATE_DIR / "rollover-ledger.jsonl")
    find = find or rollover._find_transcript
    rows, torn = read_ledger(ledger_path)
    claimant = {r["session_id"]: r["claimant"] for r in rows
                if r.get("event") == "successor_claimed" and r.get("session_id") and r.get("claimant")}
    certified = [r["session_id"] for r in rows if r.get("event") == "resume_certified" and r.get("session_id")
                 and (before is None or (_epoch(r.get("ts")) or float("inf")) < before)]
    samples, missing_claim, missing_transcript, no_mutation = [], [], [], 0
    for pred in dict.fromkeys(certified):
        succ = claimant.get(pred)
        if not succ:
            missing_claim.append(pred)
            continue
        t = find(succ)
        if not t or not Path(t).is_file():
            missing_transcript.append(succ)
            continue
        tr = session_trace(Path(t))
        if not tr["ctx"]:
            missing_transcript.append(succ)
            continue
        fm = tr["first_mutation"]
        no_mutation += fm is None
        samples.append({"predecessor": pred, "successor": succ, "first_ctx": tr["ctx"][0],
                        "calls_to_first_mutation": fm,
                        "ctx_at_first_mutation": tr["ctx"][fm - 1] if fm else None,
                        "carried_before_first_mutation": sum(tr["ctx"][:fm - 1]) if fm else None})
    measured = [s for s in samples if s["calls_to_first_mutation"]]
    first = _dist([s["first_ctx"] for s in samples], min_samples)
    return {
        "verdict": "MEASURED" if first["p50"] is not None else "INSUFFICIENT_EVIDENCE",
        "ledger": str(ledger_path), "torn_rows": torn, "certified": len(dict.fromkeys(certified)),
        "missing_claim": missing_claim, "missing_transcript": missing_transcript,
        "no_mutation": no_mutation, "first_ctx": first,
        "calls_to_first_mutation": _dist([s["calls_to_first_mutation"] for s in measured], min_samples),
        "carried_before_first_mutation": _dist([s["carried_before_first_mutation"] for s in measured],
                                               min_samples),
        "bound": "calls before the first mutation include real work: an UPPER bound on rehydration",
        "decide_assumes": "fresh = floor + capsule chars / 4 (rollover.decide), no rehydration term",
        "samples": samples,
    }


# ------------------------------------------------------------------------------ replay
def price_at(model: str, ts: Optional[float]) -> dict:
    """1h cache write / cache read from the newest book dated at or before the boundary's month."""
    try:
        import session_autopsy as sa
        books = sa._price_books()
    except Exception as exc:  # noqa: BLE001 -- unpriced is UNKNOWN, never a default price
        return rollover._unknown(f"price books unreadable: {exc.__class__.__name__}")
    if ts is None:
        return rollover._unknown("boundary has no timestamp")
    d = datetime.fromtimestamp(ts, timezone.utc)
    eligible = [b for b in books if b[0] <= (d.year, d.month)]
    row = sa._model_row(eligible[-1][1], model) if eligible else None
    if not row or row.get("cache_write_1h") is None or row.get("cache_read") is None:
        return rollover._unknown(f"no price row in force for {model or 'unknown model'}")
    return {"state": "OK", "write": float(row["cache_write_1h"]), "read": float(row["cache_read"]),
            "source": eligible[-1][2]}


def capsule_chars_before(rows: list[dict], ts: float) -> Optional[int]:
    v = sorted(r["bootstrap_chars"] for r in rows if r.get("event") == "shadow_candidate"
               and isinstance(r.get("bootstrap_chars"), int) and (_epoch(r.get("ts")) or ts) < ts)
    return v[len(v) // 2] if v else None


def capsule_chain(rows: list[dict], root: str) -> set:
    """The root plus every session joined to it by a claim, either direction, transitively."""
    edges = [(r["session_id"], r["claimant"]) for r in rows
             if r.get("event") == "successor_claimed" and r.get("session_id") and r.get("claimant")]
    chain, grew = {root}, True
    while grew:
        grew = False
        for a, b in edges:
            if (a in chain) != (b in chain):
                chain |= {a, b}
                grew = True
    return chain


class Prior:
    """`calls after a commit` from interactive sessions that ENDED before a boundary."""

    def __init__(self, sessions: list[tuple[str, Path, float]], exclude: set, rolled: set):
        self.sessions, self.exclude, self.rolled = sessions, exclude, rolled
        self._cache: dict = {}

    def _remaining(self, sid: str, path: Path) -> list[int]:
        if sid not in self._cache:
            try:
                tr = session_trace(path)
                self._cache[sid] = [tr["calls"] - i for i in tr["commit_calls"]]
            except OSError:
                self._cache[sid] = []
        return self._cache[sid]

    def at(self, ts: float) -> dict:
        lo = ts - PRIOR_DAYS * 86400
        eligible = [(s, p) for s, p, last in self.sessions if lo <= last < ts and s not in self.exclude]
        censored = [s for s, _ in eligible if s in self.rolled]
        values = [v for s, p in eligible if s not in self.rolled for v in self._remaining(s, p)]
        return {"values": values, "sessions": len(eligible) - len(censored), "censored_excluded": len(censored)}


def prior_from_index(db: Optional[Path] = None) -> list[tuple[str, Path, float]]:
    import usage_index as ux
    con = sqlite3.connect(f"file:{Path(db or ux.DEFAULT_DB)}?mode=ro", uri=True)
    try:
        q = ("SELECT c.file, max(c.ts) FROM calls c JOIN files f ON f.path = c.file "
             "WHERE c.is_sub = 0 AND f.is_sub = 0 AND c.entrypoint = 'cli' GROUP BY c.file")
        return [(Path(f).stem, Path(f), float(last)) for f, last in con.execute(q) if last is not None]
    finally:
        con.close()


def _verdict(share: Optional[float]) -> str:
    if share is None:
        return "INSUFFICIENT_EVIDENCE"
    return "WOULD_ROLLOVER" if share >= WOULD_AT else "CONTINUE" if share <= CONTINUE_AT else "INSUFFICIENT_EVIDENCE"


def judge(b: dict, capsule_chars: Optional[int], prior: dict, rehydration: list[float],
          min_samples: int = MIN_SAMPLES) -> dict:
    """Every verdict is rollover.decide. `rehydration`: carried tokens C to test (e.g. [0, p50])."""
    usage = {"state": "OK", "floor": b["floor"], "resident": b["resident"], "model": b["model"],
             "calls": b["call"]}
    ratio = price_at(b["model"], b["ts"])
    cap = capsule_chars if capsule_chars is not None else rollover.BOOTSTRAP_MAX_CHARS
    ask = lambda h: rollover.decide(usage, cap, True, None, ratio, horizon=h)
    shipped = ask(rollover.HORIZON_CALLS)
    gate = ask(10 ** 9)                     # only decide's own non-horizon gates can say no here
    out = {"call": b["call"], "resident": b["resident"], "growth_above_fresh": shipped.get("growth_above_fresh"),
           "breakeven_calls": shipped.get("breakeven_calls"), "capsule_chars": cap,
           "capsule_basis": "median sealed before T" if capsule_chars is not None else "UNKNOWN -> max",
           "price": ratio.get("source") or ratio.get("reason"), "pressure": "NOT EVALUATED (window unknown)",
           "shipped": {"would": shipped["would_rollover"], "reason": shipped["reason"]},
           "prior": {"n": len(prior["values"]), "sessions": prior["sessions"],
                     "censored_excluded": prior["censored_excluded"]}}
    if not gate["would_rollover"]:
        out["prior"]["verdict"] = out["rehydrated"] = "CONTINUE"
        out["reason"] = gate["reason"]
        return out
    if len(prior["values"]) < min_samples:
        out["prior"]["verdict"] = out["rehydrated"] = "INSUFFICIENT_EVIDENCE"
        out["reason"] = f"prior has {len(prior['values'])} values < {min_samples}"
        return out
    growth = gate["growth_above_fresh"]
    shares = {}
    for c in rehydration:
        hs = [v - c / growth for v in prior["values"]]
        shares[c] = sum(ask(h)["would_rollover"] for h in hs) / len(hs)
    out["prior"]["share"] = shares[rehydration[0]]
    out["prior"]["verdict"] = _verdict(shares[rehydration[0]])
    per = {_verdict(s) for s in shares.values()}
    out["rehydrated"] = per.pop() if len(per) == 1 else "INSUFFICIENT_EVIDENCE"
    out["rehydrated_shares"] = {str(int(c)): round(s, 3) for c, s in shares.items()}
    out["reason"] = f"break-even {gate['breakeven_calls']} calls vs prior survival"
    return out


def exposure(b: dict, total_calls: int, j: dict, rehydration: list[float]) -> Optional[dict]:
    """HINDSIGHT EVALUATION, never a decision input: mechanical reread exposure at T."""
    ratio = price_at(b["model"], b["ts"])
    g = j.get("growth_above_fresh")
    if ratio.get("state") != "OK" or not isinstance(g, int) or g <= 0:
        return None
    fresh = b["resident"] - g
    rem = total_calls - b["call"]
    premium = fresh * (ratio["write"] - ratio["read"]) / ratio["read"]
    hi = g * rem - premium - min(rehydration)
    lo = g * rem - premium - max(rehydration)
    return {"remaining_calls_actual": rem, "mechanical_exposure_read_eq": [round(lo), round(hi)],
            "label": "MECHANICAL, hindsight, growth frozen at T (lower bound of avoided reread); NOT a saving"}


def replay(session_id: str, ledger_path: Optional[Path] = None, find: Optional[Callable] = None,
           sessions: Optional[list] = None, min_samples: int = MIN_SAMPLES) -> dict:
    find = find or rollover._find_transcript
    ledger_path = Path(ledger_path or rollover.STATE_DIR / "rollover-ledger.jsonl")
    t = find(session_id)
    if not t or not Path(t).is_file():
        return {"verdict": "UNKNOWN", "reason": f"no transcript for {session_id}"}
    tr = session_trace(Path(t))
    if not tr["ctx"]:
        return {"verdict": "UNKNOWN", "reason": "no model calls"}
    rows, torn = read_ledger(ledger_path)
    rolled = {r["session_id"] for r in rows if r.get("event") == "successor_claimed" and r.get("session_id")}
    prior = Prior(sessions if sessions is not None else prior_from_index(),
                  capsule_chain(rows, session_id), rolled)
    out = {"session": session_id, "calls": tr["calls"], "floor": tr["ctx"][0],
           "max_growth_over_floor": max(tr["ctx"]) - tr["ctx"][0], "surface": sum(tr["ctx"]),
           "min_growth_gate": rollover.MIN_GROWTH_TOKENS, "torn_ledger_rows": torn, "boundaries": []}
    for b in boundaries(tr):
        fc = fresh_cost(ledger_path, find, min_samples, before=b["ts"])
        c50 = fc["carried_before_first_mutation"]["p50"]
        reh = [0.0] + ([float(c50)] if c50 is not None else [])
        j = judge(b, capsule_chars_before(rows, b["ts"]), prior.at(b["ts"]), reh, min_samples)
        j["rehydration_basis"] = (f"C in {{0, p50 {c50}}} from {fc['carried_before_first_mutation']['n']} "
                                  f"resumes certified before T" if c50 is not None
                                  else "no resumes before T: C = 0 only")
        j["evaluation"] = exposure(b, tr["calls"], j, reh)
        out["boundaries"].append(j)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    fc = sub.add_parser("fresh-cost")
    fc.add_argument("--json", action="store_true")
    fc.add_argument("--min-samples", type=int, default=MIN_SAMPLES)
    rp = sub.add_parser("replay")
    rp.add_argument("session")
    rp.add_argument("--json", action="store_true")
    rp.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "replay":
        res = replay(a.session)
        if a.out:
            Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
        if a.json:
            print(json.dumps(res, indent=1))
            return 0
        if "boundaries" not in res:
            print(f"replay: {res['verdict']} -- {res['reason']}")
            return 1
        print(f"replay {res['session']}: {res['calls']} calls, floor {res['floor']:,}, max growth over floor "
              f"{res['max_growth_over_floor']:,} (decide's growth gate {res['min_growth_gate']:,}), "
              f"{len(res['boundaries'])} commit boundaries")
        for j in res["boundaries"]:
            ev = j["evaluation"] or {}
            print(f"  call {j['call']:>4} resident {j['resident']:>9,} n*={j['breakeven_calls']} "
                  f"shipped={'WOULD' if j['shipped']['would'] else 'no'} prior={j['prior']['verdict']}"
                  f"({j['prior'].get('share')}, n={j['prior']['n']}) rehydrated={j['rehydrated']} "
                  f"exposure={ev.get('mechanical_exposure_read_eq')} rem={ev.get('remaining_calls_actual')}")
        return 0
    res = fresh_cost(min_samples=a.min_samples)
    if a.json:
        print(json.dumps(res, indent=1))
        return 0
    print(f"fresh-cost: {res['verdict']}  certified {res['certified']}, measured {len(res['samples'])}, "
          f"no claim {len(res['missing_claim'])}, no transcript {len(res['missing_transcript'])}, "
          f"never mutated {res['no_mutation']}, torn ledger rows {res['torn_rows']}")
    for k in ("first_ctx", "calls_to_first_mutation", "carried_before_first_mutation"):
        d = res[k]
        print(f"  {k}: n={d['n']} p10={d['p10']} p50={d['p50']} p90={d['p90']}")
    print(f"  {res['bound']}\n  decide assumes: {res['decide_assumes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
