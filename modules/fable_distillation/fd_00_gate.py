#!/usr/bin/env python3
"""fd_00_gate.py -- FD-00 Admission Gate (the Delta-Only law's admission clause).

The gate answers one question before a frontier token is spent: *can the Power
Pack already produce this without a frontier model?* If yes, the frontier call is
not worth admitting -- the PP is cheaper, repeatable, and model-independent. This
is FD-00's admission clause (II.9) as a four-valued typed verdict over a fixed
input, so a habit becomes a mechanism.

Verdicts (FD-00 II.9), each naming its reason so CO-12 can audit it:
  ANSWER_FROM_ASSET -- a CO-05 stored answer/asset is a direct hit (rung 1-2).
  DECLINE           -- the floor covers it: a deterministic recipe, or a PP
                       dataset already governs this class. No model at all.
  ROUTE_CHEAPER     -- a sub-frontier rung (Haiku/Sonnet) suffices per CO-03.
  ADMIT             -- genuinely above-floor (discovery / architecture / critique
                       / dependence-reducing) AND the cheapest sufficient rung is
                       the frontier model. A deposit is now OWED (FD-00 deposit
                       clause; FD-07 closes it).
  DEFER             -- too little to classify (empty / trivially short). Advisory
                       asks for a sharper task, never blocks.

`.action` collapses the verdict to admit | reject | defer for a caller that only
needs the coarse decision (the prompt's H1 contract).

Honest boundaries (the anti-duplication the whole suite guards):
  - CONSULTS CO-03 `route()` and CO-05 `vault_resolver/asset_resolver`; it never
    re-implements routing or asset freshness (those are CO-03 / CO-05's rights).
  - ADVISORY, fail-open ABSOLUTE: any error -> ADMIT (never wrongly block the
    Owner's call; FD-00 II.9 fail-open contract). It emits a recommendation and a
    typed reason; it does not gate the tool.
  - The dependence metric is CO-12's; this gate only emits the two session signals
    CO-12 already reads (opt-in via record=True), it computes no metric of its own.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

# A demand whose whole shape is a mechanical transform is at-floor by construction
# -- the PP (or any rung) reproduces it; a frontier token on it is waste (FD-00 II.5
# row 1). Matched as whole words so "reformatting" hits but "information" does not.
_MECHANICAL_KW = (
    "reformat", "format", "indent", "whitespace", "lint", "prettier", "rename",
    "boilerplate", "restate", "paraphrase", "reword", "sort imports", "prettify",
    "capitalize", "lowercase", "uppercase", "expand this", "fix the typo",
)
# Above-floor demand shapes: novelty, architecture, taste, adversarial critique,
# cross-domain synthesis, dependence reduction (FD-00 II.5 row 4 + FD-02 leverage
# taxonomy). Presence of these is what justifies a frontier token IF the cascade
# also puts the cheapest sufficient rung at the frontier.
_NOVEL_KW = (
    "design", "architect", "architecture", "novel", "critique", "evaluate",
    "trade-off", "tradeoff", "strategy", "invent", "scheme", "from scratch",
    "why does", "why is", "should we", "compare the", "reduce dependence",
    "first principles", "root cause", "counterexample", "adversarial",
)
_STOP = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is", "are",
    "this", "that", "with", "how", "what", "write", "make", "create", "add",
    "using", "use", "into", "from", "your", "please", "help", "need", "want",
}
_KB_DIR = _PP_ROOT / "vault" / "knowledge_base"


@dataclass
class AdmissionDecision:
    verdict: str                       # ANSWER_FROM_ASSET|DECLINE|ROUTE_CHEAPER|ADMIT|DEFER
    action: str                        # admit | reject | defer
    reason: str                        # typed, auditable (the CO-12 admitted-reason)
    rung: str = ""                     # the CO-03 rung consulted
    baseline_ref: str = ""             # what covered the demand (for a reject)
    signals: dict = field(default_factory=dict)


def _tokens(task: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]{4,}", (task or "").lower())
            if w not in _STOP}


def _has_word(task: str, phrases) -> str | None:
    t = (task or "").lower()
    for p in phrases:
        if " " in p:
            if p in t:
                return p
        elif re.search(rf"\b{re.escape(p)}\b", t):
            return p
    return None


def _dataset_covers(task: str, *, kb_dir: Path | None = None) -> str | None:
    """Does a PP knowledge_base dataset already govern this class? Cheap: matches
    the task's significant tokens against dataset FILENAME stems (which encode the
    topic, e.g. fd_01_fable_delta_extraction_engine). >= 2 shared significant
    tokens = covered. Fail-open -> None (miss). Never reads file bodies (bounded)."""
    try:
        base = kb_dir or _KB_DIR
        if not base.is_dir():
            return None
        tt = _tokens(task)
        if len(tt) < 2:
            return None
        for md in base.rglob("*.md"):
            stem_tokens = _tokens(md.stem.replace("_", " ").replace("-", " "))
            shared = tt & stem_tokens
            if len(shared) >= 2:
                return f"{md.name} (shared: {', '.join(sorted(shared))})"
        return None
    except Exception:  # noqa: BLE001 -- fail-open
        return None


def _route_rung(task: str, *, route_fn=None) -> tuple[str, str]:
    """Consult CO-03. Returns (rung, reason). Fail-open -> ('', '') so the caller
    proceeds to the novelty heuristic rather than crashing."""
    try:
        if route_fn is None:
            from modules.cognitive_os.router import route as route_fn  # type: ignore
        d = route_fn(task)
        return (str(getattr(d, "rung", "") or ""), str(getattr(d, "reason", "") or ""))
    except Exception:  # noqa: BLE001 -- fail-open
        return ("", "")


def check_admission(task_description: str, *, kb_dir: Path | None = None,
                    route_fn=None, record: bool = False,
                    state_dir=None) -> AdmissionDecision:
    """Classify a would-be frontier call against the CO-03/CO-05 floor and the
    demand's shape. Advisory + fail-open ABSOLUTE: any error -> ADMIT. Set
    record=True to emit the CO-12 session signal (off by default so the gate is a
    pure function for hermetic tests)."""
    try:
        task = (task_description or "").strip()
        # DEFER -- too little to classify. Advisory asks for a sharper task.
        if len(_tokens(task)) < 2:
            dec = AdmissionDecision(
                "DEFER", "defer",
                "too little to classify (empty/trivial) -- sharpen the task", "")
            return _emit(dec, task, record, state_dir)

        # At-floor by shape: a purely mechanical transform is never a delta.
        mech = _has_word(task, _MECHANICAL_KW)
        if mech:
            dec = AdmissionDecision(
                "DECLINE", "reject",
                f"at-floor: mechanical transform ({mech!r}) -- any rung reproduces it",
                "deterministic", baseline_ref="shape:mechanical")
            return _emit(dec, task, record, state_dir)

        # Consult CO-03: the cheapest sufficient rung.
        rung, rreason = _route_rung(task, route_fn=route_fn)
        if rung in ("vault", "asset"):
            dec = AdmissionDecision(
                "ANSWER_FROM_ASSET", "reject",
                f"CO-05 {rung} hit -- a stored asset resolves it (0 model tokens)",
                rung, baseline_ref=f"co05:{rung}")
            return _emit(dec, task, record, state_dir)
        if rung == "deterministic":
            dec = AdmissionDecision(
                "DECLINE", "reject",
                f"CO-03 deterministic rung -- {rreason or 'no model needed'}",
                rung, baseline_ref="co03:deterministic")
            return _emit(dec, task, record, state_dir)

        # A PP dataset already governs this class -> the floor covers it.
        covered = _dataset_covers(task, kb_dir=kb_dir)
        if covered:
            dec = AdmissionDecision(
                "DECLINE", "reject",
                f"a PP dataset already governs this class -- {covered}",
                rung or "n/a", baseline_ref=f"dataset:{covered}")
            return _emit(dec, task, record, state_dir)

        if rung in ("haiku", "sonnet"):
            dec = AdmissionDecision(
                "ROUTE_CHEAPER", "reject",
                f"CO-03 resolves at {rung} -- a sub-frontier rung suffices",
                rung, baseline_ref=f"co03:{rung}")
            return _emit(dec, task, record, state_dir)

        # The cheapest sufficient rung is the frontier model. Admit ONLY if the
        # demand's shape is genuinely above-floor (novelty/architecture/critique);
        # otherwise DEFER -- opus-routed but no clear novelty signal is a judgment
        # call the advisory surfaces rather than auto-admitting.
        novel = _has_word(task, _NOVEL_KW)
        if novel:
            dec = AdmissionDecision(
                "ADMIT", "admit",
                f"floor silent + above-floor shape ({novel!r}); cheapest rung is "
                f"frontier ({rung or 'opus'}) -- deposit owed",
                rung or "opus", baseline_ref="floor:silent")
            return _emit(dec, task, record, state_dir)

        dec = AdmissionDecision(
            "DEFER", "defer",
            f"frontier-routed ({rung or 'opus'}) but no clear novelty signal -- "
            "confirm it is above-floor before spending",
            rung or "opus", baseline_ref="floor:ambiguous")
        return _emit(dec, task, record, state_dir)
    except Exception as e:  # noqa: BLE001 -- fail-open ABSOLUTE: never block the Owner
        return AdmissionDecision(
            "ADMIT", "admit",
            f"gate error -> fail-open ADMIT (never block the call): {e}", "")


def _emit(dec: AdmissionDecision, task: str, record: bool, state_dir) -> AdmissionDecision:
    """Attach the CO-12 session signal and (opt-in) record it. The gate NEVER
    computes a dependence metric -- it only feeds the two signals CO-12 reads."""
    kind = "fd_frontier_call_admitted" if dec.action == "admit" else "fd_admission_declined"
    dec.signals = {"kind": kind, "verdict": dec.verdict, "rung": dec.rung,
                   "reason": dec.reason, "baseline_ref": dec.baseline_ref}
    if record:
        try:
            from modules.cognitive_os.co_12_telemetry import record_signal
            record_signal(kind, {"verdict": dec.verdict, "rung": dec.rung,
                                 "baseline_ref": dec.baseline_ref},
                          state_dir=state_dir)
        except Exception:  # noqa: BLE001 -- a telemetry write never breaks the gate
            pass
    return dec


def main(argv=None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("task", nargs="*")
    ap.add_argument("--record", action="store_true",
                    help="emit the CO-12 session signal for this decision")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    task = " ".join(args.task) or (sys.stdin.read() if not sys.stdin.isatty() else "")
    dec = check_admission(task, record=args.record)
    if args.json:
        print(json.dumps({"verdict": dec.verdict, "action": dec.action,
                          "reason": dec.reason, "rung": dec.rung,
                          "baseline_ref": dec.baseline_ref}))
    else:
        print(f"{dec.verdict} ({dec.action})")
        print(f"  {dec.reason}")
    # Advisory: exit 0 always (never a blocking exit code).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
