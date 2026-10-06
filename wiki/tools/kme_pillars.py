#!/usr/bin/env python3
"""kme_pillars: the measuring instrument shared by the phase-3 KME pillars of the incremental-cognition program.

One CLI, one subcommand per pillar. Pillar D (silent-success hooks: hook_additional_context rent per call) is
the first; E..I plug one observer each into the same core.

    python3 wiki/tools/kme_pillars.py d --denominator KME-L --root <projects-dir> [--root ...] [--expand]
        [--until ISO|none] [--host local|gex44] [--select kme|all] [--out-dir DIR] [--frozen-file FILE]
        [--label NAME (OTHER only)] [--role auto|second_workload] [--json]

    --denominator KME-L | KME-G   a frozen denominator of vault/programs/incremental-cognition/denominators/
                                  kme_audit_2026-10-03.json; the run recomputes its own population with the frozen
                                  selection rule (kme_report.is_kme) and compares it field by field; only an exact
                                  match lets the share be judged. --until defaults to the freeze instant for these.
    --denominator OTHER --label N a named workload (never a frozen name); written to its own file, never merged.
    --denominator CPP-D-W7        a REFERENCED denominator read from the CE ledger (frozen.denominators.D-W7), never
                                  re-measured: the window is the frozen one, the share is judged against the ledger's
                                  weighted figure, and coverage = measured calls / frozen calls (below 1 the upper
                                  bound is unknown, so UNMEASURED unless the lower bound alone clears 3 %).

    python3 wiki/tools/kme_pillars.py all ...        every pillar (D..I) in ONE scan, one measurement file each
    python3 wiki/tools/kme_pillars.py population ... print the recomputed population and per-project rows of the
        selected sessions (KME is decided by content, so run it UNFILTERED with --expand over a whole projects root to
        find every dir that holds KME sessions); writes nothing; exit 0 when the frozen population is reproduced
    --until auto [--freeze-instant ISO]   locate the cutoff at which the recomputed population equals the frozen one on
                                  EVERY field: at the freeze instant (one scan), else bisect the call instants within
                                  24 h before it; a run never exceeds 24 scans; not found is UNMEASURED
    --since ISO                   drop lines before the instant (a time window with --until)
    --project-filter REGEX        only child dirs (--expand) or roots whose name matches; an optional speed-up

Parsing is the frozen instrument's own: kme_token_audit.scan_project, imported (never forked), extended only by
its additive observer= / keep= hooks. The measurement file is written once, exclusively, under
vault/programs/incremental-cognition/measurements/<P>-<DENOMINATOR>-<UTC date>[-n].md and carries counts, paths,
hook names and numbers only. The whole file text passes through modules.secret_firewall.redact before the write.

ESTIMATE MODEL (pillar D). The numerator is the char count of every hook_additional_context attachment, converted
to tokens at 3.0 .. 4.5 chars per token. An attachment is cache-WRITTEN once (weight 2) and cache-READ on every
later call it stays resident (weight 0.1 each) until the next compaction in its own transcript file:
burden = (chars / chars_per_token) x (2 + 0.1 x (resident_calls - 1)), in the ledger's weighted-input-equivalent
unit (input 1 + cache_read 0.1 + cache_write 2 + output 5). The share is burden / the weighted denominator.
A cache TTL lapse would re-write the blob, so the model under-states; the interval is the honest output.

Verdicts: ">= 3 %" (interval low >= 3 %), "< 3 %" (interval high < 3 %), STRADDLES, UNMEASURED. UNMEASURED is never
"below materiality": a drifted population or a corpus that does not record the signal is UNMEASURED.
Exit codes: 0 measured, 2 usage / refusal, 3 UNMEASURED (the file is still written).
"""
from __future__ import annotations

import argparse
import ast
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import sqlite3
import subprocess
import sys
import urllib.parse
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import kme_report  # noqa: E402
import kme_token_audit  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DENOMS_REL = "vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json"
LEDGER_REL = "vault/programs/incremental-cognition/ledger.json"
MEASUREMENTS_REL = "vault/programs/incremental-cognition/measurements"
# commit time of FROZEN_AT 18e928af8c489f9d29dd1e76e0c7aa3c6a6975eb (2026-10-03T18:13:37+02:00) in UTC
FREEZE_INSTANT = "2026-10-03T16:13:37Z"
INSTRUMENT = "wiki/tools/kme_pillars.py"

WEIGHTS = {"input": 1.0, "cache_read": 0.1, "cache_write": 2.0, "output": 5.0}
CPT_LO = 3.0     # chars per token, low end (more tokens per char)
CPT_HI = 4.5     # chars per token, high end
THRESHOLD = 0.03
POP_FIELDS = ("sessions_active", "sessions_dead", "calls", "input", "cache_write", "cache_read", "output")
RULE_DENOMINATORS = {"D": ("KME-L", "CPP-D-W7"), "E": ("KME-L",), "F": ("KME-L",), "G": ("KME-L",),
                     "H": ("KME-L",), "I": ("KME-L",)}
VERDICTS = (">= 3 %", "< 3 %", "STRADDLES", "UNMEASURED")
FROZEN_NAMES = ("KME-L", "KME-G", "CPP-D-W7")
LABEL_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,40}$")
EXIT_OK, EXIT_USAGE, EXIT_UNMEASURED = 0, 2, 3
EXIT_DISAGREE = 1       # certify: the index selection and the champion's differ
LOCATE_MAX_SCANS = 24      # the whole of a run, including the final measuring scan after a located cutoff
LOCATE_WINDOW_H = 24       # the cutoff search looks at call instants within this many hours before the freeze instant
SCAN_COUNT = 0             # transcript-tree scans done by this process (the one-scan claim of `all` is checked on it)
CE_LEDGER_REL = "vault/programs/cognitive-economy/ledger.json"
DW7_NAME = "CPP-D-W7"
DW7_FIELDS = ("calls", "input", "cache_write", "cache_read", "output")
DW7_WINDOW_RE = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\s+(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\s*$")

FRONT_KEYS = ("instrument", "pillar", "denominator", "denominator_kind", "rule_denominators", "evidence_role",
              "terminal_evidence", "terminal_evidence_reason", "second_workload_valid", "plane", "measured_at",
              "until", "command", "population_match", "numerator", "share_interval", "share_measured_population",
              "threshold", "materiality", "materiality_reason", "observability", "second_workload_required",
              "estimate_model")
FRONT_OPTIONAL = ("since", "until_located", "coverage", "second_workload_confirms", "frozen_source")     # written only when the run has them

ESTIMATE_MODEL = (
    "chars -> tokens at 3.0..4.5 chars per token; an attachment is cache-written once (weight 2) and cache-read "
    "on every later call it stays resident (weight 0.1 each) until the next compaction in its own transcript "
    "file; burden = tokens x (2 + 0.1 x (resident_calls - 1)); share = burden / weighted denominator "
    "(input 1 + cache_read 0.1 + cache_write 2 + output 5)")


# --------------------------------------------------------------------------- arithmetic
def weighted(tok) -> float:
    """Ledger weighting over a mapping with input / cache_read / cache_write / output."""
    return sum(WEIGHTS[k] * (tok.get(k, 0) or 0) for k in WEIGHTS)


def call_weighted(rec) -> float:
    """Weighted cost of one audit call record (inp / cr / cw / out)."""
    return (rec.get("inp", 0) * WEIGHTS["input"] + rec.get("cr", 0) * WEIGHTS["cache_read"]
            + rec.get("cw", 0) * WEIGHTS["cache_write"] + rec.get("out", 0) * WEIGHTS["output"])


def burden(chars, resident_calls, cpt) -> float:
    """Weighted cost of `chars` that stay resident for `resident_calls` calls (one write, then reads)."""
    if resident_calls < 1 or chars <= 0:
        return 0.0
    return (chars / cpt) * (WEIGHTS["cache_write"] + WEIGHTS["cache_read"] * (resident_calls - 1))


def burden_interval(chars, resident_calls):
    """(low at the largest chars-per-token, high at the smallest)."""
    return burden(chars, resident_calls, CPT_HI), burden(chars, resident_calls, CPT_LO)


def resident_calls(idx, compact_points, n_order) -> int:
    """Calls an item read at call-index `idx` stays in context: until the next compaction, else the file's end.
    The exact rule of kme_token_audit's residency loop."""
    nxt = [p for p in compact_points if p > idx]
    end = nxt[0] if nxt else n_order
    return max(0, end - idx)


def counts_for_d(atype) -> bool:
    """Only hook_additional_context counts in D's numerator; other hook attachments are reported beside it."""
    return atype == "hook_additional_context"


def context_chars(a) -> int:
    c = a.get("content")
    if isinstance(c, list):
        return sum(len(str(x)) for x in c)
    if isinstance(c, str):
        return len(c)
    return len(json.dumps(a, ensure_ascii=False))


# --------------------------------------------------------------------------- frozen denominators
def dw7_spec(ce_ledger_path):
    """The referenced CPP-D-W7 denominator read (never written) from the CE ledger's frozen D-W7 entry: the
    five usage fields, its weighted_input_equivalent and its window (the two ISO tokens at the end of `source`).
    Returns the spec, or {"error": why} when the entry is absent, unparseable or self-inconsistent."""
    try:
        raw = json.loads(Path(ce_ledger_path).read_text(encoding="utf-8").lstrip("\ufeff"))
        e = raw["frozen"]["denominators"]["D-W7"]
        fields = {k: e[k] for k in DW7_FIELDS}
        wanted = e["weighted_input_equivalent"]
        m = DW7_WINDOW_RE.search(str(e["source"]))
    except (OSError, ValueError, KeyError, TypeError):
        return {"error": f"{ce_ledger_path} has no readable frozen.denominators.D-W7 entry"}
    if m is None or not all(isinstance(fields[k], (int, float)) for k in DW7_FIELDS) \
            or not isinstance(wanted, (int, float)):
        return {"error": "the D-W7 entry has no window in its source string or non-numeric figures"}
    if abs(weighted(fields) - wanted) > 1:
        return {"error": f"D-W7 weighted_input_equivalent {wanted} differs from its fields' weighted() "
                         f"{round(weighted(fields))} by more than 1"}
    return {"fields": fields, "host": "local", "select": "all", "weighted": wanted, "since": m.group(1),
            "until": m.group(2), "denominator_kind": "referenced"}


def frozen_specs(denoms_path=None, ce_ledger_path=None):
    """{"KME-L": {fields, host, select, weighted}, "KME-G": {...}, "CPP-D-W7": {...}}: the first two from the
    frozen denominator file, the third (referenced, never re-measured here) from the CE ledger when it is readable
    (a damaged D-W7 entry is {"error": why}, so it refuses only the runs that use it)."""
    raw = json.loads(Path(denoms_path or (REPO / DENOMS_REL)).read_text(encoding="utf-8"))
    out = {}
    for name, host in (("KME-L", "local"), ("KME-G", "gex44")):
        if name in raw:
            fields = {k: raw[name][k] for k in POP_FIELDS}
            out[name] = {"fields": fields, "host": host, "select": "kme", "weighted": weighted(fields),
                         "denominator_kind": "frozen"}
    ce = Path(ce_ledger_path or (REPO / CE_LEDGER_REL))
    if ce.exists():
        out[DW7_NAME] = dw7_spec(ce)
    return out


def frozen_source_entry(path, default_path):
    """{path, sha256, default} of a frozen source actually read: the repo-relative path (absolute outside the repo),
    the LF-normalised sha256 of its bytes (null if unreadable) and whether it IS the repo's committed default."""
    p = Path(path)
    try:
        is_default = p.resolve() == Path(default_path).resolve()
    except OSError:
        is_default = False
    try:
        shown = p.resolve().relative_to(REPO.resolve()).as_posix()
    except (ValueError, OSError):
        shown = str(p)
    try:
        sha = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except OSError:
        sha = None
    return {"path": shown, "sha256": sha, "default": is_default}


def compare_population(measured, frozen):
    """("exact" | "drifted", {field: [measured, frozen]} for the unequal fields)."""
    deltas = {f: [measured.get(f), frozen.get(f)] for f in POP_FIELDS if measured.get(f) != frozen.get(f)}
    return ("drifted" if deltas else "exact"), deltas


def referenced_coverage(measured_calls, frozen_calls):
    """Measured calls / frozen calls of a referenced denominator: below 1 the window was not fully observed."""
    return (measured_calls / frozen_calls) if frozen_calls else 0.0


def materiality(share_interval, population_match, observability=1.0):
    """(verdict, reason). Drifted population or an unrecorded signal is UNMEASURED, never below materiality."""
    if population_match == "drifted":
        return "UNMEASURED", "population_not_reproduced"
    if not share_interval:
        return "UNMEASURED", "no share interval (empty or non-positive denominator)"
    lo, hi = share_interval
    obs = observability if observability is not None else 0.0
    if obs < 1.0:
        if lo >= THRESHOLD:
            return ">= 3 %", "lower bound clears 3 % although the signal is recorded for only part of the population"
        return "UNMEASURED", "signal not recorded for part of the population"
    if lo >= THRESHOLD:
        return ">= 3 %", "interval low bound >= 3 %"
    if hi < THRESHOLD:
        return "< 3 %", "interval high bound < 3 %"
    return "STRADDLES", "interval contains 3 %"


# --------------------------------------------------------------------------- time window
def parse_instant(v):
    """Timestamp string -> aware UTC datetime, or None when absent / unparseable."""
    if not isinstance(v, str) or not v:
        return None
    try:
        t = datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=datetime.timezone.utc)
    return t.astimezone(datetime.timezone.utc)


