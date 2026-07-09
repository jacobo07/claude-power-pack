#!/usr/bin/env python3
"""fd_07_flywheel.py -- FD-07 close-boundary flywheel (the loop that closes).

At a frontier session's Stop, this turns the six FD stations into one closed loop:
it reads this session's captured deltas (PM-03 Findings Bus), classifies each
(NEW / STRONGER / DUP / DISCARD) against the floor, triages each to a destination,
writes it back IDEMPOTENTLY to the correct stack location, and reports loop health
THROUGH CO-12 -- so using a frontier model this week reduces the need for it next
week, without a human remembering to run a pipeline.

It is genuinely NEW as a composed operating loop but invents NO new plumbing
(FD-07 I.4): it RIDES the GK-08 Stop hook (this module IS a Stop-chain child, same
shape as session_writeback.py) and the PM-03 bus, and REPORTS through CO-12 -- it
never stands up a parallel metric. Its delta over "just run the stations" is the
three things a pipeline lacks: the closed-loop write (verified, idempotent), the
boundedness discipline (a max-step cap so it cannot spin), and the compounding
signal (deposit precision + portability, reported through CO-12, never volume).

Cadence gate: the loop turns only when `PP_FRONTIER_SESSION` marks a frontier
session (kclaude exports it -- Opus is the frontier launcher on this host). A bare
session's Stop runs normally WITHOUT the flywheel. Fail-open ABSOLUTE: any error ->
the session closes normally, no interruption; main() ALWAYS exits 0.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# Bound a single loop turn (FD-07 II.2 max-step cap): process at most this many
# undeposited findings per Stop so a huge bus cannot make the hook spin. A
# truncated turn is LOGGED, never silent (no-silent-caps doctrine).
MAX_FINDINGS_PER_TURN = int(os.environ.get("PP_FD07_MAX_FINDINGS", "25"))
_MIN_DELTA_TOKENS = 4          # below this a claim is noise, not a delta
_STRONGER_NEW_TOKENS = 3       # new tokens over a matched deposit -> STRONGER
# Token-overlap (Jaccard) bands that classify a claim against the floor of prior
# deposits. At/above _DUP the floor already holds it; in [_STRONGER, _DUP) with
# enough new tokens it improves an existing deposit; below _STRONGER it is NEW.
_DUP_JACCARD = 0.85
_STRONGER_JACCARD = 0.45

# Destination signals (FD-03 triage taxonomy). Whole-word / phrase matched.
_RULE_KW = ("never", "always", "must not", "must ", "do not", "hard rule",
            "forbidden", "sealed", "trap", "bug", "regression", "footgun")
_BENCH_KW = ("test", "verify", "gate", "benchmark", "assert", "reproduce", "v-")
_PROMPT_KW = ("prompt", "instruction", "system message", "few-shot", "persona")
_ASSET_KW = ("recipe", "template", "pattern", "checklist", "deterministic",
             "formula", "procedure", "canonical")
_STOP = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
    "this", "that", "with", "it", "as", "be", "by", "at", "was", "were", "not",
}


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(timezone.utc)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _tokens(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{4,}", (s or "").lower())
            if w not in _STOP}


def _has(text: str, phrases) -> bool:
    t = (text or "").lower()
    for p in phrases:
        if p.endswith(" ") or " " in p:
            if p in t:
                return True
        elif re.search(rf"\b{re.escape(p)}\b", t):
            return True
    return False


def _fingerprint(destination: str, claim: str) -> str:
    raw = f"{destination}|{_norm(claim)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _state_dir(state_dir=None) -> Path:
    return Path(state_dir) if state_dir else (
        Path.home() / ".claude" / "state" / "fable_distillation")


def _deposits_path(repo: str, state_dir=None) -> Path:
    enc = re.sub(r"[^a-zA-Z0-9]", "-", repo or "")
    return _state_dir(state_dir) / f"deposits_{enc}.jsonl"


def _ukdl_candidates_path(repo: str, state_dir=None) -> Path:
    enc = re.sub(r"[^a-zA-Z0-9]", "-", repo or "")
    return _state_dir(state_dir) / f"ukdl_candidates_{enc}.jsonl"


# --------------------------------------------------------------------------- #
# Stage 3 -- extract + classify (FD-01: NEW / STRONGER / DUP / DISCARD).
# --------------------------------------------------------------------------- #
def classify_delta(claim: str, existing_fps: set, existing_token_sets: list):
    """Classify a captured claim against the floor of prior deposits. Returns
    (delta_class, confidence). Deterministic, no model. Fail-open -> DISCARD."""
    try:
        toks = _tokens(claim)
        if len(toks) < _MIN_DELTA_TOKENS:
            return ("DISCARD", 0.0)                    # noise / at-floor general fact
        best_overlap, best_prior = 0.0, set()
        for prior in existing_token_sets:
            if not prior:
                continue
            inter = len(toks & prior)
            union = len(toks | prior) or 1
            j = inter / union
            if j > best_overlap:
                best_overlap, best_prior = j, prior
        if best_overlap >= _DUP_JACCARD:
            return ("DUP", best_overlap)               # the floor already holds it
        if best_overlap >= _STRONGER_JACCARD:
            new_tokens = len(toks - best_prior)
            if new_tokens >= _STRONGER_NEW_TOKENS:
                return ("STRONGER", best_overlap)      # improves an existing deposit
            return ("DUP", best_overlap)
        return ("NEW", 1.0 - best_overlap)             # above the floor
    except Exception:  # noqa: BLE001 -- fail-open
        return ("DISCARD", 0.0)


# --------------------------------------------------------------------------- #
# Stage 4 -- triage (FD-03: destination) + Stage 6 estimate (FD-04: portability).
# --------------------------------------------------------------------------- #
def triage_destination(claim: str) -> str:
    """Assign the destination form (FD-03). Deterministic. Fail-open -> dataset_part."""
    try:
        if _has(claim, _RULE_KW):
            return "hard_rule"
        if _has(claim, _BENCH_KW):
            return "benchmark"
        if _has(claim, _PROMPT_KW):
            return "prompt_fragment"
        if _has(claim, _ASSET_KW):
            return "asset"
        return "dataset_part"
    except Exception:  # noqa: BLE001
        return "dataset_part"


def estimate_portability(destination: str) -> str:
    """Estimate the least-capable substrate (FD-00 II.6). ESTIMATED, not FD-04
    tested -- the transfer test is the EXECUTION-v2 follow-up; flagged as such so
    the portability slope never rises on an unproven downgrade (FD-07 II.7)."""
    return {"asset": "deterministic", "benchmark": "deterministic",
            "hard_rule": "mid-model", "prompt_fragment": "small-model",
            "dataset_part": "frontier-only"}.get(destination, "frontier-only")


# --------------------------------------------------------------------------- #
# Stage 5 -- permanent writeback (FD-06), idempotent + append-only.
# --------------------------------------------------------------------------- #
@dataclass
class Deposit:
    fingerprint: str
    task_class: str
    claim: str
    delta_class: str            # NEW | STRONGER
    destination: str
    portability_target: str     # estimated (FD-04 confirms in v2)
    portability_proven: bool    # always False here -- honest (FD-07 II.7 gate)
    confidence: float
    baseline_ref: str
    sid: str
    ts: str
    evidence: str = ""


def _load_deposits(repo: str, state_dir=None) -> list:
    p = _deposits_path(repo, state_dir)
    if not p.is_file():
        return []
    out = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
    except OSError:
        return []
    return out


def _append_jsonl(path: Path, record: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def _writeback(repo: str, dep: Deposit, *, state_dir=None) -> dict:
    """Write a deposit to its correct stack location (FD-06). Every deposit lands
    in the append-only deposits ledger (the durable machine-owned record).
    Destination side-writes: a rule/trap ALSO queues an Owner-promotable UKDL
    candidate (never auto-mutates the curated UKDL -- recommend-and-wait, HR-SECRET-003
    discipline); an asset ALSO attempts a real CO-05 store (gated on verified+recurrent,
    so an unverified finding is recorded as a candidate, not stored). Idempotent by
    fingerprint. Returns the side-writes performed."""
    side = {"deposits_ledger": _append_jsonl(_deposits_path(repo, state_dir), asdict(dep))}
    try:
        if dep.destination == "hard_rule":
            side["ukdl_candidate"] = _append_jsonl(
                _ukdl_candidates_path(repo, state_dir),
                {"fingerprint": dep.fingerprint, "claim": dep.claim,
                 "kind": "hard_rule/trap", "portability": dep.portability_target,
                 "sid": dep.sid, "ts": dep.ts,
                 "status": "candidate -- Owner promotes to ukdl-universal.md"})
        elif dep.destination == "asset":
            from modules.cognitive_os.registry import store_asset
            # Honest: store_asset only persists a VERIFIED asset that met the
            # recurrence threshold; an unverified finding returns False and is
            # recorded as an unstored candidate, never poisoning CO-05's cheap rung.
            stored = store_asset(
                key=f"fd07:{dep.fingerprint}", kind="rule", content=dep.claim,
                applicability=sorted(_tokens(dep.claim))[:8],
                verified=False, recurrence=0)
            side["co05_stored"] = bool(stored)
    except Exception:  # noqa: BLE001 -- a side-write never breaks the deposit
        pass
    return side


# --------------------------------------------------------------------------- #
# The loop (Stages 1-9 composed; FD-07 I.5). Input = this session's undeposited
# findings; output = a bounded, recorded turn result.
# --------------------------------------------------------------------------- #
@dataclass
class FlywheelResult:
    processed: int = 0
    deposited: int = 0
    dup: int = 0
    discarded: int = 0
    truncated: bool = False
    deposits: list = field(default_factory=list)     # fingerprints
    destinations: dict = field(default_factory=dict)  # destination -> count
    note: str = ""


def _session_findings(repo: str, sid: str, *, state_dir=None, bus=None) -> list:
    """This session's captured deltas: drain the PM-03 staging file into the bus,
    then read the repo's bus findings. Fail-open -> []."""
    try:
        from modules.parallel_mesh import pm_03_bus as pm
        pm.drain_staging_findings(repo, sid)          # commit staged findings first
        b = bus or pm.FindingsBus()
        return b.load(repo)
    except Exception:  # noqa: BLE001 -- fail-open
        return []


