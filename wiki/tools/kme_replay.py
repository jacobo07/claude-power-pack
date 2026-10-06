#!/usr/bin/env python3
"""kme_replay: the pillar L offline replay ranker of the incremental-cognition program.

Frozen rule L (owner CE ledger): "offline replay of KME-L (late rollover, identical rereads, unchanged-precondition
retries) ranks live experiments; live champion/challenger sessions spend quota and need an Owner decision". This
instrument scans the transcripts ONCE through kme_pillars' own run context (frozen-source record, flag refusals, the
--until auto locator, the population match; imported, never forked), scores three candidate experiments on the SAME
weighted denominator (the run's selected population, named in the file with its label) and writes one
`L-<label>-<UTC date>.md` that ranks them by UPPER BOUND, highest first.

    python3 wiki/tools/kme_replay.py rank --denominator KME-L|KME-G|OTHER --root <projects-dir> [--root ...]
        [--label NAME (OTHER only)] [--select kme|all] [--host local|gex44] [--expand] [--project-filter REGEX]
        [--since ISO] [--until ISO|none|auto] [--freeze-instant ISO] [--frozen-file FILE] [--out-dir DIR]
        [--rollover-growth TOKENS (default 100000)] [--json]

THE THREE CANDIDATES. Every figure is an UPPER BOUND on what the experiment could save, never a realized saving:
the displacement rule is frozen (tokens a change removes may be paid again elsewhere), so every ranked entry carries
saving_status "upper_bound" and displacement "unknown". The unit is the ledger's weighted input-equivalent (input 1 +
cache_read 0.1 + cache_write 2 + output 5).

  late_rollover   replays the policy P(G) per transcript file (one thread = one context): roll over whenever the
                  simulated context's growth above the thread floor F (its first non-synthetic call's input +
                  cache_write + cache_read) reaches G tokens (default 100,000, --rollover-growth). On each later
                  call, avoided tokens = min(cut - F, ctx_k - F), where `cut` is the real context at the last
                  rollover (F before the first); upper weighted = min(avoided, cache_read_k) x 0.1 +
                  max(0, avoided - cache_read_k) x 2. An actual compaction restarts the policy. G = 50,000 /
                  100,000 / 200,000 are reported beside as sensitivity and never decide the rank.
                  THRESHOLD CHOICE: the threshold is GROWTH above the thread's own floor, not an absolute context. On
                  GEX44 the main-thread first-call floor is 172,753 .. 194,591 tokens (03-04 I smoke), above P0's
                  150,000 large-context mark, so an absolute threshold would "cross" on every first call: it would
                  measure the floor, not lateness.
  identical_rereads  the Phase 3 pillar E numerator: kme_pillars.EObserver (imported) with its state split per thread
                  (main and each inline sidechain; identical to it without inline sidechain lines); the upper bound is
                  its weighted_interval[1] (rereads of an identical file version in one thread, residency-weighted).
  unchanged_precondition_retries  the same tool with the same key (Bash / PowerShell: the stripped command text; any
                  other tool: canonical JSON of its input) repeated in one thread of a transcript file (main, or one
                  inline sidechain; two identical tool uses in ONE assistant message are not a retry) with no
                  intervening Edit / Write / MultiEdit / NotebookEdit (loose, the upper bound) or no intervening tool
                  call outside READ_ONLY_TOOLS (strict, reported beside). Read (pillar E's) and the write tools are excluded;
                  Agent / Task re-dispatches are counted beside only. Upper weighted per retry = burden(result chars,
                  residency, 3.0 chars per token) + (issuing message output tokens / its tool_use count) x 5.

UNMEASURED IS NEVER ZERO. A candidate whose signal is not observed for the whole selected population (rollover: a
session with inline sidechain lines in its main file; retries: a retry whose tool_result never appears) is UNMEASURED
with a named reason and is listed under unranked with no number; a candidate observed with no events is a MEASURED
zero and is ranked.

Exit codes: 0 every candidate measured, 3 any UNMEASURED (the file is still written), 2 usage / refusal.

WHICH L DISPOSITIONS NEED A RANKING FILE. The program done-gate (tools/test_incremental_cognition_program.py, R3) asks
for a primary KME-L ranking file from this tool only when pillar L closes as a measurement terminal:
RESEARCH_INSUFFICIENT_EVIDENCE or FALSIFIED_OR_REJECTED_BY_EVIDENCE. It asks for none, and stays silent, for
AUTHORIZATION_BOUND, IMPLEMENTED_AND_VERIFIED, MERGED_INTO_EXISTING_OWNER, DEFERRED_STRONGER_OWNER and EXTERNAL_BLOCKED
(the CE clause L4 still demands each one's own evidence kinds; AUTHORIZATION_BOUND needs the Owner's own decision file,
never a ranking). A file is terminal evidence only at the frozen rollover growth (ROLLOVER_GROWTH).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import shlex
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import kme_pillars as kp  # noqa: E402
import kme_token_audit  # noqa: E402

INSTRUMENT = "wiki/tools/kme_replay.py"
PILLAR = "L"
RULE_DENOMINATORS = ("KME-L",)
CANDIDATES = ("late_rollover", "identical_rereads", "unchanged_precondition_retries")
ROLLOVER_GROWTH = 100000
ROLLOVER_SENSITIVITY = (50000, 100000, 200000)
READ_ONLY_TOOLS = ("Read", "Grep", "Glob", "LS", "WebFetch", "WebSearch", "TodoWrite")
AGENT_TOOLS = ("Agent", "Task")
KMER_BODY_MARKER = "<!-- kmer-json -->"
KMER_BODY_END = "<!-- /kmer-json -->"
FRONT_KEYS = ("instrument", "pillar", "denominator", "denominator_kind", "rule_denominators", "evidence_role",
              "terminal_evidence", "terminal_evidence_reason", "plane", "measured_at", "until", "command",
              "population_match", "weighted_denominator", "threshold", "rollover_growth", "ranked_ids",
              "unranked_ids")
FRONT_OPTIONAL = ("until_located", "frozen_source")
ROUND = 6          # figures are rounded to 6 decimals: float noise (2200.0000000000005) is not a measurement

NAMES = {
    "late_rollover": "late rollover: context growth above the thread floor that an earlier rollover would have cut",
    "identical_rereads": "identical-version rereads, residency-weighted (the Phase 3 pillar E numerator)",
    "unchanged_precondition_retries": "the same tool call repeated with no intervening state change",
}
DEFINITIONS = {
    "late_rollover": ("policy P(G) replayed per transcript file: roll over whenever the simulated context's growth "
                      "above the thread floor (its first non-synthetic call's context) reaches G tokens; avoided "
                      "tokens on a later call = min(cut - floor, context - floor); an actual compaction restarts the "
                      "policy; upper weighted = min(avoided, cache_read) x 0.1 + the rest x 2"),
    "identical_rereads": ("Read results whose sha256 equals the previous read of the same path and offset/limit "
                          "range in the same transcript file, with no Edit / Write / MultiEdit / NotebookEdit of "
                          "that path between; upper bound = same compaction segment plus after a compaction"),
    "unchanged_precondition_retries": ("the same tool with the same key repeated in one transcript file with no "
                                       "intervening Edit / Write / MultiEdit / NotebookEdit (loose, the upper "
                                       "bound) or no intervening tool call outside the read-only tools (strict, "
                                       "beside); upper weighted = result burden at 3.0 chars per token + the "
                                       "issuing message's output share x 5"),
}
BOUND_READINGS = {
    ">= 3 %": ">= 3 %: a live experiment could clear materiality and needs the Owner's quota decision",
    "< 3 %": "< 3 %: cannot clear materiality even if fully realized",
}
CAVEATS = (
    "every figure is an UPPER BOUND, never a realized saving: the displacement rule is frozen (tokens removed here "
    "may be paid again elsewhere), so each entry carries saving_status upper_bound and displacement unknown",
    "the three candidates overlap (a reread's result and a retried command's output are also context a rollover would "
    "have cut): the figures rank experiments and must never be added together",
    "UNMEASURED is never 0: a candidate whose signal is not observed for the whole selected population is listed "
    "under unranked with its reason and no number; a candidate observed with no events is a measured zero and ranks",
    "late_rollover is a gross upper bound: the rollover's own cost (at least the floor re-read F x 0.1 per rollover, "
    "up to F x 2 when the cache is cold) and any summary a real rollover carries are NOT subtracted; `rollovers` and "
    "the floor distribution are reported so a reader can bound them; an absolute threshold would measure the floor, "
    "hence growth; the candidate ranks the policy at the stated G only",
    "unchanged_precondition_retries: the loose class counts a rerun after a Bash command that changed state (a `git "
    "commit` between two `git log -1`), and a poll whose precondition is the outside world, which is why it is the "
    "UPPER bound and strict is reported beside; Agent / Task re-dispatches are outside the candidate because their "
    "cost lives in subagent files the replay cannot link to the parent call; tool execution time is not a token cost",
    "identical_rereads is kme_pillars.EObserver with its state split per thread: its upper bound adds rereads after a "
    "compaction; a sidechain event's residency counts the calls of the whole file, so it is an upper figure too",
)


# --------------------------------------------------------------------------- seams (resolved at call time)
def rollover_segments(n_order, compact_points):
    """[(start, end)] index ranges of `order` between actual compactions (the policy restarts at each)."""
    bounds = [0] + [p for p in compact_points if 0 < p < n_order] + [n_order]
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1) if bounds[i + 1] > bounds[i]]


def rollover_avoided(cut, ctx, floor):
    """Tokens a rollover at context `cut` would have kept out of a later call whose real context is `ctx`."""
    return max(0, min(cut - floor, ctx - floor))


def rollover_weighted(avoided, cache_read):
    """Weighted cost of `avoided` tokens: the cache-read part at 0.1, any excess (not resident in the cache) at 2."""
    return min(avoided, cache_read) * kp.WEIGHTS["cache_read"] + max(0, avoided - cache_read) * kp.WEIGHTS["cache_write"]


def retry_key(name, inp):
    """Identity of a call for the retry candidate: Bash / PowerShell by the stripped command text, any other tool by
    the canonical JSON of its input (hashed, never emitted)."""
    if name in ("Bash", "PowerShell") and isinstance(inp, dict) and isinstance(inp.get("command"), str) \
            and inp["command"].strip():
        return ("cmd", name, inp["command"].strip())
    blob = json.dumps(inp, sort_keys=True, ensure_ascii=False)
    return (name, hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest())


def retry_kind(prev, now):
    """"strict" when neither epoch moved since the previous identical call, "loose" when only the mutating epoch moved
    (no write tool in between), None otherwise or when there is no previous. prev = None | (write epoch, mutating
    epoch, ...); now = (write epoch, mutating epoch)."""
    if prev is None:
        return None
    if now[0] != prev[0]:
        return None
    return "strict" if now[1] == prev[1] else "loose"


def same_message(prev, mid):
    """True when the previous identical call (a `last` / `agent_last` record whose final field is its assistant message
    id) was issued in the SAME assistant message: parallel tool uses are not a retry of each other."""
    return prev is not None and mid is not None and len(prev) >= 3 and prev[-1] == mid and mid != ""


def retry_weighted(chars, resident, share):
    """Upper weighted cost of one retry: its result's residency burden at 3.0 chars per token + the issuing message's
    output share x the output weight."""
    return kp.burden(chars, resident, kp.CPT_LO) + share * kp.WEIGHTS["output"]


def upper_bound_of(result):
    """The candidate's upper bound: its numerator's weighted_interval[1]."""
    return result["numerator"]["weighted_interval"][1]


def candidate_status(denominator_ok, observability):
    """MEASURED only when the denominator is usable AND the signal is observed for the whole population."""
    if denominator_ok and observability is not None and observability >= 1.0:
        return "MEASURED"
    return "UNMEASURED"


def rank_candidates(entries):
    """entries = [{"candidate", "upper_bound_weighted": number | None}]; None means UNMEASURED. Only an entry carrying a
    number ranks (a missing figure is never read as 0): sorted by (-upper bound, CANDIDATES order), so a tie falls in
    the fixed candidate order whatever order the entries arrive in."""
    have = [e for e in entries if e.get("upper_bound_weighted") is not None]
    return sorted(have, key=lambda e: (-e["upper_bound_weighted"], CANDIDATES.index(e["candidate"])))


def dense_ranks(ranked):
    """Dense rank per entry of an already sorted list: equal figures (the rounded upper bound shown) share a rank, the
    next distinct figure takes the next integer. A three-way tie of measured zeros reads rank 1 / 1 / 1, never an order
    of preference; the order inside a tie stays the fixed candidate order."""
    out, last, r = [], object(), 0
    for e in ranked:
        fig = _r(e["upper_bound_weighted"])
        if fig != last:
            r += 1
            last = fig
        out.append(r)
    return out


def split_ranking(results):
    """results = {candidate id: a MEASURED entry (carries upper_bound_weighted) | an UNMEASURED entry (status
    UNMEASURED, reason) | None (no observer result)} -> (ranked, unranked). Every candidate not ranked is listed under
    unranked with a reason and no number."""
    entries, notes = [], {}
    for cid in CANDIDATES:
        r = results.get(cid)
        if r is None:
            notes[cid] = {"candidate": cid, "status": "UNMEASURED", "reason": "input missing: no observer result",
                          "observability": None}
            entries.append({"candidate": cid, "upper_bound_weighted": None})
        elif r.get("status") == "UNMEASURED":
            notes[cid] = r
            entries.append({"candidate": cid, "upper_bound_weighted": None})
        else:
            entries.append(r)
    ranked = rank_candidates(entries)
    done = {e["candidate"] for e in ranked}
    return ranked, [notes[cid] for cid in CANDIDATES if cid in notes and cid not in done]


def bound_label(upper, weighted):
    """An upper bound read against the materiality threshold on that bound: >= 3 % could clear it (a live experiment
    needs the Owner's quota decision), < 3 % cannot even if fully realized."""
    return ">= 3 %" if upper / weighted >= kp.THRESHOLD else "< 3 %"


def denominator_for(cid, scan):
    """The weighted denominator a candidate is scored on: the scan's own, the same for every candidate."""
    return scan["measured"]["weighted"]


def in_selection(sid, selected):
    return sid in selected


# --------------------------------------------------------------------------- observers
def thread_of(o):
    """The thread a transcript line belongs to inside one file: "main", or one inline sidechain (`isSidechain: true`,
    told apart by its agentId). A subagent's calls and the main thread's are separate contexts, so the retry and reread
    candidates never pair across them."""
    if isinstance(o, dict) and o.get("isSidechain") is True:
        aid = o.get("agentId")
        return "side:" + (aid if isinstance(aid, str) else "")
    return "main"


class RereadObserver(kp.EObserver):
    """identical_rereads: kme_pillars.EObserver with its per-file state split per THREAD (WR-06): main and each inline
    sidechain keep their own read / write / last-hash state, so a subagent's Read of a file never makes the main
    thread's next Read an "identical reread". Without inline sidechain lines it is EObserver exactly (V-KMER-REREADS-
    EQUALS-E); pillar E's own instrument is untouched. A tool_result is routed to the thread that issued its tool_use,
    whatever flag the result row carries."""

    def __init__(self):
        super().__init__()
        self._keys = collections.defaultdict(set)
        self._tid_key = {}

    def on_line(self, path, o, idx, sess):
        key = path
        if isinstance(o, dict):
            t = thread_of(o)
            key = path if t == "main" else f"{path}\0{t}"
            msg = o.get("message")
            content = msg.get("content") if isinstance(msg, dict) else None
            for c in kp._blocks(content):
                if not isinstance(c, dict):
                    continue
                if o.get("type") == "assistant" and c.get("type") == "tool_use":
                    self._tid_key[(path, c.get("id"))] = key
                elif o.get("type") == "user" and c.get("type") == "tool_result" \
                        and (path, c.get("tool_use_id")) in self._tid_key:
                    key = self._tid_key[(path, c.get("tool_use_id"))]
                    break
        self._keys[path].add(key)
        super().on_line(key, o, idx, sess)

    def on_file_end(self, path, sess, order, calls, compact_points):
        for key in sorted(self._keys.pop(path, {path})):
            super().on_file_end(key, sess, order, calls, compact_points)
        for k in [k for k in self._tid_key if k[0] == path]:
            del self._tid_key[k]


class RolloverObserver(kp.PillarObserver):
    """late_rollover: replays P(G) over each transcript file's calls (one thread = one context), for the run's G and
    every G of ROLLOVER_SENSITIVITY. A session whose main file carries usage-bearing inline sidechain lines
    (`isSidechain: true`) holds subagent calls this observer cannot separate from the main thread: it is unobserved,
    so the observability drops below 1 and the candidate is UNMEASURED (the IObserver rule)."""
    pillar = "L"

    def __init__(self, growth=ROLLOVER_GROWTH):
        self.growth = growth
        self.growths = sorted(set(ROLLOVER_SENSITIVITY) | {growth})
        self.threads = []
        self.inline = collections.Counter()

    def on_line(self, path, o, idx, sess):
        if isinstance(o, dict) and o.get("isSidechain") is True and not kp.is_subagent_path(path) \
                and o.get("type") == "assistant" and isinstance(o.get("message"), dict) \
                and isinstance(o["message"].get("usage"), dict):
            self.inline[id(sess)] += 1

    def _replay(self, growth, floor, order, calls, compact_points):
        lo = hi = 0.0
        avoided_total = rollovers = 0
        for start, end in rollover_segments(len(order), compact_points):
            cut = floor
            for i in range(start, end):
                r = calls[order[i]]
                if r.get("model") == "<synthetic>":
                    continue
                ctx = r["inp"] + r["cw"] + r["cr"]
                av = rollover_avoided(cut, ctx, floor)
                avoided_total += av
                lo += av * kp.WEIGHTS["cache_read"]
                hi += rollover_weighted(av, r["cr"])
                if (ctx - (cut - floor)) - floor >= growth:
                    cut = ctx
                    rollovers += 1
        return {"lo": lo, "hi": hi, "avoided": avoided_total, "rollovers": rollovers}

    def on_file_end(self, path, sess, order, calls, compact_points):
        real = [k for k in order if calls[k].get("model") != "<synthetic>"]
        if not real:
            return
        first = calls[real[0]]
        floor = first["inp"] + first["cw"] + first["cr"]
        self.threads.append({"sid": id(sess), "floor": floor,
                             "by_g": {g: self._replay(g, floor, order, calls, compact_points) for g in self.growths}})

    def result(self, selected, sessions, population):
        ths = [t for t in self.threads if in_selection(t["sid"], selected)]

        def total(g, field):
            return sum(t["by_g"][g][field] for t in ths)
        lo, hi = total(self.growth, "lo"), total(self.growth, "hi")
        calls = population["calls"]
        seen = sum(s["main"].get("calls", 0) + s["sub"].get("calls", 0)
                   for s in sessions if id(s) in selected and not self.inline[id(s)])
        return {
            "numerator": {"name": NAMES["late_rollover"], "definition": DEFINITIONS["late_rollover"],
                          "kind": "late rollover", "chars": 0, "weighted_lo": lo, "weighted_hi": hi,
                          "weighted_interval": [lo, hi]},
            "observability": (seen / calls) if calls else None,
            "details": {"growth": self.growth, "threads": len(ths),
                        "threads_crossing": sum(1 for t in ths if t["by_g"][self.growth]["rollovers"]),
                        "rollovers": int(total(self.growth, "rollovers")),
                        "avoided_tokens": int(total(self.growth, "avoided")),
                        "floor": kp.distribution([t["floor"] for t in ths]),
                        "sensitivity": [{"growth": g, "upper_bound_weighted": _r(total(g, "hi")),
                                         "rollovers": int(total(g, "rollovers"))} for g in self.growths],
                        "sessions_with_inline_sidechain": sum(1 for s in sessions
                                                              if id(s) in selected and self.inline[id(s)])},
        }


class RetryObserver(kp.PillarObserver):
    """unchanged_precondition_retries: the same tool call repeated with no intervening state change, per transcript file.

    Two epoch counters per file: the write epoch (bumped by Edit / Write / MultiEdit / NotebookEdit) and the mutating
    epoch (bumped by every tool call outside READ_ONLY_TOOLS, writes and Agent / Task included). A call whose key was
    issued before is a retry: "strict" when neither epoch moved since that previous call, "loose" when only the mutating
    epoch moved (no write in between), nothing when a write came between. Read (pillar E's) and the write tools are
    never retries; an Agent / Task re-dispatch is counted beside only. A retry is paired with its tool_result; one whose
    result never appears is unobserved (the candidate is then UNMEASURED)."""
    pillar = "L"

    def __init__(self):
        self.events = []
        self.agents = []
        self._state = {}
        self._owner = {}

    def _st(self, path, thread="main"):
        st = self._state.get((path, thread))
        if st is None:
            st = {"w": 0, "m": 0, "last": {}, "agent_last": {}, "tid_key": {}, "ev_by_tid": {}, "seen": set(),
                  "msgs": {}, "events": []}
            self._state[(path, thread)] = st
        return st

    def on_line(self, path, o, idx, sess):
        if not isinstance(o, dict):
            return
        st = self._st(path, thread_of(o))
        msg = o.get("message")
        if not isinstance(msg, dict):
            return
        content = msg.get("content")
        blocks = content if isinstance(content, list) else []
        if o.get("type") == "assistant":
            mid = msg.get("id") or o.get("uuid")
            m = st["msgs"].setdefault(mid, {"out": 0, "tools": 0})
            usage = msg.get("usage")
            if isinstance(usage, dict):
                m["out"] = max(m["out"], usage.get("output_tokens") or 0)
            for c in blocks:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    self._owner[(path, c.get("id"))] = st
                    self._on_tool_use(st, c, mid, m, sess)
        elif o.get("type") == "user":
            for c in blocks:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    # a result belongs to the thread that issued its tool_use, whatever flag its own row carries
                    self._on_result(self._owner.get((path, c.get("tool_use_id")), st), c, idx)

    def _on_tool_use(self, st, c, mid, m, sess):
        tid = c.get("id")
        if tid is not None:
            if tid in st["seen"]:       # a streamed duplicate of a block already seen
                return
            st["seen"].add(tid)
        m["tools"] += 1
        name = c.get("name")
        inp = c.get("input") if isinstance(c.get("input"), dict) else {}
        if name == "Read":
            return
        if name in kp.WRITE_TOOLS:
            st["w"] += 1
            st["m"] += 1
            return
        key = retry_key(name, inp)
        if name in AGENT_TOOLS:
            pa = st["agent_last"].get(key)
            if retry_kind(pa, (st["w"], st["m"])) and not same_message(pa, mid):
                self.agents.append(id(sess))
            st["m"] += 1
            st["agent_last"][key] = (st["w"], st["m"], mid)
            return
        prev = st["last"].get(key)
        kind = retry_kind(prev, (st["w"], st["m"]))
        if same_message(prev, mid):
            kind = None         # issued together with the earlier call: its result had not been seen
        after_error = bool(prev[2]) if prev else False
        if name not in READ_ONLY_TOOLS:
            st["m"] += 1
        st["last"][key] = [st["w"], st["m"], False, tid, mid]
        st["tid_key"][tid] = key
        if kind:
            sig = kp.cmd_signature(str(inp.get("command") or "")) if name in ("Bash", "PowerShell") else name
            ev = {"sid": id(sess), "tid": tid, "mid": mid, "kind": kind, "tool": name, "sig": sig,
                  "after_error": after_error, "chars": None, "idx": None, "resident": 0, "share": 0.0}
            st["ev_by_tid"][tid] = ev
            st["events"].append(ev)

    def _on_result(self, st, c, idx):
        tid = c.get("tool_use_id")
        key = st["tid_key"].get(tid)
        if key is not None:
            entry_ = st["last"].get(key)
            if entry_ is not None and entry_[3] == tid:
                entry_[2] = bool(c.get("is_error"))
        ev = st["ev_by_tid"].get(tid)
        if ev is not None:
            ev["chars"] = len(kme_token_audit.text_of(c.get("content")))
            ev["idx"] = idx

    def on_file_end(self, path, sess, order, calls, compact_points):
        for key in sorted(k for k in self._state if k[0] == path):
            st = self._state.pop(key)
            for ev in st["events"]:
                m = st["msgs"].get(ev["mid"], {"out": 0, "tools": 1})
                ev["share"] = m["out"] / max(1, m["tools"])
                if ev["chars"] is not None:
                    ev["resident"] = kp.resident_calls(ev["idx"], compact_points, len(order))
                self.events.append(ev)
        for k in [k for k in self._owner if k[0] == path]:
            del self._owner[k]

    def result(self, selected, sessions, population):
        evs = [e for e in self.events if in_selection(e["sid"], selected)]
        paired = [e for e in evs if e["chars"] is not None]
        lo = sum(kp.burden(e["chars"], e["resident"], kp.CPT_HI) for e in paired if e["kind"] == "strict")
        hi = sum(retry_weighted(e["chars"], e["resident"], e["share"]) for e in paired)
        by_sig = {}
        for e in paired:
            row = by_sig.setdefault((e["tool"], e["sig"]), {"tool": e["tool"], "signature": e["sig"], "count": 0,
                                                              "weighted": 0.0})
            row["count"] += 1
            row["weighted"] += retry_weighted(e["chars"], e["resident"], e["share"])
        top = sorted(by_sig.values(), key=lambda x: (-x["weighted"], x["tool"], x["signature"]))[:10]
        for row in top:
            row["weighted"] = round(row["weighted"], ROUND)
        return {
            "numerator": {"name": NAMES["unchanged_precondition_retries"],
                          "definition": DEFINITIONS["unchanged_precondition_retries"],
                          "kind": "unchanged-precondition retries", "chars": sum(e["chars"] for e in paired),
                          "weighted_lo": lo, "weighted_hi": hi, "weighted_interval": [lo, hi]},
            "observability": (len(paired) / len(evs)) if evs else 1.0,
            "details": {"retries": len(evs), "strict": sum(1 for e in evs if e["kind"] == "strict"),
                        "loose_only": sum(1 for e in evs if e["kind"] == "loose"),
                        "after_error": sum(1 for e in evs if e["after_error"]),
                        "results_unobserved": len(evs) - len(paired),
                        "agent_redispatches": sum(1 for sid in self.agents if in_selection(sid, selected)),
                        "by_tool": dict(sorted(collections.Counter(e["tool"] for e in evs).items())),
                        "top_signatures": top},
        }


def factories(growth):
    """{candidate id: zero-argument constructor}; identical_rereads is the Phase 3 E observer class itself."""
    return {"late_rollover": lambda: RolloverObserver(growth), "identical_rereads": RereadObserver,
            "unchanged_precondition_retries": RetryObserver}


# --------------------------------------------------------------------------- CLI
def build_parser():
    ap = argparse.ArgumentParser(prog="kme_replay.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")
    sp = sub.add_parser("rank", help="rank the three candidate experiments by upper bound on one denominator")
    sp.add_argument("--denominator", required=True, choices=["KME-L", "KME-G", "OTHER"])
    sp.add_argument("--label", default=None, help="name of the OTHER workload (A-Z 0-9 -)")
    sp.add_argument("--select", choices=["kme", "all"], default=None)
    sp.add_argument("--host", default=None)
    sp.add_argument("--root", action="append", required=True)
    sp.add_argument("--expand", action="store_true")
    sp.add_argument("--project-filter", default=None)
    sp.add_argument("--since", default=None)
    sp.add_argument("--until", default=None)
    sp.add_argument("--freeze-instant", default=None)
    sp.add_argument("--frozen-file", default=None)
    sp.add_argument("--out-dir", default=None)
    sp.add_argument("--rollover-growth", type=int, default=ROLLOVER_GROWTH,
                    help=f"late_rollover threshold: context growth above the thread floor (default {ROLLOVER_GROWTH})")
    sp.add_argument("--json", action="store_true")
    kp.add_plan_args(sp)
    sp.set_defaults(frozen_ce_ledger=None, role="auto")
    return ap


def command_string(argv):
    parts = list(sys.argv) if argv is None else [INSTRUMENT] + list(argv)
    return shlex.join([os.path.basename(sys.executable) or "python3"] + parts)


def terminal_ok(role, match, frozen_source, unranked, growth=ROLLOVER_GROWTH):
    """A ranking file is terminal evidence only for a primary run whose population reproduced the frozen one, read from
    the committed frozen source (a missing record is not the committed source), with every candidate measured, at the
    frozen rollover growth (ROLLOVER_GROWTH): a late_rollover figure at any other G is a statement about that G, so
    another G is sensitivity / smoke only."""
    src_default = bool(frozen_source) and bool(frozen_source.get("all_default"))
    pinned = type(growth) is int and growth == ROLLOVER_GROWTH
    return role == "primary" and match == "exact" and src_default and not unranked and pinned


def _r(x):
    return None if x is None else round(float(x), ROUND)


def entry_figures(pres, upper, share):
    """The figures a ranked entry carries: the upper bound and its share of the denominator, rounded to ROUND decimals,
    and the numerator's identity (name, kind, chars). Never a `weighted_lo` / `weighted_interval`: the observer's low side
    is the gross cost of the avoided tokens, not a lower bound on a saving, and a consumer reading a ranked entry as a
    kme_pillars interval would take it for one."""
    num = pres["numerator"]
    return {"upper_bound_weighted": _r(upper), "upper_bound_share": _r(share),
            "numerator": {"name": num["name"], "kind": num["kind"], "chars": num["chars"]}}


def scrub_details(cid, details):
    """A ranking file never carries the absolute paths the transcripts read (IN-02): identical_rereads' top_paths becomes
    {path_sha256_12, ext, count, chars}, order kept. A digest tells two files apart and the extension what kind they
    are; the path itself (a customer name, an .env.production) is something no regex redactor can know is sensitive."""
    if cid != "identical_rereads" or not isinstance(details, dict) or "top_paths" not in details:
        return details
    out = []
    for t in details["top_paths"]:
        raw = str(t.get("path", ""))
        ext = os.path.splitext(os.path.basename(raw))[1].lower()
        out.append({"path_sha256_12": hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:12],
                    "ext": ext if ext and len(ext) <= 12 and all(ch.isalnum() or ch == "." for ch in ext) else "",
                    "count": t.get("count"), "chars": t.get("chars")})
    return dict(details, top_paths=out)


