"""Obligation inventory (ASC-01) -- extends backlog_autopilot, adds no parallel system.

Obligations are DISCOVERED by walking what exists, never curated by hand
(PR-COVERAGE-BY-CONSTRUCTION-001). Every discovered source file/entry becomes a
raw record; raw records collapse into canonical identities by a normalised-title
fingerprint. Nothing is dropped: a duplicate is a member of an identity, an
unreadable source is an explicit UNREADABLE record, a seed that matches nothing is
reported NOT_OBSERVED/REFERENCED_ELSEWHERE (never silently absent).

Epistemic discipline: `state` is only what the source text itself says
(RESOLVED / OPEN-by-marker / UNKNOWN). The inventory never claims IMPLEMENTED.

CLI: python -m modules.backlog_autopilot.inventory [--root R] [--out F] [--verify]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = 1
_STOP = frozenset(
    "a an the of to and or for in on with from by at as is be this that remaining "
    "followups followup absorption plan phase mission backlog md".split())

# Seeds named by the Owner prompt: each must resolve to >=1 discovered record.
SEEDS: dict[str, tuple[str, ...]] = {
    "taste-skill": ("taste",),
    "meta-astryx": ("astryx",),
    "brand-identity-logos": ("brand-identity", "brand identity"),
    "21-design-resources": ("21-design-resources", "21 design resources"),
    "animejs": ("animejs", "anime.js"),
    "synsation-ux": ("synsation",),
    "ui-ux-pro-max": ("ui-ux-pro-max", "ui/ux pro max"),
    "addy-osmani-agent-skills": ("addyosmani", "addy osmani"),
    "design-index": ("design index", "design-index"),
    "ccf": ("ccf",),
}


def _fp_tokens(title: str) -> frozenset[str]:
    t = re.sub(r"^\d{4}-\d{2}-\d{2}[_ -]*", "", title.lower())
    toks = re.findall(r"[a-z0-9]+", t)
    return frozenset(x for x in toks if x not in _STOP and len(x) > 1)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines()[:40]:
        m = re.match(r"#{1,3}\s+(.+)", line)
        if m:
            return m.group(1).strip()
    return fallback


def _state_of(text: str) -> str:
    head = text[:1500]
    if re.search(r"\[RESOLVED[^\]]*\]|\bStatus:\s*(DONE|COMPLETE|RESOLVED|CLOSED)", head, re.I):
        return "RESOLVED"
    if re.search(r"\bStatus:\s*(PENDING|OPEN|APPROVED|PLANNED|BLOCKED|PARTIAL)", head, re.I):
        return "OPEN"
    return "UNKNOWN"


def _rec(kind: str, path: str, title: str, state: str, ref: str = "") -> dict:
    return {"kind": kind, "source": path, "ref": ref, "title": title, "state": state}


def _read(p: Path):
    try:
        return p.read_text(encoding="utf-8", errors="replace"), None
    except OSError as e:  # explicit, never silent
        return None, str(e)


def discover(root: Path) -> list[dict]:
    """Raw records from every source family. Deterministic order."""
    root = Path(root)
    recs: list[dict] = []

    def rel(p: Path) -> str:
        return p.relative_to(root).as_posix()

    def files(pattern: str):
        return sorted({p for p in root.glob(pattern) if p.is_file()})

    # file-per-obligation families
    for kind, pats in (
        ("backlog", ["vault/backlog/*.md", "vault/backlog/*.patch"]),
        ("plan", ["vault/plans/*.md"]),
        ("audit", ["vault/audits/*.md"]),
        ("handoff", ["vault/handoffs/*.md"]),
        ("resumption", ["RESUMPTION*.md", "vault/programs/**/RESUMPTION*.md"]),
    ):
        for pat in pats:
            for p in files(pat):
                text, err = _read(p)
                if text is None:
                    recs.append(_rec(kind, rel(p), p.stem, "UNREADABLE", err or ""))
                    continue
                if p.suffix == ".patch":
                    recs.append(_rec(kind, rel(p), p.stem, "UNKNOWN"))
                else:
                    recs.append(_rec(kind, rel(p), _first_heading(text, p.stem),
                                     _state_of(text)))

    # OWNER_QUEUE: one obligation per `## ` section
    oq = root / "vault/OWNER_QUEUE.md"
    if oq.is_file():
        text, err = _read(oq)
        if text is None:
            recs.append(_rec("owner_queue", rel(oq), "OWNER_QUEUE", "UNREADABLE", err or ""))
        else:
            for i, m in enumerate(re.finditer(r"^##\s+(.+)$", text, re.M)):
                h = m.group(1).strip()
                st = "RESOLVED" if re.search(r"\[RESOLVED", h, re.I) else "OPEN"
                recs.append(_rec("owner_queue", rel(oq), h, st, f"section-{i}"))

    # liveness registry: PLANNED entries are standing obligations
    reg = root / "vault/liveness/reachability_registry.json"
    if reg.is_file():
        try:
            mods = json.loads(reg.read_text(encoding="utf-8")).get("modules", {})
            for name, v in sorted(mods.items()):
                cls = v.get("class") if isinstance(v, dict) else None
                if cls == "PLANNED":
                    recs.append(_rec("liveness_planned", rel(reg), name, "OPEN", name))
        except (OSError, ValueError) as e:
            recs.append(_rec("liveness_planned", rel(reg), "registry", "UNREADABLE", str(e)))

    # capability SUPPLY (not obligations): skills, vendor skills, commands, agents
    for kind, pat in (("skill", "skills/*"), ("vendor_skill", "vendor/skills/*"),
                      ("command", "commands/*.md"), ("agent", "agents/*.md"),
                      ("agent", ".claude/agents/*.md")):
        for p in sorted(root.glob(pat)):
            if p.name.startswith(".") or p.name in ("README.md", "NOTICE.md"):
                continue
            recs.append(_rec(kind, rel(p), p.stem if p.is_file() else p.name, "UNKNOWN"))
    return recs


def canonicalise(recs: list[dict], threshold: float = 0.85) -> list[dict]:
    """Collapse raw records to canonical identities. Same kind-group only.

    Obligations (backlog/plan/audit/handoff/resumption/owner_queue/liveness) share one
    group so a backlog item and its plan collapse; capability supply never merges with
    obligations. Greedy single-link on Jaccard of normalised title tokens."""
    group_of = lambda k: "supply" if k in ("skill", "vendor_skill", "command", "agent") else "obligation"
    idents: list[dict] = []
    for r in recs:
        toks = _fp_tokens(r["title"]) or _fp_tokens(r["source"])
        g = group_of(r["kind"])
        # liveness entries are module-keyed; never merge them by title similarity
        exact_only = r["kind"] == "liveness_planned"
        hit = None
        for ident in idents:
            if ident["group"] != g:
                continue
            if exact_only or ident["exact_only"]:
                same = ident["tokens"] == toks and ident["kinds"] == {r["kind"]}
            else:
                same = _jaccard(ident["tokens"], toks) >= threshold
            if same:
                hit = ident
                break
        if hit is None:
            hit = {"group": g, "tokens": toks, "exact_only": exact_only,
                   "kinds": set(), "members": [], "states": set()}
            idents.append(hit)
        hit["members"].append(r)
        hit["kinds"].add(r["kind"])
        hit["states"].add(r["state"])
    out = []
    for ident in idents:
        key = "|".join(sorted(ident["tokens"])) or ident["members"][0]["source"]
        cid = "OBL-" + hashlib.sha1(
            (ident["group"] + ":" + key).encode()).hexdigest()[:10]
        out.append({
            "id": cid, "group": ident["group"], "title": ident["members"][0]["title"],
            "kinds": sorted(ident["kinds"]), "states": sorted(ident["states"]),
            "members": ident["members"],
        })
    return sorted(out, key=lambda x: x["id"])


_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
_SELF = ("vault/programs/ascension/", ".planning/workstreams/ascension/",
         "vault/plans/ascension-backlog-capability", "modules/backlog_autopilot/inventory.py",
         "tools/test_asc_inventory.py")


def _grep_refs(root: Path, needles: tuple[str, ...], limit: int = 6) -> list[str]:
    import os
    hits: list[str] = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in _SKIP_DIRS]
        for n in sorted(fn):
            p = Path(dp, n)
            r = p.relative_to(root).as_posix()
            if r.startswith(_SELF) or p.suffix not in (".md", ".py", ".json", ".js", ".txt", ".yml", ".yaml", ".out"):
                continue
            try:
                if p.stat().st_size > 2_000_000:
                    continue
                low = p.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            if any(x in low for x in needles):
                hits.append(r)
                if len(hits) >= limit:
                    return hits
    return hits


def resolve_seeds(recs: list[dict], root: Path) -> dict[str, dict]:
    """Each Owner seed -> IN_INVENTORY | REFERENCED_ELSEWHERE | NOT_OBSERVED.
    NOT_OBSERVED means 'not seen by this instrument on this plane', never ABSENT."""
    hay = [(r, (r["title"] + " " + r["source"]).lower()) for r in recs]
    res = {}
    for name, needles in SEEDS.items():
        hits = sorted({r["source"] for r, h in hay if any(n in h for n in needles)})
        if hits:
            res[name] = {"status": "IN_INVENTORY", "sources": hits[:12], "n_sources": len(hits)}
            continue
        refs = _grep_refs(Path(root), needles)
        res[name] = {"status": "REFERENCED_ELSEWHERE" if refs else "NOT_OBSERVED",
                     "sources": refs, "n_sources": len(refs)}
    return res


def build(root: Path) -> dict:
    root = Path(root)
    recs = discover(root)
    idents = canonicalise(recs)
    return {
        "schema": SCHEMA, "root_name": root.name,
        "raw_count": len(recs), "identity_count": len(idents),
        "obligation_identities": sum(1 for i in idents if i["group"] == "obligation"),
        "unreadable": [r["source"] for r in recs if r["state"] == "UNREADABLE"],
        "seeds": resolve_seeds(recs, root),
        "identities": idents,
    }


def census(root: Path) -> set[str]:
    """INDEPENDENT census (plain os.walk, not discover()) of source paths the
    inventory must cover. If discover() silently omits a family member, the census
    disagrees."""
    import os
    root = Path(root)
    found: set[str] = set()
    for sub, exts in (("vault/backlog", (".md", ".patch")), ("vault/plans", (".md",)),
                      ("vault/audits", (".md",)), ("vault/handoffs", (".md",))):
        d = root / sub
        if d.is_dir():
            for n in os.listdir(d):
                if n.endswith(exts) and (d / n).is_file():
                    found.add(f"{sub}/{n}")
    for dp, _dn, fn in os.walk(root / "vault/programs") if (root / "vault/programs").is_dir() else []:
        for n in fn:
            if n.startswith("RESUMPTION") and n.endswith(".md"):
                found.add(Path(dp, n).relative_to(root).as_posix())
    if (root / "RESUMPTION_FILE.md").is_file():
        found.add("RESUMPTION_FILE.md")
    return found


def verify(inv: dict, root: Path) -> list[str]:
    """Return failures ([] == PASS). Every member of the independent census must be a
    member of some identity; no UNRESOLVED seed may be hidden; unreadable is a failure."""
    covered = {m["source"] for i in inv["identities"] for m in i["members"]}
    fails = [f"OMITTED: {p}" for p in sorted(census(root) - covered)]
    fails += [f"UNREADABLE: {p}" for p in inv.get("unreadable", [])]
    if inv["raw_count"] != sum(len(i["members"]) for i in inv["identities"]):
        fails.append("COUNT: raw_count != sum(members)")
    return fails


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    inv = build(root)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(inv, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    un = {k: v["status"] for k, v in inv["seeds"].items() if v["status"] != "IN_INVENTORY"}
    print(f"raw={inv['raw_count']} identities={inv['identity_count']} "
          f"obligations={inv['obligation_identities']} seeds_not_in_inventory={un}")
    if a.verify:
        f = verify(inv, root)
        for x in f:
            print(x)
        print("VERIFY", "FAIL" if f else "PASS")
        return 1 if f else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
