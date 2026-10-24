#!/usr/bin/env python
"""S6 blocker compiler: every BLOCKED transition and Owner-hold park carries a typed blocker (flow-compression, FC-08).

A `mission_blocked` row used to carry a sentence. Nothing could read "what unblocks this" or "is there other safe
work" from a sentence, so a mission parked on a permission prompt looked the same as one parked on spent capital.
`compile_blocker` maps what the writer already has (reason, hold, typed intent, record) to

    {class, unblock_condition{kind, ...}, unblock_text, independent_work, independent_reason, owner_required, rule}

Properties this module keeps, each pinned by a V-S6 gate:
  * Pure and deterministic: same inputs, same output. No clock, no network, no launch. The compiler REPORTS.
  * The classes come from the host ledger (`census`), not from imagination. A reason nothing matches is UNKNOWN,
    and UNKNOWN is never independent work.
  * `independent_work` is true only on POSITIVE evidence read from ROADMAP/STATE by `plan_evidence`; absent or
    unreadable evidence is false with reason `unmeasured` (absent is not true, and absent is not zero).
  * It never expands authority (FC-06): an outward / irreversible / resource-blocked item stays an Owner act, and
    the autonomy gate is consulted, not duplicated.
  * Stdlib only at module level; autonomy_gate and blocked_intent are imported lazily so a missing optional piece
    degrades one rule, never the compiler.

CLI:
    python tools/blocker_compiler.py census [--json|--md] [--out PATH] [--ledger PATH]
    python tools/blocker_compiler.py decisions --cwd DIR [--workstream WS] [--batch KEY]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
GM_PY = TOOLS / "gsd_mission.py"

# ------------------------------------------------------------------------------------------------ taxonomy
HOST_GATE = "HOST_GATE"
COMMAND_REQUEST = "COMMAND_REQUEST"
DECISION_REQUEST = "DECISION_REQUEST"
RESOURCE_REQUEST = "RESOURCE_REQUEST"
PUBLISH_BOUNDARY = "PUBLISH_BOUNDARY"
CAPITAL_EXHAUSTED = "CAPITAL_EXHAUSTED"
COST_HOLD_RECOVERING = "COST_HOLD_RECOVERING"
PROVIDER_LIMIT = "PROVIDER_LIMIT"
WAIT_RESOURCE = "WAIT_RESOURCE"
GSD_HOLD = "GSD_HOLD"
CAPSULE_NOT_CERTIFIED = "CAPSULE_NOT_CERTIFIED"
CAPSULE_SEAL_REFUSED = "CAPSULE_SEAL_REFUSED"
SETUP_HOLD = "SETUP_HOLD"
OWNER_PARK = "OWNER_PARK"
UNKNOWN = "UNKNOWN"
CLASSES = (HOST_GATE, COMMAND_REQUEST, DECISION_REQUEST, RESOURCE_REQUEST, PUBLISH_BOUNDARY, CAPITAL_EXHAUSTED,
           COST_HOLD_RECOVERING, PROVIDER_LIMIT, WAIT_RESOURCE, GSD_HOLD, CAPSULE_NOT_CERTIFIED,
           CAPSULE_SEAL_REFUSED, SETUP_HOLD, OWNER_PARK, UNKNOWN)

# Classes that block ONE unit of work: another unit may be runnable. Every other class is mission-wide.
UNIT_SCOPED = frozenset({HOST_GATE, COMMAND_REQUEST, DECISION_REQUEST, RESOURCE_REQUEST, PUBLISH_BOUNDARY})

_NEEDS_RE = re.compile(r"host needs:\s*(.+)$", re.I | re.S)
_HOST_WAIT_RE = re.compile(r"\bwaiting for (permission prompt|input needed)\b", re.I)
_CAPITAL_RE = re.compile(r"authority exhausted|mission authority|\btranche\b|\ballowance\b|\bceiling\b|hard stop|"
                         r"more budget|budget (?:option|decision|tranche)|decision on budget|raise (?:the )?authority",
                         re.I)
_PROVIDER_RE = re.compile(r"rate limited|weekly limit|usage limit|account .{0,24}limit", re.I)
_UNTIL_RE = re.compile(r"(?:resets?|until)\s+([^·;\n]{3,60})", re.I)
_SETUP_RE = re.compile(r"not trusted|trust consent|envelope before|bounding before release|"
                       r"launched worker blocked before its first turn|stall budget before|before first launch", re.I)
_GSD_RE = re.compile(r"^gsd (NO_PHASES|UNAVAILABLE)\b", re.I)
_CAPSULE_SEAL_RE = re.compile(r"capsule-v2 seal impossible", re.I)
_CERT_RE = re.compile(r"^resume_not_certified\b", re.I)


def _needs(reason: str) -> str:
    m = _NEEDS_RE.search(reason or "")
    return m.group(1).strip() if m else ""


def _hold_type(hold: dict | None) -> str | None:
    """gsd_hold | capsule_hold | owner_hold, inferred by the SHAPE the writers produce."""
    if not isinstance(hold, dict) or not hold:
        return None
    if "outcome" in hold:
        return "gsd_hold"
    if hold.get("kind") in ("resume_not_certified", "seal_refused"):
        return "capsule_hold"
    return "owner_hold"


def _is_cost(hold: dict | None) -> bool:
    return bool(hold) and (hold.get("kind") == "cost" or str(hold.get("reason") or "").startswith("cost breaker"))


def _authority_hold(hold: dict | None) -> bool:
    return bool(hold) and str(hold.get("reason") or "").startswith("cost breaker (mission authority)")


def _cmd(verb: str, mid: str | None, extra: str = "") -> str:
    return f'python "{GM_PY}" {verb} --mission {mid or "<MISSION>"}{(" " + extra) if extra else ""}'


def _autonomy(text: str):
    """The autonomy gate's verdict for `text`, or None when it cannot be loaded (that rule then does not fire)."""
    try:
        root = str(TOOLS.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from modules.autonomy_gate import gate
        return gate.classify(text)
    except Exception:  # noqa: BLE001 -- an unloadable optional classifier removes one rule, nothing more
        return None


def _intent(needs: str, intent: dict | None) -> dict | None:
    if intent:
        return intent
    if not needs:
        return None
    try:
        sys.path.insert(0, str(TOOLS))
        import blocked_intent as bint
        return bint.intent(needs, None)
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------------------------------------------ rule table
# Data, not control flow: (rule name, class, matcher(ctx)->bool, builder(ctx)->(condition, text, owner_required)).
# First match wins, so the ORDER is the precedence and is read top to bottom.
def _owner_act(command: str | None, what: str):
    return {"kind": "owner_act", "command": command, "what": what}


def _b_cert(c):
    return ({"kind": "cause_delta", "what": "a successor certifies the capsule (certification lifts the hold)"},
            "A successor must certify the capsule; the supervisor lifts this hold itself when it does.", False)


def _b_seal(c):
    return ({"kind": "cause_delta", "what": "the work tree changes or the hold's backoff expires, then the seal is re-judged"},
            "The capsule cannot be sealed from durable state; the supervisor re-judges after a tree change or its backoff.",
            False)


def _b_gsd(c):
    hold = c["hold"] or {}
    what = hold.get("unblock") or "GSD answers OK for this project"
    return ({"kind": "cause_delta", "what": what},
            f"GSD must answer OK again ({what}); no relay runs until then.", False)


def _b_capital(c):
    wait = (c["hold"] or {}).get("wait") or {}
    cmd = wait.get("resume") or (_cmd("authority", c["mid"], "--tokens <NEW_TOTAL>") + " ; " + _cmd("release", c["mid"]))
    return (_owner_act(cmd, "raise the mission authority, then release the hold"),
            "The mission authority is spent; only the Owner raises it.", True)


def _b_cost(c):
    return ({"kind": "cause_delta", "what": "recovery names a materially different strategy or the work tree changes"},
            "The cost breaker holds the worker; autonomous recovery decides the next step.", False)


def _b_provider(c):
    m = _UNTIL_RE.search(c["reason"])
    return ({"kind": "time_delta", "until_text": m.group(1).strip() if m else None,
             "what": "the provider limit resets"},
            "The provider limit has to reset; nothing the Owner types lifts it sooner.", False)


def _b_resource(c):
    return ({"kind": "resource_supplied", "what": "the held resource (memory, disk, account) is available again"},
            "A resource this mission needs is exhausted; it resumes when the resource is supplied.", False)


def _b_hostgate(c):
    m = _HOST_WAIT_RE.search(c["reason"])
    gate = m.group(1).lower() if m else "host gate"
    return ({"kind": "host_gate", "gate": gate, "needs": c["needs"] or None},
            f"A host-side gate ({gate}) must be opened on the host; no directive opens it.", True)


def _b_publish(c):
    kind = (c["auto"] or {}).get("kind") or "outward"
    return (_owner_act(None, f"authorize or perform the outward action ({kind}) named in the ask"),
            f"The ask is an outward-facing action ({kind}); the Owner performs or authorizes it.", True)


def _b_intent(c):
    it = c["intent"] or {}
    action = it.get("action")
    kind = it.get("kind")
    # A standing answer is the one block answered without the Owner, and only when the WRITER passed the typed intent
    # (it delivered the answer). An intent the compiler derived itself from text is a reading, not an answer given.
    if action == "ANSWER_STANDING" and c["intent_passed"]:
        return ({"kind": "standing_answer", "what": "the standing answer is delivered to the worker"},
                "A command request: the supervisor answers it with the standing answer; the Owner is not needed.", False)
    if action == "REPOINT" and c["intent_passed"]:
        return ({"kind": "standing_answer", "what": "point the worker at the files already supplied"},
                "The files were already supplied; the worker is re-pointed to them.", False)
    what = {DECISION_REQUEST: "answer the decision the worker asked for",
            RESOURCE_REQUEST: "supply the files or targets the worker asked for"}.get(kind, "answer the ask")
    return (_owner_act(_cmd("decide", c["mid"], '--text "<DECISION>"'), what),
            "The Owner answers the ask; it is delivered to the mission as a recorded decision.", True)


def _b_setup(c):
    return (_owner_act(_cmd("release", c["mid"]), "complete the setup step the hold names, then release"),
            "A setup step is outstanding (trust, envelope or bounding); the Owner completes it and releases.", True)


def _b_park(c):
    return (_owner_act(_cmd("release", c["mid"]), "release the hold when the Owner's reason no longer applies"),
            "The Owner (or the Owner's tooling) parked this mission; it resumes on release.", True)


def _b_unknown(c):
    return ({"kind": "unknown", "what": "no unblock condition could be derived from this reason"},
            "Unclassified: read the reason; no unblock condition could be derived.", True)


def _m_cert(c):
    return c["hold_kind"] == "resume_not_certified" or bool(_CERT_RE.search(c["reason"]))


def _m_seal(c):
    return c["hold_kind"] == "seal_refused" or bool(_CAPSULE_SEAL_RE.search(c["reason"]))


def _m_gsd(c):
    return c["htype"] == "gsd_hold" or bool(_GSD_RE.search(c["reason"]))


def _m_wait_capital(c):
    return ((c["hold"] or {}).get("wait") or {}).get("type") == "CAPITAL_EXHAUSTED"


def _m_provider(c):
    return bool(_PROVIDER_RE.search(c["reason"]))


def _m_resource_kind(c):
    return (c["hold"] or {}).get("kind") == "resource"


def _m_capital_text(c):
    return bool(_CAPITAL_RE.search(c["reason"]))


def _m_authority_trip(c):
    return _authority_hold(c["hold"]) or c["reason"].startswith("cost breaker (mission authority)")


def _m_cost(c):
    return _is_cost(c["hold"]) or bool(re.match(r"^cost breaker", c["reason"], re.I))


def _m_hostgate(c):
    return bool(_HOST_WAIT_RE.search(c["reason"]))


def _m_publish(c):
    a = c["auto"]
    # irreversible (a force push) is as much an Owner boundary as a plain push: typed, never left UNKNOWN
    return bool(a) and a.get("owner") == "OWNER" and a.get("category") in ("outward-facing", "irreversible")


def _m_intent(c):
    return bool(c["intent"]) and c["intent"].get("kind") in (DECISION_REQUEST, RESOURCE_REQUEST, COMMAND_REQUEST)


def _m_intent_hostgate(c):
    return bool(c["intent"]) and c["intent"].get("kind") == "HOST_GATE"


def _m_setup(c):
    return bool(_SETUP_RE.search(c["reason"]))


def _m_park(c):
    return c["htype"] == "owner_hold" or c["is_hold_context"]


RULES = (
    ("capsule_resume_not_certified", CAPSULE_NOT_CERTIFIED, _m_cert, _b_cert),
    ("capsule_seal_refused", CAPSULE_SEAL_REFUSED, _m_seal, _b_seal),
    ("gsd_hold", GSD_HOLD, _m_gsd, _b_gsd),
    ("amr_wait_capital_exhausted", CAPITAL_EXHAUSTED, _m_wait_capital, _b_capital),
    ("authority_trip", CAPITAL_EXHAUSTED, _m_authority_trip, _b_capital),
    ("provider_limit_text", PROVIDER_LIMIT, _m_provider, _b_provider),
    ("hold_kind_resource", WAIT_RESOURCE, _m_resource_kind, _b_resource),
    ("cost_hold", COST_HOLD_RECOVERING, _m_cost, _b_cost),
    ("capital_text", CAPITAL_EXHAUSTED, _m_capital_text, _b_capital),
    # Census-driven: the host labels "approve Write: <path>" permission prompts, so the host-gate wording must be
    # read BEFORE the typed intent, which would call them a DECISION.
    ("host_wait_gate", HOST_GATE, _m_hostgate, _b_hostgate),
    ("autonomy_outward", PUBLISH_BOUNDARY, _m_publish, _b_publish),
    ("intent_ask", None, _m_intent, _b_intent),
    ("intent_host_gate", HOST_GATE, _m_intent_hostgate, _b_hostgate),
    ("setup_text", SETUP_HOLD, _m_setup, _b_setup),
    ("owner_park", OWNER_PARK, _m_park, _b_park),
)


def _scope_of(klass: str) -> str:
    return "unit" if klass in UNIT_SCOPED else "mission"


# ------------------------------------------------------------------------------------------------ evidence
_PHASE_LINE = re.compile(r"^- \[(?P<box>[ xX])\] \*\*Phase (?P<n>\d+(?:\.\d+)?)\b")
_HEAD = re.compile(r"^### Phase (?P<n>\d+(?:\.\d+)?)\b")
_DEPS = re.compile(r"^\*\*Depends on\*\*:\s*(?P<d>.*)$", re.I)


def _num(s: str) -> float:
    return float(s)


def plan_evidence(cwd: str | None, workstream: str | None) -> dict:
    """What ROADMAP.md and STATE.md say about runnable units. {measured, reason, current, units, candidates}.

    measured is False (never an empty candidate list) when the files are missing, unreadable, or give no parseable
    units or no current phase: absent is not zero. A unit is a candidate only if it lies AFTER the blocked unit, is
    not checked off, and every unit it depends on is checked off and is not the blocked unit. A stale unchecked box
    BEHIND the cursor is not a candidate."""
    if not cwd:
        return {"measured": False, "reason": "no cwd", "units": [], "candidates": []}
    root = Path(cwd) / ".planning"
    base = root / "workstreams" / workstream if workstream else root
    try:
        roadmap = (base / "ROADMAP.md").read_text(encoding="utf-8")
        state = (base / "STATE.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {"measured": False, "reason": f"unreadable: {type(exc).__name__}", "units": [], "candidates": []}
    cur = re.search(r"^current_phase:\s*\"?(\d+(?:\.\d+)?)\"?\s*$", state, re.M)
    boxes: dict[float, bool] = {}
    deps: dict[float, list[float]] = {}
    section = None
    for line in roadmap.splitlines():
        m = _PHASE_LINE.match(line)
        if m:
            boxes[_num(m["n"])] = m["box"] in "xX"
            continue
        h = _HEAD.match(line)
        if h:
            section = _num(h["n"])
            continue
        d = _DEPS.match(line.strip())
        if d and section is not None:
            deps[section] = [_num(x) for x in re.findall(r"Phase (\d+(?:\.\d+)?)", d["d"])]
    if not boxes:
        return {"measured": False, "reason": "no phase checklist parsed from ROADMAP.md", "units": [], "candidates": []}
    if not cur:
        return {"measured": False, "reason": "STATE.md names no current_phase", "units": sorted(boxes), "candidates": []}
    current = _num(cur.group(1))
    candidates = []
    for n in sorted(boxes):
        if n <= current or boxes[n]:
            continue
        needs = deps.get(n, [])
        if all(boxes.get(x, False) and x != current for x in needs):
            candidates.append(n)
    return {"measured": True, "reason": "ok", "current": current, "units": sorted(boxes), "candidates": candidates}


def _independent(klass: str, rec: dict | None, hold: dict | None, evidence) -> tuple[bool, str]:
    """(independent_work, reason). Positive evidence or false with the reason it is false."""
    if klass == UNKNOWN:
        return False, "unclassified"
    if _scope_of(klass) == "mission":
        return False, "mission_wide"
    holds = [hold, (rec or {}).get("owner_hold")]
    if any(_is_cost(h) or _authority_hold(h) for h in holds if h):
        return False, "authority_exhausted"
    ev = evidence() if callable(evidence) else evidence
    if not ev or not ev.get("measured"):
        return False, "unmeasured"
    if not ev.get("candidates"):
        return False, "no_other_unit"
    return True, f"unit(s) {', '.join(str(int(c) if c == int(c) else c) for c in ev['candidates'])} runnable without the blocked unit"


# ------------------------------------------------------------------------------------------------ compiler
def compile_blocker(reason: str | None, *, hold: dict | None = None, intent: dict | None = None,
                    rec: dict | None = None, cwd: str | None = None, workstream: str | None = None,
                    evidence=None, is_hold: bool = False) -> dict:
    """The typed blocker for one BLOCKED transition or hold park. Pure; never raises for odd input shapes
    (the writer wraps it anyway and falls back to UNKNOWN with the exception class on the row)."""
    reason = str(reason or "")
    hold = hold if isinstance(hold, dict) else None
    needs = _needs(reason)
    ctx = {"reason": reason, "hold": hold, "htype": _hold_type(hold), "hold_kind": (hold or {}).get("kind"),
           "needs": needs, "mid": (rec or {}).get("mission_id"), "is_hold_context": bool(is_hold),
           "intent": _intent(needs, intent), "intent_passed": bool(intent), "auto": None}
    if needs or reason:
        ctx["auto"] = _autonomy(needs or reason) if (needs or "push" in reason.lower()) else None
    klass, name, build = UNKNOWN, "no_rule_matched", _b_unknown
    for rname, rklass, match, builder in RULES:
        if match(ctx):
            name, build = rname, builder
            if rklass is None:
                kind = (ctx["intent"] or {}).get("kind")
                rklass = kind if kind in CLASSES else UNKNOWN
            klass = rklass
            break
    cond, text, owner_required = build(ctx)
    if evidence is None and cwd:
        ev = (lambda: plan_evidence(cwd, workstream))
    else:
        ev = evidence
    indep, why = _independent(klass, rec, hold, ev)
    return {"class": klass, "unblock_condition": cond, "unblock_text": text, "independent_work": indep,
            "independent_reason": why, "owner_required": bool(owner_required), "rule": name}


# ------------------------------------------------------------------------------------------------ decisions
# D-08 / D-09: foreseeable Owner decisions, listed ONCE at arm instead of discovered one by one in live workers.
# Read-only. The compiler never resolves anything outward, irreversible or capital: those stay the Owner's (FC-06).
ASK_MARKERS = re.compile(r"OWNER DECISION NEEDED|needs? (?:the )?Owner|requires? (?:the )?Owner|Owner must|"
                         r"awaiting (?:the )?Owner|Owner-only", re.I)
# Guard / negation phrasing: a rule ABOUT the Owner boundary is not a question for the Owner.
GUARD_FILTER = re.compile(r"\b(?:never|must not|no owner|without the owner|does not need|do not need|not needed|"
                          r"stop only on)\b", re.I)
ANSWER_MARK = re.compile(r"\b(?:DECIDED|ANSWERED|RESOLVED|Owner chose)\b")
# Items FC-06 protects even where the generic classifier would call them self-answerable ("raise the capital
# ceiling" is an Owner act, and the classifier has no capital category). Fail toward the Owner.
PROTECTED = re.compile(r"capital|\bceiling\b|\btop-?up\b|authority|branch protection|\bprotection\b|force[- ]push", re.I)
OUTWARD_CATEGORIES = ("outward-facing", "irreversible", "resource-blocked")


def decisions_on() -> bool:
    return (os.environ.get("CPP_BLOCKER_COMPILE") or "").strip().lower() not in ("0", "off", "false")


def _norm(text: str) -> str:
    return " ".join(re.sub(r"^[\s>*\-\d.)]+", "", text).lower().split())


def item_id(category: str, text: str) -> str:
    return "OD-" + hashlib.sha256(f"{category}|{_norm(text)}".encode("utf-8")).hexdigest()[:8]


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def foreseeable_decisions(cwd: str, workstream: str | None, *, records=None, policy=None, authorized=(),
                          read=None, use_filters: bool = True) -> dict:
    """{measured, items, omitted, resolved_by_policy, sources}. Writes nothing.

    A source that cannot be read is listed as unmeasured and makes `measured` False: it is never read as
    "no decisions" (absent is not zero)."""
    cwd_p = Path(cwd)
    reader = read or _read_text
    if workstream:
        srcs = [cwd_p / "vault" / "specs" / f"{workstream}.md",
                cwd_p / ".planning" / "workstreams" / workstream / "ROADMAP.md",
                cwd_p / ".planning" / "workstreams" / workstream / "STATE.md"]
    else:
        srcs = [cwd_p / ".planning" / "ROADMAP.md", cwd_p / ".planning" / "STATE.md"]
    sources, cands = [], []
    for sp in srcs:
        text = reader(sp)
        if text is None:
            sources.append({"path": str(sp), "status": "unmeasured"})
            continue
        sources.append({"path": str(sp), "status": "ok"})
        for no, line in enumerate(text.splitlines(), 1):
            if use_filters and not ASK_MARKERS.search(line):
                continue
            if use_filters and GUARD_FILTER.search(line):
                continue
            if not use_filters and not line.strip():
                continue
            cands.append((str(sp), no, re.sub(r"^[\s>*\-]+", "", line).strip()))
    recs = [r for r in (records or []) if isinstance(r, dict) and r.get("workstream") == workstream]
    live_ids = {d.get("id") for r in recs for d in (r.get("decisions") or []) if not d.get("superseded_by")}
    directives = [str(d) for r in recs for d in (r.get("directives") or [])]
    pol = policy
    items, omitted, resolved, seen = [], [], [], set()
    for path, no, text in cands:
        verdict = _autonomy_for(text, authorized)
        protected = bool(PROTECTED.search(text))
        if use_filters and not ((verdict or {}).get("owner") == "OWNER" or protected):
            continue
        category = (verdict or {}).get("category") if (verdict or {}).get("owner") == "OWNER" else "protected"
        if category == "gate-error":
            category = "protected"
        iid = item_id(category, text)
        if iid in seen:
            continue
        seen.add(iid)
        item = {"id": iid, "category": category, "kind": (verdict or {}).get("kind"), "text": text[:300],
                "source": path, "line": no, "resolution": "OWNER", "rule": None}
        if ANSWER_MARK.search(text):
            omitted.append({**item, "reason": "doc answer marker on the line"})
        elif iid in live_ids:
            omitted.append({**item, "reason": "live decision recorded on a mission of the same goal"})
        elif any(f"answers:{iid}" in d for d in directives):
            omitted.append({**item, "reason": "directive answers it"})
        elif category == "preference" and not protected:
            if pol is None:
                pol = _repo_policy(cwd)
            q = _gate_question(text, (pol or {}).get("values") or {})
            if q.get("result") == "RESOLVE_BY_POLICY" and q.get("key") and (pol or {}).get("source"):
                resolved.append({**item, "resolution": "RESOLVE_BY_POLICY",
                                 "rule": {"key": q["key"], "source": pol["source"], "fingerprint": pol.get("fingerprint")}})
            else:
                items.append(item)
        else:
            items.append(item)
    return {"measured": all(s["status"] == "ok" for s in sources), "items": items, "omitted": omitted,
            "resolved_by_policy": resolved, "sources": sources}


def _autonomy_for(text: str, authorized=()):
    try:
        root = str(TOOLS.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from modules.autonomy_gate import gate
        return gate.classify(text, authorized=authorized)
    except Exception:  # noqa: BLE001 -- fail toward the Owner: an unloadable gate cannot clear an item
        return {"owner": "OWNER", "category": "gate-error", "why": "autonomy gate unavailable"}


def _repo_policy(cwd: str) -> dict:
    try:
        sys.path.insert(0, str(TOOLS))
        import mission_policy as mp
        return mp.repo_policy(cwd)
    except Exception:  # noqa: BLE001 -- no policy readable means nothing is resolved by policy
        return {"values": {}, "source": None, "fingerprint": None}


def _gate_question(text: str, values: dict) -> dict:
    try:
        sys.path.insert(0, str(TOOLS))
        import mission_policy as mp
        return mp.gate_question(text, values)
    except Exception:  # noqa: BLE001
        return {"result": "OWNER_REQUIRED"}


def batch_key(workstream: str | None, ids) -> str:
    return hashlib.sha256(f"{workstream or ''}|{','.join(sorted(ids))}".encode("utf-8")).hexdigest()[:12]


def print_batch(key: str, ledger: Path | str | None = None) -> dict:
    """A recorded batch, read back from the ledger, with the exact command the Owner runs to answer each item."""
    path = Path(ledger) if ledger else _default_ledger()
    for r in _read_rows(path):
        if r.get("event") == "owner_decisions_batched" and r.get("batch_key") == key:
            items = [{**it, "answer_command": f'python "{GM_PY}" decide --mission <MISSION> --id {it["id"]} --text "<ANSWER>"'}
                     for it in r.get("items") or []]
            return {"batch_key": key, "workstream": r.get("workstream"), "cwd": r.get("cwd"), "items": items,
                    "omitted": r.get("omitted"), "resolved_by_policy": r.get("resolved_by_policy")}
    return {"batch_key": key, "items": [], "error": "no such batch in the ledger"}


# ------------------------------------------------------------------------------------------------ census
CENSUS_EVENTS = ("mission_blocked", "blocked_intent", "owner_hold_set", "recovery_owner_boundary")


def _default_ledger() -> Path:
    sys.path.insert(0, str(TOOLS))
    import gsd_long_run as lr
    return Path(lr.ledger_path())


def _read_rows(path: Path) -> list[dict]:
    out = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                out.append(r)
    except OSError:
        pass
    return out


def census(ledger: Path | str | None = None) -> dict:
    """Read-only census of the blocking rows in a ledger, each compiled. {ledger, rows, populations, classes, unknown}.
    Never writes. `classes[class]` = {count, rules, examples}; `unknown` lists the distinct unclassified reasons."""
    path = Path(ledger) if ledger else _default_ledger()
    rows = _read_rows(path)
    pops = {e: 0 for e in CENSUS_EVENTS}
    classes: dict[str, dict] = {}
    unknown: dict[str, int] = {}
    intent_rows = {"blocked_intent": []}
    for r in rows:
        ev = r.get("event")
        if ev not in CENSUS_EVENTS:
            continue
        pops[ev] += 1
        if ev == "blocked_intent":
            intent_rows["blocked_intent"].append((r.get("kind"), r.get("action")))
            continue
        if ev == "recovery_owner_boundary":
            hold = {"kind": "cost", "reason": str(r.get("why") or ""),
                    "wait": {"type": r.get("wait_type")}}
            reason = str(r.get("why") or "")
            c = compile_blocker(reason, hold=hold, is_hold=True, evidence={"measured": False})
        elif ev == "owner_hold_set":
            reason = str(r.get("reason") or "")
            reason = reason[len("owner hold: "):] if reason.startswith("owner hold: ") else reason
            c = compile_blocker(reason, hold=None, is_hold=True, evidence={"measured": False})
        else:
            reason = str(r.get("reason") or "")
            c = compile_blocker(reason, evidence={"measured": False})
        slot = classes.setdefault(c["class"], {"count": 0, "rules": {}, "examples": []})
        slot["count"] += 1
        slot["rules"][c["rule"]] = slot["rules"].get(c["rule"], 0) + 1
        if len(slot["examples"]) < 3 and reason[:120] not in slot["examples"]:
            slot["examples"].append(reason[:120])
        if c["class"] == UNKNOWN:
            unknown[reason[:160]] = unknown.get(reason[:160], 0) + 1
    return {"ledger": str(path), "rows": len(rows), "populations": pops, "classes": classes,
            "unknown": unknown, "blocked_intent_kinds": intent_rows["blocked_intent"]}


def census_md(c: dict, *, date: str) -> str:
    out = [f"# Phase 6 census (blocker taxonomy evidence)", "",
           f"Ledger: `{c['ledger']}`", f"Rows read: {c['rows']} (census date {date})", "",
           "## Populations (rows per event)", "", "| event | rows |", "| --- | --- |"]
    out += [f"| {e} | {n} |" for e, n in c["populations"].items()]
    out += ["", "## Class to evidence", "", "| class | rows | rules that fired | example reasons |", "| --- | --- | --- | --- |"]
    for klass in CLASSES:
        s = c["classes"].get(klass)
        if not s:
            out.append(f"| {klass} | 0 | (none observed) | - |")
            continue
        rules = ", ".join(f"{k} x{v}" for k, v in sorted(s["rules"].items()))
        ex = "; ".join(e.replace("|", "/") for e in s["examples"])
        out.append(f"| {klass} | {s['count']} | {rules} | {ex} |")
    total = sum(s["count"] for s in c["classes"].values())
    unk = c["classes"].get(UNKNOWN, {}).get("count", 0)
    out += ["", f"Compiled rows: {total}; UNKNOWN residual: {unk}.", "", "## UNKNOWN residual (distinct reasons)", ""]
    out += [f"- x{n}: {r}" for r, n in sorted(c["unknown"].items(), key=lambda kv: -kv[1])] or ["- none"]
    out += ["", "A class with zero observed rows is allowed only when it is already a named hold kind in code "
            "(CAPSULE_NOT_CERTIFIED, CAPSULE_SEAL_REFUSED, GSD_HOLD, WAIT_RESOURCE).", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="blocker_compiler")
    sub = ap.add_subparsers(dest="cmd", required=True)
    cp = sub.add_parser("census")
    cp.add_argument("--json", action="store_true")
    cp.add_argument("--md", action="store_true")
    cp.add_argument("--out")
    cp.add_argument("--ledger")
    dp = sub.add_parser("decisions")
    dp.add_argument("--cwd", default=os.getcwd())
    dp.add_argument("--workstream")
    dp.add_argument("--batch")
    a = ap.parse_args(argv)
    if a.cmd == "census":
        c = census(a.ledger)
        import datetime
        text = census_md(c, date=datetime.date.today().isoformat()) if a.md else json.dumps(c, indent=2, sort_keys=True)
        if a.out:
            Path(a.out).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 0
    if a.cmd == "decisions":
        if a.batch:
            print(json.dumps(print_batch(a.batch), indent=2, sort_keys=True))
            return 0
        print(json.dumps(foreseeable_decisions(a.cwd, a.workstream), indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