def _events_of(cid, pres):
    d = pres["details"]
    if cid == "late_rollover":
        return {"rollovers": d.get("rollovers"), "threads": d.get("threads"),
                "threads_crossing": d.get("threads_crossing")}
    if cid == "identical_rereads":
        cl = d.get("classes", {})
        return {"identical_same_segment": cl.get("identical_same_segment", {}).get("count", 0),
                "identical_after_compaction": cl.get("identical_after_compaction", {}).get("count", 0)}
    return {"retries": d.get("retries"), "strict": d.get("strict"), "loose_only": d.get("loose_only")}


def _unmeasured_reason(cid, den_reason, pres):
    if den_reason:
        return f"denominator not usable: {den_reason}"
    obs = pres["observability"]
    obs_txt = "none (no calls in the population)" if obs is None else f"{obs:.4f}"
    d = pres["details"]
    if cid == "late_rollover":
        return (f"observability {obs_txt}: {d.get('sessions_with_inline_sidechain', 0)} session(s) hold inline "
                f"sidechain lines in their main file, so their threads cannot be separated")
    if cid == "unchanged_precondition_retries":
        return (f"observability {obs_txt}: {d.get('results_unobserved', 0)} of {d.get('retries', 0)} retried "
                f"call(s) have no tool_result in the transcript")
    return f"observability {obs_txt}"


