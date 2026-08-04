"""STOP #1 disposition ledger -- the transition producer the portfolio tier lacked.

Every corpus audit in this estate ends at a STOP #1 and records its own state in its
own frontmatter. Nothing ever transitions that field. So a plan struck three weeks ago
still reads `status: STOP #1 -- awaiting Owner selection`, and the only way to learn the
truth is to cross-read a closure report filed somewhere else.

The estate has a sealed name for this: `feedback_status_field_nobody_can_transition` --
a field with no transition producer is decoration, and the ledger lies. It lied in the
safe-sounding direction: a stale "awaiting" reads as work outstanding, so the portfolio
looked more blocked than it was, and "four open STOP #1s" was quoted in three separate
audits without anyone being able to check it.

WHY THIS DOES NOT EDIT THE PLANS
--------------------------------
It would be one line to rewrite each stale `status:`. That is refused. The RE Baseline
closure report established the rule: *rewriting a sealed artifact to match a later
verdict destroys the record of what was believed when.* A plan is a dated statement of
belief; a plan whose status is silently corrected is no longer evidence of anything.

So the plans stay sealed and this emits a DERIVED ledger. Being derived is what makes it
un-staleable -- it is regenerated from the filesystem on every run, so it cannot drift
from the evidence the way a hand-maintained list does. This is the same move
`mirror_discovery` made when it replaced two hand-written lists with a discovery
producer.

HOW A DISPOSITION IS ESTABLISHED
--------------------------------
Never asserted, always witnessed. A plan is only reclassified when ANOTHER artifact --
never itself -- states an outcome for its family. Absent a witness the plan is OPEN,
which is the conservative reading: this tool can create work, never silently close it.

    RESOLVED  the plan's OWN status already states an outcome
    CONTRADICTED     status is open-shaped, but another artifact witnesses an outcome
    OPEN      status is open-shaped and no witness exists -- genuinely outstanding
    UNKNOWN   no parseable status

The denominator is DISCOVERED from `vault/plans/*.md`, never enumerated by hand
(`PR-COVERAGE-BY-CONSTRUCTION-001`): an audit set enrolled by hand measures memory.

    python -m modules.owner_queue.stop_ledger            # print the ledger
    python -m modules.owner_queue.stop_ledger --write    # regenerate the markdown

Fail-open: no function raises. An unreadable plan is UNKNOWN, never silently dropped.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = PP_ROOT / "vault" / "plans"
LEDGER_PATH = PLANS_DIR / "STOP_LEDGER.md"

RESOLVED = "RESOLVED"
CONTRADICTED = "CONTRADICTED"
OPEN = "OPEN"
UNKNOWN = "UNKNOWN"

# A status is "open-shaped" if it claims work is outstanding.
_OPEN_SHAPE = re.compile(
    r"awaiting|blocking|pending|no dataset written|verdicts delivered|"
    r"presented inline|delivered inline",
    re.I,
)
# ...and "closed-shaped" if it states its own outcome. Checked FIRST: a status reading
# "STOP #1 RESOLVED -- Owner selected Option B" matches both, and the resolution wins.
_CLOSED_SHAPE = re.compile(
    r"\bRESOLVED\b|\bCLOSED\b|\bSHIPPED\b|\bSTRUCK\b|\bDISCARDED\b|\bREFUSED\b|"
    r"\bbuilt \+ tested\b|\bapproved by owner\b",
    re.I,
)
# A witness verb: another artifact stating what became of a family.
_WITNESS = re.compile(
    r"\bSTRUCK\b|\bstruck\b|\bshelved\b|\brefused\b|\bdiscarded\b|\bratified\b|"
    r"\bshipped instead\b|\bCLOSED\b|\bRESOLVED\b|\bDO-NOT-BUILD\b|\bwas never built\b",
)
_STOP_TOKEN = re.compile(r"STOP[\s#-]*1|STOP_1|STOP\b", re.I)

_MAX_BYTES = 600_000
# Family tokens shorter than this match too much prose to be evidence of anything.
_MIN_TOKEN = 3


@dataclass
class Row:
    plan: str
    family: str
    status_text: str
    disposition: str
    witnesses: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _read(p: Path) -> str:
    try:
        if p.stat().st_size > _MAX_BYTES:
            return ""
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _status_of(text: str) -> str:
    """The frontmatter status line, if any. Only the leading block is inspected: a
    'status:' inside the body is prose, not a declaration."""
    head = text[:4000]
    m = re.search(r"^\s*status:\s*(.+)$", head, re.I | re.M)
    return m.group(1).strip() if m else ""


def _family_of(stem: str) -> str:
    """`igef-2026-07-29` -> `igef`. The date suffix is stripped so a family is
    searchable across artifacts that never repeat its filename."""
    s = re.sub(r"[-_]?\d{4}-\d{2}-\d{2}.*$", "", stem)
    s = re.sub(r"[-_]?(corpus|audit|compendium|runtime|plan)$", "", s)
    return s.strip("-_") or stem


def discover(plans_dir: Path | None = None) -> list:
    """Every plan carrying a STOP-shaped status. DISCOVERED, never curated."""
    d = Path(plans_dir) if plans_dir else PLANS_DIR
    out = []
    try:
        candidates = sorted(d.glob("*.md"))
    except OSError:
        return out
    for p in candidates:
        if p.name == LEDGER_PATH.name:
            continue
        text = _read(p)
        if not text:
            continue
        status = _status_of(text)
        if not status or not _STOP_TOKEN.search(status):
            continue
        out.append((p, status, _family_of(p.stem)))
    return out


def _witnesses_for(family: str, self_path: Path, search_roots: list) -> list:
    """Artifacts OTHER than the plan itself that state an outcome for this family.

    Self-witnessing is excluded by construction: a plan asserting its own resolution is
    the very thing whose trustworthiness is in question."""
    if len(family) < _MIN_TOKEN:
        return []
    token = re.compile(r"\b" + re.escape(family) + r"\b", re.I)
    found = []
    for root in search_roots:
        try:
            files = [f for f in Path(root).rglob("*.md") if f.is_file()]
        except OSError:
            continue
        for f in files:
            try:
                if f.resolve() == self_path.resolve():
                    continue
            except OSError:
                continue
            text = _read(f)
            if not text or not token.search(text):
                continue
            for line in text.splitlines():
                if token.search(line) and _WITNESS.search(line):
                    try:
                        rel = str(f.relative_to(PP_ROOT)).replace("\\", "/")
                    except ValueError:
                        rel = f.name
                    found.append(f"{rel}: {line.strip()[:150]}")
                    break
            if len(found) >= 3:      # three witnesses is a finding; thirty is noise
                return found
    return found


def build(plans_dir: Path | None = None, search_roots: list | None = None) -> list:
    d = Path(plans_dir) if plans_dir else PLANS_DIR
    roots = search_roots if search_roots is not None else [
        d, PP_ROOT / "vault" / "knowledge_base", PP_ROOT / "vault" / "audits"
    ]
    rows = []
    for path, status, family in discover(d):
        if not status:
            rows.append(Row(path.name, family, "", UNKNOWN))
            continue
        # Closed-shape is tested first: a status may match both, and its own stated
        # resolution outranks the generic open-shaped words around it.
        if _CLOSED_SHAPE.search(status):
            rows.append(Row(path.name, family, status, RESOLVED))
            continue
        if _OPEN_SHAPE.search(status):
            w = _witnesses_for(family, path, roots)
            rows.append(Row(path.name, family, status, CONTRADICTED if w else OPEN, w))
            continue
        rows.append(Row(path.name, family, status, UNKNOWN))
    return rows


def render(rows: list) -> str:
    counts = {k: sum(1 for r in rows if r.disposition == k)
              for k in (OPEN, CONTRADICTED, RESOLVED, UNKNOWN)}
    out = [
        "# STOP #1 Disposition Ledger",
        "",
        "**Derived — do not hand-edit.** Regenerate with "
        "`python -m modules.owner_queue.stop_ledger --write`.",
        "",
        "The plan files are sealed records of what was believed when, and are never "
        "rewritten to match a later verdict. This ledger carries the transition their "
        "`status:` field has no producer for.",
        "",
        f"**{len(rows)} STOP-bearing plans** — "
        f"OPEN {counts[OPEN]} · CONTRADICTED {counts[CONTRADICTED]} · "
        f"RESOLVED {counts[RESOLVED]} · UNKNOWN {counts[UNKNOWN]}",
        "",
        "| plan | family | disposition | status as written | witness |",
        "|---|---|---|---|---|",
    ]
    order = {OPEN: 0, CONTRADICTED: 1, UNKNOWN: 2, RESOLVED: 3}
    for r in sorted(rows, key=lambda x: (order.get(x.disposition, 9), x.plan)):
        w = r.witnesses[0].replace("|", "\\|")[:110] if r.witnesses else "-"
        st = r.status_text.replace("|", "\\|")[:70] or "-"
        out.append(f"| `{r.plan}` | {r.family} | **{r.disposition}** | {st} | {w} |")
    out += [
        "",
        "## Reading",
        "",
        "- **OPEN** — open-shaped status and no artifact anywhere witnesses an outcome. "
        "Genuinely outstanding; these are the ones to act on.",
        "- **CONTRADICTED** — the plan still reads as awaiting, but another artifact states what "
        "became of it. The work is done; only the record disagrees.",
        "- **RESOLVED** — the plan's own status states its outcome.",
        "",
        "A disposition is never asserted, only witnessed, and a plan may not witness "
        "itself. Absent evidence the verdict is OPEN — this producer can create work, "
        "never silently close it. CONTRADICTED means *a contradiction exists*, never "
        "*this is resolved*; verify the witness before acting on it.",
        "",
        "### Known limits of the witness test",
        "",
        "**False positives — precedent citation.** An audit that cites another family's "
        "verdict as prior art (an `| EFAIF | DO-NOT-BUILD |` row inside a base-rate "
        "table) produces a line carrying both the family token and a disposition verb, "
        "indistinguishable by line-level matching from a statement about that family's "
        "own STOP. This is exactly why the verdict is CONTRADICTED rather than RESOLVED: "
        "the tool surfaces the disagreement and a human adjudicates it.",
        "",
        "**False negatives — family-token drift.** A disposition recorded under a name "
        "other than the filename is missed. `e-passes-audit` is the live instance: it "
        "was struck on 2026-07-29, but the closure report records that outcome as "
        "`E1-E5`, so no line carries the token `e-passes` and the plan reads OPEN here. "
        "Misses fall toward OPEN, which is the safe direction — this producer "
        "over-reports outstanding work, never under-reports it.",
        "",
    ]
    return "\n".join(out)


def write(rows: list, path: Path | None = None) -> bool:
    p = Path(path) if path else LEDGER_PATH
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(render(rows), encoding="utf-8")
        return True
    except OSError:
        return False


def main(argv: list | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    rows = build()
    if not rows:
        print("no STOP-bearing plans found in vault/plans/")
        return 0
    print(render(rows))
    if "--write" in args:
        ok = write(rows)
        try:
            rel = LEDGER_PATH.relative_to(PP_ROOT)
        except ValueError:
            rel = LEDGER_PATH
        print(f"\n{'wrote' if ok else 'FAILED to write'} {rel}")
    counts = {k: sum(1 for r in rows if r.disposition == k)
              for k in (OPEN, CONTRADICTED, RESOLVED, UNKNOWN)}
    print("STOP_LEDGER " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
