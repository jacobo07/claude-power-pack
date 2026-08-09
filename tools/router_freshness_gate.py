"""Router freshness gate -- MEMORY.md must resolve, and every rule store must be reachable.

PR-COVERAGE-BY-CONSTRUCTION-001 applied to the knowledge router.

The set of rule stores is WALKED OFF DISK, never listed here. A registry enrolled
by hand measures memory: a store nobody wrote down is not scored missing, it is
absent from the denominator, and absence reads as health.

Why store-level and not rule-level: MEMORY.md carries one durable pointer to the
UKDL corpus, and that corpus contains every sealed id. A gate asking "is rule X
reachable" would resolve through that single pointer for every id forever and
could never fail -- vacuous by construction (T-NEVER-GATE-ON-A-RATIO, same defect
in a different costume). Asking "is every STORE reachable" stays falsifiable: a
new file that starts accumulating sealed rules is unreachable until the router
gains a pointer to it.

Exit 0 clean, exit 1 on any failed gate. Named ids and integers, never a ratio.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_DIR = REPO_ROOT.parents[1]          # ~/.claude
KNOWLEDGE_VAULT = CLAUDE_DIR / "knowledge_vault"

# A file is a rule STORE when it holds at least this many DISTINCT sealed ids.
# Measured separation on 2026-08-09 across 340 id-bearing files: the two canonical
# corpora hold 238 (ukdl-universal.md) and 156 (core/HARD-RULES.md); the densest
# non-corpus file -- a session log that merely cites rules -- holds 34. Any value
# in 35..156 separates them. 50 sits near the low end of that gap, so a document
# that grows into a corpus reports as a store and fails loudly, rather than
# silently accumulating sealed rules outside the router.
DENSITY_STORE_MIN = 50

# MEMORY.md is an index, not a store. The budget is enforced elsewhere as a lint;
# the gate treats a breach as a failure because an over-budget router is the
# observable symptom of inline knowledge creeping back in.
ROUTER_MAX_LINES = 200

RULE_ID = re.compile(r"\b((?:T|PR|HR)-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\b")
ENTRY = re.compile(r"^-\s*\[(?P<title>[^\]]+)\]\((?P<path>[^)]+)\)")
BULLET = re.compile(r"^-\s+")

SEARCH_ROOTS = ("vault", "governance", "knowledge")


def router_path(repo_root: Path = REPO_ROOT) -> Path:
    """Derive the project's MEMORY.md from the repo path, using the harness slug rule."""
    slug = re.sub(r"[:\\/.]", "-", str(repo_root))
    return CLAUDE_DIR / "projects" / slug / "memory" / "MEMORY.md"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return ""


def parse_router(router: Path) -> tuple[list[dict], list[str]]:
    """Return (entries, inline_lines). An entry records its resolved target."""
    entries: list[dict] = []
    inline: list[str] = []
    base = router.parent
    for raw in _read(router).splitlines():
        line = raw.strip()
        if not BULLET.match(line):
            continue
        m = ENTRY.match(line)
        if not m:
            inline.append(line)
            continue
        target = (base / m.group("path")).resolve()
        entries.append({
            "title": m.group("title"),
            "path": m.group("path"),
            "target": target,
            "resolves": target.exists(),
        })
    return entries, inline


def discover_stores(repo_root: Path = REPO_ROOT) -> list[dict]:
    """Walk disk for files dense enough in sealed ids to count as a rule store."""
    roots = [repo_root / d for d in SEARCH_ROOTS] + [KNOWLEDGE_VAULT]
    stores: list[dict] = []
    for root in roots:
        if not root.is_dir():
            continue
        for f in root.rglob("*.md"):
            if ".git" in f.parts:
                continue
            ids = set(RULE_ID.findall(_read(f)))
            if len(ids) >= DENSITY_STORE_MIN:
                stores.append({"path": f.resolve(), "ids": len(ids)})
    stores.sort(key=lambda s: -s["ids"])
    return stores


def run(repo_root: Path = REPO_ROOT) -> int:
    router = router_path(repo_root)
    failures: list[str] = []

    print(f"router: {router}")
    if not router.exists():
        print("V-ROUTER-LINKS      FAIL  router absent")
        return 1

    entries, inline = parse_router(router)
    line_count = len(_read(router).splitlines())

    # V-ROUTER-LINKS -- every pointer resolves to a file that exists.
    broken = [e for e in entries if not e["resolves"]]
    if broken:
        failures.append("V-ROUTER-LINKS")
        print(f"V-ROUTER-LINKS      FAIL  {len(broken)} of {len(entries)} do not resolve")
        for e in broken:
            print(f"    unresolved: {e['path']}  ({e['title']})")
    else:
        print(f"V-ROUTER-LINKS      PASS  {len(entries)} entries resolve")

    # V-ROUTER-PURITY -- the router indexes, it does not store.
    if inline:
        failures.append("V-ROUTER-PURITY")
        print(f"V-ROUTER-PURITY     FAIL  {len(inline)} entries carry no pointer")
        for line in inline[:10]:
            print(f"    inline: {line[:90]}")
    else:
        print(f"V-ROUTER-PURITY     PASS  0 inline entries")

    # V-ROUTER-STORES -- every discovered store is reachable from the router.
    stores = discover_stores(repo_root)
    reachable = {e["target"] for e in entries if e["resolves"]}
    unreachable = [s for s in stores if s["path"] not in reachable]
    if unreachable:
        failures.append("V-ROUTER-STORES")
        print(f"V-ROUTER-STORES     FAIL  {len(unreachable)} of {len(stores)} stores unreachable")
        for s in unreachable:
            print(f"    unreachable store: {s['path']}  ({s['ids']} sealed ids)")
    else:
        print(f"V-ROUTER-STORES     PASS  {len(stores)} stores reachable")

    # V-ROUTER-BUDGET -- an over-budget router is inline knowledge creeping back.
    if line_count > ROUTER_MAX_LINES:
        failures.append("V-ROUTER-BUDGET")
        print(f"V-ROUTER-BUDGET     FAIL  {line_count} lines exceeds {ROUTER_MAX_LINES}")
    else:
        print(f"V-ROUTER-BUDGET     PASS  {line_count} of {ROUTER_MAX_LINES} lines")

    print(f"ROUTER_GATE={'PASS' if not failures else 'FAIL'}  failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run())