def _first_ts(path):
    """First parseable timestamp of a file (lookahead for leading timestamp-less lines)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:  # noqa: BLE001 -- an unparseable line has no timestamp, the scan counts it
                    continue
                if isinstance(o, dict):
                    t = parse_instant(o.get("timestamp"))
                    if t is not None:
                        return t
    except OSError:
        return None
    return None


def fmt_instant(t):
    """Aware datetime -> ISO Z text: whole seconds when exact, else milliseconds when exact, else microseconds."""
    t = t.astimezone(datetime.timezone.utc)
    if t.microsecond == 0:
        return t.strftime("%Y-%m-%dT%H:%M:%SZ")
    if t.microsecond % 1000 == 0:
        return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond:06d}Z"


_UNSET = object()


def make_keep(since, until):
    """Stateful per-path line predicate for kme_token_audit.scan_file(keep=...). A timestamp-less line inherits the
    last timestamp seen in its file; leading timestamp-less lines take the file's first parseable timestamp; a file
    with no timestamp at all keeps nothing."""
    state = {}

    def keep(path, o):
        if not isinstance(o, dict):
            return True
        st = state.setdefault(path, {"last": None, "first": _UNSET})
        t = parse_instant(o.get("timestamp"))
        if t is not None:
            st["last"] = t
        else:
            t = st["last"]
            if t is None:
                if st["first"] is _UNSET:
                    st["first"] = _first_ts(path)
                t = st["first"]
        if t is None:
            return False
        if since is not None and t < since:
            return False
        if until is not None and t > until:
            return False
        return True
    return keep


# --------------------------------------------------------------------------- cutoff locator
class _ScanBudget(Exception):
    pass


def cutoff_accepts(match, measured, frozen):
    """A located cutoff is accepted only when the recomputed population equals the frozen one on EVERY field."""
    return match == "exact"


def locate_cutoff(probe, frozen, freeze, first=None, max_scans=LOCATE_MAX_SCANS, window_h=LOCATE_WINDOW_H):
    """Find the instant at which the recomputed population equals the frozen one on every field.

    probe(until, want_instants) -> (population fields, call instants or None) performs ONE scan of the corpus
    truncated at `until`. Order: (1) the freeze instant itself (`first` is that scan when the caller already ran it);
    exact -> done. (2) The corpus holds fewer calls at the freeze than the frozen figure -> not found. (3) Bisect
    the sorted call instants within `window_h` hours before the freeze for the smallest instant reaching the frozen
    call count (the call count is monotone in the cutoff) and accept it only on an every-field match; if the calls
    match but another field does not, try the instant just before the next call (later non-call lines, streamed
    duplicates). Anything else is not found. Never more than `max_scans` scans. Returns {method: exact_at_freeze |
    bisect | not_found, until (datetime | None), scans, why}."""
    scans = 0
    seen = {}

    def result(method, why, until=None):
        return {"method": method, "until": until, "scans": scans, "why": why}

    def run(until, want):
        nonlocal scans
        if until in seen and not want:
            return seen[until], None
        if scans >= max_scans:
            raise _ScanBudget()
        scans += 1
        m, inst = probe(until, want)
        seen[until] = m
        return m, inst

    try:
        if first is None:
            m_f, inst = run(freeze, True)
        else:
            scans = 1
            m_f, inst = first
            seen[freeze] = m_f
        match, deltas = compare_population(m_f, frozen)
        if cutoff_accepts(match, m_f, frozen):
            return result("exact_at_freeze", "the population at the freeze instant equals the frozen one", freeze)
        want_calls = frozen["calls"]
        if m_f.get("calls", 0) < want_calls:
            return result("not_found", f"the corpus holds {m_f.get('calls')} calls at the freeze instant, below the "
                                       f"frozen {want_calls}: no earlier cutoff can reach it")
        floor = freeze - datetime.timedelta(hours=window_h)
        instants = sorted({t for t in (inst or ()) if floor <= t <= freeze})
        if not instants:
            return result("not_found", f"no call instants within {window_h} h before the freeze instant")
        lo, hi = 0, len(instants) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            m, _ = run(instants[mid], False)
            if m.get("calls", 0) >= want_calls:
                hi = mid
            else:
                lo = mid + 1
        cand = instants[lo]
        m, _ = run(cand, False)
        match, deltas = compare_population(m, frozen)
        if cutoff_accepts(match, m, frozen):
            return result("bisect", f"first call instant reaching {want_calls} calls", cand)
        if m.get("calls") == want_calls and lo + 1 < len(instants):
            cand2 = instants[lo + 1] - datetime.timedelta(microseconds=1)
            m2, _ = run(cand2, False)
            match2, deltas2 = compare_population(m2, frozen)
            if cutoff_accepts(match2, m2, frozen):
                return result("bisect", "just before the call instant after the first one reaching "
                                        f"{want_calls} calls", cand2)
            deltas = deltas2
        return result("not_found", "no cutoff within the window reproduces every field; at the best candidate the "
                                   f"fields [measured, frozen] differ: {json.dumps(deltas, sort_keys=True)}")
    except _ScanBudget:
        return result("not_found", f"scan budget of {max_scans} exhausted before a cutoff reproduced the population")


# --------------------------------------------------------------------------- observers
class PillarObserver:
    """Base of the per-pillar observers plugged into kme_token_audit.scan_file."""
    pillar = "?"

    def on_line(self, path, o, idx, sess):
        pass

    def on_file_end(self, path, sess, order, calls, compact_points):
        pass

    def result(self, selected, sessions, population):
        raise NotImplementedError


class _Fanout:
    """Fans lines out to the pillar observers and counts the kept lines per session."""

    def __init__(self, observers):
        self.observers = list(observers)
        self.kept = collections.Counter()

    def on_line(self, path, o, idx, sess):
        self.kept[id(sess)] += 1
        for ob in self.observers:
            ob.on_line(path, o, idx, sess)

    def on_file_end(self, path, sess, order, calls, compact_points):
        for ob in self.observers:
            ob.on_file_end(path, sess, order, calls, compact_points)


class InstantObserver(PillarObserver):
    """Collects the timestamp of every usage-bearing assistant line (a call instant) of every scanned file, for the
    cutoff locator; `lo` drops instants earlier than the search window."""
    pillar = "?"

    def __init__(self, lo=None):
        self.lo = lo
        self.rows = []

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict) or o.get("type") != "assistant":
            return
        msg = o.get("message")
        if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
            return
        t = parse_instant(o.get("timestamp"))
        if t is not None and (self.lo is None or t >= self.lo):
            self.rows.append((id(sess), t))

    def for_selected(self, selected):
        return sorted({t for sid, t in self.rows if sid in selected})


class DObserver(PillarObserver):
    """Pillar D: hook_additional_context chars, weighted by residency (calls until the next compaction)."""
    pillar = "D"
    ERROR_TYPES = ("hook_blocking_error", "hook_non_blocking_error")

    def __init__(self):
        self.records = []
        self._by_path = collections.defaultdict(list)
        self.others = []
        self.attach_sessions = set()
        self.hook_sessions = set()

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict) or o.get("type") != "attachment":
            return
        a = o.get("attachment")
        if not isinstance(a, dict):
            a = {}
        self.attach_sessions.add(id(sess))
        atype = a.get("type")
        if isinstance(atype, str) and atype.startswith("hook_"):
            # IN-01: a session is OBSERVED for D only when a hook attachment (any hook_* type) was seen in it. A
            # transcript format that records only file / todo_reminder attachments cannot show hook delivery, so
            # its silence is not evidence of zero additional context.
            self.hook_sessions.add(id(sess))
        hook = str(a.get("hookName") or a.get("hookEvent") or "?")[:60]
        if counts_for_d(atype):
            rec = {"sid": id(sess), "path": path, "idx": idx, "chars": context_chars(a), "hook": hook,
                   "resident": 0}
            self.records.append(rec)
            self._by_path[path].append(rec)
        elif isinstance(atype, str) and atype.startswith("hook_"):
            self.others.append((id(sess), atype, hook, len(json.dumps(a, ensure_ascii=False))))

    def on_file_end(self, path, sess, order, calls, compact_points):
        for rec in self._by_path.pop(path, []):
            rec["resident"] = resident_calls(rec["idx"], compact_points, len(order))

    def result(self, selected, sessions, population):
        recs = [r for r in self.records if r["sid"] in selected]
        chars = sum(r["chars"] for r in recs)
        lo = hi = 0.0
        by_hook = {}
        for r in recs:
            blo, bhi = burden_interval(r["chars"], r["resident"])
            lo += blo
            hi += bhi
            h = by_hook.setdefault(r["hook"], {"hook": r["hook"], "count": 0, "chars": 0,
                                               "weighted_lo": 0.0, "weighted_hi": 0.0})
            h["count"] += 1
            h["chars"] += r["chars"]
            h["weighted_lo"] += blo
            h["weighted_hi"] += bhi
        rows = sorted(by_hook.values(), key=lambda x: (-x["chars"], x["hook"]))[:20]
        for h in rows:
            h["weighted_lo"] = round(h["weighted_lo"], 3)
            h["weighted_hi"] = round(h["weighted_hi"], 3)
        others, errors = {}, collections.Counter()
        for sid, atype, hook, n in self.others:
            if sid not in selected:
                continue
            e = others.setdefault(atype, [0, 0])
            e[0] += 1
            e[1] += n
            if atype in self.ERROR_TYPES:
                errors[hook] += 1
        tool_uses = sum(s["tool_uses"] for s in sessions if id(s) in selected)
        calls = population["calls"]
        att_calls = sum(s["main"].get("calls", 0) + s["sub"].get("calls", 0)
                        for s in sessions if id(s) in selected and id(s) in self.hook_sessions)
        return {
            "numerator": {
                "kind": "hook_additional_context chars", "attachments": len(recs), "chars": chars,
                "tokens_interval": [chars / CPT_HI, chars / CPT_LO],
                "weighted_interval": [lo, hi], "tool_uses": tool_uses,
                "chars_per_tool_use": (chars / tool_uses) if tool_uses else None,
                "chars_per_call": (chars / calls) if calls else None,
            },
            "observability": (att_calls / calls) if calls else None,
            "details": {
                "by_hook": rows,
                "other_hook_attachments": others,
                "hook_errors": dict(errors),
                "sessions_with_attachment_lines": sum(1 for s in sessions
                                                      if id(s) in selected and id(s) in self.attach_sessions),
                "sessions_with_hook_attachments": sum(1 for s in sessions
                                                      if id(s) in selected and id(s) in self.hook_sessions),
            },
        }


# --------------------------------------------------------------------------- pillar E
STUB_PREFIX = "File unchanged since last read"
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
E_CLASSES = ("first", "stub", "identical_same_segment", "identical_after_compaction", "rewritten_identical",
             "changed_after_write", "changed_outside_tools", "unhashable")


def is_stub_text(text) -> bool:
    """The harness's own answer to a reread of an unchanged file: already virtualized, never pure waste."""
    return text.lstrip().startswith(STUB_PREFIX)


def classify_read(prev, h, wcount, seg):
    """E class of a hashed Read result against the previous read of the same (path, range) in the same transcript
    file. prev = None | (hash, writes_seen, segment); h = this result's hash; wcount = writes to the path so far;
    seg = this file's compaction count now."""
    if prev is None:
        return "first"
    p_hash, p_writes, p_seg = prev
    written = wcount > p_writes
    if h == p_hash:
        if written:
            return "rewritten_identical"
        return "identical_same_segment" if seg == p_seg else "identical_after_compaction"
    return "changed_after_write" if written else "changed_outside_tools"


def _blocks(content):
    return content if isinstance(content, list) else []


class EObserver(PillarObserver):
    """Pillar E: rereads of an identical file version within one transcript file (one thread = one context).

    Per transcript file: Read tool_use id -> (path, range); Edit / Write / MultiEdit / NotebookEdit bump a per-path
    write counter; a Read result is hashed (sha256 of the extracted text, never emitted) and classified against the
    previous read of the same (path, range) in that file. Only identical_same_segment is in the lower bound, the
    upper bound adds identical_after_compaction. A stub or an errored result is never an identical reread."""
    pillar = "E"

    def __init__(self):
        self.events = []
        self._by_path = collections.defaultdict(list)
        self._state = {}

    def _st(self, path):
        st = self._state.get(path)
        if st is None:
            st = {"reads": {}, "writes": collections.Counter(), "last": {}, "seg": 0}
            self._state[path] = st
        return st

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict):
            return
        st = self._st(path)
        t = o.get("type")
        if t == "system" and o.get("subtype") == "compact_boundary":
            st["seg"] += 1
            return
        msg = o.get("message")
        if not isinstance(msg, dict):
            return
        content = msg.get("content")
        if t == "assistant":
            for c in _blocks(content):
                if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                    continue
                inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                name = c.get("name")
                if name == "Read" and inp.get("file_path"):
                    st["reads"][c.get("id")] = (str(inp["file_path"]),
                                                (inp.get("offset"), inp.get("limit"), inp.get("pages")))
                elif name in WRITE_TOOLS:
                    target = inp.get("file_path") or inp.get("notebook_path")
                    if target:
                        st["writes"][str(target)] += 1
        elif t == "user":
            for c in _blocks(content):
                if not (isinstance(c, dict) and c.get("type") == "tool_result"):
                    continue
                rec = st["reads"].get(c.get("tool_use_id"))
                if rec is None or c.get("is_error"):
                    continue
                self._on_read_result(path, st, rec, c, idx, sess)

    def _on_read_result(self, path, st, rec, block, idx, sess):
        target, rng = rec
        raw = block.get("content")
        text = kme_token_audit.text_of(raw)
        chars = len(text)
        if is_stub_text(text):
            klass_ = "stub"
        elif any(isinstance(x, dict) and x.get("type") == "image" for x in _blocks(raw)):
            klass_ = "unhashable"     # an image result carries no text to hash: equal "[image]" would be a false match
        else:
            h = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
            wcount = st["writes"][target]
            klass_ = classify_read(st["last"].get((target, rng)), h, wcount, st["seg"])
            st["last"][(target, rng)] = (h, wcount, st["seg"])
        ev = {"sid": id(sess), "idx": idx, "chars": chars, "class": klass_, "path": target, "resident": 0}
        self.events.append(ev)
        self._by_path[path].append(ev)

    def on_file_end(self, path, sess, order, calls, compact_points):
        for ev in self._by_path.pop(path, []):
            ev["resident"] = resident_calls(ev["idx"], compact_points, len(order))

    def result(self, selected, sessions, population):
        evs = [e for e in self.events if e["sid"] in selected]
        classes = {k: {"count": 0, "chars": 0, "char_x_calls": 0} for k in E_CLASSES}
        lo = hi = 0.0
        per_path = {}
        for e in evs:
            c = classes[e["class"]]
            c["count"] += 1
            c["chars"] += e["chars"]
            c["char_x_calls"] += e["chars"] * e["resident"]
            if e["class"] in ("identical_same_segment", "identical_after_compaction"):
                blo, bhi = burden_interval(e["chars"], e["resident"])
                hi += bhi
                if e["class"] == "identical_same_segment":
                    lo += blo
                pp = per_path.setdefault(e["path"], {"path": e["path"], "count": 0, "chars": 0})
                pp["count"] += 1
                pp["chars"] += e["chars"]
        top = sorted(per_path.values(), key=lambda x: (-x["chars"], x["path"]))[:20]
        same, after = classes["identical_same_segment"], classes["identical_after_compaction"]
        chars = same["chars"] + after["chars"]
        return {
            "numerator": {
                "name": "identical-version rereads, residency-weighted",
                "definition": ("Read results whose sha256 equals the previous read of the same path and "
                               "offset/limit range in the same transcript file, with no Edit / Write / MultiEdit / "
                               "NotebookEdit of that path between; lower bound = same compaction segment only, "
                               "upper bound adds rereads after a compaction"),
                "kind": "identical-version rereads", "chars": chars, "chars_lower": same["chars"],
                "weighted_lo": lo, "weighted_hi": hi, "weighted_interval": [lo, hi],
            },
            "observability": 1.0,
            "details": {"classes": classes, "top_paths": top, "reads_total": len(evs)},
        }


# --------------------------------------------------------------------------- pillar F
_GSD_ROOTS = ("gsd-core", "get-shit-done")
_GSD_DIRS = {"workflows": "workflow", "references": "reference", "templates": "template"}
INIT_RE = re.compile(r"""(?:gsd-tools(?:\.cjs)?|gsd_run|\$\{?GSD_TOOLS\}?)['"]?\s+(?:query\s+)?init[. ]""")
SKILL_BODY_PREFIX = "Base directory for this skill:"


def gsd_doc_kind(path):
    """workflow / reference / template / skill / command for a GSD document path, else None. Three shapes:
    <gsd-core|get-shit-done>/<workflows|references|templates>/**.md ; skills/gsd-<name>/SKILL.md ;
    commands/gsd/<name>.md (either path separator)."""
    if not isinstance(path, str) or not path:
        return None
    parts = [x for x in re.split(r"[\\/]+", path) if x]
    if not parts or not parts[-1].lower().endswith(".md"):
        return None
    for i in range(len(parts) - 2):
        if parts[i] in _GSD_ROOTS and parts[i + 1] in _GSD_DIRS:
            return _GSD_DIRS[parts[i + 1]]
    if len(parts) >= 3 and parts[-1] == "SKILL.md" and parts[-2].startswith("gsd-") and parts[-3] == "skills":
        return "skill"
    if len(parts) >= 3 and parts[-2] == "gsd" and parts[-3] == "commands":
        return "command"
    return None


def pair_ratio(doc_chars, init_chars, n_paired):
    """doc chars per init-JSON char over the paired turns; None (never 0) when no turn holds both an init call and
    a doc: the absence of the compact state is not proof that it is small."""
    if n_paired < 1 or init_chars <= 0:
        return None
    return round(doc_chars / init_chars, 2)


def _basename(path):
    parts = [x for x in re.split(r"[\\/]+", str(path)) if x]
    return parts[-1] if parts else ""


def _user_text(content):
    """(text, has_tool_result) of a user message's content."""
    if isinstance(content, str):
        return content, False
    texts, tr = [], False
    for c in _blocks(content):
        if isinstance(c, dict):
            if c.get("type") == "tool_result":
                tr = True
            elif c.get("type") == "text":
                texts.append(c.get("text", ""))
        elif isinstance(c, str):
            texts.append(c)
    return "\n".join(texts), tr


class FObserver(PillarObserver):
    """Pillar F: residency (chars x resident calls) of GSD workflow docs, from every channel they arrive by, beside
    the size of the `gsd-tools ... init.*` JSON that exists for the same step (same human-prompt turn)."""
    pillar = "F"

    def __init__(self):
        self.docs = []
        self.inits = []
        self._by_path = collections.defaultdict(list)
        self._state = {}

    def _st(self, path):
        st = self._state.get(path)
        if st is None:
            st = {"reads": {}, "inits": set(), "turn": 0}
            self._state[path] = st
        return st

    def _doc(self, path, st, sess, idx, chars, kind, name):
        ev = {"sid": id(sess), "file": path, "turn": st["turn"], "idx": idx, "chars": chars, "kind": kind,
              "name": name, "resident": 0}
        self.docs.append(ev)
        self._by_path[path].append(ev)

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict):
            return
        st = self._st(path)
        t = o.get("type")
        if t == "attachment":
            a = o.get("attachment")
            if isinstance(a, dict):
                self._on_attachment(path, st, a, idx, sess)
            return
        msg = o.get("message")
        if not isinstance(msg, dict):
            return
        content = msg.get("content")
        if t == "assistant":
            for c in _blocks(content):
                if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                    continue
                inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                name = c.get("name")
                if name == "Read" and inp.get("file_path"):
                    k = gsd_doc_kind(str(inp["file_path"]))
                    if k:
                        st["reads"][c.get("id")] = (str(inp["file_path"]), k)
                elif name in ("Bash", "PowerShell") and INIT_RE.search(str(inp.get("command") or "")):
                    st["inits"].add(c.get("id"))
        elif t == "user":
            text, has_result = _user_text(content)
            for c in _blocks(content):
                if isinstance(c, dict) and c.get("type") == "tool_result" and not c.get("is_error"):
                    self._on_result(path, st, c, idx, sess)
            if has_result:
                return
            if not o.get("isMeta") and not text.startswith(SKILL_BODY_PREFIX):
                st["turn"] += 1                      # a human prompt starts a new turn
            if text.startswith(SKILL_BODY_PREFIX):
                first = text[len(SKILL_BODY_PREFIX):].strip().split("\n", 1)[0].strip()
                base = _basename(first)
                if base.startswith("gsd-"):
                    self._doc(path, st, sess, idx, len(text), "skill_body", base)
            elif "<command-name>/gsd" in text and "<objective>" in text:
                m = re.search(r"<command-name>/([^<\s]+)", text)
                self._doc(path, st, sess, idx, len(text), "command_body", m.group(1) if m else "gsd")

    def _on_result(self, path, st, block, idx, sess):
        tid = block.get("tool_use_id")
        text = kme_token_audit.text_of(block.get("content"))
        rec = st["reads"].get(tid)
        if rec is not None:
            self._doc(path, st, sess, idx, len(text), rec[1], _basename(rec[0]))
        if tid in st["inits"]:
            ev = {"sid": id(sess), "file": path, "turn": st["turn"], "idx": idx, "chars": len(text), "resident": 0}
            self.inits.append(ev)
            self._by_path[path].append(ev)

    def _on_attachment(self, path, st, a, idx, sess):
        atype = a.get("type")
        if atype == "file":
            content = a.get("content")
            inner = content.get("file") if isinstance(content, dict) else None
            fname = a.get("filename") or (inner.get("filePath") if isinstance(inner, dict) else None) \
                or a.get("displayPath")
            k = gsd_doc_kind(str(fname)) if fname else None
            if k:
                body = inner.get("content") if isinstance(inner, dict) and "content" in inner else content
                chars = len(body) if isinstance(body, str) else len(str(body))
                self._doc(path, st, sess, idx, chars, k, _basename(fname))
        elif atype == "invoked_skills":
            for sk in a.get("skills") if isinstance(a.get("skills"), list) else []:
                if not isinstance(sk, dict):
                    continue
                name = str(sk.get("name") or "")
                spath = str(sk.get("path") or "").replace("\\", "/")
                if name.startswith("gsd-") or "skills/gsd-" in spath:
                    body = sk.get("content")
                    chars = len(body) if isinstance(body, str) else len(str(body))
                    self._doc(path, st, sess, idx, chars, "invoked_skill", name or _basename(spath))

    def on_file_end(self, path, sess, order, calls, compact_points):
        for ev in self._by_path.pop(path, []):
            ev["resident"] = resident_calls(ev["idx"], compact_points, len(order))

    def result(self, selected, sessions, population):
        docs = [e for e in self.docs if e["sid"] in selected]
        inits = [e for e in self.inits if e["sid"] in selected]
        lo = hi = 0.0
        by_kind, by_name = {}, {}
        for e in docs:
            blo, bhi = burden_interval(e["chars"], e["resident"])
            lo += blo
            hi += bhi
            k = by_kind.setdefault(e["kind"], {"count": 0, "chars": 0, "char_x_calls": 0,
                                               "weighted_lo": 0.0, "weighted_hi": 0.0})
            k["count"] += 1
            k["chars"] += e["chars"]
            k["char_x_calls"] += e["chars"] * e["resident"]
            k["weighted_lo"] += blo
            k["weighted_hi"] += bhi
            n = by_name.setdefault((e["kind"], e["name"]), {"doc": e["name"], "kind": e["kind"], "count": 0,
                                                            "chars": 0, "char_x_calls": 0})
            n["count"] += 1
            n["chars"] += e["chars"]
            n["char_x_calls"] += e["chars"] * e["resident"]
        for k in by_kind.values():
            k["weighted_lo"] = round(k["weighted_lo"], 3)
            k["weighted_hi"] = round(k["weighted_hi"], 3)
        top = sorted(by_name.values(), key=lambda x: (-x["char_x_calls"], x["doc"]))[:20]
        ilo = ihi = 0.0
        for e in inits:
            blo, bhi = burden_interval(e["chars"], e["resident"])
            ilo += blo
            ihi += bhi
        chars_total = sum(e["chars"] for e in inits)
        doc_turns, init_turns = collections.Counter(), collections.Counter()
        for e in docs:
            doc_turns[(e["file"], e["turn"])] += e["chars"]
        for e in inits:
            init_turns[(e["file"], e["turn"])] += e["chars"]
        paired = [k for k in init_turns if k in doc_turns]
        p_doc = sum(doc_turns[k] for k in paired)
        p_init = sum(init_turns[k] for k in paired)
        ratio = pair_ratio(p_doc, p_init, len(paired))
        chars = sum(e["chars"] for e in docs)
        return {
            "numerator": {
                "name": "GSD workflow-doc residency",
                "definition": ("chars x resident calls of GSD workflow / reference / template docs, skill bodies, "
                               "invoked_skills re-injections and gsd command bodies, from Read results, file "
                               "attachments, skill-body user text and command bodies; residency = calls until the "
                               "next compaction in the same transcript file"),
                "kind": "GSD workflow-doc residency", "chars": chars,
                "weighted_lo": lo, "weighted_hi": hi, "weighted_interval": [lo, hi],
            },
            "observability": 1.0,
            "details": {
                "by_kind": by_kind, "top_docs": top,
                "init": {"count": len(inits), "chars_total": chars_total,
                         "chars_mean": (chars_total / len(inits)) if inits else None,
                         "weighted_lo": round(ilo, 3), "weighted_hi": round(ihi, 3)},
                "paired_turns": {"count": len(paired), "doc_chars": p_doc, "init_chars": p_init, "ratio": ratio},
                "init_json_present": bool(inits),
                "docs_total": len(docs),
            },
        }


