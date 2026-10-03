#!/usr/bin/env python
"""test_listing_floor_verdict.py -- pillar B verdict gate (skill-capability, SC-B, decision D-04).

    python3 tools/test_listing_floor_verdict.py                  # check (default mode)
    python3 tools/test_listing_floor_verdict.py --jsonl PATH     # verdict clauses on one jsonl only
    python3 tools/test_listing_floor_verdict.py --json           # derived figures as one JSON object
    python3 tools/test_listing_floor_verdict.py --write-evidence # render the D-LISTING measurement file

What it reads: wiki/tools/listing_floor_probe.results.jsonl (rows selected BY LABEL, never by
position or count; the probe appends, so the file grows) and the frozen D-LISTING denominator in
vault/programs/skill-capability/ledger.json (read only, never written). Nothing is typed in: the K4
verdict is recomputed from the rows `champion-startup` / `challenger-startup`.

Verdict (K4 falsification of "hide listing entries behind a gateway"):
  V-LF-TOKENS  challenger startup_tokens >= champion startup_tokens (model-visible, primary).
  V-LF-CAP     challenger listing chars >= cap - band. cap = D-LISTING.listing_chars_cap and
               band = floor(cap * CAP_BIND_FRACTION), CAP_BIND_FRACTION = 0.01. Claude's discretion
               per CONTEXT: within 1% of its cap a listing is still cap-bound; V-LF-TOKENS carries
               the falsification on its own.

Output lines: `  ok   V-LF-X <evidence>` / `  FAIL V-LF-X <diagnostic>` / `  INCONCLUSIVE V-LF-X <why>`,
last line `LF_PASS=<passed>/<total>`. Exit codes: 0 pass, 1 fail or inconclusive, 2 could not run.
INCONCLUSIVE is never a pass: a gate that could not read its source must not look green.

The planes: the rows are laptop fresh-session readings (derived from their Windows cwd); this
script's derivation is host-independent and consumes no session. GEX44 is a different install, so
nothing here is a GEX44 listing measurement.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSONL_REL = "wiki/tools/listing_floor_probe.results.jsonl"
LEDGER_REL = "vault/programs/skill-capability/ledger.json"
EVIDENCE_REL = "vault/programs/skill-capability/evidence/B-listing-floor.md"
SELF_REL = "tools/test_listing_floor_verdict.py"

K4_LABELS = ("R2R1", "R3", "champion-startup", "challenger-startup")
CAP_BIND_FRACTION = 0.01


# --------------------------------------------------------------------------- sources


def load_rows(path) -> list:
    """Parse one JSON object per line. Raises OSError / ValueError; callers turn that into INCONCLUSIVE."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise ValueError(f"{path}:{n} is not JSON ({exc})")
    return rows


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def k4_arms(rows):
    """Select the two startup arms by label. Returns (arms, refusal); exactly one is None."""
    arms = {}
    for key, label in (("champion", "champion-startup"), ("challenger", "challenger-startup")):
        hits = [r for r in rows if isinstance(r, dict) and r.get("label") == label]
        if len(hits) != 1:
            return None, f"label {label} appears {len(hits)} times (need exactly 1)"
        row = hits[0]
        listing = row.get("listing")
        if not isinstance(listing, dict):
            return None, f"{label}: listing is not an object ({str(listing)[:60]!r})"
        if not _is_int(listing.get("chars")):
            return None, f"{label}: listing.chars is not an int"
        if not _is_int(row.get("startup_tokens")):
            return None, f"{label}: startup_tokens is not an int"
        arms[key] = row
    return arms, None


def frozen() -> dict:
    """The frozen object of the ledger. Read only."""
    return json.loads((REPO / LEDGER_REL).read_text(encoding="utf-8"))["frozen"]


def band_of(cap: int) -> int:
    return int(math.floor(cap * CAP_BIND_FRACTION))


# --------------------------------------------------------------------------- clauses
# every clause returns (status, text); status in ok | FAIL | INCONCLUSIVE


def clause_tokens(arms):
    champ, chall = arms["champion"]["startup_tokens"], arms["challenger"]["startup_tokens"]
    delta = chall - champ
    text = f"challenger startup_tokens {chall} vs champion {champ} (delta {delta:+d})"
    if delta >= 0:
        return "ok", text + ": not below champion"
    return "FAIL", text + ": challenger is below champion, the floor fell"


def clause_cap(arms, denoms):
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    band = band_of(cap)
    chars = arms["challenger"]["listing"]["chars"]
    gap = cap - chars
    text = f"challenger listing chars {chars}, cap {cap}, gap {gap} chars ({gap / cap * 100:.2f}% of cap), band {band}"
    if chars >= cap - band:
        return "ok", text + ": still cap-bound"
    return "FAIL", text + ": listing is meaningfully below the cap"


def evaluate_core(rows, denoms):
    """V-LF-SOURCES, V-LF-TOKENS, V-LF-CAP. Returns (results, arms)."""
    arms, refusal = k4_arms(rows)
    if refusal:
        return [("V-LF-SOURCES", "INCONCLUSIVE", refusal),
                ("V-LF-TOKENS", "INCONCLUSIVE", "no arms"),
                ("V-LF-CAP", "INCONCLUSIVE", "no arms")], None
    res = [("V-LF-SOURCES", "ok", "champion-startup and challenger-startup resolved, one row each")]
    res.append(("V-LF-TOKENS",) + clause_tokens(arms))
    res.append(("V-LF-CAP",) + clause_cap(arms, denoms))
    return res, arms