def run_flywheel(repo: str, sid: str = "", *, findings=None, state_dir=None,
                 now: datetime | None = None, record: bool = True,
                 max_findings: int = MAX_FINDINGS_PER_TURN) -> FlywheelResult:
    """Close one loop turn over the session's findings. `findings` may be supplied
    (each a dict/obj with topic+claim) for a hermetic test; otherwise they are read
    from the PM-03 bus. Every step fail-open; a bad finding is skipped, not fatal."""
    res = FlywheelResult()
    try:
        ts = _now(now).isoformat()
        # Prior deposits = the floor this turn subtracts against (Stage 9 feedback:
        # a deposit already in the ledger raises the floor for the next classify).
        prior = _load_deposits(repo, state_dir)
        seen_fps = {d.get("fingerprint") for d in prior}
        prior_token_sets = [_tokens(d.get("claim", "")) for d in prior]

        raw = findings if findings is not None else _session_findings(
            repo, sid, state_dir=state_dir)
        # Normalize to (topic, claim, evidence) tuples.
        items = []
        for f in raw or []:
            topic = getattr(f, "topic", None) if not isinstance(f, dict) else f.get("topic")
            claim = getattr(f, "claim", None) if not isinstance(f, dict) else f.get("claim")
            evid = (getattr(f, "evidence", "") if not isinstance(f, dict)
                    else f.get("evidence", "")) or ""
            if claim:
                items.append((topic or "", str(claim), str(evid)))

        if len(items) > max_findings:
            res.truncated = True
            items = items[:max_findings]

        for topic, claim, evidence in items:
            res.processed += 1
            cls, conf = classify_delta(claim, seen_fps, prior_token_sets)
            if cls == "DISCARD":
                res.discarded += 1
                continue
            dest = triage_destination(claim)
            fp = _fingerprint(dest, claim)
            if fp in seen_fps or cls == "DUP":
                res.dup += 1
                seen_fps.add(fp)
                continue
            dep = Deposit(
                fingerprint=fp, task_class=(topic or "general")[:80], claim=claim,
                delta_class=cls, destination=dest,
                portability_target=estimate_portability(dest),
                portability_proven=False, confidence=round(float(conf), 3),
                baseline_ref="co05+deposits", sid=sid, ts=ts, evidence=evidence)
            _writeback(repo, dep, state_dir=state_dir)
            seen_fps.add(fp)
            prior_token_sets.append(_tokens(claim))
            res.deposited += 1
            res.deposits.append(fp)
            res.destinations[dest] = res.destinations.get(dest, 0) + 1
            if record:
                _record_deposit_signal(dep, state_dir)

        if res.truncated:
            res.note = (f"max-step cap {max_findings} reached -- "
                        f"{len(raw or []) - max_findings} finding(s) deferred to next turn")
        if record:
            _record_turn_signal(repo, sid, res, state_dir)
        return res
    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE
        res.note = f"flywheel error (fail-open): {e}"
        return res