# --------------------------------------------------------------------------- subagent meta (H and I)
_META_CACHE = {}


def read_subagent_meta(path):
    """The `<name>.meta.json` beside a subagent transcript `<name>.jsonl` as a dict, read-only and once per path
    within a scan (the cache is cleared by scan()); {} on absence, bad JSON or a non-object."""
    path = str(path)
    if path in _META_CACHE:
        return _META_CACHE[path]
    meta = {}
    if path.endswith(".jsonl"):
        try:
            with open(path[:-len(".jsonl")] + ".meta.json", "r", encoding="utf-8") as fh:
                got = json.load(fh)
            if isinstance(got, dict):
                meta = got
        except (OSError, ValueError):
            meta = {}
    _META_CACHE[path] = meta
    return meta


def subagent_type(path):
    """(agent type name, absent): the sanitized agentType of the subagent's meta.json, else ("unknown", True)."""
    name = re.sub(r"[^A-Za-z0-9_.:-]", "", str(read_subagent_meta(path).get("agentType") or ""))[:40]
    return (name, False) if name else ("unknown", True)


def is_subagent_path(path):
    return "/subagents/" in str(path).replace("\\", "/")


# --------------------------------------------------------------------------- pillar G
# Heuristic text markers (English only). Every pattern is a module constant so the gates and drills can drive it.
FALSIFY_RE = re.compile(
    r"\b(?:falsified|falsification|falsify|falsifies|disproven|disproved|refuted|ruled out|rejected by evidence"
    r"|no measurable (?:effect|saving|savings|reduction))\b", re.I)
SEALED_RE = re.compile(r"\b(?:sealed|locked decision|decision locked)\b", re.I)
RETEST_RE = re.compile(
    r"\b(?:re-?test(?:ed|ing|s)?|re-?run(?:ning|s)?|re-?measure(?:d|ment|s)?|(?:try|test) (?:it |that |this )?again"
    r"|another (?:attempt|experiment|try)|second (?:attempt|experiment)|challenger|retry|retries)\b", re.I)
RELITIGATE_RE = re.compile(
    r"\b(?:re-?open(?:ed|ing|s)?|revisit(?:ed|ing|s)?|reconsider(?:ed|ing|s)?|overturn(?:ed|ing|s)?"
    r"|undo the decision)\b", re.I)
NEGATED_RE = re.compile(r"\b(?:do not|don't|dont|never|no need to|without)\s+(?:" + RETEST_RE.pattern + "|"
                        + RELITIGATE_RE.pattern + ")", re.I)
CITE_RE = re.compile(
    r"\b(?:already|previously|known)\s+(?:falsified|sealed|ruled out)\b|\b(?:was|were)\s+(?:falsified|sealed|ruled out)\b"
    r"|\bfalsified\s+(?:in|at|by|twice|x2)\b|\bper\s+(?:the\s+)?sealed\b|\bas\s+sealed\b", re.I)
DECISION_ID_RE = re.compile(r"\b([A-Z]{1,3})-?(\d{1,3})\b")
SENT_SPLIT_RE = re.compile(r"[.!?;]+(?:\s+|$)|\n+")
STOPWORDS = frozenset((
    "the and for are was were with that this from into onto behind then than them they but not you our its has "
    "have had will would should could can may might must all any each per via one two now here there when what "
    "which who how why also only just more most some such over under after before between about because while "
    "where does did done being been get got let use used using make made next first last other another still "
    "very much many both either neither than too yet said says say see seen look looks need needs want wants "
    "like likewise okay yes").split())
MARKER_WORDS = frozenset((
    "falsified falsification falsify falsifies disproven disproved refuted ruled rejected evidence sealed locked "
    "decision retest tested testing tests test rerun running run remeasure measured measure again try attempt "
    "experiment second challenger retry retries reopen reopened open revisit reconsider overturn undo already "
    "previously known not never without").split())


def _norm_word(w):
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def _words(sentence):
    return re.findall(r"[a-z]+", sentence.lower())


def _content(tokens):
    return [t for t in tokens if 3 <= len(t) <= 20 and t not in STOPWORDS and t not in MARKER_WORDS]


def strip_negated(sentence):
    """Remove 'do not re-test' style phrases before RETEST / RELITIGATE are looked for."""
    return NEGATED_RE.sub(" ", sentence)


def _decision_ids(sentence):
    return [f"{m.group(1)}-{int(m.group(2))}" for m in DECISION_ID_RE.finditer(sentence)]


def _decision_ids_raw(sentence):
    return [m.group(0) for m in DECISION_ID_RE.finditer(sentence)]


def _subject(sentence, marker):
    """Last two content words before the marker, or the first two after it when the marker opens the sentence
    and is followed by ':'. May be one or no words (kept for loose matching only)."""
    before = _content(_words(sentence[:marker.start()]))
    if not before and sentence[marker.end():].lstrip().startswith(":"):
        return tuple(_content(_words(sentence[marker.end():]))[:2])
    return tuple(before[-2:])


def contains_seq(words, seq):
    n = len(seq)
    if n == 0 or n > len(words):
        return False
    return any(words[i:i + n] == list(seq) for i in range(len(words) - n + 1))


def is_earlier(rec_key, cand_key) -> bool:
    """A record only counts as the earlier half of a re-test when it precedes the candidate in time."""
    return rec_key < cand_key


def overlap_loose(a, b) -> bool:
    shared = len(a & b)
    return shared >= 2 and shared / max(1, min(len(a), len(b))) >= 0.4


_EPOCH = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


class GObserver(PillarObserver):
    """Pillar G: falsified hypotheses and sealed decisions that later text re-tests or re-litigates. Heuristic: the
    count is an interval (strict subject phrase match .. loose window overlap), never a point."""
    pillar = "G"

    def __init__(self):
        self.records = []
        self.cands = []
        self.reuse = []
        self._state = {}
        self._pref = {}
        self._by_path = collections.defaultdict(list)
        self._seq = 0

    def _st(self, path):
        st = self._state.get(path)
        if st is None:
            st = {"turn": 0, "starts": [0], "msg": {}, "ts": None, "blk": 0}
            self._state[path] = st
        return st

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict):
            return
        st = self._st(path)
        t = parse_instant(o.get("timestamp"))
        if t is not None:
            st["ts"] = t
        msg = o.get("message")
        if not isinstance(msg, dict):
            return
        content = msg.get("content")
        typ = o.get("type")
        if typ == "user":
            text, has_result = _user_text(content)
            if not has_result and not o.get("isMeta") and not text.startswith(SKILL_BODY_PREFIX):
                st["turn"] += 1
                st["starts"].append(idx)
            return
        if typ != "assistant":
            return
        call = None
        if isinstance(msg.get("usage"), dict):
            key = (msg.get("id") or o.get("uuid"), o.get("requestId"))
            call = st["msg"].setdefault(key, idx)
        for c in _blocks(content):
            if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str):
                self._text(path, st, sess, c["text"], call, t)

    def _text(self, path, st, sess, text, call, t):
        st["blk"] += 1
        blk = (path, st["blk"])
        self._seq += 1
        key = (t or st["ts"] or _EPOCH, self._seq)
        base = {"sid": id(sess), "file": path, "blk": blk, "key": key, "call": call, "turn": st["turn"],
                "session": str(sess.get("session") or "")[:8]}
        for sent in SENT_SPLIT_RE.split(text):
            s = sent.replace("’", "'").strip()
            if len(s) < 4:
                continue
            tokens = _words(s)
            cw = [_norm_word(w) for w in _content(tokens)]
            if CITE_RE.search(s):
                self.reuse.append(dict(base))
            elif FALSIFY_RE.search(s):
                subj = _subject(s, FALSIFY_RE.search(s))
                self._record("falsified", base, s, subj, None, cw)
            elif SEALED_RE.search(s):
                ids = _decision_ids(s)
                subj = () if ids else _subject(s, SEALED_RE.search(s))
                self._record("sealed", base, s, subj, ids[0] if ids else None, cw,
                             _decision_ids_raw(s)[0] if ids else None)
            stripped = strip_negated(s)
            kinds = []
            if RETEST_RE.search(stripped):
                kinds.append("retest")
            if RELITIGATE_RE.search(stripped):
                kinds.append("relitigate")
            if kinds:
                cand = dict(base, kinds=kinds, content=frozenset(cw), seqw=[_norm_word(w) for w in tokens],
                            ids=frozenset(_decision_ids(s)), chars=len(s))
                self.cands.append(cand)
                self._by_path[path].append(cand)

    def _record(self, kind, base, s, subj, ident, cw, ident_raw=None):
        self.records.append(dict(base, kind=kind, subject_raw=tuple(subj), ident_raw=ident_raw,
                                 subject=tuple(_norm_word(w) for w in subj), ident=ident, content=frozenset(cw)))

    def on_file_end(self, path, sess, order, calls, compact_points):
        st = self._state.get(path)
        pref = [0.0]
        for key in order:
            r = calls[key]
            pref.append(pref[-1] + (0.0 if r.get("model") == "<synthetic>" else call_weighted(r)))
        self._pref[path] = pref
        starts = (st or {"starts": [0]})["starts"] + [len(order)]
        for cand in self._by_path.pop(path, []):
            c = cand["call"]
            if c is None or c >= len(order):
                cand["span"] = None
                continue
            nxt = [x for x in starts if x > c]
            cand["span"] = (c, nxt[0] if nxt else len(order))

    def _match(self, selected):
        recs = [r for r in self.records if r["sid"] in selected]
        cands = [c for c in self.cands if c["sid"] in selected]
        by_word, by_id = collections.defaultdict(list), collections.defaultdict(list)
        for i, r in enumerate(recs):
            for w in r["content"]:
                by_word[w].append(i)
            if r["ident"]:
                by_id[r["ident"]].append(i)
        hits = []        # (cand, strict record idx set, loose record idx set)
        for cand in cands:
            shared = collections.Counter()
            for w in cand["content"]:
                for i in by_word.get(w, ()):
                    shared[i] += 1
            pool = set(shared)
            for ident in cand["ids"]:
                pool.update(by_id.get(ident, ()))
            strict, loose = set(), set()
            for i in pool:
                r = recs[i]
                if r["blk"] == cand["blk"] or not is_earlier(r["key"], cand["key"]):
                    continue
                is_strict = (bool(r["ident"]) and r["ident"] in cand["ids"]) or \
                    (len(r["subject"]) == 2 and contains_seq(cand["seqw"], r["subject"]))
                if is_strict:
                    strict.add(i)
                if is_strict or overlap_loose(r["content"], cand["content"]):
                    loose.add(i)
            if loose:
                hits.append((cand, strict, loose))
        return recs, cands, hits

    def result(self, selected, sessions, population):
        recs, cands, hits = self._match(selected)
        out = {}
        for kind in ("falsified", "sealed"):
            idxs = [i for i, r in enumerate(recs) if r["kind"] == kind]
            sset = set().union(*[h[1] for h in hits]) if hits else set()
            lset = set().union(*[h[2] for h in hits]) if hits else set()
            out[kind] = {"records": len(idxs), "strict": len([i for i in idxs if i in sset]),
                         "loose": len([i for i in idxs if i in lset])}
        lower_calls = {}
        spans = collections.defaultdict(list)
        sample_pool = []
        for cand, strict, loose in hits:
            if cand["span"] is None:
                continue
            spans[cand["file"]].append(cand["span"])
            if strict:
                lower_calls[(cand["file"], cand["span"][0])] = True
                r = recs[sorted(strict)[0]]
                subj = " ".join(r["subject_raw"]) if len(r["subject_raw"]) == 2 else (r["ident_raw"] or "")
                sample_pool.append((cand["key"], {"kind": "falsification" if r["kind"] == "falsified" else "sealed",
                                                  "subject": subj, "session": cand["session"],
                                                  "call": cand["span"][0]}))
        lo = sum(self._pref[f][c + 1] - self._pref[f][c] for f, c in lower_calls)
        hi = 0.0
        for f, rngs in spans.items():
            pref = self._pref[f]
            covered = set()
            for a, b in rngs:
                covered.update(range(a, b))
            hi += sum(pref[i + 1] - pref[i] for i in covered)
        hi = max(hi, lo)
        sample_pool.sort(key=lambda x: x[0])
        n = len(sample_pool)
        picks = list(range(n)) if n <= 20 else sorted({round(i * (n - 1) / 19) for i in range(20)})
        strict_c = [h for h in hits if h[1]]
        reuse_n = len([r for r in self.reuse if r["sid"] in selected])
        return {
            "numerator": {
                "name": "re-tested falsified hypotheses and re-litigated sealed decisions (heuristic)",
                "definition": ("assistant text sentences carrying a re-test / re-litigation marker that match a "
                               "strictly earlier falsification or sealed-decision sentence (strict = the subject "
                               "phrase or decision id recurs; loose = content-word overlap); lower bound = measured "
                               "weighted cost of the calls carrying strict matches, upper bound = the whole turns "
                               "of the calls carrying loose matches"),
                "kind": "heuristic re-test interval", "chars": sum(h[0]["chars"] for h in strict_c),
                "weighted_lo": lo, "weighted_hi": hi, "weighted_interval": [lo, hi],
            },
            "observability": 1.0,
            "details": {
                "retested_falsifications": out["falsified"], "relitigated_sealed": out["sealed"],
                "reuse_citations": reuse_n,
                "candidates": {"retest": len([c for c in cands if "retest" in c["kinds"]]),
                               "relitigate": len([c for c in cands if "relitigate" in c["kinds"]]),
                               "strict_matched": len(strict_c), "loose_matched": len(hits)},
                "samples": [sample_pool[i][1] for i in picks],
                "sample_note": "up to 20 strict matches, evenly spread in time, for a human precision check",
            },
        }


# --------------------------------------------------------------------------- pillar H
VERIFY_CMD_RE = re.compile(
    r"\btest_[\w.-]*\.(?:py|js|cjs|mjs)\b|\bpytest\b|\bnpm\s+(?:run\s+)?test\b|\bnode\s+--test\b|\bmix\s+test\b"
    r"|\bgo\s+test\b|\bcargo\s+test\b|--selftest\b|--final\b|--drill\b|\bverify\b|\btsc\b[^\n]*--noEmit", re.I)
VERIFIER_AGENT_RE = re.compile(r"verif|checker|review|audit|arbiter|judge|\bqa\b|tester", re.I)
# a command segment whose program only reads or moves files is not a verification run even when it names a test file
NON_RUN_PROGRAMS = frozenset((
    "cat ls head tail less more wc grep egrep fgrep rg git sed awk echo printf cp mv rm mkdir touch chmod stat file "
    "diff find ln which type nl tee vim nano open code").split())
WRAPPERS = frozenset(("timeout", "time", "env", "nice", "sudo", "nohup", "stdbuf", "command", "exec"))
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SIG_TOKEN_RE = re.compile(r"[A-Za-z0-9./:_-]{1,80}")
SEG_SPLIT_RE = re.compile(r"&&|\|\||[;|\n]")
H_DEFINITION = ("verification: test/gate tool calls + output carriage (CE P definition) + verifier subagents")
H_SENSITIVITY_LABEL = "full-call-cost sensitivity, not the frozen definition, not used for the verdict"


