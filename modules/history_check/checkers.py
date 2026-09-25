"""Judge a distributed primitive from its recorded history, never from its own verdict.

Clean-room reconstruction of the Jepsen checking discipline (UWCP assimilation R3,
vault/specs/uwcp-assimilation.md §14); concepts only, no upstream code:
  - operations are {type: invoke|ok|fail|info}; `info` means indeterminate -- it
    may or may not have happened, and its effect window is unbounded to the right.
    It is never folded into `fail` (jepsen tutorial 03-client.md; checker.clj).
  - checkers are pure functions of the history; they never ask the system.
  - a checker that crashes is UNKNOWN, never PASS (`check-safe`).
  - an always-valid checker (`unbridled-optimism`) exists so a harness can prove
    it is not being lied to: substituting it must turn a known-bad history green.
Divergence from Jepsen, on purpose: Jepsen lets FAIL outrank UNKNOWN in the merged
verdict. Here `any_unknown` is always reported separately, because a run that
could not judge a property proves nothing about it, whatever the others found.

Checker names are the TLA+ invariant names in vault/specs/tla/UWCP.tla, so a model
counterexample and a runtime violation cite the same id.

History inputs must come from INDEPENDENT sources (lease journal, dispatcher
history, the fenced resources' own accept/refuse logs, the goal log). A history
built only from the subject's final status is the subject grading itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"
OP_TYPES = frozenset({"invoke", "ok", "fail", "info"})


@dataclass(frozen=True)
class Verdict:
    name: str
    valid: str                         # PASS | FAIL | UNKNOWN
    judged: int = 0                    # how many ops this checker actually evaluated
    detail: str = ""
    witness: tuple = ()                # the ops that prove a FAIL


@dataclass(frozen=True)
class Report:
    valid: str
    any_unknown: bool
    verdicts: tuple = field(default_factory=tuple)

    def by_name(self) -> dict:
        return {v.name: v for v in self.verdicts}


class HistoryError(ValueError):
    """The history itself is malformed -- the input, not the subject, is wrong."""


def validate(history: list[dict]) -> list[dict]:
    """Every op needs a type, an f and a position; positions strictly increase."""
    last = None
    for i, op in enumerate(history):
        if op.get("type") not in OP_TYPES:
            raise HistoryError(f"op {i}: type {op.get('type')!r} not in {sorted(OP_TYPES)}")
        if not op.get("f"):
            raise HistoryError(f"op {i}: no f")
        idx = op.get("index")
        if not isinstance(idx, int):
            raise HistoryError(f"op {i}: no integer index")
        if last is not None and idx <= last:
            raise HistoryError(f"op {i}: index {idx} does not follow {last}")
        last = idx
    return history


def _ops(history: list[dict], f: str, types: tuple = ("ok",)) -> list[dict]:
    return [op for op in history if op["f"] == f and op["type"] in types]


# --- checkers ----------------------------------------------------------------

def AtMostOneValidOwner(history: list[dict]) -> Verdict:
    """No two leases ACTIVE on one resource class at the same point of the history.
    Consumes f in {dispatch, renew} (start/extend) and {release, expire,
    queue_expire, consume} (end), each ok, with value {lease_id, classes}."""
    active: dict[str, str] = {}
    judged = 0
    for op in history:
        if op["type"] != "ok":
            continue
        v = op.get("value") or {}
        if op["f"] == "dispatch":
            judged += 1
            for c in v.get("classes", ()):
                other = active.get(c)
                if other and other != v["lease_id"]:
                    return Verdict("AtMostOneValidOwner", FAIL, judged,
                                   f"class {c}: {v['lease_id']} dispatched while {other} active",
                                   (op,))
                active[c] = v["lease_id"]
        elif op["f"] in ("release", "expire", "queue_expire", "consume"):
            judged += 1
            for c in v.get("classes", ()):
                if active.get(c) == v["lease_id"]:
                    del active[c]
    return Verdict("AtMostOneValidOwner", PASS, judged)


def StaleFenceCannotAdvance(history: list[dict]) -> Verdict:
    """A resource never ACCEPTS an effect carrying a fence lower than one it already
    accepted for the same class. Consumes f=effect ok|fail with {cls, fence} --
    from the resource's own log, not the actor's."""
    high: dict[str, int] = {}
    judged = 0
    for op in _ops(history, "effect", ("ok",)):
        judged += 1
        v = op["value"]
        c, fence = v["cls"], int(v["fence"])
        if fence < high.get(c, 0):
            return Verdict("StaleFenceCannotAdvance", FAIL, judged,
                           f"class {c}: accepted fence {fence} after {high[c]}", (op,))
        high[c] = max(high.get(c, 0), fence)
    return Verdict("StaleFenceCannotAdvance", PASS, judged)


def DuplicateEnqueueOneJob(history: list[dict]) -> Verdict:
    """One run_token never produces two queue jobs. f=enqueue ok {run_token, job_id}."""
    seen: dict[str, str] = {}
    judged = 0
    for op in _ops(history, "enqueue"):
        judged += 1
        v = op["value"]
        prev = seen.get(v["run_token"])
        if prev is not None and prev != v["job_id"]:
            return Verdict("DuplicateEnqueueOneJob", FAIL, judged,
                           f"run_token {v['run_token']} -> jobs {prev} and {v['job_id']}", (op,))
        seen[v["run_token"]] = v["job_id"]
    return Verdict("DuplicateEnqueueOneJob", PASS, judged)


def UnknownNeverPass(history: list[dict]) -> Verdict:
    """An epoch whose outcome was ever indeterminate (an `info` observe/probe) and
    never later resolved by an ok observation cannot be judged PASS.
    f in {observe, probe} (info|ok) {epoch_id}; f=judge ok {epoch_id, verdict}."""
    unresolved: set[str] = set()
    judged = 0
    for op in history:
        v = op.get("value") or {}
        if op["f"] in ("observe", "probe"):
            judged += 1
            if op["type"] == "info":
                unresolved.add(v["epoch_id"])
            elif op["type"] == "ok":
                unresolved.discard(v["epoch_id"])
        elif op["f"] == "judge" and op["type"] == "ok":
            judged += 1
            if v.get("verdict") == PASS and v["epoch_id"] in unresolved:
                return Verdict("UnknownNeverPass", FAIL, judged,
                               f"epoch {v['epoch_id']} judged PASS while indeterminate", (op,))
    return Verdict("UnknownNeverPass", PASS, judged)


def NoReplaceOnUnknown(history: list[dict]) -> Verdict:
    """While an epoch is indeterminate, no successor epoch is dispatched for the
    same goal -- an `info` must never license a replacement (UNKNOWN != ABSENT).
    Resolution: an ok observe/probe, or an ok cancel of the goal."""
    open_unknown: dict[str, str] = {}      # goal_id -> epoch_id
    judged = 0
    for op in history:
        v = op.get("value") or {}
        if op["f"] in ("observe", "probe"):
            judged += 1
            if op["type"] == "info":
                open_unknown[v["goal_id"]] = v["epoch_id"]
            elif op["type"] == "ok" and open_unknown.get(v["goal_id"]) == v["epoch_id"]:
                del open_unknown[v["goal_id"]]
        elif op["f"] == "cancel" and op["type"] == "ok":
            open_unknown.pop(v["goal_id"], None)
        elif op["f"] == "begin" and op["type"] == "ok":
            judged += 1
            pending = open_unknown.get(v["goal_id"])
            if pending and pending != v["epoch_id"]:
                return Verdict("NoReplaceOnUnknown", FAIL, judged,
                               f"goal {v['goal_id']}: began {v['epoch_id']} while {pending} "
                               "was indeterminate", (op,))
    return Verdict("NoReplaceOnUnknown", PASS, judged)


def CancelledNeverResumes(history: list[dict]) -> Verdict:
    """After an ok cancel of a goal, no ok begin/resume for it."""
    cancelled: set[str] = set()
    judged = 0
    for op in history:
        if op["type"] != "ok":
            continue
        v = op.get("value") or {}
        if op["f"] == "cancel":
            judged += 1
            cancelled.add(v["goal_id"])
        elif op["f"] in ("begin", "resume"):
            judged += 1
            if v.get("goal_id") in cancelled:
                return Verdict("CancelledNeverResumes", FAIL, judged,
                               f"goal {v['goal_id']}: {op['f']} after cancel", (op,))
    return Verdict("CancelledNeverResumes", PASS, judged)


def ReceiptOnlyForOpenEpoch(history: list[dict]) -> Verdict:
    """An ok receipt ingest names an epoch that has not ended."""
    ended: set[str] = set()
    judged = 0
    for op in history:
        if op["type"] != "ok":
            continue
        v = op.get("value") or {}
        if op["f"] == "end":
            ended.add(v["epoch_id"])
        elif op["f"] == "receipt":
            judged += 1
            if v["epoch_id"] in ended:
                return Verdict("ReceiptOnlyForOpenEpoch", FAIL, judged,
                               f"receipt accepted for ended epoch {v['epoch_id']}", (op,))
    return Verdict("ReceiptOnlyForOpenEpoch", PASS, judged)


def unbridled_optimism(history: list[dict]) -> Verdict:
    """The null checker. Exists only as a negative control for harnesses."""
    return Verdict("unbridled_optimism", PASS, len(history))


ALL = (AtMostOneValidOwner, StaleFenceCannotAdvance, DuplicateEnqueueOneJob, UnknownNeverPass,
       NoReplaceOnUnknown, CancelledNeverResumes, ReceiptOnlyForOpenEpoch)


# --- composition ----------------------------------------------------------------

def check_safe(checker, history) -> Verdict:
    try:
        v = checker(history)
    except Exception as exc:          # the checker, not the subject, failed
        return Verdict(getattr(checker, "__name__", "checker"), UNKNOWN, 0,
                       f"checker crashed: {type(exc).__name__}: {exc}")
    if not isinstance(v, Verdict) or v.valid not in (PASS, FAIL, UNKNOWN):
        return Verdict(getattr(checker, "__name__", "checker"), UNKNOWN, 0,
                       f"checker returned {v!r}")
    return v


def compose(history, checkers=ALL, *, min_judged: int = 1) -> Report:
    """Run every checker. A checker that judged fewer than `min_judged` ops has
    measured nothing and reports UNKNOWN, never PASS."""
    validate(history)
    out = []
    for c in checkers:
        v = check_safe(c, history)
        if v.valid == PASS and v.judged < min_judged:
            v = Verdict(v.name, UNKNOWN, v.judged,
                        f"judged {v.judged} ops, floor {min_judged}: nothing measured")
        out.append(v)
    any_unknown = any(v.valid == UNKNOWN for v in out)
    if any(v.valid == FAIL for v in out):
        valid = FAIL
    elif any_unknown:
        valid = UNKNOWN
    else:
        valid = PASS
    return Report(valid, any_unknown, tuple(out))


# --- adapters -------------------------------------------------------------------

def from_lease_journal(records: list[dict], start_index: int = 0) -> list[dict]:
    """modules.lease journal records -> ok ops (each record was fsynced before ack)."""
    classes: dict[str, list] = {}
    ops = []
    for i, r in enumerate(records):
        if r["op"] == "grant":
            classes[r["lease_id"]] = list(r["classes"])
        ops.append({"index": start_index + i, "type": "ok", "f": r["op"],
                    "process": r.get("host", ""), "time": r.get("ts"), "source": "lease",
                    "value": {"lease_id": r["lease_id"],
                              "classes": classes.get(r["lease_id"], [])}})
    return ops
