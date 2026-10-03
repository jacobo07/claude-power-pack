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
import collections
import datetime
import hashlib
import json
import os
import re
import shlex
import socket
import sys
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

FRONT_KEYS = ("instrument", "pillar", "denominator", "denominator_kind", "rule_denominators", "evidence_role",
              "terminal_evidence", "terminal_evidence_reason", "second_workload_valid", "plane", "measured_at",
              "until", "command", "population_match", "numerator", "share_interval", "share_measured_population",
              "threshold", "materiality", "materiality_reason", "observability", "second_workload_required",
              "estimate_model")

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
def frozen_specs(denoms_path):
    """{"KME-L": {fields, host, select, weighted}, "KME-G": {...}} from the frozen denominator file."""
    raw = json.loads(Path(denoms_path).read_text(encoding="utf-8"))
    out = {}
    for name, host in (("KME-L", "local"), ("KME-G", "gex44")):
        if name in raw:
            fields = {k: raw[name][k] for k in POP_FIELDS}
            out[name] = {"fields": fields, "host": host, "select": "kme", "weighted": weighted(fields)}
    return out


def compare_population(measured, frozen):
    """("exact" | "drifted", {field: [measured, frozen]} for the unequal fields)."""
    deltas = {f: [measured.get(f), frozen.get(f)] for f in POP_FIELDS if measured.get(f) != frozen.get(f)}
    return ("drifted" if deltas else "exact"), deltas


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


class DObserver(PillarObserver):
    """Pillar D: hook_additional_context chars, weighted by residency (calls until the next compaction)."""
    pillar = "D"
    ERROR_TYPES = ("hook_blocking_error", "hook_non_blocking_error")

    def __init__(self):
        self.records = []
        self._by_path = collections.defaultdict(list)
        self.others = []
        self.attach_sessions = set()

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict) or o.get("type") != "attachment":
            return
        a = o.get("attachment")
        if not isinstance(a, dict):
            a = {}
        self.attach_sessions.add(id(sess))
        atype = a.get("type")
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
                        for s in sessions if id(s) in selected and id(s) in self.attach_sessions)
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
        ratio = round(p_doc / p_init, 2) if paired and p_init > 0 else None
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


OBSERVERS = {"D": DObserver, "E": EObserver, "F": FObserver}
PILLAR_HELP = {"D": "silent-success hooks: hook_additional_context rent per call",
               "E": "large-source read virtualization: rereads of identical file versions",
               "F": "GSD operational projection: workflow-doc residency beside the init JSON"}


# --------------------------------------------------------------------------- scan + population
def scan(roots, expand, host, observers, keep):
    """Frozen-parser scan of every root; returns (sessions, fanout, dirs)."""
    dirs = []
    for r in roots:
        if expand:
            dirs += [os.path.join(r, d) for d in sorted(os.listdir(r)) if os.path.isdir(os.path.join(r, d))]
        else:
            dirs.append(r)
    fan = _Fanout(observers)
    sessions = []
    for d in dirs:
        for s in kme_token_audit.scan_project(d, observer=fan, keep=keep):
            kme_token_audit.finish_session(s, host)
            sessions.append(s)
    return sessions, fan, dirs


def population(sessions, spec, kept, window_active):
    """The frozen report's population for the selected sessions. With a time window active a session none of whose
    lines were kept does not exist yet (dropped, not a dead session)."""
    pop = {f: 0 for f in POP_FIELDS}
    selected = set()
    for s in sessions:
        if window_active and kept.get(id(s), 0) == 0:
            continue
        if spec.get("select", "kme") == "kme" and not kme_report.is_kme(s):
            continue
        calls = s["main"].get("calls", 0) + s["sub"].get("calls", 0)
        if calls == 0:
            pop["sessions_dead"] += 1
            continue
        pop["sessions_active"] += 1
        selected.add(id(s))
        pop["calls"] += calls
        for src, dst in (("inp", "input"), ("cw", "cache_write"), ("cr", "cache_read"), ("out", "output")):
            pop[dst] += s["main"].get(src, 0) + s["sub"].get(src, 0)
    pop["weighted"] = weighted(pop)
    pop["selected"] = selected
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
    return out