def _program_tokens(seg):
    toks = seg.split()
    i = 0
    while i < len(toks):
        t = toks[i]
        if ASSIGN_RE.match(t):
            i += 1
        elif t in WRAPPERS:
            i += 1
            if t == "timeout" and i < len(toks) and re.fullmatch(r"\d+[smhd]?", toks[i]):
                i += 1
        else:
            break
    return toks[i:]


HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
QUOTED_RE = re.compile(r"\"(?:[^\"\\]|\\.){0,2000}\"|'[^']{0,2000}'", re.S)
INSTALL_RE = re.compile(r"\b(?:pip3?|pipx|conda|apt|apt-get|brew)\b|\bnpm\s+(?:i|install|ci)\b|\buv\s+(?:pip|add|sync)\b")


def _code_only(command):
    """The command without heredoc bodies and quoted strings: text that merely mentions a test is not a test run
    (the cost is a run hidden inside `bash -c "..."`, which is not seen; the caveat says so)."""
    kept, end = [], None
    for line in (command or "").split("\n"):
        if end is not None:
            if line.strip() == end:
                end = None
            continue
        m = HEREDOC_RE.search(line)
        if m:
            end = m.group(2)
        kept.append(line)
    return QUOTED_RE.sub('""', "\n".join(kept))


def verify_segment(command):
    """The first command segment of a Bash command that is a verification run, else None."""
    for seg in SEG_SPLIT_RE.split(_code_only(command)):
        seg = seg.strip()
        if not seg or not VERIFY_CMD_RE.search(seg) or INSTALL_RE.search(seg):
            continue
        toks = _program_tokens(seg)
        if toks and os.path.basename(toks[0]) not in NON_RUN_PROGRAMS:
            return seg
    return None


SIG_PATH_RE = re.compile(r"[./]?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?")
SIG_URLISH_RE = re.compile(r"://|^//|[?@#=]|%[0-9A-Fa-f]{2}")
SIG_RUN_RE = re.compile(r"[A-Za-z0-9]{20,}")
_SIG_REDACT = []


def _opaque_run(tok):
    """True when `tok` holds a long opaque run (a key, a hash, a token): 20+ letters/digits mixing both, or 32+ of
    either. Such a run is never written: it is a secret candidate however it is shaped."""
    for m in SIG_RUN_RE.finditer(tok):
        run = m.group(0)
        if len(run) >= 32 or (re.search(r"[A-Za-z]", run) and re.search(r"[0-9]", run)):
            return True
    return False


def _sig_redact(text):
    """The Secret Firewall's redact() over a signature. Unavailable means the signature is dropped (fail closed)."""
    if not _SIG_REDACT:
        try:
            _SIG_REDACT.append(_load_redact())
        except Exception:  # noqa: BLE001 -- no redaction available: write nothing of the command
            _SIG_REDACT.append(None)
    fn = _SIG_REDACT[0]
    return "(other)" if fn is None else fn(text)


def _sig_base(tok):
    """A path token's last segment: the directories around a script (a customer name, a home directory) never reach a
    signature (STATE debt 3 / 05 IN-02 residual). A token without a slash is returned unchanged."""
    t = tok.rstrip("/")
    return os.path.basename(t) if "/" in t and os.path.basename(t) else tok


def cmd_signature(seg):
    """Program name and at most one non-URL subcommand or script token, never flags, values or arguments (WR-02).
    The program must be a bare name or a plain path; the second token is kept only as a short lowercase word, `-m
    <module>`, or a plain path; a URL (scheme, query, userinfo, fragment) becomes `<url>` and a long opaque run
    becomes `<opaque>`. Any path keeps its basename only. The result then goes through redact()."""
    toks = _program_tokens(seg.split("\n", 1)[0])
    if not toks or toks[0].startswith("-") or not SIG_PATH_RE.fullmatch(toks[0]) or len(toks[0]) > 80 \
            or _opaque_run(toks[0]):
        return "(other)"
    out = [_sig_base(toks[0])]
    if len(toks) > 2 and toks[1] == "-m" and re.fullmatch(r"[A-Za-z0-9_.]{1,40}", toks[2]) \
            and not _opaque_run(toks[2]):
        out += ["-m", toks[2]]
    elif len(toks) > 1 and not toks[1].startswith("-"):
        t = toks[1]
        if SIG_URLISH_RE.search(t):
            out.append("<url>")
        elif _opaque_run(t) and re.fullmatch(r"[A-Za-z0-9_.:/-]+", t):
            out.append("<opaque>")
        elif len(t) <= 80 and SIG_PATH_RE.fullmatch(t) and (re.fullmatch(r"[A-Za-z]{1,20}", t) or re.search(r"[./]", t)):
            out.append(_sig_base(t))
    return _sig_redact(" ".join(out))


def h_numerator_interval(lo, hi, sensitivity_weighted):
    """The verdict interval of H: the frozen definition only. The full-call-cost sensitivity never enters."""
    return lo, hi


def ce_owner_verdicts(repo=REPO, ref=CE_LEDGER_REL, pillars=("P", "G")):
    """The CE ledger's terminals for `pillars`, read with git at HEAD (the R2 owner_ledger form: commit + pillar +
    terminal). A terminal is None while the pillar is open. Anything unreadable is UNMEASURABLE, never a terminal."""
    exe = os.environ.get("CPP_GIT_EXE") or shutil.which("git")
    if not exe:
        return {"status": "UNMEASURABLE", "why": "git executable not found"}

    def git(*args):
        try:
            return subprocess.run([exe, "-C", str(repo)] + list(args), capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.SubprocessError) as exc:
            return exc

    head = git("rev-parse", "HEAD")
    if isinstance(head, Exception) or head.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", head.stdout.strip()):
        return {"status": "UNMEASURABLE", "why": "cannot resolve HEAD in the repository"}
    commit = head.stdout.strip()
    shown = git("show", f"HEAD:{ref}")
    if isinstance(shown, Exception) or shown.returncode != 0:
        return {"status": "UNMEASURABLE", "why": f"{ref} is not readable at HEAD {commit[:8]}"}
    try:
        led = json.loads(shown.stdout.lstrip("﻿"))
        state = led["state"]
        out = {}
        for p in pillars:
            if p not in state:
                return {"status": "UNMEASURABLE", "why": f"pillar {p} is absent from the ledger state at {commit[:8]}"}
            out[p] = (state[p] or {}).get("terminal")
    except (ValueError, KeyError, TypeError, AttributeError):
        return {"status": "UNMEASURABLE", "why": f"{ref} at {commit[:8]} is not a ledger with a state map"}
    return {"ref": ref, "commit": commit, "pillars": out}