def rank_result(ctx, sc, loc, until, argv, growth):
    label = ctx["label"]
    match, deltas, frozen_pop, _coverage = kp._match(ctx, sc, loc)
    w = sc["measured"]["weighted"]
    den_reason = None
    if loc is not None and loc["method"] == "not_found":
        den_reason = "cutoff_not_found: the freeze-time cutoff could not be located, so the population is not reproduced"
    elif match not in ("exact", "not_frozen"):
        den_reason = (f"population_not_reproduced: population_match={match}, the run's population is not the named "
                      f"denominator")
    elif not w > 0:
        den_reason = "empty denominator (weighted 0)"
    results = {}
    for cid in CANDIDATES:
        pres = sc["obs"][cid].result(sc["selected"], sc["sessions"], sc["pop"])
        if candidate_status(den_reason is None, pres["observability"]) != "MEASURED":
            results[cid] = {"candidate": cid, "status": "UNMEASURED",
                            "reason": _unmeasured_reason(cid, den_reason, pres),
                            "observability": _r(pres["observability"])}
            continue
        upper = upper_bound_of(pres)
        den = denominator_for(cid, sc)
        share = upper / den
        bound = bound_label(upper, den)
        results[cid] = dict({"candidate": cid, "name": NAMES[cid], "definition": DEFINITIONS[cid]},
                            **entry_figures(pres, upper, share),
                            **{"bound_vs_threshold": bound, "bound_reading": BOUND_READINGS[bound],
                               "saving_status": "upper_bound", "displacement": "unknown",
                               "events": _events_of(cid, pres), "details": scrub_details(cid, pres["details"])})
    ranked, unranked = split_ranking(results)
    for e, r in zip(ranked, dense_ranks(ranked)):
        e["rank"] = r
    in_rule = label in RULE_DENOMINATORS
    role = "primary" if in_rule else "smoke"
    fsrc = ctx.get("frozen_source")
    terminal = terminal_ok(role, match, fsrc, unranked, growth=growth)
    if role == "primary":
        src = "the committed frozen source" if (fsrc and fsrc.get("all_default")) else \
            "NOT the committed frozen source (a frozen source flag points elsewhere)"
        un = ",".join(u["candidate"] for u in unranked) or "none"
        t_reason = ("primary file: the label is in rule L's denominators "
                    f"{list(RULE_DENOMINATORS)}; terminal only with an exact population, the committed frozen source, "
                    f"every candidate measured and rollover_growth {ROLLOVER_GROWTH} (population_match={match}, "
                    f"frozen source: {src}, unranked={un}, rollover_growth={growth}"
                    + ("" if growth == ROLLOVER_GROWTH else f": not the frozen {ROLLOVER_GROWTH}, sensitivity only")
                    + ")")
    else:
        t_reason = (f"smoke: {label} is outside rule L's denominators {list(RULE_DENOMINATORS)}; evidence about the "
                    f"instrument, not a pillar terminal")
    res = {
        "instrument": INSTRUMENT, "pillar": PILLAR, "denominator": label, "denominator_kind": ctx["kind"],
        "rule_denominators": list(RULE_DENOMINATORS), "evidence_role": role, "terminal_evidence": terminal,
        "terminal_evidence_reason": t_reason, "plane": kp.plane_name(),
        "measured_at": kp._utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": kp.fmt_instant(until) if until is not None else None, "command": command_string(argv),
        "population_match": match, "weighted_denominator": _r(w), "threshold": kp.THRESHOLD,
        "rollover_growth": growth, "ranked_ids": [e["candidate"] for e in ranked],
        "unranked_ids": [e["candidate"] for e in unranked],
        "ranked": ranked, "unranked": unranked,
        "host": ctx["host"], "select": ctx["select"], "population": sc["measured"], "frozen_population": frozen_pop,
        "population_deltas": deltas, "caveats": list(CAVEATS),
        "corpus": {"roots": len(ctx["roots"]), "project_dirs": len(sc["dirs"]),
                   "sessions_scanned": len(sc["sessions"]), "sessions_selected_active": len(sc["selected"]),
                   "project_filter": ctx["pf"].pattern if ctx["pf"] else None},
        "since": kp.fmt_instant(ctx["since"]) if ctx["since"] is not None else None,
        "until_located": kp._located_block(loc, until), "frozen_source": fsrc,
    }
    return res