def render_measurement(res) -> str:
    lines = ["---"]
    for k in FRONT_KEYS:
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


# --------------------------------------------------------------------------- CLI
def _build_parser():
    ap = argparse.ArgumentParser(prog="kme_pillars.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="pillar", required=True, metavar="PILLAR")
    for p, helptext in PILLAR_HELP.items():
        sp = sub.add_parser(p.lower(), help=helptext)
        sp.add_argument("--denominator", required=True, choices=["KME-L", "KME-G", "OTHER"])
        sp.add_argument("--label", default=None, help="name of the OTHER workload (A-Z 0-9 -)")
        sp.add_argument("--select", choices=["kme", "all"], default=None)
        sp.add_argument("--host", default=None)
        sp.add_argument("--root", action="append", required=True)
        sp.add_argument("--expand", action="store_true")
        sp.add_argument("--until", default=None, help="ISO instant or 'none' (default: freeze instant for frozen "
                                                       "denominators, none for OTHER)")
        sp.add_argument("--out-dir", default=None)
        sp.add_argument("--frozen-file", default=None)
        sp.add_argument("--role", choices=["auto", "second_workload"], default="auto")
        sp.add_argument("--json", action="store_true")
    return ap


def _fail(msg):
    print(f"kme_pillars: {msg}", file=sys.stderr)
    return EXIT_USAGE


def main(argv=None):
    ap = _build_parser()
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else list(argv))
    except SystemExit as e:
        return int(e.code or 0)
    pillar = a.pillar.upper()

    try:
        redact = _load_redact()
    except Exception as exc:  # noqa: BLE001 -- no redaction available means nothing is written
        return _fail(f"secret_firewall unavailable ({exc.__class__.__name__}); nothing written")

    frozen_kind = a.denominator in ("KME-L", "KME-G")
    if a.denominator == "OTHER":
        if not a.label or not LABEL_RE.match(a.label):
            return _fail("--denominator OTHER needs --label matching ^[A-Z0-9][A-Z0-9-]{1,40}$")
        if a.label in FROZEN_NAMES:
            return _fail(f"--label {a.label} is a frozen denominator name; a named workload may not take it")
        label = a.label
    else:
        if a.label:
            return _fail("--label is only valid with --denominator OTHER")
        label = a.denominator
    if frozen_kind and a.select == "all":
        return _fail("--select all is not the frozen selection rule of a frozen denominator")
    in_rule = label in RULE_DENOMINATORS[pillar]
    if a.role == "second_workload" and in_rule:
        return _fail(f"{label} is in pillar {pillar}'s own frozen rule {RULE_DENOMINATORS[pillar]}; "
                     f"it cannot be its second workload")

    if a.until is None:
        until = parse_instant(FREEZE_INSTANT) if frozen_kind else None
    elif a.until.lower() == "none":
        until = None
    else:
        until = parse_instant(a.until)
        if until is None:
            return _fail(f"--until {a.until!r} is not an ISO instant")
    for r in a.root:
        if not os.path.isdir(r):
            return _fail(f"--root {r} is not a directory")

    spec = {"select": a.select or "kme"}
    frozen = None
    if frozen_kind:
        fpath = a.frozen_file or str(REPO / DENOMS_REL)
        try:
            specs = frozen_specs(fpath)
        except (OSError, ValueError, KeyError) as exc:
            return _fail(f"frozen file {fpath} unreadable ({exc.__class__.__name__})")
        if a.denominator not in specs:
            return _fail(f"frozen file {fpath} has no {a.denominator} entry")
        frozen = specs[a.denominator]
        spec["select"] = frozen["select"]
    host = a.host or (frozen["host"] if frozen else "local")

    obs = OBSERVERS[pillar]()
    keep = make_keep(None, until) if until is not None else None
    sessions, fan, dirs = scan(a.root, a.expand, host, [obs], keep)
    pop = population(sessions, spec, fan.kept, keep is not None)
    selected = pop.pop("selected")
    measured = {f: pop[f] for f in POP_FIELDS}
    measured["weighted"] = pop["weighted"]
    sel_sessions = [s for s in sessions if id(s) in selected]
    pres = obs.result(selected, sessions, pop)

    if frozen is not None:
        match, deltas = compare_population(measured, frozen["fields"])
        frozen_pop = dict(frozen["fields"], weighted=frozen["weighted"])
    else:
        match, deltas, frozen_pop = "not_frozen", {}, None

    wlo, whi = pres["numerator"]["weighted_interval"]
    w = pop["weighted"]
    share_meas = [wlo / w, whi / w] if w > 0 else None
    share = share_meas if match in ("exact", "not_frozen") else None
    verdict, reason = materiality(share, match, pres["observability"])

    if a.role == "second_workload":
        role = "second_workload"
    else:
        role = "primary" if in_rule else "smoke"
    terminal = role == "primary" and match == "exact" and verdict != "UNMEASURED"
    rule = list(RULE_DENOMINATORS[pillar])
    if role == "primary":
        if terminal:
            t_reason = (f"primary file: {label} is in pillar {pillar}'s frozen rule {rule} and its population "
                        f"reproduced the frozen denominator")
        else:
            t_reason = (f"primary file but not terminal: population_match={match}, materiality={verdict} "
                        f"(a terminal needs an exact population and a measured verdict)")
    elif role == "second_workload":
        t_reason = (f"second_workload file: confirms a primary file on {rule}; never terminal itself")
    else:
        t_reason = (f"smoke: {label} is outside pillar {pillar}'s frozen rule {rule} (the rule names KME-L and "
                    f"CPP-D-W7); evidence about the instrument, not a pillar terminal")
    sw_valid = (match in ("exact", "not_frozen")) if role == "second_workload" else None

    res = {
        "instrument": INSTRUMENT, "pillar": pillar, "denominator": label,
        "denominator_kind": "frozen" if frozen_kind else "named_workload", "rule_denominators": rule,
        "evidence_role": role, "terminal_evidence": terminal, "terminal_evidence_reason": t_reason,
        "second_workload_valid": sw_valid, "plane": plane_name(),
        "measured_at": _utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": until.strftime("%Y-%m-%dT%H:%M:%SZ") if until is not None else None,
        "command": command_string(argv), "population_match": match,
        "numerator": pres["numerator"],
        "share_interval": share, "share_measured_population": share_meas, "threshold": THRESHOLD,
        "materiality": verdict, "materiality_reason": reason, "observability": pres["observability"],
        "second_workload_required": verdict in (">= 3 %", "STRADDLES"), "estimate_model": ESTIMATE_MODEL,
        "host": host, "select": spec["select"],
        "population": measured, "frozen_population": frozen_pop, "population_deltas": deltas,
        "details": pres["details"], "caveats": list(CAVEATS),
        "corpus": {"roots": len(a.root), "project_dirs": len(dirs), "sessions_scanned": len(sessions),
                   "sessions_selected_active": len(sel_sessions)},
    }

    out_dir = Path(a.out_dir) if a.out_dir else REPO / MEASUREMENTS_REL
    stem = f"{pillar}-{label}-{_utcnow().strftime('%Y-%m-%d')}"
    text = redact(render_measurement(res))
    path = write_measurement(out_dir, stem, text)
    if a.json:
        print(redact(json.dumps(res, ensure_ascii=True)))
    print(f"KMEP pillar={pillar} denominator={label} population={match} materiality={verdict} file={path}")
    return EXIT_UNMEASURED if verdict == "UNMEASURED" else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