def verdict_of(results) -> str:
    st = {n: s for n, s, _ in results}
    if "FAIL" in (st.get("V-LF-TOKENS"), st.get("V-LF-CAP")):
        return "NOT_FALSIFIED"
    if st.get("V-LF-TOKENS") == "ok" and st.get("V-LF-CAP") == "ok":
        return "FALSIFIED"
    return "INCONCLUSIVE"


# --------------------------------------------------------------------------- render


def sessions_host(arms) -> str:
    cwds = [arms[k].get("cwd") or "" for k in ("champion", "challenger")]
    return "laptop" if all(c.startswith("C:\\Users\\User\\") for c in cwds) else "host unknown"


def row_by_label(rows, label):
    hits = [r for r in rows if isinstance(r, dict) and r.get("label") == label]
    return hits[0] if len(hits) == 1 else None


def command_for(row) -> str:
    cmd = f"python wiki/tools/listing_floor_probe.py --label {row['label']}"
    if row.get("settings_file"):
        cmd += f" --settings-file {row['settings_file']}"
    if row.get("cwd"):
        cmd += f" --cwd {row['cwd']}"
    return cmd + " --prompt <not recorded in the row>"


def render(rows, denoms, fro) -> str:
    """Pure and deterministic: no timestamps, no host, no HEAD sha, nothing that depends on the
    total row count of the live (append-only) jsonl."""
    results, arms = evaluate_core(rows, denoms)
    if arms is None:
        raise ValueError(results[0][2])
    cap = denoms["D-LISTING"]["listing_chars_cap"]
    rule = next(p["rule"] for p in fro["pillars"] if p["id"] == "B")
    L = []
    L.append("# [B] listing floor -- D-LISTING measurement")
    L.append("")
    L.append(f"Planes: sessions host `{sessions_host(arms)}` (derived: both arms' `cwd` start with "
             "`C:\\Users\\User\\`); derivation host-independent (this file is rendered from committed rows by "
             f"`{SELF_REL}`, nothing typed in).")
    L.append("")
    L.append("Frozen pillar B rule (ledger, quoted):")
    L.append("")
    L.append(f"> {rule}")
    L.append("")
    L.append("## Arms (fresh-session first-call figures, one session each)")
    L.append("")
    L.append("| label | session_id | ts | cwd | settings_file | listing chars | startup_tokens |")
    L.append("|---|---|---|---|---|---|---|")
    for k in ("champion", "challenger"):
        r = arms[k]
        L.append(f"| {r['label']} | {r.get('session_id')} | {r.get('ts')} | {r.get('cwd')} | "
                 f"{r.get('settings_file')} | {r['listing']['chars']} | {r['startup_tokens']} |")
    L.append("")
    L.append("## Verdict (recomputed from the rows)")
    L.append("")
    for n, s, t in results:
        L.append(f"- {s} {n}: {t}")
    L.append(f"- verdict: {verdict_of(results)} (frozen cap {cap}, band {band_of(cap)})")
    L.append("")
    L.append("## Commands")
    L.append("")
    for label in K4_LABELS:
        row = row_by_label(rows, label)
        L.append(f"command: {command_for(row)}" if row else f"- row {label} absent")
    L.append("command: python3 tools/test_listing_floor_verdict.py   (check; `python` on the laptop)")
    L.append("command: python3 tools/test_listing_floor_verdict.py --write-evidence   (render this file)")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- driver


def emit(results) -> int:
    passed = 0
    for name, status, text in results:
        print(f"  {status:<4} {name} {text}")
        passed += status == "ok"
    print(f"LF_PASS={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


def default_results(rows, denoms, fro):
    results, arms = evaluate_core(rows, denoms)
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jsonl", help="evaluate the verdict clauses on this jsonl only")
    ap.add_argument("--json", action="store_true", help="print the derived figures as JSON")
    ap.add_argument("--write-evidence", action="store_true", help=f"render {EVIDENCE_REL}")
    args = ap.parse_args(argv)
    try:
        fro = frozen()
        denoms = fro["denominators"]
        denoms["D-LISTING"]["listing_chars_cap"]
    except (OSError, ValueError, KeyError) as exc:
        print(f"LF_VERDICT=COULD_NOT_RUN frozen ledger unreadable: {exc}")
        return 2
    path = args.jsonl or str(REPO / JSONL_REL)
    try:
        rows = load_rows(path)
    except (OSError, ValueError) as exc:
        return emit([("V-LF-SOURCES", "INCONCLUSIVE", str(exc))])
    if args.write_evidence:
        try:
            text = render(rows, denoms, fro)
        except ValueError as exc:
            print(f"cannot render: {exc}")
            return 1
        out = REPO / EVIDENCE_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {EVIDENCE_REL} ({len(text)} chars)")
        return 0
    if args.jsonl:
        results, _ = evaluate_core(rows, denoms)
        return emit(results)
    return emit(default_results(rows, denoms, fro))


if __name__ == "__main__":
    sys.exit(main())