def render_rank(res):
    lines = ["---"]
    for k in FRONT_KEYS:
        lines.append(f"{k}: {json.dumps(res[k], ensure_ascii=False)}")
    for k in FRONT_OPTIONAL:
        if res.get(k) is not None:
            lines.append(f"{k}: {json.dumps(res[k], ensure_ascii=False)}")
    lines.append("---")
    label, w = res["denominator"], res["weighted_denominator"]
    lines += ["", f"# Pillar L offline replay ranking -- {label} ({res['evidence_role']}, plane {res['plane']})", ""]
    lines += ["## Population", "", f"match: **{res['population_match']}**", "",
              "| field | measured | frozen | delta |", "|---|---|---|---|"]
    meas, froz = res["population"], res.get("frozen_population") or {}
    for f in kp.POP_FIELDS:
        m, z = meas.get(f), froz.get(f)
        d = (m - z) if isinstance(z, (int, float)) and isinstance(m, (int, float)) else ""
        lines.append(f"| {f} | {m} | {z if z is not None else 'n/a'} | {d} |")
    lines.append(f"| weighted | {meas.get('weighted')} | {froz.get('weighted', 'n/a')} | |")
    lines += ["", "## Ranking (upper bounds -- never a realized saving)", "",
              f"| rank | candidate | upper bound (weighted) | share of {label} weighted {w} | vs 3 % | events |",
              "|---|---|---|---|---|---|"]
    for e in res["ranked"]:
        lines.append(f"| {e['rank']} | {e['candidate']} | {e['upper_bound_weighted']} | "
                     f"{e['upper_bound_share']:.6f} | {e['bound_vs_threshold']} | "
                     f"{json.dumps(e['events'], sort_keys=True)} |")
    if not res["ranked"]:
        lines.append("| - | none | - | - | - | - |")
    lines += ["", "## Unranked (UNMEASURED -- never 0)", ""]
    if res["unranked"]:
        lines += [f"- {u['candidate']}: UNMEASURED, {u['reason']}" for u in res["unranked"]]
    else:
        lines.append("none")
    lines += ["", "## Candidate details", ""]
    for e in res["ranked"]:
        lines += [f"### {e['candidate']}", f"- {e['name']}", f"- definition: {e['definition']}",
                  f"- reading: {e['bound_reading']}", f"- saving_status: {e['saving_status']}, displacement "
                  f"{e['displacement']}", f"- details: {json.dumps(e['details'], sort_keys=True, ensure_ascii=False)}", ""]
    lines += ["## Caveats", ""] + [f"- {c}" for c in res["caveats"]]
    lines += ["", KMER_BODY_MARKER, json.dumps(res, indent=1, ensure_ascii=False), KMER_BODY_END, ""]
    return "\n".join(lines)


