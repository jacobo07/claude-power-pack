"""Reconciliation ledger (ASC-02) -- extends backlog_autopilot; consumes inventory.py identities.

One row per canonical obligation identity. Fields map onto CapabilityContract
(modules/capability_runtime/contract.py): owner, entrypoint, consumers, required_evidence
(tests + execution_evidence), retirement_condition (close_condition). State vocabulary is the
Owner law's own words (backlog != implementation != activation != execution), NOT a new
truth enum; EXECUTED/VERIFIED are assigned ONLY from recorded execution evidence, never
from static reading, so a static pass can never claim them.

  BACKLOG_ONLY    no implementation path exists for it
  SOURCE_FOUND    implementation path(s) exist; no entrypoint evidence
  IMPLEMENTED     path(s) + an entrypoint (main/CLI/command doc) + a test referencing it
  ACTIVATED       IMPLEMENTED + a code consumer outside its own dir/tests/docs. STATIC WIRING ONLY:
                  a source citing a path in passing can still reach it (measured noise, Phase 2
                  spot-check), so ACTIVATED never raises OPERATIONAL without execution evidence
  CLAIM_REJECTED  the source CLAIMS resolved/absorbed but no implementation path exists
                  (a name in a dataset, no code)
  UNKNOWN         unreadable / no signal

Two coverages, two fixed denominators (computed BEFORE any numerator):
  RECONCILIATION = rows whose state, owner and destination (next_action) are all proven
                   / ALL obligation rows
  OPERATIONAL    = applicable rows (claim a capability: have an implementation path or a
                   RESOLVED claim) that are ACTIVATED and carry execution evidence
                   / ALL applicable rows
BLOCKED rows stay in both denominators. Nothing is ever removed to raise a ratio.

CLI: python -m modules.backlog_autopilot.ledger [--root R] [--out F] [--verify]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from . import inventory as inv

PATH_RE = re.compile(r"(?<![\w/.-])((?:modules|tools|skills|commands|agents|hooks|vendor)/[\w./-]*[\w])")
CODE_SUFFIX = (".py", ".js", ".sh", ".cjs", ".ts")  # a doc or JSON mentioning a path is not a consumer
INDEX_DIRS = ("modules", "tools", "hooks", "commands", "agents", "skills")
STATES = ("BACKLOG_ONLY", "SOURCE_FOUND", "IMPLEMENTED", "ACTIVATED", "CLAIM_REJECTED", "UNKNOWN")
EVIDENCE_FILE = "vault/programs/ascension/phase2/execution_evidence.json"


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _section_text(root: Path, m: dict) -> str:
    if m["kind"] == "owner_queue":
        text = _read(root / m["source"])
        i = int(m["ref"].split("-")[1]) if m["ref"].startswith("section-") else 0
        parts = re.split(r"^##\s+", text, flags=re.M)
        return parts[i + 1] if i + 1 < len(parts) else ""
    if m["kind"] == "liveness_planned":
        return f"modules/{m['ref']}"
    if m["source"].endswith(".json"):
        return ""
    return _read(root / m["source"])


def build_code_index(root: Path) -> dict[str, str]:
    """relpath -> lowercase text, for consumer/test lookup. One pass; bounded file size."""
    idx: dict[str, str] = {}
    for d in INDEX_DIRS:
        for dp, dn, fn in os.walk(root / d):
            dn[:] = [x for x in dn if x not in (".git", "node_modules", "__pycache__")]
            for n in fn:
                if n.endswith(CODE_SUFFIX):
                    p = Path(dp, n)
                    try:
                        if p.stat().st_size <= 600_000:
                            idx[p.relative_to(root).as_posix()] = p.read_text(
                                encoding="utf-8", errors="ignore").lower()
                    except OSError:
                        pass
    return idx


def _impl_paths(root: Path, text: str) -> list[str]:
    out = []
    for m in PATH_RE.finditer(text):
        t = m.group(1).rstrip(".")
        for cand in (t, t + ".py"):
            if (root / cand).exists() and cand not in out:
                out.append(cand)
                break
    return out[:12]


def _mentions(txt: str, stem: str, dotted: str) -> bool:
    """Path or dotted import as a whole token (not a prefix of a longer name)."""
    for needle in (stem, dotted):
        i = txt.find(needle)
        while i != -1:
            j = i + len(needle)
            if j >= len(txt) or not (txt[j].isalnum() or txt[j] == "_"):
                return True
            i = txt.find(needle, i + 1)
    return False


def _is_test(rel: str) -> bool:
    b = rel.rsplit("/", 1)[-1]
    return b.startswith("test_") or ".test." in b or "/tests/" in rel


def _probe(root: Path, row_members: list[dict], idx: dict, evidence: dict) -> dict:
    texts = [_section_text(root, m) for m in row_members]
    claimed = {m["state"] for m in row_members}
    impls = sorted({p for t in texts for p in _impl_paths(root, t)})
    own_srcs = {m["source"] for m in row_members}
    if "UNREADABLE" in claimed:
        return {"state": "UNKNOWN", "owner": None, "impl": [], "entrypoint": None, "consumers": [],
                "tests": [], "claimed": sorted(claimed)}
    stems = {p: (p[:-3] if p.endswith(".py") else p) for p in impls}
    tests, consumers, entry = [], [], None
    for p, stem in stems.items():
        dotted = stem.replace("/", ".")
        pdir = p.rsplit("/", 1)[0] + "/" if "/" in p else ""
        body = idx.get(p, "")
        if os.path.isfile(root / p) and (
                "__main__" in body or "def main(" in body or p.startswith(("commands/", "hooks/"))
                or p.startswith("skills/")):
            entry = entry or p
        for rel, txt in idx.items():
            if rel == p or rel in own_srcs:
                continue
            if _mentions(txt, stem.lower(), dotted.lower()):
                if _is_test(rel):
                    tests.append(rel)
                elif not rel.startswith(pdir):
                    consumers.append(rel)
    tests, consumers = sorted(set(tests))[:8], sorted(set(consumers))[:8]
    claims_done = "RESOLVED" in claimed
    if not impls:
        state = "CLAIM_REJECTED" if claims_done else "BACKLOG_ONLY"
    elif entry and tests and consumers:
        state = "ACTIVATED"
    elif entry and tests:
        state = "IMPLEMENTED"
    else:
        state = "SOURCE_FOUND"
    owner = None
    if impls:
        parts = impls[0].split("/")
        owner = "/".join(parts[:2]) if parts[0] in ("modules", "vendor") and len(parts) > 2 else parts[0] + "/" + parts[1] if len(parts) > 1 else parts[0]
    return {"state": state, "owner": owner, "impl": impls, "entrypoint": entry,
            "consumers": consumers, "tests": tests, "claimed": sorted(claimed)}


_NEXT = {
    "BACKLOG_ONLY": "decide REUSE/EXTEND/MERGE/CONNECT/GENERALIZE/BUILD against an existing owner; do not announce available",
    "SOURCE_FOUND": "add an entrypoint and a test that drives it from both poles",
    "IMPLEMENTED": "connect a real consumer, then record execution evidence",
    "ACTIVATED": "record execution evidence from a real run",
    "CLAIM_REJECTED": "source claims done but no implementation path exists: re-open, or cite the code that closes it",
    "UNKNOWN": "make the source readable, then re-run",
}


def build(root: Path, inventory: dict | None = None) -> dict:
    root = Path(root)
    inventory = inventory or inv.build(root)
    idx = build_code_index(root)
    ev_p = root / EVIDENCE_FILE
    try:
        evidence = json.loads(ev_p.read_text(encoding="utf-8")) if ev_p.is_file() else {}
    except (OSError, ValueError):
        evidence = {}
    rows = []
    for ident in inventory["identities"]:
        if ident["group"] != "obligation":
            continue
        pr = _probe(root, ident["members"], idx, evidence)
        ev = evidence.get(ident["id"])
        blocked = any(re.search(r"BLOCKED", m["title"], re.I) for m in ident["members"])
        row = {
            "id": ident["id"], "title": ident["title"], "provenance": [m["source"] for m in ident["members"]],
            "kinds": ident["kinds"], "claimed_states": pr["claimed"], "state": pr["state"],
            "owner": pr["owner"], "implementation": pr["impl"], "entrypoint": pr["entrypoint"],
            "consumers": pr["consumers"], "tests": pr["tests"],
            "execution_evidence": ev if (ev and ev.get("exit") == 0) else None,
            "license": "UNKNOWN", "blocked": blocked, "next_action": _NEXT[pr["state"]],
            "close_condition": ("claim cites existing code + gate" if pr["state"] != "BACKLOG_ONLY"
                                else "implementation or retirement recorded by Owner"),
        }
        rows.append(row)
    return {"schema": 1, "basis": "static-reference (paths cited by the source, code-file consumers); "
            "execution evidence only from " + EVIDENCE_FILE, "rows": rows, **coverage(rows)}


def _applicable(r: dict) -> bool:
    return bool(r["implementation"]) or "RESOLVED" in r["claimed_states"]


def coverage(rows: list[dict]) -> dict:
    n_all = len(rows)
    # state, owner AND destination must all be proven. A row with no implementation path has a
    # proven STATE but no owner, so it is NOT reconciled until an owner decision is recorded.
    recon = [r for r in rows if r["state"] != "UNKNOWN" and r["owner"] is not None and r["next_action"]]
    app = [r for r in rows if _applicable(r)]
    op = [r for r in app if r["state"] == "ACTIVATED" and r["execution_evidence"]]
    by = {s: sum(1 for r in rows if r["state"] == s) for s in STATES}
    return {
        "reconciliation": {"numerator": len(recon), "denominator": n_all,
                           "ratio": round(len(recon) / n_all, 4) if n_all else None},
        "operational": {"numerator": len(op), "denominator": len(app),
                        "ratio": round(len(op) / len(app), 4) if app else None},
        "by_state": by,
        "blocked_in_denominator": sum(1 for r in rows if r["blocked"]),
    }


def verify(led: dict, inventory: dict) -> list[str]:
    """[] == PASS. A row dropped from the ledger (denominator shrink) or a ratio that disagrees
    with its own rows fails; so does a ledger row claiming an unprovable state."""
    fails = []
    want = {i["id"] for i in inventory["identities"] if i["group"] == "obligation"}
    got = {r["id"] for r in led["rows"]}
    fails += [f"DROPPED: {x}" for x in sorted(want - got)]
    fails += [f"UNKNOWN_ID: {x}" for x in sorted(got - want)]
    if led["reconciliation"]["denominator"] != len(want):
        fails.append("DENOMINATOR: reconciliation != obligation identities")
    again = coverage(led["rows"])
    if again["reconciliation"] != led["reconciliation"] or again["operational"] != led["operational"]:
        fails.append("RATIO: stored coverage disagrees with rows")
    for r in led["rows"]:
        if r["state"] == "ACTIVATED" and not (r["entrypoint"] and r["tests"] and r["consumers"]):
            fails.append(f"UNPROVEN_ACTIVATED: {r['id']}")
        if r["state"] in ("IMPLEMENTED", "SOURCE_FOUND", "ACTIVATED") and not r["implementation"]:
            fails.append(f"NO_IMPL: {r['id']} {r['state']}")
        if r["state"] == "BACKLOG_ONLY" and "RESOLVED" in r["claimed_states"]:
            fails.append(f"FALSE_ABSORPTION_ACCEPTED: {r['id']}")
    return fails


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    inventory = inv.build(root)
    led = build(root, inventory)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(led, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RECONCILIATION {led['reconciliation']}  OPERATIONAL {led['operational']}")
    print(f"by_state {led['by_state']} blocked={led['blocked_in_denominator']}")
    if a.verify:
        f = verify(led, inventory)
        for x in f[:20]:
            print(x)
        print("VERIFY", "FAIL" if f else "PASS")
        return 1 if f else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
