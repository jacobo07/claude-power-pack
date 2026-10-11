"""A6 Proof of Non-Work + A5 per-unit economic receipt. Pure, deterministic, no model.

A claim PROVEN at a dependency fingerprint needs no worker while that fingerprint is unchanged.
The fingerprint is a sha256 over (path, content sha256) of every declared dependency. A missing
dependency, an empty dependency list or an unreadable proof ledger never yields NO_WORK: absence
is not proof, so the unit stays admissible and runs.

  ledger  = {"claims": {claim_id: {"status": "PROVEN", "fingerprint": hex, "deps": [paths]}}}
  route   = {..., "proof": {"claim": claim_id, "deps": [paths relative to root]}}
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
import os  # noqa: E402
LEDGER_PATH = Path(os.environ.get("CPP_CLAIM_LEDGER") or REPO_ROOT / "vault" / "config" / "claim-proofs.json")
RECEIPTS_PATH = Path(os.environ.get("CPP_UNIT_RECEIPTS") or REPO_ROOT / "vault" / "config" / "unit-receipts.jsonl")
PROVEN = "PROVEN"


def fingerprint(deps, root: Path | str | None = None) -> str | None:
    """sha256 over sorted (path, file sha256). None when deps is empty or any dep is not a file."""
    root = Path(root or REPO_ROOT)
    if not isinstance(deps, (list, tuple)) or not deps or not all(isinstance(d, str) and d for d in deps):
        return None
    h = hashlib.sha256()
    for d in sorted(set(deps)):
        p = root / d
        if not p.is_file():
            return None
        h.update(d.encode() + b"\0" + hashlib.sha256(p.read_bytes()).hexdigest().encode() + b"\n")
    return h.hexdigest()


def load_ledger(path: Path | str | None = None) -> dict:
    p = Path(path or LEDGER_PATH)
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {"claims": {}}
    return data if isinstance(data.get("claims"), dict) else {"claims": {}}


def record_proof(claim: str, deps, *, root=None, ledger_path=None, status: str = PROVEN) -> dict:
    fp = fingerprint(deps, root)
    if fp is None:
        raise ValueError("cannot prove a claim over missing or empty dependencies")
    p = Path(ledger_path or LEDGER_PATH)
    data = load_ledger(p)
    data["claims"][claim] = {"status": status, "fingerprint": fp, "deps": sorted(set(deps))}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data["claims"][claim]


def check(proof: dict | None, *, root=None, ledger_path=None) -> dict:
    """{"no_work": bool, "reason": str}. no_work only for PROVEN at the identical fingerprint."""
    if not isinstance(proof, dict) or not proof.get("claim"):
        return {"no_work": False, "reason": "no proof declared"}
    fp = fingerprint(proof.get("deps"), root)
    if fp is None:
        return {"no_work": False, "reason": "dependency fingerprint unknown (missing or empty deps)"}
    rec = load_ledger(ledger_path)["claims"].get(proof["claim"])
    if not rec or rec.get("status") != PROVEN:
        return {"no_work": False, "reason": f"claim {proof['claim']} is not PROVEN in the ledger"}
    if rec.get("fingerprint") != fp:
        return {"no_work": False, "reason": f"claim {proof['claim']} proven at a different fingerprint"}
    return {"no_work": True, "reason": f"claim {proof['claim']} PROVEN at unchanged fingerprint {fp[:12]}"}


def unit_claim(packet_path) -> dict:
    """The default proof of a compiled work unit: claim 'unit:<packet stem>' over the packet file."""
    p = Path(packet_path).expanduser().resolve()
    return {"claim": f"unit:{p.stem}", "deps": [str(p)]}


def populate_from_receipts(receipt_dir, *, ledger_path=None) -> list:
    """Deterministic ledger fill: every `<id>-receipt.md` whose line 2 is exactly `Status: DONE`, with
    its packet `<id>.md` beside it, becomes PROVEN over that packet. Anything else is skipped."""
    done = []
    for rc in sorted(Path(receipt_dir).glob("*-receipt.md")):
        try:
            lines = rc.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            continue
        pkt = rc.with_name(rc.name[: -len("-receipt.md")] + ".md")
        if len(lines) < 2 or lines[1].strip() != "Status: DONE" or not pkt.is_file():
            continue
        c = unit_claim(pkt)
        record_proof(c["claim"], c["deps"], ledger_path=ledger_path)
        done.append(c["claim"])
    return done


def unit_receipt(unit: str, *, calls: int, processed: int, tier: str, boundaries: int,
                 lower_bound: int | None) -> dict:
    """A5 economic receipt. Overhead is processed / lower_bound; None when either is unknown or <= 0
    (unknown spend is not zero, an unknown bound is not 1.0)."""
    for k, v in (("calls", calls), ("processed", processed), ("boundaries", boundaries)):
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError(f"{k} must be a non-negative integer")
    ov = None
    if isinstance(lower_bound, int) and not isinstance(lower_bound, bool) and lower_bound > 0 and processed > 0:
        ov = round(processed / lower_bound, 3)
    return {"unit": unit, "calls": calls, "processed": processed, "tier": tier,
            "semantic_boundaries": boundaries, "lower_bound": lower_bound, "overhead_multiplier": ov}