class HObserver(PillarObserver):
    """Pillar H: verification share, by CE pillar P's definition (test / gate tool calls + their output carriage)
    plus verifier subagents (agentType from the subagent's meta.json) counted once at their measured weighted cost."""
    pillar = "H"

    def __init__(self):
        self.events = []
        self.agents = []
        self._by_path = collections.defaultdict(list)
        self._state = {}

    def _st(self, path):
        st = self._state.get(path)
        if st is None:
            st = {"tools": {}, "msg": {}}
            self._state[path] = st
        return st

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict):
            return
        msg = o.get("message")
        if not isinstance(msg, dict):
            return
        st = self._st(path)
        content = msg.get("content")
        if o.get("type") == "assistant":
            key = None
            if isinstance(msg.get("usage"), dict):
                key = (msg.get("id") or o.get("uuid"), o.get("requestId"))
                st["msg"].setdefault(key, idx)
            for c in _blocks(content):
                if not (isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") in ("Bash", "PowerShell")):
                    continue
                inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                seg = verify_segment(str(inp.get("command") or ""))
                if seg is None:
                    continue
                ev = {"sid": id(sess), "file": path, "call_key": key,
                      "in_chars": len(json.dumps(inp, ensure_ascii=False)), "sig": cmd_signature(seg),
                      "res_chars": 0, "ridx": None, "resident": 0, "call_w": 0.0, "dropped": False}
                st["tools"][c.get("id")] = ev
                self.events.append(ev)
                self._by_path[path].append(ev)
        elif o.get("type") == "user":
            for c in _blocks(content):
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    ev = st["tools"].get(c.get("tool_use_id"))
                    if ev is not None:
                        ev["res_chars"] = len(kme_token_audit.text_of(c.get("content")))
                        ev["ridx"] = idx

    def on_file_end(self, path, sess, order, calls, compact_points):
        evs = self._by_path.pop(path, [])
        for ev in evs:
            if ev["ridx"] is not None:
                ev["resident"] = resident_calls(ev["ridx"], compact_points, len(order))
            rec = calls.get(ev["call_key"]) if ev["call_key"] is not None else None
            if rec is not None and rec.get("model") != "<synthetic>":
                ev["call_w"] = call_weighted(rec)
        if not is_subagent_path(path):
            return
        atype, absent = subagent_type(path)
        weighted_calls = [call_weighted(calls[k]) for k in order if calls[k].get("model") != "<synthetic>"]
        verifier = (not absent) and bool(VERIFIER_AGENT_RE.search(atype))
        self.agents.append({"sid": id(sess), "type": atype, "absent": absent, "verifier": verifier,
                            "calls": len(weighted_calls), "weighted": sum(weighted_calls)})
        if verifier:
            for ev in evs:
                ev["dropped"] = True

    def result(self, selected, sessions, population):
        evs = [e for e in self.events if e["sid"] in selected and not e["dropped"]]
        agents = [a for a in self.agents if a["sid"] in selected]
        lo = hi = 0.0
        res_chars = 0
        sigs = {}
        for e in evs:
            ilo, ihi = e["in_chars"] / CPT_HI * WEIGHTS["output"], e["in_chars"] / CPT_LO * WEIGHTS["output"]
            blo, bhi = burden_interval(e["res_chars"], e["resident"]) if e["ridx"] is not None else (0.0, 0.0)
            lo += ilo + blo
            hi += ihi + bhi
            res_chars += e["res_chars"]
            g = sigs.setdefault(e["sig"], {"signature": e["sig"], "count": 0, "result_chars": 0,
                                           "weighted_lo": 0.0, "weighted_hi": 0.0})
            g["count"] += 1
            g["result_chars"] += e["res_chars"]
            g["weighted_lo"] += ilo + blo
            g["weighted_hi"] += ihi + bhi
        rows = sorted(sigs.values(), key=lambda x: (-x["result_chars"], x["signature"]))[:20]
        for g in rows:
            g["weighted_lo"] = round(g["weighted_lo"], 3)
            g["weighted_hi"] = round(g["weighted_hi"], 3)
        ver_types, other_types = {}, collections.Counter()
        vw = 0.0
        for a in agents:
            if a["verifier"]:
                t = ver_types.setdefault(a["type"], [0, 0, 0.0])
                t[0] += 1
                t[1] += a["calls"]
                t[2] += a["weighted"]
                vw += a["weighted"]
            else:
                other_types[a["type"]] += 1
        carrying = {}
        for e in evs:
            if e["call_key"] is not None:
                carrying[(e["file"], e["call_key"])] = e["call_w"]
        sens_w = sum(carrying.values()) + vw
        tool_part = [lo, hi]
        lo, hi = lo + vw, hi + vw
        lo, hi = h_numerator_interval(lo, hi, sens_w)
        w = population.get("weighted") or 0
        return {
            "numerator": {
                "name": H_DEFINITION,
                "definition": ("Bash / PowerShell tool calls whose command is a test or gate run (their input at "
                               "the output weight 5, their result at its residency burden until the next "
                               "compaction) plus every call of a subagent whose meta.json agentType names a "
                               "verifier, at measured weighted cost, once (the tool calls inside a verifier "
                               "subagent are not added again)"),
                "kind": "verification share", "chars": res_chars,
                "weighted_lo": lo, "weighted_hi": hi, "weighted_interval": [lo, hi],
            },
            "observability": 1.0,
            "details": {
                "verification_tool_calls": len(evs), "result_chars": res_chars, "cmd_signatures": rows,
                "weighted_tool_calls": tool_part, "weighted_verifier_subagents": vw,
                "verifier_agent_types": {k: [v[0], v[1], v[2]] for k, v in sorted(ver_types.items())},
                "other_agent_types": dict(sorted(other_types.items())),
                "meta_absent": sum(1 for a in agents if a["absent"]),
                "upper_sensitivity": {"share": (sens_w / w) if w > 0 else None, "weighted": sens_w,
                                      "label": H_SENSITIVITY_LABEL},
                "consumed_owner_verdicts": ce_owner_verdicts(),
            },
        }


# --------------------------------------------------------------------------- pillar I
def distribution(values):
    """{n, min, p10, median, p90, max, total} of a list of numbers; percentiles are nearest-rank, the median of an
    even count is the mean of the two middle values. An empty list has n 0 and None elsewhere (total 0)."""
    v = sorted(values)
    n = len(v)
    if n == 0:
        return {"n": 0, "min": None, "p10": None, "median": None, "p90": None, "max": None, "total": 0}

    def rank(p):
        return v[max(0, min(n - 1, -(-p * n // 100) - 1))]
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2
    return {"n": n, "min": v[0], "p10": rank(10), "median": med, "p90": rank(90), "max": v[-1], "total": sum(v)}


class IObserver(PillarObserver):
    """Pillar I: the bootstrap cost of each subagent. Per subagent transcript file: its first non-synthetic call's
    context (input + cache_write + cache_read), that call's weighted cost, and the floor's rent, i.e. that first-call
    context re-read at the cache-read weight on each of the file's later calls. Beside it the main thread's own
    first-call context. A session whose main file carries inline sidechain lines (`isSidechain: true`) holds
    subagent calls this observer cannot separate, so it is unobserved for I (absent is not zero)."""
    pillar = "I"

    def __init__(self):
        self.subs = []
        self.mains = []
        self.inline = collections.Counter()

    def on_line(self, path, o, idx, sess):
        if isinstance(o, dict) and o.get("isSidechain") is True and not is_subagent_path(path):
            self.inline[id(sess)] += 1

    def on_file_end(self, path, sess, order, calls, compact_points):
        real = [k for k in order if calls[k].get("model") != "<synthetic>"]
        if not real:
            return
        first = calls[real[0]]
        ctx = first["inp"] + first["cw"] + first["cr"]
        if not is_subagent_path(path):
            self.mains.append({"sid": id(sess), "first_ctx": ctx})
            return
        atype, _absent = subagent_type(path)
        self.subs.append({"sid": id(sess), "type": atype, "first_ctx": ctx, "first_weighted": call_weighted(first),
                          "calls": len(real), "floor_rent": ctx * WEIGHTS["cache_read"] * (len(real) - 1),
                          "cold": first["cw"] > first["cr"]})

    def result(self, selected, sessions, population):
        subs = [e for e in self.subs if e["sid"] in selected]
        mains = [e for e in self.mains if e["sid"] in selected]
        total = sum(e["first_weighted"] + e["floor_rent"] for e in subs)
        by_type = {}
        for e in subs:
            t = by_type.setdefault(e["type"], {"files": 0, "first_ctx_total": 0, "weighted": 0.0})
            t["files"] += 1
            t["first_ctx_total"] += e["first_ctx"]
            t["weighted"] += e["first_weighted"] + e["floor_rent"]
        calls = population["calls"]
        seen = sum(s["main"].get("calls", 0) + s["sub"].get("calls", 0)
                   for s in sessions if id(s) in selected and id(s) not in self.inline)
        return {
            "numerator": {
                "name": "subagent first-call context: first-call weighted + floor rent (measured tokens)",
                "definition": ("per subagent transcript file: the weighted cost of its first non-synthetic call "
                               "(input 1 + cache_read 0.1 + cache_write 2 + output 5) plus the floor rent, that "
                               "first call's context (input + cache_write + cache_read) read at weight 0.1 on each "
                               "of the file's later calls; measured usage, no chars-per-token estimate"),
                "kind": "subagent bootstrap", "chars": 0,
                "weighted_lo": total, "weighted_hi": total, "weighted_interval": [total, total],
            },
            "observability": (seen / calls) if calls else None,
            "details": {
                "subagent_files": len(subs), "first_ctx": distribution([e["first_ctx"] for e in subs]),
                "main_first_ctx": distribution([e["first_ctx"] for e in mains]),
                "by_agent_type": {k: {"files": v["files"], "first_ctx_total": v["first_ctx_total"],
                                      "weighted": round(v["weighted"], 3)} for k, v in sorted(by_type.items())},
                "first_weighted_total": sum(e["first_weighted"] for e in subs),
                "floor_rent_total": sum(e["floor_rent"] for e in subs),
                "cold_files": sum(1 for e in subs if e["cold"]),
                "sessions_with_inline_sidechain": sum(1 for s in sessions if id(s) in selected and self.inline[id(s)]),
            },
        }


OBSERVERS = {"D": DObserver, "E": EObserver, "F": FObserver, "G": GObserver, "H": HObserver, "I": IObserver}
PILLAR_HELP = {"D": "silent-success hooks: hook_additional_context rent per call",
               "E": "large-source read virtualization: rereads of identical file versions",
               "F": "GSD operational projection: workflow-doc residency beside the init JSON",
               "G": "derived cognition: re-tested falsified hypotheses and re-litigated sealed decisions (interval)",
               "H": "proof reuse: verification share (test / gate runs, verifier subagents) + the CE P / G owner read",
               "I": "startup floor + subagent bootstrap: first-call context of every subagent file, beside the main thread's"}


# --------------------------------------------------------------------------- scan + population
def _scope_dirs(roots, expand, project_filter=None):
    """The project dirs a scan of these roots reads: every child dir (expand) or the root itself, kept when the
    compiled `project_filter` matches (re.search) the child / root basename. One rule for scan() and for the
    challenger's source-watermark walk, so the walk can never list a dir the scan would not."""
    dirs = []
    for r in roots:
        if expand:
            dirs += [os.path.join(r, d) for d in sorted(os.listdir(r)) if os.path.isdir(os.path.join(r, d))
                     and (project_filter is None or project_filter.search(d))]
        elif project_filter is None or project_filter.search(os.path.basename(r.rstrip("/\\"))):
            dirs.append(r)
    return dirs


def scan(roots, expand, host, observers, keep, project_filter=None, select=None):
    """Frozen-parser scan of every root; returns (sessions, fanout, dirs). `project_filter` (a compiled regex) keeps
    only the child dirs (expand) or the roots whose basename it matches (re.search). `select(proj, sid, path)` (the
    challenger's index tier) is forwarded to scan_project: a refused transcript file is never opened."""
    global SCAN_COUNT
    SCAN_COUNT += 1
    _META_CACHE.clear()
    dirs = _scope_dirs(roots, expand, project_filter)
    fan = _Fanout(observers)
    sessions = []
    for d in dirs:
        for s in kme_token_audit.scan_project(d, observer=fan, keep=keep, select=select):
            kme_token_audit.finish_session(s, host)
            sessions.append(s)
    return sessions, fan, dirs


def population(sessions, spec, kept, window_active):
    """The frozen report's population for the selected sessions. With a time window active a session none of whose
    lines were kept does not exist yet (dropped, not a dead session)."""
    pop = {f: 0 for f in POP_FIELDS}
    selected = set()
    projects = {}
    for s in sessions:
        if window_active and kept.get(id(s), 0) == 0:
            continue
        if spec.get("select", "kme") == "kme" and not kme_report.is_kme(s):
            continue
        calls = s["main"].get("calls", 0) + s["sub"].get("calls", 0)
        pr = projects.setdefault(s.get("project") or "?", {"project": s.get("project") or "?", "sessions_active": 0,
                                                           "sessions_dead": 0, "calls": 0, "cache_read": 0})
        if calls == 0:
            pop["sessions_dead"] += 1
            pr["sessions_dead"] += 1
            continue
        pop["sessions_active"] += 1
        pr["sessions_active"] += 1
        pr["calls"] += calls
        pr["cache_read"] += s["main"].get("cr", 0) + s["sub"].get("cr", 0)
        selected.add(id(s))
        pop["calls"] += calls
        for src, dst in (("inp", "input"), ("cw", "cache_write"), ("cr", "cache_read"), ("out", "output")):
            pop[dst] += s["main"].get(src, 0) + s["sub"].get(src, 0)
    pop["weighted"] = weighted(pop)
    pop["selected"] = selected
    pop["projects"] = projects
    return pop


# --------------------------------------------------------------------------- rendering + writing
def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def plane_name():
    h = socket.gethostname()
    return "gex44" if "gex44" in h.lower() else h


def command_string(argv):
    parts = list(sys.argv) if argv is None else [INSTRUMENT] + list(argv)
    return shlex.join([os.path.basename(sys.executable) or "python3"] + parts)


def _pillar_details(p, det):
    """Human-readable details lines for pillars other than D (the json block carries the full structure)."""
    out = []
    if p == "E":
        for k, c in det.get("classes", {}).items():
            out.append(f"- class {k}: {c['count']} reads, {c['chars']} chars, {c['char_x_calls']} char x calls")
        for t in det.get("top_paths", []):
            out.append(f"- reread path {t['path']}: {t['count']} rereads, {t['chars']} chars")
    elif p == "F":
        for k, c in det.get("by_kind", {}).items():
            out.append(f"- kind {k}: {c['count']} docs, {c['chars']} chars, {c['char_x_calls']} char x calls, "
                       f"weighted {c['weighted_lo']}..{c['weighted_hi']}")
        for t in det.get("top_docs", []):
            out.append(f"- doc {t['doc']} ({t['kind']}): {t['count']} deliveries, {t['chars']} chars, "
                       f"{t['char_x_calls']} char x calls")
        out.append(f"- gsd-tools init calls: {json.dumps(det.get('init'))}")
        out.append(f"- paired turns (doc and init in the same human-prompt turn): {json.dumps(det.get('paired_turns'))}")
        out.append(f"- init_json_present: {det.get('init_json_present')}")
    elif p == "G":
        out.append(f"- re-tested falsifications (records / strict / loose): {json.dumps(det.get('retested_falsifications'))}")
        out.append(f"- re-litigated sealed decisions (records / strict / loose): {json.dumps(det.get('relitigated_sealed'))}")
        out.append(f"- reuse citations (cited, never counted as re-tests): {det.get('reuse_citations')}")
        out.append(f"- candidates: {json.dumps(det.get('candidates'))}")
        for m in det.get("samples", []):
            out.append(f"- sample: {m['kind']} subject={m['subject']} session={m['session']} call={m['call']}")
    elif p == "H":
        out.append(f"- verification tool calls: {det.get('verification_tool_calls')}, result chars: {det.get('result_chars')}")
        out.append(f"- weighted split: tool calls + carriage (CE P definition) {json.dumps(det.get('weighted_tool_calls'))}, "
                   f"verifier subagents {det.get('weighted_verifier_subagents')}")
        for g in det.get("cmd_signatures", []):
            out.append(f"- command {g['signature']}: {g['count']} calls, {g['result_chars']} result chars, "
                       f"weighted {g['weighted_lo']}..{g['weighted_hi']}")
        out.append(f"- verifier subagents [files, calls, weighted]: {json.dumps(det.get('verifier_agent_types'))}")
        out.append(f"- other subagent types (names only): {json.dumps(det.get('other_agent_types'))}")
        out.append(f"- subagent files without meta.json: {det.get('meta_absent')}")
        out.append(f"- upper_sensitivity: {json.dumps(det.get('upper_sensitivity'))}")
        ow = det.get("consumed_owner_verdicts") or {}
        out.append(f"- consumed_owner_verdicts: {json.dumps(ow)}")
        pil = ow.get("pillars")
        if not pil:
            out.append("- R2 (consume the CE P and G verdicts) is not satisfiable: the owner ledger could not be read.")
        elif any(v is None for v in pil.values()):
            out.append("- R2 (consume the CE P and G verdicts) is NOT satisfiable at this commit: the CE terminal of "
                       + ", ".join(k for k, v in pil.items() if v is None)
                       + " is null (open on this history). Recorded as open, not as a pass.")
        else:
            out.append("- CE owner terminals are present at this commit: " + json.dumps(pil))
    elif p == "I":
        out.append(f"- subagent files: {det.get('subagent_files')}, cold first calls: {det.get('cold_files')}, "
                   f"sessions with inline sidechain lines (unobserved): {det.get('sessions_with_inline_sidechain')}")
        out.append(f"- subagent first-call context distribution: {json.dumps(det.get('first_ctx'))}")
        out.append(f"- main-thread first-call context distribution: {json.dumps(det.get('main_first_ctx'))}")
        out.append(f"- weighted split: first calls {det.get('first_weighted_total')}, floor rent {det.get('floor_rent_total')}")
        for k, v in det.get("by_agent_type", {}).items():
            out.append(f"- agent type {k}: {v['files']} files, first-call context total {v['first_ctx_total']}, "
                       f"weighted {v['weighted']}")
    return out


def render_measurement(res) -> str:
    lines = ["---"]
    for k in FRONT_KEYS:
        lines.append(f"{k}: {json.dumps(res[k], ensure_ascii=False)}")
    for k in FRONT_OPTIONAL:
        if res.get(k) is not None:
            lines.append(f"{k}: {json.dumps(res[k], ensure_ascii=False)}")
    lines.append("---")
    p = res["pillar"]
    lines += ["", f"# Pillar {p} measurement: {PILLAR_HELP.get(p, p)} -- {res['denominator']} "
                  f"({res['evidence_role']}, plane {res['plane']})", ""]
    lines += ["## Population", "", f"match: **{res['population_match']}**", "",
              "| field | measured | frozen | delta |", "|---|---|---|---|"]
    meas, froz = res["population"], res.get("frozen_population") or {}
    for f in POP_FIELDS:
        m, z = meas.get(f), froz.get(f)
        d = (m - z) if isinstance(z, (int, float)) and isinstance(m, (int, float)) else ""
        lines.append(f"| {f} | {m} | {z if z is not None else 'n/a'} | {d} |")
    lines.append(f"| weighted | {meas.get('weighted')} | {froz.get('weighted', 'n/a')} | |")
    n = res["numerator"]
    if p == "D":
        num_lines = [f"- kind: {n.get('kind')}", f"- attachments: {n.get('attachments')}",
                     f"- chars: {n.get('chars')}", f"- tokens interval: {n.get('tokens_interval')}",
                     f"- weighted interval: {n.get('weighted_interval')}",
                     f"- chars per tool use: {n.get('chars_per_tool_use')}",
                     f"- chars per call: {n.get('chars_per_call')}"]
    else:
        num_lines = [f"- name: {n.get('name')}", f"- definition: {n.get('definition')}",
                     f"- chars: {n.get('chars')}", f"- weighted interval: {n.get('weighted_interval')}"]
    lines += ["", "## Numerator", ""] + num_lines + [
        f"- share interval (judged): {res['share_interval']}",
        f"- share interval (measured population): {res['share_measured_population']}",
        f"- materiality: {res['materiality']} ({res['materiality_reason']})",
        f"- observability: {res['observability']}"]
    det = res["details"]
    lines += ["", "## Details", ""]
    if p == "D":
        for h in det.get("by_hook", []):
            lines.append(f"- hook {h['hook']}: {h['count']} attachments, {h['chars']} chars, "
                         f"weighted {h['weighted_lo']}..{h['weighted_hi']}")
        lines.append(f"- other hook attachments (never in the numerator): "
                     f"{json.dumps(det.get('other_hook_attachments'))}")
        lines.append(f"- hook errors: {json.dumps(det.get('hook_errors'))}")
    else:
        lines += _pillar_details(p, det)
    lines += ["", "## Caveats", ""] + [f"- {c}" for c in res["caveats"]]
    lines += ["", "<!-- kmep-json -->", json.dumps(res, indent=1, ensure_ascii=False), "<!-- /kmep-json -->", ""]
    return "\n".join(lines)


def write_measurement(out_dir, stem, text):
    """Single exclusive write of <stem>.md, or <stem>-2.md, -3.md ...; an existing file is never truncated."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        path = out_dir / (f"{stem}.md" if n == 1 else f"{stem}-{n}.md")
        try:
            with open(path, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            return path
        except FileExistsError:
            n += 1


def _load_redact():
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from modules.secret_firewall import redact
    return redact


CAVEATS = (
    "chars-per-token is an interval (3.0 .. 4.5), not a point; the share is an interval for that reason",
    "single-write residency model: a cache TTL lapse re-writes the blob, so the model under-states the burden",
    "a streamed assistant message split by a time cutoff keeps only the kept lines' usage",
    "a hook that injects context through a channel other than a hook_additional_context attachment is not "
    "measured here; hook_success / hook_system_message are reported beside the numerator, never inside it",
    "only active sessions (calls > 0) of the selected population enter the numerator and the denominator",
)


G_CAVEATS = (
    "heuristic: sentence-level English text markers, no semantic reading; the count is an interval, never a point",
    "precision is not measured by the instrument: up to 20 strict matches are sampled (two-word subject, session "
    "prefix, call index) for a human to read in the named session; recall is unknown",
    "subjects are the two content words before a falsification marker (or a decision id), so two unrelated "
    "findings that share a phrase collide, and a first-time statement phrased 'was falsified' is read as a citation",
    "share interval: lower = measured weighted cost of the calls carrying strict matches, upper = the whole turns "
    "of the calls carrying loose matches; no chars-per-token estimate is involved",
    "only assistant text blocks of the selected active sessions are read; user text, tool results and thinking "
    "are not",
)
H_CAVEATS = CAVEATS[:2] + (
    "verification = Bash / PowerShell commands matching a test or gate pattern; heredoc bodies and quoted strings "
    "are blanked first, a segment whose program only reads or moves files (cat, grep, git ...) or installs a "
    "package is not a run; plus subagents whose meta.json agentType names a verifier; a test run hidden inside "
    "bash -c \"...\", a hook or a script wrapper is not seen",
    "a subagent transcript without a meta.json beside it has an unknown agent type and is never counted as a "
    "verifier subagent (details.meta_absent counts them)",
    "upper_sensitivity is the full cost of every call that issued a verification command, plus verifier subagents; "
    "it is reported beside the verdict and never decides it",
    "the CE P and G verdicts are read with git at HEAD (details.consumed_owner_verdicts); a null terminal means open, "
    "and the consumption (R2) is then not satisfiable",
)
I_CAVEATS = CAVEATS[:2] + (
    "subagent first-call context = input + cache_write + cache_read of the first non-synthetic call of each "
    "subagent transcript file; the floor rent assumes that context stays cached and unchanged for the file's later "
    "calls (read at weight 0.1 each); a cache expiry would re-write it, so the rent under-states",
    "a cold first call (cache_write > cache_read) is a cache write a later subagent may have reused; reported as "
    "details.cold_files, not removed from the numerator",
    "a session whose main file carries inline sidechain lines (isSidechain true) holds subagent calls this "
    "observer cannot separate: it is unobserved for I and lowers the observability, never read as zero",
    "frozen rule I: the measured subagent first-call context is added to CE B / SC A-C; no rule or skill is moved "
    "here, and the share is a measurement, not a saving",
)
CAVEATS_BY_PILLAR = {"G": G_CAVEATS, "H": H_CAVEATS, "I": I_CAVEATS}
ESTIMATE_MODEL_G = ("no char estimate: weighted cost of the carrying calls from their recorded usage "
                    "(input 1 + cache_read 0.1 + cache_write 2 + output 5); lower = calls with strict matches, "
                    "upper = their whole turns for loose matches; share = cost / weighted denominator")
ESTIMATE_MODEL_I = ("no char estimate: measured usage only; per subagent file = first-call weighted cost + first-call "
                    "context x 0.1 x (later calls); share = sum over the selected population / weighted denominator "
                    "(input 1 + cache_read 0.1 + cache_write 2 + output 5)")
ESTIMATE_MODELS = {"G": ESTIMATE_MODEL_G, "I": ESTIMATE_MODEL_I}   # H keeps the default chars-per-token model


# --------------------------------------------------------------------------- access plan (challenger)
PLANS = ("champion", "scoped", "challenger", "auto")
INDEX_MIN_SCHEMA = 5
CERT_SCHEMA = "kmep-cert/1"
CERT_SUFFIX = ".kmep-cert.json"
_KP_REL = "wiki/tools/kme_pillars.py"
_KR_REL = "wiki/tools/kme_replay.py"

# --- invalidation keys -----------------------------------------------------------------------------------------
# The certificate is a persisted claim: "for THIS question, the index selection equals the champion's, under THESE code
# and definition digests". Two keys bind it to code. The selection-parser digest covers everything that decides WHICH
# sessions are in the population (the frozen parser, the champion classifier, the index substrate, this file's own
# population / window rules); a change anywhere in it invalidates every session's cached decision. The metric digests
# cover what is MEASURED from the selected sessions (one per pillar, plus the population definition); a pillar's change
# names that pillar and does not touch the selection. Both read SOURCE TEXT only (ast segments of module-level names),
# so neither module is imported to compute them.
SELECTION_SOURCES = ("tools/usage_index.py", "wiki/tools/kme_token_audit.py", "wiki/tools/kme_report.py")
SELECTION_NAMES = ("population", "make_keep", "parse_instant", "_first_ts", "_UNSET")     # of this file
_COMMON = ("CPT_HI", "CPT_LO", "POP_FIELDS", "WEIGHTS", "THRESHOLD", "materiality", "burden", "burden_interval",
           "resident_calls")
METRIC_DEFINITIONS = {
    "population": ((_KP_REL, ("POP_FIELDS", "WEIGHTS", "weighted")),),
    "D": ((_KP_REL, ("DObserver", "THRESHOLD", "materiality", "ESTIMATE_MODEL", "CAVEATS", "CPT_HI", "CPT_LO",
                     "POP_FIELDS", "WEIGHTS", "burden", "burden_interval", "context_chars", "counts_for_d",
                     "resident_calls")),),
    "E": ((_KP_REL, ("EObserver", "THRESHOLD", "materiality", "ESTIMATE_MODEL", "CAVEATS", "CPT_HI", "CPT_LO",
                     "WEIGHTS", "E_CLASSES", "STUB_PREFIX", "WRITE_TOOLS", "_blocks", "burden", "burden_interval",
                     "classify_read", "is_stub_text", "resident_calls")),),
    "F": ((_KP_REL, ("FObserver", "THRESHOLD", "materiality", "ESTIMATE_MODEL", "CAVEATS", "CPT_HI", "CPT_LO",
                     "WEIGHTS", "INIT_RE", "SKILL_BODY_PREFIX", "_GSD_DIRS", "_GSD_ROOTS", "_basename", "_blocks",
                     "_user_text", "burden", "burden_interval", "gsd_doc_kind", "pair_ratio", "resident_calls")),),
    "G": ((_KP_REL, ("GObserver", "THRESHOLD", "materiality", "ESTIMATE_MODEL_G", "G_CAVEATS", "WEIGHTS", "CITE_RE",
                     "DECISION_ID_RE", "FALSIFY_RE", "MARKER_WORDS", "NEGATED_RE", "RELITIGATE_RE", "RETEST_RE",
                     "SEALED_RE", "SENT_SPLIT_RE", "SKILL_BODY_PREFIX", "STOPWORDS", "_EPOCH", "_blocks", "_content",
                     "_decision_ids", "_decision_ids_raw", "_norm_word", "_subject", "_user_text", "_words",
                     "call_weighted", "contains_seq", "is_earlier", "overlap_loose", "strip_negated")),),
    "H": ((_KP_REL, ("HObserver", "THRESHOLD", "materiality", "ESTIMATE_MODEL", "CAVEATS", "H_CAVEATS", "ASSIGN_RE",
                     "CE_LEDGER_REL", "CPT_HI", "CPT_LO", "HEREDOC_RE", "H_DEFINITION", "H_SENSITIVITY_LABEL",
                     "INSTALL_RE", "NON_RUN_PROGRAMS", "POP_FIELDS", "QUOTED_RE", "SEG_SPLIT_RE", "SIG_PATH_RE",
                     "SIG_RUN_RE", "SIG_URLISH_RE", "VERIFIER_AGENT_RE", "VERIFY_CMD_RE", "WEIGHTS", "WRAPPERS",
                     "_SIG_REDACT", "_blocks", "_code_only", "_opaque_run", "_program_tokens", "_sig_base",
                     "_sig_redact", "burden", "burden_interval", "call_weighted", "ce_owner_verdicts",
                     "cmd_signature", "h_numerator_interval", "is_subagent_path", "read_subagent_meta",
                     "resident_calls", "subagent_type", "verify_segment")),),
    "I": ((_KP_REL, ("IObserver", "THRESHOLD", "materiality", "ESTIMATE_MODEL_I", "I_CAVEATS", "CAVEATS",
                     "POP_FIELDS", "WEIGHTS", "call_weighted", "distribution", "is_subagent_path",
                     "read_subagent_meta", "subagent_type")),),
    "L": ((_KR_REL, ("AGENT_TOOLS", "BOUND_READINGS", "CANDIDATES", "CAVEATS", "DEFINITIONS", "NAMES",
                     "READ_ONLY_TOOLS", "ROLLOVER_GROWTH", "ROLLOVER_SENSITIVITY", "ROUND", "RULE_DENOMINATORS",
                     "RereadObserver", "RetryObserver", "RolloverObserver", "_events_of", "_r",
                     "_unmeasured_reason", "bound_label", "candidate_status", "denominator_for", "dense_ranks",
                     "entry_figures", "in_selection", "rank_candidates", "rank_result", "retry_key", "retry_kind",
                     "retry_weighted", "rollover_avoided", "rollover_segments", "rollover_weighted",
                     "same_message", "scrub_details", "split_ranking", "terminal_ok", "thread_of",
                     "upper_bound_of")),
          (_KP_REL, ("ASSIGN_RE", "CPT_HI", "CPT_LO", "DW7_FIELDS", "EObserver", "E_CLASSES", "POP_FIELDS",
                     "SIG_PATH_RE", "SIG_RUN_RE", "SIG_URLISH_RE", "STUB_PREFIX", "THRESHOLD", "WEIGHTS", "WRAPPERS",
                     "WRITE_TOOLS", "_SIG_REDACT", "_blocks", "_opaque_run", "_program_tokens", "_sig_base",
                     "_sig_redact", "burden", "burden_interval", "classify_read", "cmd_signature",
                     "compare_population", "distribution", "is_stub_text", "is_subagent_path",
                     "referenced_coverage", "resident_calls"))),
}
PILLAR_KEYS = ("D", "E", "F", "G", "H", "I", "L")


def _source_text(rel):
    """Text of a repo source (a path relative to the repo root, or an absolute one). One seam, so a test can show a
    definition change without editing a committed file."""
    return Path(rel if os.path.isabs(rel) else REPO / rel).read_text(encoding="utf-8")


def _source_bytes(rel):
    return Path(rel if os.path.isabs(rel) else REPO / rel).read_bytes()


def _module_segments(rel, names, cache=None):
    """[(name, source text of its module-level def / assignment, or None when the name is gone)] read by `ast` from the
    file text: the file is parsed, never imported. A name that disappears reads as None, so a rename is a change."""
    cache = {} if cache is None else cache
    if rel not in cache:
        text = _source_text(rel)
        defs = {}
        for node in ast.parse(text).body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                defs[node.name] = node
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        defs[t.id] = node
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                defs[node.target.id] = node
        cache[rel] = (text, defs)
    text, defs = cache[rel]
    return [(n, ast.get_source_segment(text, defs[n]) if n in defs else None) for n in names]


def _digest(parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=True).encode("utf-8")).hexdigest()


def selection_parser_digest():
    """Digest of every source that decides WHICH sessions a population holds: the SELECTION_SOURCES files (bytes, keyed
    by basename) and this file's population / window rules (SELECTION_NAMES segments)."""
    parts = [["file", os.path.basename(rel), hashlib.sha256(_source_bytes(rel)).hexdigest()]
             for rel in SELECTION_SOURCES]
    parts += [["name", n, seg] for n, seg in _module_segments(_KP_REL, SELECTION_NAMES)]
    return _digest(sorted(parts, key=lambda p: (p[0], p[1])))


def metric_digests():
    """{key: digest of that key's definition}: key is `population` or a pillar letter (D..I, L)."""
    cache = {}
    return {key: _digest([[rel, n, seg] for rel, names in parts for n, seg in _module_segments(rel, names, cache)])
            for key, parts in METRIC_DEFINITIONS.items()}


def _metric_changed(cert_metric, live):
    """Pillar letters whose definition digest differs from the certificate's (the population key is its own guard)."""
    return sorted(k for k in PILLAR_KEYS if (cert_metric or {}).get(k) != live.get(k))


def _check_attribution(index_ver, live_ver, cert_ver):
    """None when the attribution version agrees across the index, the loaded substrate and the certificate, else the
    reason text."""
    vals = {"index": str(index_ver), "substrate": str(live_ver), "certificate": str(cert_ver)}
    if len(set(vals.values())) == 1:
        return None
    return "attribution version differs: " + ", ".join(f"{k} {v}" for k, v in vals.items())


class PlanRefused(Exception):
    """A guard of the challenger's access plan failed: `guard` names it, `reason` is the index's own or the guard's."""

    def __init__(self, guard, reason, guards=None):
        super().__init__(f"{guard}: {reason}")
        self.guard = guard
        self.reason = reason
        self.guards = list(guards or []) + [{"guard": guard, "ok": False, "reason": reason}]


def add_plan_args(sp):
    """The access-plan flags, shared by every kme_pillars subcommand and by kme_replay rank."""
    sp.add_argument("--plan", choices=PLANS, default="champion",
                    help="access plan (KS-4): champion = today's scan (default); scoped = project-scoped raw; "
                         "challenger = the certified index selects the sessions, only their transcripts are read "
                         "(refused with exit 3 when a guard fails); auto = challenger, deopting to scoped / global raw")
    sp.add_argument("--index-db", default=None, help="usage index read by the challenger / auto plans "
                                                     "(default: tools/usage_index.py DEFAULT_DB)")
    sp.add_argument("--cert", default=None, help="certificate the challenger / auto plans require, written by "
                                                 "`kme_pillars.py certify` (default: <index-db>" + CERT_SUFFIX + ")")
    sp.add_argument("--path-log", default=None, help="append one redacted JSON access-plan record per run")
    sp.add_argument("--cross-project", action="store_true",
                    help="the question is explicitly cross-project: allows an unfiltered challenger / auto run, "
                         "and the global raw tier under auto")


_UX_MODULE = []


def _usage_index():
    """tools/usage_index.py, loaded once by path and only for the challenger / auto plans."""
    if not _UX_MODULE:
        spec = importlib.util.spec_from_file_location("_kmep_usage_index", REPO / "tools" / "usage_index.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _UX_MODULE.append(mod)
    return _UX_MODULE[0]


def _open_index_ro(path):
    """Read-only connection to the index (mode=ro URI). Never the usage_index connect helper: that one runs the schema
    script and so writes."""
    real = os.path.realpath(str(path))
    return sqlite3.connect("file:" + urllib.parse.quote(real) + "?mode=ro", uri=True)


def _question(ctx):
    """The question a certificate answers: what a different run must repeat to reuse it."""
    until = ctx["freeze"] if ctx["auto"] else ctx["until"]
    return {"denominator": ctx["label"], "select": ctx["select"], "host": ctx["host"],
            "project_filter": ctx["pf"].pattern if ctx["pf"] else None,
            "cross_project": bool(ctx.get("cross_project")), "expand": bool(ctx["expand"]),
            "roots": sorted(os.path.realpath(r) for r in ctx["roots"]),
            "until": fmt_instant(until) if until is not None else None}


def _pairs_digest(pairs):
    return hashlib.sha256(json.dumps(sorted([list(p) for p in pairs]), ensure_ascii=True).encode("utf-8")).hexdigest()


def _sid_text(pairs, limit=3):
    ids = [f"{p}/{s}" for p, s in sorted(pairs)]
    return ", ".join(ids[:limit]) + (f", +{len(ids) - limit} more" if len(ids) > limit else "")


def _index_open(ctx, guards):
    """Open the index read-only and run the guards index_open and kind. Returns (con, db, meta)."""
    db = ctx.get("index_db") or str(_usage_index().DEFAULT_DB)
    if not os.path.isfile(db):
        raise PlanRefused("index_open", f"index_missing: {db}", guards)
    try:
        con = _open_index_ro(db)
        row = con.execute("SELECT v FROM meta WHERE k='schema_version'").fetchone()
        meta = dict(con.execute("SELECT k, v FROM meta WHERE k IN ('pattern_set', 'attr_version', 'attr_registry')"))
    except sqlite3.Error as exc:
        raise PlanRefused("index_open", f"index_unreadable: {exc.__class__.__name__}", guards)
    try:
        ver = int(row[0]) if row else 0
        if ver < INDEX_MIN_SCHEMA:
            raise PlanRefused("index_open", f"schema: {ver} < {INDEX_MIN_SCHEMA}", guards)
        guards.append({"guard": "index_open", "ok": True, "reason": f"schema {ver}"})
        if ctx["kind"] != "frozen" or ctx["den"] not in ("KME-L", "KME-G") or ctx["select"] != "kme":
            raise PlanRefused("kind", f"{ctx['den']}/{ctx['select']} has no certified index tier", guards)
        if ctx["since"] is not None:
            raise PlanRefused("kind", "--since has no certified index tier (the index answers as of an instant)", guards)
        guards.append({"guard": "kind", "ok": True, "reason": f"{ctx['den']}/kme"})
    except PlanRefused:
        con.close()
        raise
    meta["schema_version"] = ver
    return con, db, meta


def _index_population(ctx, con, guards):
    """The index's own population answer for this question, refused unless EXACT against the run's frozen fields (the
    index's reasons are quoted, never read as a zero). Returns (answer, selected pairs incl. dead sessions, files rows)."""
    until = ctx["freeze"] if ctx["auto"] else ctx["until"]
    try:
        ans = _usage_index().population(
            con, until=fmt_instant(until) if until is not None else None,
            project_filter=ctx["pf"].pattern if ctx["pf"] else None, select="kme", host=ctx["host"],
            expected=ctx["frozen"]["fields"], detail=True)
        rows = con.execute("SELECT path, size, mtime_ns, offset, archived, project, session_key, first_ts "
                           "FROM files").fetchall()
    except sqlite3.Error as exc:
        raise PlanRefused("population", f"population: UNMEASURED: index_unreadable: {exc.__class__.__name__}", guards)
    if ans["verdict"] != "EXACT":
        raise PlanRefused("population", f"population: {ans['verdict']}: {'; '.join(ans['reasons'])}"
                          if ans["reasons"] else f"population: {ans['verdict']}: deltas {sorted(ans.get('deltas') or {})}",
                          guards)
    guards.append({"guard": "population", "ok": True, "reason": "EXACT"})
    selected = {(r["project"], r["session_key"]) for r in ans["detail"] if r["selected"] and not r["archived"]}
    return ans, selected, rows


def _disk_files(dirs):
    """Every in-scope transcript the scan would register, by stat only: {realpath: (project, session, size, mtime_ns)}.
    The project and session are the ones scan_project computes (basename of the scanned dir, first path component of
    the relative path), which are what the select callable is asked about."""
    out = {}
    for d in dirs:
        proj = os.path.basename(d.rstrip("/\\"))
        for root, _dns, fns in os.walk(d):
            real_root = None
            for f in fns:
                if not f.endswith(".jsonl"):
                    continue
                full = os.path.join(root, f)
                sid = os.path.relpath(full, d).replace("\\", "/").split("/")[0].replace(".jsonl", "")
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                if real_root is None:
                    real_root = os.path.realpath(root)
                key = os.path.realpath(full) if os.path.islink(full) else os.path.join(real_root, f)
                out[key] = (proj, sid, st.st_size, st.st_mtime_ns)
    return out


def _scope_state(ctx, rows):
    """The index's files rows and the disk, both limited to the dirs this run's scan would read (T-02-13: no other
    project is listed). Returns {"disk": {path: (proj, sid, size, mtime_ns)}, "idx": {path: row dict}}. Raises
    PlanRefused("watermark", "root_not_indexed: ...") when no in-scope disk path is present in the index at all: the
    index was built over another tree than --root, so none of its decisions describe this one."""
    dirs = _scope_dirs(ctx["roots"], ctx["expand"], ctx["pf"])
    disk = _disk_files(dirs)
    real_dirs = [os.path.realpath(d) for d in dirs]
    idx = {}
    for path, size, mtime_ns, offset, archived, project, skey, first_ts in rows:
        if archived or not any(path == d or path.startswith(d + os.sep) for d in real_dirs):
            continue
        idx[path] = {"size": size, "mtime_ns": mtime_ns, "offset": offset, "project": project, "skey": skey,
                     "first_ts": first_ts}
    if not disk:
        raise PlanRefused("watermark", "root_not_indexed: no in-scope transcript exists under the roots", None)
    if not any(p in idx for p in disk):
        raise PlanRefused("watermark", f"root_not_indexed: none of the {len(disk)} in-scope transcript(s) on disk is "
                                       f"held by the index (it was built over another tree)", None)
    return {"disk": disk, "idx": idx}


def _watermark(ctx, state, cert):
    """Closure-exact staleness: the (project, session) pairs whose sources changed since the index (or the certificate)
    last saw them. A disk file is stale when its (size, mtime_ns) differs from the index row's, when the row's own
    offset is short of its size, or when the index has no row for it and the certificate's `uncovered` map does not
    vouch for its exact (size, mtime_ns); an index row with no file on disk marks its session stale too."""
    disk, idx = state["disk"], state["idx"]
    uncovered = (cert or {}).get("uncovered") or {}
    stale = set()
    for path, (proj, sid, size, mtime_ns) in disk.items():
        row = idx.get(path)
        if row is None:
            if uncovered.get(path) != [size, mtime_ns]:
                stale.add((proj, sid))
        elif (row["size"], row["mtime_ns"]) != (size, mtime_ns) or row["offset"] != row["size"]:
            stale.add((proj, sid))
    for path, row in idx.items():
        if path not in disk:
            stale.add((row["project"], row["skey"]))
    return stale


def _no_first_ts_sessions(until, state):
    """IN-04 (review 01-REVIEW): with `until` set, the index's population drops a session none of whose files carries a
    first timestamp, without a reason. Those sessions are named here so they are read raw instead."""
    if until is None:
        return set()
    firsts = {}
    for row in state["idx"].values():
        firsts.setdefault((row["project"], row["skey"]), []).append(row["first_ts"])
    return {k for k, v in firsts.items() if all(x is None for x in v)}


def _load_cert(ctx, guards):
    path = ctx.get("cert")
    if not path or not os.path.isfile(path):
        raise PlanRefused("certificate", f"cert_missing: {path}", guards)
    try:
        cert = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PlanRefused("certificate", f"cert_unreadable: {exc.__class__.__name__}: {path}", guards)
    if not isinstance(cert, dict) or cert.get("schema") != CERT_SCHEMA:
        raise PlanRefused("certificate", f"cert_schema: {cert.get('schema') if isinstance(cert, dict) else None!r} "
                                         f"!= {CERT_SCHEMA!r}", guards)
    try:
        for k in ("question", "index", "keys", "uncovered"):
            if not isinstance(cert[k], dict):
                raise KeyError(k)
        cert["keys"]["metric"]["population"]
        cert["keys"]["parser"]
        cert["index"]["pattern_set"]
        cert["index"]["attr_version"]
    except (KeyError, TypeError) as exc:
        raise PlanRefused("certificate", f"cert_malformed: missing {exc}", guards)
    return cert


def _check_certificate(ctx, cert, meta, guards):
    """The certificate guards, in order: question, pattern set, attribution version, parser digest, population metric.
    Sets ctx["keys"] (the live digests) and ctx["metric_changed"] (the pillars whose definition moved) before any key
    guard can refuse, so a refusal still records them."""
    q = _question(ctx)
    for field in q:
        if cert["question"].get(field) != q[field]:
            raise PlanRefused("certificate", f"question.{field}: certificate {cert['question'].get(field)!r} != run "
                                             f"{q[field]!r}", guards)
    guards.append({"guard": "certificate", "ok": True, "reason": "question equal"})
    try:
        live_pattern = _usage_index()._live_pattern_set()
    except Exception as exc:  # noqa: BLE001 -- typed, never silent
        raise PlanRefused("pattern", f"classifier unavailable: {exc.__class__.__name__}: {exc}", guards)
    if cert["index"]["pattern_set"] != live_pattern:
        raise PlanRefused("pattern", f"pattern set differs: certificate {str(cert['index']['pattern_set'])[:12]} != "
                                     f"champion's current {live_pattern[:12]}", guards)
    guards.append({"guard": "pattern", "ok": True, "reason": live_pattern[:12]})
    bad = _check_attribution(meta.get("attr_version"), _usage_index().ATTR_VERSION, cert["index"]["attr_version"])
    if bad:
        raise PlanRefused("attribution", bad, guards)
    guards.append({"guard": "attribution", "ok": True, "reason": f"version {cert['index']['attr_version']}"})
    try:
        live_parser, live_metric = selection_parser_digest(), metric_digests()
    except (OSError, SyntaxError, ValueError) as exc:
        raise PlanRefused("parser", f"keys unreadable: {exc.__class__.__name__}: {exc}", guards)
    ctx["keys"] = {"parser": live_parser, "metric": live_metric}
    cert_metric = cert["keys"]["metric"]
    ctx["metric_changed"] = _metric_changed(cert_metric, live_metric)
    if cert["keys"]["parser"] != live_parser:
        raise PlanRefused("parser", f"selection parser digest differs: certificate {str(cert['keys']['parser'])[:12]} "
                                    f"!= live {live_parser[:12]}", guards)
    guards.append({"guard": "parser", "ok": True, "reason": live_parser[:12]})
    if cert_metric.get("population") != live_metric["population"]:
        raise PlanRefused("metric", f"population definition differs: certificate {str(cert_metric.get('population'))[:12]} "
                                    f"!= live {live_metric['population'][:12]}; pillar definitions changed: "
                                    f"{ctx['metric_changed']}", guards)
    guards.append({"guard": "metric", "ok": True,
                   "reason": f"population {live_metric['population'][:12]}; pillars changed: {ctx['metric_changed']}"})


def _make_select(read_set, admitted):
    """The select callable of the index tier: a file is opened only when its session is in the read set."""
    def select(proj, sid, path):
        if (proj, sid) not in read_set:
            return False
        try:
            admitted[path] = os.stat(path).st_size
        except OSError:
            admitted[path] = None
        return True
    return select


def _index_tier(ctx):
    """The certified-index tier: the set of (project, session) to read for this run, as an access dict
    {"tier": "index", "select": callable, "read_set": set, "guards": [...], "admitted": {path: bytes}, ...}.
    Guards in order: index_open, kind, certificate (+ pattern, attribution, parser, metric), population, watermark,
    no_first_ts. Raises PlanRefused(guard, reason) on the first failed guard; an UNMEASURED / DRIFTED index answer is
    refused with the index's own reasons, never read as a zero."""
    guards = []
    con, db, meta = _index_open(ctx, guards)
    try:
        cert = _load_cert(ctx, guards)
        _check_certificate(ctx, cert, meta, guards)
        _ans, index_selected, rows = _index_population(ctx, con, guards)
    finally:
        con.close()
    try:
        state = _scope_state(ctx, rows)
    except PlanRefused as exc:
        raise PlanRefused(exc.guard, exc.reason, guards)
    stale = _watermark(ctx, state, cert)
    guards.append({"guard": "watermark", "ok": True,
                   "reason": f"{len(stale)} stale session(s)" + (f": {_sid_text(stale)}" if stale else "")})
    until = ctx["freeze"] if ctx["auto"] else ctx["until"]
    no_first = _no_first_ts_sessions(until, state)
    guards.append({"guard": "no_first_ts", "ok": True,
                   "reason": f"{len(no_first)} session(s) without a first timestamp read raw (review IN-04)"
                             + (f": {_sid_text(no_first)}" if no_first else "")})
    read_set = index_selected | stale | no_first
    admitted = {}
    return {"tier": "index", "select": _make_select(read_set, admitted), "read_set": read_set, "guards": guards,
            "admitted": admitted, "index_db": db, "index_selected": index_selected, "stale": stale,
            "no_first_ts": no_first}


def _selected_pairs(sc):
    """(project, session) of every session the champion's rule selects in a scan, dead sessions included: the same
    decision kme_pillars.population makes, as a set of identities instead of counts."""
    out = set()
    for s in sc["sessions"]:
        if sc["window"] and sc["kept"].get(id(s), 0) == 0:
            continue
        if kme_report.is_kme(s):
            out.add((s["project"], s["session"]))
    return out


def _selection_agreement(champion, index):
    """(agree, only the champion selects, only the index selects)."""
    only_c, only_i = sorted(champion - index), sorted(index - champion)
    return (not only_c and not only_i), only_c, only_i


def _shadow_check(ctx, sc, access):
    """The post-scan shadow guard: the in-process population must be exact against the frozen fields, and the champion's
    classifier must select every index-selected session whose sources are unchanged (and nothing the index did not
    select). Raises PlanRefused("shadow", ...): an auto run deopts, a challenger run is refused."""
    match, deltas = compare_population(sc["measured"], ctx["frozen"]["fields"])
    if match != "exact":
        raise PlanRefused("shadow", f"in-process population is {match} against the frozen fields (differing: "
                                    f"{sorted(deltas)})", access["guards"])
    proc = _selected_pairs(sc)
    skip = access["stale"] | access["no_first_ts"]
    agree, only_c, only_i = _selection_agreement(proc - skip, access["index_selected"] - skip)
    if not agree:
        raise PlanRefused("shadow", f"selection differs from the index: {len(only_i)} index-selected session(s) not "
                                    f"selected by the champion classifier ({_sid_text(only_i)}), {len(only_c)} "
                                    f"champion-selected session(s) the index did not select ({_sid_text(only_c)})",
                          access["guards"])


# --------------------------------------------------------------------------- certify
def _atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def _certify(a, argv):
    """`certify`: write a certificate only when the index population is EXACT against the frozen denominator AND a
    champion scan of the same scope selects exactly the same sessions as the index. Exit 0 CERTIFIED, 1 NOT_CERTIFIED
    (disagreement, nothing written), 3 UNMEASURED (an index guard failed, nothing written), 2 usage."""
    try:
        redact = _load_redact()
    except Exception as exc:  # noqa: BLE001 -- no redaction available means nothing is written
        return _fail(f"secret_firewall unavailable ({exc.__class__.__name__}); nothing written")
    a.plan, a.path_log = "challenger", None
    ctx, rc = _prepare(a, [])
    if ctx is None:
        return rc
    cert_real = os.path.realpath(a.cert)
    for r in a.root:
        root_real = os.path.realpath(r)
        if cert_real == root_real or os.path.commonpath([cert_real, root_real]) == root_real:
            return _fail(f"--cert {a.cert} resolves inside --root {r}: the instrument never writes into a scanned "
                         f"corpus; nothing written")

    def verdict(v, selected=0, uncovered=0, path="none"):
        print(f"KMEP-CERT verdict={v} selected={selected} uncovered={uncovered} cert={path}")

    guards = []
    try:
        con, db, meta = _index_open(ctx, guards)
        try:
            ans, idx_pairs, rows = _index_population(ctx, con, guards)
        finally:
            con.close()
        state = _scope_state(ctx, rows)
    except PlanRefused as exc:
        print(f"kme_pillars: certify refused: {exc.guard}: {exc.reason}", file=sys.stderr)
        verdict("UNMEASURED")
        return EXIT_UNMEASURED
    until = ctx["freeze"] if ctx["auto"] else ctx["until"]
    ctx["access"] = None
    sc = _measure(ctx, [], until)
    match, deltas = compare_population(sc["measured"], ctx["frozen"]["fields"])
    if match != "exact":
        print(f"kme_pillars: champion population is {match} against the frozen fields (differing: {sorted(deltas)}) "
              f"while the index is EXACT: not certified", file=sys.stderr)
        verdict("NOT_CERTIFIED", len(idx_pairs))
        return EXIT_DISAGREE
    champ_pairs = _selected_pairs(sc)
    agree, only_c, only_i = _selection_agreement(champ_pairs, idx_pairs)
    if not agree:
        print(f"kme_pillars: selection differs: champion {len(champ_pairs)} vs index {len(idx_pairs)}; only the "
              f"champion selects {len(only_c)} (first {[f'{p}/{s}' for p, s in only_c[:5]]}), only the index selects "
              f"{len(only_i)} (first {[f'{p}/{s}' for p, s in only_i[:5]]})", file=sys.stderr)
        verdict("NOT_CERTIFIED", len(idx_pairs))
        return EXIT_DISAGREE
    uncovered = {p: [size, mt] for p, (_proj, _sid, size, mt) in state["disk"].items() if p not in state["idx"]}
    cert = {"schema": CERT_SCHEMA, "question": _question(ctx),
            "index": {"path": os.path.realpath(db), "schema_version": meta["schema_version"],
                      "pattern_set": meta.get("pattern_set"), "attr_version": meta.get("attr_version"),
                      "attr_registry": meta.get("attr_registry")},
            "keys": {"parser": selection_parser_digest(), "metric": metric_digests()},
            "selected": {"sessions": len(idx_pairs), "digest": _pairs_digest(idx_pairs)},
            "uncovered": uncovered,
            "shadow": {"champion_selected": len(champ_pairs), "index_selected": len(idx_pairs), "agree": True},
            "certified_at": _utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "plane": plane_name(),
            "command": command_string(argv)}
    _atomic_write(a.cert, redact(json.dumps(cert, indent=1, sort_keys=True, ensure_ascii=True)) + "\n")
    verdict("CERTIFIED", len(idx_pairs), len(uncovered), a.cert)
    return EXIT_OK


PATH_SCHEMA = 2     # 2: adds `keys`, `metric_changed` and read_set.stale / read_set.no_first_ts


def _walk_read_set(dirs):
    """(files, bytes) of every transcript under the scanned dirs: what a raw tier plans to read."""
    files = nbytes = 0
    for d in dirs:
        for root, _dns, fns in os.walk(d):
            for f in fns:
                if f.endswith(".jsonl"):
                    files += 1
                    try:
                        nbytes += os.stat(os.path.join(root, f)).st_size
                    except OSError:
                        pass
    return files, nbytes


def _path_record(ctx, tool, subcommand, sc, refusal):
    """The access-plan record of one run: counts, flag values, digests and guard reasons only (reasons name session
    ids and in-scope relative paths, never line content)."""
    access = ctx.get("access")
    if refusal is not None:
        taken, guards, deopt = "refused", refusal.guards, {"guard": refusal.guard, "reason": refusal.reason}
        read_set = {"basis": "planned", "sessions": 0, "files": 0, "bytes": 0, "stale": None, "no_first_ts": None}
    else:
        taken = ctx.get("tier", ctx.get("plan", "champion"))
        d = ctx.get("deopt")
        deopt = {"guard": d["guard"], "reason": d["reason"]} if d else None
        guards = (access or {}).get("guards") or (d["guards"] if d else [])
        if access:
            adm = access["admitted"]
            read_set = {"basis": "planned", "sessions": len(access["read_set"]), "files": len(adm),
                        "bytes": sum(v for v in adm.values() if v),
                        "stale": sorted(f"{p}/{s}" for p, s in access["stale"]),
                        "no_first_ts": sorted(f"{p}/{s}" for p, s in access["no_first_ts"])}
        elif ctx.get("path_log") and sc is not None:
            files, nbytes = _walk_read_set(sc["dirs"])
            read_set = {"basis": "planned", "sessions": len(sc["sessions"]), "files": files, "bytes": nbytes,
                        "stale": None, "no_first_ts": None}
        else:
            read_set = {"basis": "unwalked", "sessions": None, "files": None, "bytes": None, "stale": None,
                        "no_first_ts": None}
    until = ctx["freeze"] if ctx["auto"] else ctx["until"]
    return {"schema": PATH_SCHEMA, "tool": tool, "subcommand": subcommand, "plan_requested": ctx.get("plan"),
            "plan_taken": taken, "guards": guards, "deopt": deopt, "read_set": read_set,
            "sessions_registered": len(sc["sessions"]) if sc is not None else None,
            "index_db": ctx.get("index_db"), "denominator": ctx["label"],
            "project_filter": ctx["pf"].pattern if ctx["pf"] else None,
            "until": fmt_instant(until) if until is not None else None,
            "cross_project": ctx.get("cross_project", False), "keys": ctx.get("keys"),
            "metric_changed": ctx.get("metric_changed"), "plane": plane_name()}


def report_path(ctx, redact, tool, subcommand, sc, refusal=None):
    """One KMEP-PATH stderr line for every non-champion run (and any run with --path-log), and one redacted JSON line
    appended to --path-log (HR-SECRET-002: the record passes the same redaction as the measurement file)."""
    rec = _path_record(ctx, tool, subcommand, sc, refusal)
    if ctx.get("plan") != "champion" or ctx.get("path_log"):
        files = rec["read_set"]["files"]
        print(f"KMEP-PATH plan={rec['plan_requested']} taken={rec['plan_taken']} "
              f"deopt={rec['deopt']['guard'] if rec['deopt'] else 'none'} "
              f"read_files={files if files is not None else 'unwalked'}", file=sys.stderr)
    if ctx.get("path_log"):
        line = redact(json.dumps(rec, sort_keys=True, ensure_ascii=True))
        try:
            lp = Path(ctx["path_log"])
            lp.parent.mkdir(parents=True, exist_ok=True)
            with open(lp, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            print(f"{tool}: path log not written ({exc.__class__.__name__})", file=sys.stderr)


def resolve_logged(ctx, pillars, redact, tool, subcommand, observer_factories=None):
    """_resolve plus the access-plan report. A PlanRefused is reported (stderr + path log) and re-raised: the caller
    returns EXIT_UNMEASURED and writes nothing."""
    try:
        out = _resolve(ctx, pillars, observer_factories)
    except PlanRefused as exc:
        print(f"{tool}: plan {ctx['plan']} refused: {exc.guard}: {exc.reason}", file=sys.stderr)
        report_path(ctx, redact, tool, subcommand, None, exc)
        raise
    report_path(ctx, redact, tool, subcommand, out[0])
    return out


# --------------------------------------------------------------------------- CLI
def build_parser():
    ap = argparse.ArgumentParser(prog="kme_pillars.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="PILLAR")

    def common(sp, measuring, plan_args=True):
        sp.add_argument("--denominator", required=True, choices=["KME-L", "KME-G", DW7_NAME, "OTHER"])
        sp.add_argument("--label", default=None, help="name of the OTHER workload (A-Z 0-9 -)")
        sp.add_argument("--select", choices=["kme", "all"], default=None)
        sp.add_argument("--host", default=None)
        sp.add_argument("--root", action="append", required=True)
        sp.add_argument("--expand", action="store_true")
        sp.add_argument("--project-filter", default=None, help="regex (re.search) on each child dir name under "
                                                               "--expand, or on the basename of a plain root")
        sp.add_argument("--since", default=None, help="ISO instant: lines before it are dropped")
        sp.add_argument("--until", default=None, help="ISO instant, 'none', or 'auto' (locate the freeze-time cutoff; "
                                                      "frozen KME denominators only)")
        sp.add_argument("--freeze-instant", default=None, help="the instant --until auto starts from "
                                                               f"(default {FREEZE_INSTANT})")
        sp.add_argument("--frozen-file", default=None)
        sp.add_argument("--frozen-ce-ledger", default=None, help="CE ledger read for the referenced CPP-D-W7 denominator")
        if plan_args:
            add_plan_args(sp)
        if measuring:
            sp.add_argument("--out-dir", default=None)
            sp.add_argument("--role", choices=["auto", "second_workload"], default="auto")
            sp.add_argument("--json", action="store_true")
    for p, helptext in PILLAR_HELP.items():
        common(sub.add_parser(p.lower(), help=helptext), True)
    common(sub.add_parser("all", help="every pillar in ONE scan, one measurement file per pillar"), True)
    cp = sub.add_parser("certify", help="certify the index selection of one question: writes the certificate the "
                                        "challenger / auto plans require, only when the index population is EXACT "
                                        "and a champion scan of the same scope selects the same sessions")
    common(cp, False, plan_args=False)
    cp.add_argument("--index-db", default=None, help="usage index to certify (default: tools/usage_index.py DEFAULT_DB)")
    cp.add_argument("--cert", required=True, help="where the certificate is written (never inside a --root)")
    cp.add_argument("--cross-project", action="store_true",
                    help="the certified question is explicitly cross-project (no --project-filter)")
    common(sub.add_parser("population", help="print the recomputed population (and per-project rows of the "
                                              "selected sessions) and whether it reproduces the frozen one; "
                                              "writes nothing"), False)
    return ap


def _fail(msg):
    print(f"kme_pillars: {msg}", file=sys.stderr)
    return EXIT_USAGE


def _prepare(a, pillars):
    """Validate the flags and build the run context. Returns (ctx, None) or (None, exit code)."""
    den = a.denominator
    kme_kind = den in ("KME-L", "KME-G")
    dw7 = den == DW7_NAME
    if den == "OTHER":
        if not a.label or not LABEL_RE.match(a.label):
            return None, _fail("--denominator OTHER needs --label matching ^[A-Z0-9][A-Z0-9-]{1,40}$")
        if a.label in FROZEN_NAMES:
            return None, _fail(f"--label {a.label} is a frozen denominator name; a named workload may not take it")
        label = a.label
    else:
        if a.label:
            return None, _fail("--label is only valid with --denominator OTHER")
        label = den
    if kme_kind and a.select == "all":
        return None, _fail("--select all is not the frozen selection rule of a frozen denominator")
    role = getattr(a, "role", "auto")
    if role == "second_workload":
        clash = [p for p in pillars if label in RULE_DENOMINATORS[p]]
        if clash:
            return None, _fail(f"{label} is in pillar {clash[0]}'s own frozen rule {RULE_DENOMINATORS[clash[0]]}; "
                               f"it cannot be its second workload")
    if dw7:
        if a.select is not None:
            return None, _fail(f"--select is fixed to all for {DW7_NAME}")
        if a.since is not None or a.until is not None or a.freeze_instant is not None:
            return None, _fail(f"the window of {DW7_NAME} is the frozen one: --since / --until / --freeze-instant "
                               f"are not accepted")
    auto = a.until is not None and a.until.lower() == "auto"
    if auto and not kme_kind:
        return None, _fail("--until auto locates a frozen population's cutoff: only --denominator KME-L / KME-G")
    if auto and a.since is not None:
        return None, _fail("--since cannot be combined with --until auto")
    if a.freeze_instant is not None and not auto:
        return None, _fail("--freeze-instant is only meaningful with --until auto")
    freeze = parse_instant(a.freeze_instant) if a.freeze_instant is not None else parse_instant(FREEZE_INSTANT)
    if freeze is None:
        return None, _fail(f"--freeze-instant {a.freeze_instant!r} is not an ISO instant")
    since = None
    if a.since is not None:
        since = parse_instant(a.since)
        if since is None:
            return None, _fail(f"--since {a.since!r} is not an ISO instant")
    until = None
    if auto:
        until = freeze
    elif a.until is None:
        until = parse_instant(FREEZE_INSTANT) if kme_kind else None
    elif a.until.lower() != "none":
        until = parse_instant(a.until)
        if until is None:
            return None, _fail(f"--until {a.until!r} is not an ISO instant")
    for r in a.root:
        if not os.path.isdir(r):
            return None, _fail(f"--root {r} is not a directory")
    if pillars:     # a measuring run writes a file: never into a scanned corpus (a5 / a7 / b001 are read-only trees)
        out_real = os.path.realpath(a.out_dir if getattr(a, "out_dir", None) else str(REPO / MEASUREMENTS_REL))
        for r in a.root:
            root_real = os.path.realpath(r)
            if out_real == root_real or os.path.commonpath([out_real, root_real]) == root_real:
                return None, _fail(f"--out-dir {a.out_dir or MEASUREMENTS_REL} resolves inside --root {r}: the "
                                   f"instrument never writes into a scanned corpus; nothing written")
    pf = None
    if a.project_filter is not None:
        try:
            pf = re.compile(a.project_filter)
        except re.error as exc:
            return None, _fail(f"--project-filter {a.project_filter!r} is not a regex ({exc})")

    kind, frozen, select = "named_workload", None, a.select or "kme"
    fsrc = None
    if kme_kind or dw7:
        # WR-07: record which frozen source the run read; a source other than the committed default (a flag pointing
        # elsewhere) can never make a terminal file
        denoms_default, ce_default = REPO / DENOMS_REL, REPO / CE_LEDGER_REL
        entries = {}
        if kme_kind or a.frozen_file:
            entries["frozen_file"] = frozen_source_entry(a.frozen_file or denoms_default, denoms_default)
        if dw7 or a.frozen_ce_ledger:
            entries["ce_ledger"] = frozen_source_entry(a.frozen_ce_ledger or ce_default, ce_default)
        fsrc = dict(entries, all_default=all(e["default"] for e in entries.values()))
    if kme_kind:
        fpath = a.frozen_file or str(REPO / DENOMS_REL)
        try:
            specs = frozen_specs(fpath, a.frozen_ce_ledger)
        except (OSError, ValueError, KeyError) as exc:
            return None, _fail(f"frozen file {fpath} unreadable ({exc.__class__.__name__})")
        if den not in specs:
            return None, _fail(f"frozen file {fpath} has no {den} entry")
        kind, frozen, select = "frozen", specs[den], specs[den]["select"]
    elif dw7:
        frozen = dw7_spec(a.frozen_ce_ledger or str(REPO / CE_LEDGER_REL))
        if "error" in frozen:
            return None, _fail(frozen["error"])
        kind, select = "referenced", "all"
        since, until = parse_instant(frozen["since"]), parse_instant(frozen["until"])
    host = a.host or (frozen["host"] if frozen else "local")
    plan = getattr(a, "plan", "champion")
    cross = bool(getattr(a, "cross_project", False))
    index_db = getattr(a, "index_db", None)
    cert = getattr(a, "cert", None)
    path_log = getattr(a, "path_log", None)
    if plan == "scoped" and pf is None:
        return None, _fail("--plan scoped needs --project-filter (a scoped read has a scope)")
    if plan in ("challenger", "auto"):
        if pf is None and not cross:
            return None, _fail(f"--plan {plan} needs --project-filter, or --cross-project to ask a global question "
                               f"(--cross-project is the only way to read outside one scope)")
        index_db = index_db or str(_usage_index().DEFAULT_DB)
        cert = cert or (index_db + CERT_SUFFIX)
    else:
        if cross:
            return None, _fail(f"--cross-project is only valid with --plan challenger or auto, not {plan}")
        if index_db is not None:
            return None, _fail(f"--index-db is only valid with --plan challenger or auto, not {plan}")
        if cert is not None:
            return None, _fail(f"--cert is only valid with --plan challenger or auto, not {plan}")
    if path_log is not None:      # the path log is a write: never into a scanned corpus either
        log_real = os.path.realpath(path_log)
        for r in a.root:
            root_real = os.path.realpath(r)
            if log_real == root_real or os.path.commonpath([log_real, root_real]) == root_real:
                return None, _fail(f"--path-log {path_log} resolves inside --root {r}: the instrument never writes "
                                   f"into a scanned corpus; nothing written")
    return {"plan": plan, "index_db": index_db, "cert": cert, "path_log": path_log, "cross_project": cross, "label": label, "den": den, "kind": kind, "frozen": frozen, "select": select, "host": host,
            "since": since, "until": until, "auto": auto, "freeze": freeze, "roots": a.root, "expand": a.expand,
            "pf": pf, "role": role, "pillars": list(pillars), "frozen_source": fsrc}, None


def _measure(ctx, pillars, until, want_instants=False, observer_factories=None):
    """ONE scan with the named pillar observers (plus the call-instant observer on request) truncated at `until`."""
    obs = {p: (OBSERVERS if observer_factories is None else observer_factories)[p]() for p in pillars}
    inst = InstantObserver(ctx["freeze"] - datetime.timedelta(hours=LOCATE_WINDOW_H)) if want_instants else None
    keep = make_keep(ctx["since"], until) if (ctx["since"] is not None or until is not None) else None
    sessions, fan, dirs = scan(ctx["roots"], ctx["expand"], ctx["host"], list(obs.values()) + ([inst] if inst else []),
                               keep, ctx["pf"], (ctx.get("access") or {}).get("select"))
    pop = population(sessions, {"select": ctx["select"]}, fan.kept, keep is not None)
    selected = pop.pop("selected")
    measured = {f: pop[f] for f in POP_FIELDS}
    measured["weighted"] = pop["weighted"]
    return {"sessions": sessions, "dirs": dirs, "pop": pop, "selected": selected, "measured": measured, "obs": obs,
            "instants": inst.for_selected(selected) if inst else None, "until": until,
            "kept": fan.kept, "window": keep is not None}


def _resolve(ctx, pillars, observer_factories=None):
    """The measuring scan for the run, through the access plan. champion / scoped: today's scan, no index call.
    challenger: the index tier (PlanRefused propagates, nothing is read). auto: the index tier, deopting on a
    PlanRefused to scoped raw (a filter was given) or global raw (--cross-project), the deopt kept in ctx["deopt"].
    Returns (scan, until, located) where located is None or the locator's verdict."""
    plan = ctx.get("plan", "champion")
    ctx["access"], ctx["deopt"], ctx["tier"] = None, None, plan
    ctx["keys"] = ctx["metric_changed"] = None
    if plan in ("challenger", "auto"):
        try:
            ctx["access"] = _index_tier(ctx)
            ctx["tier"] = "index"
            return _resolve_scan(ctx, pillars, observer_factories)
        except PlanRefused as exc:
            if plan == "challenger":
                raise
            ctx["access"] = None
            ctx["deopt"] = {"guard": exc.guard, "reason": exc.reason, "guards": exc.guards}
            ctx["tier"] = "scoped" if ctx["pf"] is not None else "global"
    return _resolve_scan(ctx, pillars, observer_factories)


def _resolve_scan(ctx, pillars, observer_factories=None):
    """The scan of the chosen tier: at the fixed cutoff, or at the located one for --until auto. On the index tier the
    shadow guard runs right after the measuring scan (for --until auto: after the freeze-instant scan, before any
    probe), so the locator can never bisect on a scan the index and the champion disagree about."""
    access = ctx.get("access") or {}
    index = access.get("tier") == "index"
    if not ctx["auto"]:
        sc = _measure(ctx, pillars, ctx["until"], observer_factories=observer_factories)
        if index:
            _shadow_check(ctx, sc, access)
        return sc, ctx["until"], None
    frozen = ctx["frozen"]["fields"]
    first = _measure(ctx, pillars, ctx["freeze"], want_instants=True, observer_factories=observer_factories)
    if index:
        _shadow_check(ctx, first, access)

    def probe(until, want):
        sc = _measure(ctx, [], until, want)
        return sc["measured"], sc["instants"]
    loc = locate_cutoff(probe, frozen, ctx["freeze"], first=(first["measured"], first["instants"]),
                        max_scans=LOCATE_MAX_SCANS - 1)
    if loc["method"] == "exact_at_freeze":
        return first, ctx["freeze"], loc
    if loc["method"] == "bisect":
        final = _measure(ctx, pillars, loc["until"], observer_factories=observer_factories)
        loc["scans"] += 1
        if compare_population(final["measured"], frozen)[0] == "exact":
            return final, loc["until"], loc
        loc.update(method="not_found", until=None, why="the corpus changed between the probe and the final scan: "
                                                       "the located cutoff no longer reproduces the population")
    return first, ctx["freeze"], loc


def _located_block(loc, until):
    if loc is None:
        return None
    return {"method": loc["method"], "scans": loc["scans"], "why": loc["why"],
            "located": fmt_instant(loc["until"]) if loc["until"] is not None else None,
            "freeze_instant": fmt_instant(until) if loc["method"] == "not_found" and until else None}


def _match(ctx, sc, loc):
    """(population_match, deltas, frozen_population, coverage) of a scan against the context's denominator."""
    measured, frozen = sc["measured"], ctx["frozen"]
    if ctx["kind"] == "frozen":
        match, deltas = compare_population(measured, frozen["fields"])
        if loc is not None and loc["method"] == "not_found":
            match = "drifted"
        return match, deltas, dict(frozen["fields"], weighted=frozen["weighted"]), None
    if ctx["kind"] == "referenced":
        f = frozen["fields"]
        deltas = {k: [measured.get(k), f[k]] for k in DW7_FIELDS if measured.get(k) != f[k]}
        return "referenced", deltas, dict(f, weighted=frozen["weighted"]), referenced_coverage(measured["calls"], f["calls"])
    return "not_frozen", {}, None, None


def _result(ctx, sc, pillar, loc, until, argv):
    label, kind = ctx["label"], ctx["kind"]
    match, deltas, frozen_pop, coverage = _match(ctx, sc, loc)
    pres = sc["obs"][pillar].result(sc["selected"], sc["sessions"], sc["pop"])
    measured = sc["measured"]
    wlo, whi = pres["numerator"]["weighted_interval"]
    w = measured["weighted"]
    share_meas = [wlo / w, whi / w] if w > 0 else None
    pobs = pres["observability"]
    # A referenced denominator (CPP-D-W7) is judged against the CE ledger's frozen figures. Coverage < 1: the measured
    # numerator is a subset, so numerator / frozen weighted is a conservative LOWER bound (dividing by the measured
    # weighted would overstate it), and the verdict is UNMEASURED unless that lower bound alone clears 3 %. Coverage
    # exactly 1 with all five usage fields equal: reproduced. Anything else at coverage >= 1 (more calls than the frozen
    # window, or the same count with different usage) is a different population: its numerator cannot be divided by the
    # frozen denominator, so the judged share is withheld (UNMEASURED); share_measured_population still reports the
    # share over the measured denominator.
    ref_ok = kind == "referenced" and coverage == 1.0 and not deltas
    ref_over = kind == "referenced" and coverage >= 1.0 and not ref_ok
    if kind == "referenced":
        wf = ctx["frozen"]["weighted"]
        share = None if ref_over else ([wlo / wf, whi / wf] if wf > 0 else None)
        obs = None if pobs is None else pobs * min(1.0, coverage)
    else:
        share = share_meas if match in ("exact", "not_frozen") else None
        obs = pobs
    verdict, reason = materiality(share, "drifted" if ref_over else match, obs)
    if ref_over:
        reason = f"referenced_population_not_reproduced (coverage {coverage:.4f}, fields differing: {sorted(deltas)})"
    if loc is not None and loc["method"] == "not_found":
        reason = "cutoff_not_found"
    in_rule = label in RULE_DENOMINATORS[pillar]
    role = "second_workload" if ctx["role"] == "second_workload" else ("primary" if in_rule else "smoke")
    full = match == "exact" or (match == "referenced" and ref_ok)
    fsrc = ctx.get("frozen_source")
    src_default = fsrc is None or fsrc["all_default"]
    terminal = role == "primary" and full and verdict != "UNMEASURED" and src_default
    # a second workload is VALID (usable as a measurement beside a primary) only when its population is reproduced (or
    # the workload is not frozen) AND the reading is measured: an UNMEASURED run is not a second workload at all.
    # Whether it CONFIRMS is a separate, narrower question: frozen rule E says "confirmed on a second workload", and
    # only a lower bound at or above 3 % confirms; "< 3 %" is a valid measurement that disconfirms, STRADDLES
    # is valid but undecided (second_workload_confirms stays false for both).
    sw_valid = ((full or match == "not_frozen") and verdict != "UNMEASURED") if role == "second_workload" else None
    sw_confirms = (sw_valid and verdict == ">= 3 %") if role == "second_workload" else None
    rule = list(RULE_DENOMINATORS[pillar])
    ref_note = f" (referenced from the CE ledger, coverage {coverage:.4f})" if kind == "referenced" else ""
    if role == "primary":
        if terminal:
            t_reason = (f"primary file: {label} is in pillar {pillar}'s frozen rule {rule} and its population "
                        f"reproduced the frozen denominator{ref_note}")
        else:
            t_reason = (f"primary file but not terminal: population_match={match}, materiality={verdict}{ref_note}"
                        f"{'' if src_default else ', frozen source is not the repo default'} "
                        f"(a terminal needs an exact or fully covered population, a measured verdict and the "
                        f"committed frozen source)")
    elif role == "second_workload":
        t_reason = (f"second_workload file: a measurement beside a primary file on {rule} (valid={sw_valid}, "
                    f"confirms={sw_confirms}, materiality={verdict}); never terminal itself{ref_note}")
    else:
        t_reason = (f"smoke: {label} is outside pillar {pillar}'s frozen rule {rule} (the rule names KME-L and "
                    f"CPP-D-W7); evidence about the instrument, not a pillar terminal")
    caveats = list(CAVEATS_BY_PILLAR.get(pillar, CAVEATS))
    if kind == "referenced":
        caveats.append("CPP-D-W7 is a REFERENCED denominator read from the CE ledger and never re-measured: its calls "
                       "were deduplicated across files keeping the last copy (tools/usage_index.py) while this "
                       "instrument deduplicates per file and max-merges, so coverage >= 1 does not prove the same "
                       "call set, so a terminal needs coverage exactly 1 AND all five usage fields equal; coverage > 1 or "
                       "differing fields withhold the share (UNMEASURED); coverage < 1 makes the upper bound unknown "
                       "(UNMEASURED unless the lower bound, over the frozen denominator, alone clears 3 %)")
    if loc is not None:
        caveats.append(f"the cutoff was located by --until auto ({loc['method']}, {loc['scans']} scans): "
                       f"{loc['why']}")
    res = {
        "instrument": INSTRUMENT, "pillar": pillar, "denominator": label,
        "denominator_kind": kind, "rule_denominators": rule,
        "evidence_role": role, "terminal_evidence": terminal, "terminal_evidence_reason": t_reason,
        "second_workload_valid": sw_valid, "second_workload_confirms": sw_confirms, "plane": plane_name(),
        "measured_at": _utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": fmt_instant(until) if until is not None else None,
        "command": command_string(argv), "population_match": match,
        "numerator": pres["numerator"],
        "share_interval": share, "share_measured_population": share_meas, "threshold": THRESHOLD,
        "materiality": verdict, "materiality_reason": reason, "observability": obs,
        "second_workload_required": verdict in (">= 3 %", "STRADDLES"),
        "estimate_model": ESTIMATE_MODELS.get(pillar, ESTIMATE_MODEL),
        "host": ctx["host"], "select": ctx["select"],
        "population": measured, "frozen_population": frozen_pop, "population_deltas": deltas,
        "details": pres["details"], "caveats": caveats,
        "corpus": {"roots": len(ctx["roots"]), "project_dirs": len(sc["dirs"]), "sessions_scanned": len(sc["sessions"]),
                   "sessions_selected_active": len(sc["selected"]),
                   "project_filter": ctx["pf"].pattern if ctx["pf"] else None},
        "since": fmt_instant(ctx["since"]) if ctx["since"] is not None else None,
        "until_located": _located_block(loc, until),
        "coverage": coverage,
        "frozen_source": fsrc,
    }
    return res


def _population_report(ctx, sc, loc, until):
    match, deltas, frozen_pop, coverage = _match(ctx, sc, loc)
    rows = sorted(({k: v for k, v in r.items()} for r in sc["pop"]["projects"].values()),
                  key=lambda r: (-r["calls"], r["project"]))
    rep = {"denominator": ctx["label"], "denominator_kind": ctx["kind"], "select": ctx["select"],
           "until": fmt_instant(until) if until is not None else None,
           "since": fmt_instant(ctx["since"]) if ctx["since"] is not None else None,
           "until_located": _located_block(loc, until), "population": sc["measured"], "frozen": frozen_pop,
           "population_match": match, "deltas": deltas, "coverage": coverage, "per_project": rows,
           "corpus": {"roots": len(ctx["roots"]), "project_dirs": len(sc["dirs"]),
                      "sessions_scanned": len(sc["sessions"]), "project_filter": ctx["pf"].pattern if ctx["pf"] else None}}
    ok = match in ("exact", "not_frozen") or (match == "referenced" and coverage == 1.0 and not deltas)
    return rep, ok


def main(argv=None):
    ap = build_parser()
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else list(argv))
    except SystemExit as e:
        return int(e.code or 0)
    if a.cmd == "certify":
        return _certify(a, argv)
    pillars = list(OBSERVERS) if a.cmd == "all" else ([] if a.cmd == "population" else [a.cmd.upper()])

    try:
        redact = _load_redact()
    except Exception as exc:  # noqa: BLE001 -- no redaction available means nothing is written
        return _fail(f"secret_firewall unavailable ({exc.__class__.__name__}); nothing written")

    ctx, rc = _prepare(a, pillars)
    if ctx is None:
        return rc
    try:
        sc, until, loc = resolve_logged(ctx, pillars, redact, "kme_pillars", a.cmd)
    except PlanRefused:
        return EXIT_UNMEASURED

    if a.cmd == "population":
        rep, ok = _population_report(ctx, sc, loc, until)
        print(redact(json.dumps(rep, indent=1, ensure_ascii=True)))
        return EXIT_OK if ok else EXIT_UNMEASURED

    out_dir = Path(a.out_dir) if a.out_dir else REPO / MEASUREMENTS_REL
    unmeasured = False
    for pillar in pillars:
        res = _result(ctx, sc, pillar, loc, until, argv)
        stem = f"{pillar}-{ctx['label']}-{_utcnow().strftime('%Y-%m-%d')}"
        path = write_measurement(out_dir, stem, redact(render_measurement(res)))
        if a.json:
            print(redact(json.dumps(res, ensure_ascii=True)))
        cut = f" cutoff={loc['method']}" if loc is not None else ""
        print(f"KMEP pillar={pillar} denominator={ctx['label']} population={res['population_match']} "
              f"materiality={res['materiality']}{cut} file={path}")
        unmeasured = unmeasured or res["materiality"] == "UNMEASURED"
    return EXIT_UNMEASURED if unmeasured else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