def main(argv=None):
    ap = build_parser()
    try:
        a = ap.parse_args(sys.argv[1:] if argv is None else list(argv))
    except SystemExit as e:
        return int(e.code or 0)
    try:
        redact = kp._load_redact()
    except Exception as exc:  # noqa: BLE001 -- no redaction available means nothing is written
        return kp._fail(f"secret_firewall unavailable ({exc.__class__.__name__}); nothing written")
    if a.rollover_growth < 1:
        return kp._fail("--rollover-growth must be at least 1")
    ctx, rc = kp._prepare(a, [PILLAR])
    if ctx is None:
        return rc
    try:
        sc, until, loc = kp.resolve_logged(ctx, list(CANDIDATES), redact, "kme_replay", a.cmd,
                                           observer_factories=factories(a.rollover_growth))
    except kp.PlanRefused:
        return kp.EXIT_UNMEASURED
    res = rank_result(ctx, sc, loc, until, argv, a.rollover_growth)
    out_dir = Path(a.out_dir) if a.out_dir else kp.REPO / kp.MEASUREMENTS_REL
    stem = f"{PILLAR}-{ctx['label']}-{kp._utcnow().strftime('%Y-%m-%d')}"
    path = kp.write_measurement(out_dir, stem, redact(render_rank(res)))
    if a.json:
        print(redact(json.dumps(res, ensure_ascii=True)))
    for e in res["ranked"]:
        print(f"KMER rank={e['rank']} candidate={e['candidate']} upper_bound={e['upper_bound_weighted']} "
              f"upper_bound_share={e['upper_bound_share']:.6f} vs_threshold={e['bound_vs_threshold'].replace(' ', '')}")
    for u in res["unranked"]:
        print(f"KMER unranked candidate={u['candidate']} status=UNMEASURED reason={u['reason']}")
    ids = ",".join(res["ranked_ids"]) or "none"
    uids = ",".join(res["unranked_ids"]) or "none"
    print(f"KMER ranked={ids} unranked={uids} denominator={ctx['label']} population={res['population_match']} "
          f"weighted={res['weighted_denominator']} file={path}")
    return kp.EXIT_UNMEASURED if res["unranked"] else kp.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
