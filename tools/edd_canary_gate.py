#!/usr/bin/env python3
"""Master Done-Gate for the EDD compiled-execution canary (vault/specs/edd-compiled-execution-canary.md).

Exits 0 only when every check below observed its evidence. A check that could not look
(missing file, unreadable record, command not run) FAILS -- absence is never a pass.

The canary's spend is MEASURED here from the transcripts (tools/mission_spend.py over the
mission record), never read from the worker's receipt: a self-reported figure is a claim.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
WS = ROOT / ".planning/workstreams/edd"
STATE = Path.home() / ".claude/state"
OLD = "m-ee81e1595007"
TRIP = 12_000_000
STATUSES = {"ALREADY_IMPLEMENTED", "UNDER_ANOTHER_NAME", "PARTIAL", "DOCUMENTED_ONLY", "DATASET_ONLY",
            "REGISTERED_UNREACHABLE", "REACHABLE_NOT_EFFECTIVE", "NEW", "NOT_A_SYSTEM"}
NEEDS_REFS = {"ALREADY_IMPLEMENTED", "UNDER_ANOTHER_NAME", "PARTIAL", "REGISTERED_UNREACHABLE",
              "REACHABLE_NOT_EFFECTIVE"}
REF = re.compile(r"`?([\w./\-]+\.[A-Za-z]{1,5}):(\d+)`?")

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, bool(ok), detail))


def load_record(mid: str) -> dict | None:
    p = STATE / f"gsd-mission-{mid}.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text(encoding="utf-8"))
    return r.get("mission", r)


def matrix_rows(text: str) -> dict[str, dict]:
    rows = {}
    for ln in text.splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 5 and re.fullmatch(r"C-\d{2}", cells[0]):
            rows[cells[0]] = {"status": cells[2].strip("` *"), "producer": cells[3], "consumer": cells[4],
                              "raw": ln}
    return rows


def ref_resolves(ref: str) -> bool:
    m = REF.search(ref)
    if not m:
        return False
    p = ROOT / m.group(1)
    if not p.is_file():
        return False
    with p.open(encoding="utf-8", errors="replace") as fh:
        return int(m.group(2)) <= sum(1 for _ in fh)


def main() -> int:
    from gsd_dossier import concepts_from_contract
    receipt_p = WS / "canary/RECEIPT.json"
    receipt = json.loads(receipt_p.read_text(encoding="utf-8")) if receipt_p.exists() else None
    check("G0 receipt exists", receipt is not None, str(receipt_p))
    receipt = receipt or {}

    old = load_record(OLD)
    check("G1 old mission halted", bool(old) and old.get("state") == "HALTED",
          f"{OLD} state={old and old.get('state')}")
    canary_id = receipt.get("mission_id")
    rec = load_record(canary_id) if canary_id else None
    check("G1 canary envelope bounded", bool(rec) and bool(rec.get("token_estimate")),
          f"{canary_id} token_estimate={rec and rec.get('token_estimate')}")

    concepts = concepts_from_contract((WS / "source/MISSION_PROMPT.md").read_text(encoding="utf-8"))
    mp = WS / "OWNERSHIP_MATRIX.md"
    mtext = mp.read_text(encoding="utf-8") if mp.exists() else ""
    rows = matrix_rows(mtext)
    missing = [c["id"] for c in concepts if c["id"] not in rows]
    check("G2 every concept has a row", bool(concepts) and not missing,
          f"{len(concepts)} concepts, missing {missing[:10]}")
    bad_status = [k for k, r in rows.items() if r["status"] not in STATUSES]
    check("G2 statuses in vocabulary", bool(rows) and not bad_status, f"bad {bad_status[:10]}")
    unresolved = [k for k, r in rows.items() if r["status"] in NEEDS_REFS
                  and not (ref_resolves(r["producer"]) and ref_resolves(r["consumer"]))]
    check("G3 producer+consumer refs resolve", bool(rows) and not unresolved, f"unresolved {unresolved[:10]}")
    new_rows = [k for k, r in rows.items() if r["status"] == "NEW"]
    no_proof = [k for k in new_rows if not re.search(rf"^#+\s*13Q\s+{k}\b", mtext, re.M)]
    check("G4 NEW rows carry 13Q proof", not no_proof, f"NEW={new_rows} without proof={no_proof}")

    spec = ROOT / "vault/specs/edd.md"
    stext = spec.read_text(encoding="utf-8") if spec.exists() else ""
    check("G5 spec with covers", bool(re.search(r"^covers:\s*\[[^\]]+\]", stext, re.M)), str(spec))

    spent = None
    if rec:
        import mission_spend
        spent = mission_spend.processed_tokens(rec)
    check("G6 measured canary spend <= trip", spent is not None and spent <= TRIP,
          f"measured={spent} trip={TRIP} self_reported={receipt.get('processed_tokens')}")
    reasons = receipt.get("boundaries") or []
    check("G6 every boundary has a reason", bool(reasons) and all(b.get("reason") for b in reasons),
          f"{len(reasons)} boundaries")

    rf = WS / "canary/REFORECAST.md"
    rtext = rf.read_text(encoding="utf-8").lower() if rf.exists() else ""
    check("G7 reforecast low/central/high", all(w in rtext for w in ("low", "central", "high")), str(rf))
    learn = receipt.get("learning_paths") or []
    absent = [p for p in learn if not (ROOT / p).exists()]
    check("G8 KV/UKDL/CBR entries exist", bool(learn) and not absent, f"{len(learn)} paths, absent {absent}")

    # Liveness of the new tools. modules/liveness/reachability.py scans modules/ only, so it can
    # never see tools/ -- a check through it would pass by construction. The real consumer
    # chain is: gsd_dossier produced the dossier, the packet names it, the worker read it.
    summ = WS / "canary/dossier/dossier.summary.json"
    packet = WS / "canary/WU-1.md"
    read = receipt.get("pages_read") or []
    check("G9 dossier produced, named by packet, consumed by worker",
          summ.exists() and packet.exists() and "dossier.md" in packet.read_text(encoding="utf-8")
          and any("dossier.md" in str(x) for x in read),
          f"summary={summ.exists()} packet={packet.exists()} pages_read={len(read)}")

    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}  -- {detail}")
    passed = sum(ok for _, ok, _ in results)
    print(f"EDD_CANARY_GATE={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
