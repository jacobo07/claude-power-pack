"""One reading of a work-unit receipt, shared by every layer that decides whether a unit closed.

    from receipt_judge import receipt_status, is_closed, is_done

Before APR-1 three parsers read the same file three ways (gsdx_chain.receipt_status, gsd_mission._receipt_present,
gsd_mission.receipt_complete). A receipt with no `Status:` line was "present" to the mission layer (worker COMPLETED,
halt-continue skipped) and UNREADABLE to the chain (unit not done), so nobody owned the unit: EWC K5, 2026-10-11.

receipt_status(path) ->
    None            file absent
    "STUB"          the title block (first 3 lines) says stub, whatever its Status line says
    "UNREADABLE"    the file exists but carries no status (JSON `status` or a line-leading `Status:`)
    "IN_PROGRESS"   `Status: IN PROGRESS` / `IN_PROGRESS` / `WIP`
    otherwise the first status word, upper-cased: DONE, DONE_WITH_LIMITS, PARTIAL, BLOCKED_HUMAN, FAILED, ...
    "DIVERGENT"     a certificate sidecar (`<receipt>.certificate.json`, written by tools/claim_evidence.py from a
                    deterministic command) disagrees with the receipt's `Claims:` or `Status:` (D28 Ph1a). Worker prose
                    said 14 MATCH, the ledger said 12: the certified value wins and the unit is not closed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# line-leading, tolerant of list/quote/bold decoration: "Status: DONE", "- **Status:** DONE", "> Status: **DONE**"
_VALUE = r"Status[ \t]*\**[ \t]*:[ \t]*[*_ \t]*([A-Za-z][A-Za-z_]*)(?:[ \t]+([A-Za-z]+))?"
_LINE = re.compile(r"^[ \t>*_\-|]*" + _VALUE, re.M | re.I)
# real receipts also say it mid-sentence ("Mission: m-x. Status: DONE, local half only"): fallback, word-bounded
_ANY = re.compile(r"(?<![A-Za-z])" + _VALUE, re.I)
_STUB = re.compile(r"\bstub\b", re.I)
IN_PROGRESS = {"IN", "IN_PROGRESS", "INPROGRESS", "WIP"}
# a worker that wrote one of these has NOT closed its unit: the mission layer must treat it as no receipt
NOT_CLOSED = {None, "UNREADABLE", "STUB", "PARTIAL", "IN_PROGRESS", "DIVERGENT"}
# "Claims: match=12, sent=22" -- the numbers a worker asserts, in a form a certificate can be compared against
_CLAIMS = re.compile(r"^[ \t>*_\-|]*Claims[ \t]*\**[ \t]*:[ \t]*\**(.+)$", re.M | re.I)
_PAIR = re.compile(r"([A-Za-z][A-Za-z0-9_.]*)[ \t]*=[ \t]*([^;\s]+)")  # "4,388,094" stays one value
DIVERGENCE = "CLAIM_EVIDENCE_DIVERGENCE"


def status_of_text(text: str) -> str:
    if _STUB.search("\n".join(text.splitlines()[:3])):
        return "STUB"
    s = None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            s = str(obj.get("status", "")).strip()
            m = re.match(r"([A-Za-z][A-Za-z_]*)", s)
            s = m.group(1).upper() if m else None
    except ValueError:
        m = _LINE.search(text) or _ANY.search(text)
        if m:
            s = m.group(1).upper()
            if s == "IN" and (m.group(2) or "").upper() == "PROGRESS":
                s = "IN_PROGRESS"
    if not s:
        return "UNREADABLE"
    return "IN_PROGRESS" if s in IN_PROGRESS else s


def claims_of_text(text: str) -> dict:
    out = {}
    for line in _CLAIMS.findall(text):
        for k, v in _PAIR.findall(line):
            out[k.lower()] = v.strip("*_`,.")
    return out


def certificate_path(path) -> Path:
    return Path(str(path) + ".certificate.json")


def _norm(v) -> str:
    s = str(v).strip().lower()
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    try:
        f = float(s)
        return repr(int(f)) if f == int(f) else repr(f)
    except ValueError:
        return s


def divergences(path) -> list:
    """Typed rows, one per claimed value the certificate contradicts (and the status, when the certificate has one).
    No certificate = nothing is certified = no divergence can be stated (the receipt is read as before)."""
    p, cp = Path(path), certificate_path(path)
    if not p.exists() or not cp.exists():
        return []
    try:
        cert = json.loads(cp.read_text(encoding="utf-8-sig"))
        values = {str(k).lower(): v for k, v in (cert.get("values") or {}).items()}
    except (OSError, ValueError, AttributeError):
        return [{"class": DIVERGENCE, "key": "certificate", "claim": None, "certified": "UNREADABLE"}]
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    rows = [{"class": DIVERGENCE, "key": k, "claim": v, "certified": values[k]}
            for k, v in sorted(claims_of_text(text).items()) if k in values and _norm(v) != _norm(values[k])]
    cs = values.get("status")
    if cs is not None and str(cs).upper() != status_of_text(text):
        rows.append({"class": DIVERGENCE, "key": "status", "claim": status_of_text(text), "certified": str(cs).upper()})
    return rows


def receipt_status(path) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return "UNREADABLE"
    s = status_of_text(text)
    if s not in ("STUB", "UNREADABLE") and divergences(p):
        return "DIVERGENT"
    return s


def is_closed(path) -> bool:
    """The worker gave the unit an explicit verdict (DONE, BLOCKED_HUMAN, FAILED, ...): do not renew it as unfinished."""
    return receipt_status(path) not in NOT_CLOSED


def is_done(path) -> bool:
    return receipt_status(path) == "DONE"
