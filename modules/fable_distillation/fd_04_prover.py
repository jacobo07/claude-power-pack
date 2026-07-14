#!/usr/bin/env python3
"""fd_04_prover.py -- FD-04 portability prover (the declared-v2 producer).

A deposit leaves FD-07 with `portability_proven=False` -- an ESTIMATE, honest by
design (FD-07 II.7 gate). This module is the only producer that can flip that
state: it re-verifies a deposit's claim against repo reality through
deterministic, read-only probes (file / dir / attr / grep), records the proof in
a SIBLING append-only ledger (deposit rows are never rewritten), and reports
through CO-12 -- FD feeds the signal, CO-12 stays the single accountant
(Invariant 1, FD-07 I.4).

The proof IS the evaluation asset: every stored probe set is re-runnable, so
`recheck()` doubles as the replay + regression pipeline -- a probe that held
yesterday and fails today names the regressed deposit. One module, four
evaluation areas (portability proof, benchmark generation, replay, regression).

Verdict discipline: proving is fail-CLOSED (any probe failure, missing deposit,
or internal error yields FAILED/ERROR -- never a silent PROVEN); read surfaces
(`proven_fingerprints`) are fail-open ABSOLUTE so consumers degrade to the
pre-FD-04 behavior, never crash. Attestations (mid/small-model substrates a
deterministic probe cannot cover) are recorded as method="attestation" with
mandatory evidence, never conflated with probe-proofs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.fable_distillation.fd_07_flywheel import (  # noqa: E402
    _append_jsonl, _load_deposits, _now, _state_dir)

# Substrates a proof may claim. "frontier-only" is deliberately absent: proving
# that a claim needs the frontier is not a downgrade and never flips the flag.
_TARGETS = ("deterministic", "small-model", "mid-model")
_MAX_GREP_BYTES = 2_000_000     # a grep probe refuses files above this bound
_SNIP_EVIDENCE = 500            # attestation evidence stored at most this long
_SNIP_MATCH = 80                # grep match excerpt kept in probe evidence


# --------------------------------------------------------------------------- #
# Proofs ledger -- sibling of fd_07's deposits ledger, same slug convention.
# --------------------------------------------------------------------------- #
def _proofs_path(repo: str, state_dir=None) -> Path:
    enc = re.sub(r"[^a-zA-Z0-9]", "-", repo or "")
    return _state_dir(state_dir) / f"fd04_proofs_{enc}.jsonl"


def _read_jsonl(path: Path) -> list:
    if not path.is_file():
        return []
    out = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
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


def _latest_by_fp(records: list) -> dict:
    """Latest record per fingerprint (append-only ledger: later lines win)."""
    out: dict = {}
    for r in records:
        fp = r.get("fingerprint")
        if fp:
            out[fp] = r
    return out


def proven_fingerprints(repo: str, state_dir=None) -> set:
    """Fingerprints whose LATEST proof record is PROVEN. Fail-open ABSOLUTE ->
    empty set (consumers then behave exactly as before FD-04 existed)."""
    try:
        return {fp for fp, r in
                _latest_by_fp(_read_jsonl(_proofs_path(repo, state_dir))).items()
                if r.get("verdict") == "PROVEN"}
    except Exception:  # noqa: BLE001
        return set()


# --------------------------------------------------------------------------- #
# Deterministic probes -- read-only, each returns (ok, evidence).
# --------------------------------------------------------------------------- #
def _resolve(repo: str, path: str) -> Path:
    p = Path(path or "")
    return p if p.is_absolute() else Path(repo or ".") / (path or "")


def run_probe(spec: dict, repo: str) -> tuple:
    """Execute one probe spec. Unknown types and internal errors are FALSE with
    the reason as evidence (fail-closed: an unrunnable probe proves nothing)."""
    try:
        kind = spec.get("type")
        if kind == "file_exists":
            p = _resolve(repo, spec.get("path", ""))
            ok = p.is_file()
            return ok, f"{p} -- {'exists' if ok else 'NOT FOUND'}"
        if kind == "dir_exists":
            p = _resolve(repo, spec.get("path", ""))
            ok = p.is_dir()
            return ok, f"{p} -- {'exists' if ok else 'NOT FOUND'}"
        if kind in ("attr_exists", "function_exists"):
            # COMPOSES the premise verifier (BL-PREMISE-001) -- import checks
            # are its right, never re-implemented here. PP-root-scoped modules.
            from modules.error_prevention.premise_verifier import verify_attr_exists
            r = verify_attr_exists(spec.get("module", ""),
                                   spec.get("attr") or spec.get("function") or "")
            return bool(r.verified), r.evidence
        if kind == "grep":
            p = _resolve(repo, spec.get("path", ""))
            if not p.is_file():
                return False, f"{p} -- NOT FOUND"
            if p.stat().st_size > _MAX_GREP_BYTES:
                return False, f"{p} -- exceeds probe size bound ({_MAX_GREP_BYTES} B)"
            text = p.read_text(encoding="utf-8", errors="replace")
            hit = re.search(spec.get("pattern", ""), text)
            return bool(hit), (f"pattern matched: {hit.group(0)[:_SNIP_MATCH]}"
                               if hit else "pattern not found")
        return False, f"unknown probe type: {kind}"
    except Exception as e:  # noqa: BLE001 -- an erroring probe proves nothing
        return False, f"probe error (fail-closed): {type(e).__name__}: {e}"


def _replay_spec(stored: dict) -> dict:
    """Strip a stored probe result back to its executable spec."""
    return {k: v for k, v in stored.items() if k not in ("ok", "evidence")}


# --------------------------------------------------------------------------- #
# prove / attest -- the two producers. Both idempotent by fingerprint.
# --------------------------------------------------------------------------- #
def _deposit_exists(repo: str, fingerprint: str, state_dir) -> bool:
    return any(d.get("fingerprint") == fingerprint
               for d in _load_deposits(repo, state_dir))


def _signal(kind: str, payload: dict, state_dir) -> None:
    try:
        from modules.cognitive_os.co_12_telemetry import record_signal
        record_signal(kind, payload, state_dir=state_dir)
    except Exception:  # noqa: BLE001 -- a signal never breaks a proof
        pass


def prove(repo: str, fingerprint: str, probes: list, *,
          achieved_target: str = "deterministic", sid: str = "",
          state_dir=None, now: datetime | None = None) -> dict:
    """Run deterministic probes against a deposited claim. ALL probes must pass
    for PROVEN; anything else is FAILED (recorded honestly, never counted) or
    ERROR (bad input / missing deposit). Fail-CLOSED throughout."""
    try:
        if not isinstance(probes, list) or not probes:
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": "no probes supplied -- a proof without probes is a claim"}
        if achieved_target not in _TARGETS:
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": f"achieved_target must be one of {_TARGETS}"}
        if not _deposit_exists(repo, fingerprint, state_dir):
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": "deposit not found in ledger -- prove() only covers "
                            "deposited claims"}
        prior = _latest_by_fp(_read_jsonl(_proofs_path(repo, state_dir))).get(fingerprint)
        if prior and prior.get("verdict") == "PROVEN":
            return {**prior, "note": "already-proven (idempotent -- no new record/signal)"}

        results, ok_all = [], True
        for spec in probes:
            ok, ev = run_probe(spec if isinstance(spec, dict) else {}, repo)
            ok_all = ok_all and ok
            results.append({**(spec if isinstance(spec, dict) else {"type": "invalid"}),
                            "ok": ok, "evidence": ev})
        rec = {"fingerprint": fingerprint,
               "verdict": "PROVEN" if ok_all else "FAILED",
               "method": "probes", "achieved_target": achieved_target,
               "probes": results, "sid": sid, "ts": _now(now).isoformat()}
        _append_jsonl(_proofs_path(repo, state_dir), rec)
        if ok_all:
            _signal("fd_portability_proven",
                    {"fingerprint": fingerprint, "achieved_target": achieved_target,
                     "method": "probes", "probes": len(results)}, state_dir)
        return rec
    except Exception as e:  # noqa: BLE001 -- fail-closed: an error is never PROVEN
        return {"verdict": "ERROR", "fingerprint": fingerprint,
                "note": f"prover error (fail-closed): {type(e).__name__}: {e}"}


def attest(repo: str, fingerprint: str, *, substrate: str, evidence: str,
           sid: str = "", state_dir=None, now: datetime | None = None) -> dict:
    """Record that a NON-frontier substrate re-derived the deposited claim (the
    downgrade a deterministic probe cannot cover). Requires non-empty evidence;
    recorded as method='attestation', never conflated with probe-proofs."""
    try:
        if substrate not in _TARGETS:
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": f"substrate must be one of {_TARGETS}"}
        if not (evidence or "").strip():
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": "attestation requires non-empty evidence -- an "
                            "unevidenced attestation is a wish"}
        if not _deposit_exists(repo, fingerprint, state_dir):
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": "deposit not found in ledger"}
        prior = _latest_by_fp(_read_jsonl(_proofs_path(repo, state_dir))).get(fingerprint)
        if prior and prior.get("verdict") == "PROVEN":
            return {**prior, "note": "already-proven (idempotent -- no new record/signal)"}
        rec = {"fingerprint": fingerprint, "verdict": "PROVEN",
               "method": "attestation", "achieved_target": substrate,
               "probes": [], "evidence": evidence.strip()[:_SNIP_EVIDENCE],
               "sid": sid, "ts": _now(now).isoformat()}
        _append_jsonl(_proofs_path(repo, state_dir), rec)
        _signal("fd_portability_proven",
                {"fingerprint": fingerprint, "achieved_target": substrate,
                 "method": "attestation", "probes": 0}, state_dir)
        return rec
    except Exception as e:  # noqa: BLE001
        return {"verdict": "ERROR", "fingerprint": fingerprint,
                "note": f"attest error (fail-closed): {type(e).__name__}: {e}"}


def record_cross_model(repo: str, fingerprint: str, *, results: list,
                       sid: str = "", state_dir=None,
                       now: datetime | None = None) -> dict:
    """Record a cross-model contrast run (fd_04_contrast is the instrument; this
    is the ledger authority). A deposit is PROVEN portable when at least one
    non-frontier substrate REPRODUCED the judgment; the achieved target is the
    CHEAPEST such substrate, because that is the rung the capability retires to.

    No substrate reproducing is not an error -- it is the measurement. It records
    FAILED, and that deposit is the round's frontier residue.
    """
    try:
        if not isinstance(results, list) or not results:
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": "no substrate results -- a contrast without a run is a claim"}
        if not _deposit_exists(repo, fingerprint, state_dir):
            return {"verdict": "ERROR", "fingerprint": fingerprint,
                    "note": "deposit not found in ledger"}

        order = {t: i for i, t in enumerate(("small-model", "mid-model"))}
        won = [r for r in results if r.get("verdict") == "REPRODUCED"
               and r.get("substrate") in order]
        won.sort(key=lambda r: order.get(r.get("substrate"), 99))
        achieved = won[0]["substrate"] if won else None

        rec = {"fingerprint": fingerprint,
               "verdict": "PROVEN" if won else "FAILED",
               "method": "cross_model",
               "achieved_target": achieved or "none",
               "probes": [], "results": results,
               "sid": sid, "ts": _now(now).isoformat()}
        _append_jsonl(_proofs_path(repo, state_dir), rec)
        _signal("fd_portability_proven" if won else "fd_portability_residue",
                {"fingerprint": fingerprint, "achieved_target": achieved or "none",
                 "method": "cross_model", "substrates": len(results)}, state_dir)
        return rec
    except Exception as e:  # noqa: BLE001 -- fail-closed: an error is never PROVEN
        return {"verdict": "ERROR", "fingerprint": fingerprint,
                "note": f"cross-model record error (fail-closed): "
                        f"{type(e).__name__}: {e}"}


# --------------------------------------------------------------------------- #
# recheck -- the replay + regression pipeline: re-run every stored probe set.
# --------------------------------------------------------------------------- #
def recheck(repo: str, state_dir=None) -> dict:
    """Re-execute the stored probes of every probe-PROVEN deposit. A probe that
    held at proof time and fails now flags its deposit as regressed.
    Attestations are skipped (nothing deterministic to replay)."""
    try:
        latest = _latest_by_fp(_read_jsonl(_proofs_path(repo, state_dir)))
        checked, ok_count, regressed = 0, 0, []
        for fp in sorted(latest):
            rec = latest[fp]
            if rec.get("verdict") != "PROVEN" or rec.get("method") != "probes":
                continue
            checked += 1
            alive = all(run_probe(_replay_spec(p), repo)[0]
                        for p in rec.get("probes") or [])
            if alive:
                ok_count += 1
            else:
                regressed.append(fp)
        out = {"checked": checked, "ok": ok_count, "regressed": regressed}
        _signal("fd_portability_recheck",
                {"checked": checked, "ok": ok_count,
                 "regressed_count": len(regressed)}, state_dir)
        return out
    except Exception as e:  # noqa: BLE001 -- fail-open on read, but say so
        return {"checked": 0, "ok": 0, "regressed": [],
                "note": f"recheck error: {type(e).__name__}: {e}"}


# --------------------------------------------------------------------------- #
# CLI -- PowerShell-safe: probes arrive via JSON file (BOM-tolerant), never argv.
# --------------------------------------------------------------------------- #
def _read_probes_json(src: str) -> list:
    if src == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(src).read_text(encoding="utf-8-sig", errors="replace")
    return json.loads(raw.lstrip("﻿"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="FD-04 portability prover")
    ap.add_argument("--repo", default=str(_PP_ROOT))
    ap.add_argument("--state-dir", default=None)
    ap.add_argument("--prove", metavar="FINGERPRINT")
    ap.add_argument("--probes-json", metavar="FILE|-",
                    help="JSON list of probe specs (utf-8, BOM tolerated)")
    ap.add_argument("--target", default="deterministic", choices=_TARGETS)
    ap.add_argument("--attest", metavar="FINGERPRINT")
    ap.add_argument("--substrate", choices=_TARGETS)
    ap.add_argument("--evidence", default="")
    ap.add_argument("--sid", default="")
    ap.add_argument("--recheck", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    if args.prove:
        probes = _read_probes_json(args.probes_json) if args.probes_json else []
        rec = prove(args.repo, args.prove, probes, achieved_target=args.target,
                    sid=args.sid, state_dir=args.state_dir)
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 0 if rec.get("verdict") == "PROVEN" else 1
    if args.attest:
        rec = attest(args.repo, args.attest, substrate=args.substrate or "",
                     evidence=args.evidence, sid=args.sid, state_dir=args.state_dir)
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 0 if rec.get("verdict") == "PROVEN" else 1
    if args.recheck:
        out = recheck(args.repo, state_dir=args.state_dir)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if not out["regressed"] else 1
    if args.list:
        latest = _latest_by_fp(_read_jsonl(_proofs_path(args.repo, args.state_dir)))
        print(json.dumps({fp: {"verdict": r.get("verdict"),
                               "method": r.get("method"),
                               "achieved_target": r.get("achieved_target"),
                               "ts": r.get("ts")}
                          for fp, r in sorted(latest.items())},
                         ensure_ascii=False, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