def _record_deposit_signal(dep: Deposit, state_dir) -> None:
    try:
        from modules.cognitive_os.co_12_telemetry import record_signal
        record_signal("fd_delta_deposited",
                      {"delta_class": dep.delta_class, "destination": dep.destination,
                       "portability_target": dep.portability_target,
                       "portability_proven": dep.portability_proven,
                       "fingerprint": dep.fingerprint}, state_dir=state_dir)
    except Exception:  # noqa: BLE001
        pass


def _record_turn_signal(repo: str, sid: str, res: FlywheelResult, state_dir) -> None:
    try:
        from modules.cognitive_os.co_12_telemetry import record_signal
        record_signal("fd_flywheel_turn",
                      {"processed": res.processed, "deposited": res.deposited,
                       "dup": res.dup, "discarded": res.discarded,
                       "truncated": res.truncated, "sid": sid}, state_dir=state_dir)
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- #
# Stop-hook entry (rides the GK-08 Stop boundary; same shape as session_writeback).
# --------------------------------------------------------------------------- #
def _is_frontier_session() -> bool:
    """kclaude exports PP_FRONTIER_SESSION=1 for a frontier (Opus) launch. Absent
    -> the flywheel does not run and the Stop hook is a no-op."""
    return str(os.environ.get("PP_FRONTIER_SESSION", "")).strip() in ("1", "true", "yes")


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
    except OSError:
        raw = ""
    try:
        data = json.loads(raw or "{}")
    except (json.JSONDecodeError, ValueError):
        data = {}
    cwd = data.get("cwd") or os.getcwd()
    sid = data.get("session_id", "") or ""

    if not _is_frontier_session():
        # Not a frontier session -> no loop turn owed. Silent, exit 0.
        try:
            sys.stdout.write("{}")
        except OSError:
            pass
        return 0

    res = run_flywheel(cwd, sid)
    # Visible loop summary (systemMessage-routable by the dispatcher). The
    # honest header the done-gate looks for.
    summary = (f"FD-07: {res.processed} hallazgos procesados, "
               f"{res.deposited} deltas reales depositados"
               + (f", {res.dup} dup, {res.discarded} descartados" if res.processed else "")
               + (f" [{res.note}]" if res.note else ""))
    if res.destinations:
        dests = ", ".join(f"{k}={v}" for k, v in sorted(res.destinations.items()))
        summary += f" -> {dests}"
    try:
        # Stop event does NOT accept hookSpecificOutput.additionalContext; the
        # dispatcher salvages systemMessage. Fail-open, never blocks close.
        sys.stdout.write(json.dumps({"systemMessage": summary}))
    except OSError:
        pass
    return 0  # ALWAYS exit 0 -- the flywheel never blocks session close


if __name__ == "__main__":
    sys.exit(main())
