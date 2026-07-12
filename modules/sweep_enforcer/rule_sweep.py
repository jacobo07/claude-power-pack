"""Sweep Enforcer (P3) -- a prevention rule is not sealable unsweep.

UKDL U-2: "Prevention rule applied to NEW code, not legacy code that
already matches the pattern." The system wrote that lesson down and
then violated it twice more. AKOS Check 11 was written, applied to
manifest.py (3 loaders), and never swept -- writer.py carried the
identical defect one commit away and survived on luck.

A rule that fixes the one file that triggered it is not a prevention
rule. It is a one-file fix wearing a rule's clothes.

So the enforcer does not ASK whether a sweep was run. It RUNS the
sweep, at seal time, against the live tree:

    spec = SweepSpec(
        site_pattern=r"def load_\\w+\\(",        # every site the rule governs
        fix_pattern=r'startswith\\("_"\\)',      # what compliance looks like
        include="**/*.py",
    )
    result = sweep(spec, root)
    verdict = seal("U-27", "loader must skip _-prefixed keys", result)

A claimed list of patched sites is exactly the evidence that failed
last time, so it is not accepted as input. Compliance is observed in
the file or it is a gap.

Where a rule governs N sites, patrolling N sites forever is the weaker
answer. The enforcer proposes the collapse -- one shared helper the
rule can be enforced at once -- instead of policing the sweep.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

# How far past a site's match compliance may live (the enclosing block).
DEFAULT_WINDOW_LINES = 40
# At or above this many governed sites, hand-patrol is the wrong answer.
COLLAPSE_THRESHOLD = 2

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv",
             "_audit_cache", "dist", "build", ".mypy_cache"}


class Verdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED_NO_SWEEP = "REJECTED_NO_SWEEP"
    REJECTED_GAPS = "REJECTED_GAPS"


@dataclass(frozen=True)
class SweepSpec:
    """What the rule governs, and what compliance looks like."""
    site_pattern: str      # every site the rule applies to
    fix_pattern: str       # a site that already complies
    include: str = "**/*.py"
    window_lines: int = DEFAULT_WINDOW_LINES


@dataclass(frozen=True)
class Site:
    path: str
    line: int
    text: str
    compliant: bool

    def __str__(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass
class SweepResult:
    spec: SweepSpec
    root: str
    sites: list[Site] = field(default_factory=list)
    swept_at: str = ""
    command: str = ""

    @property
    def gaps(self) -> list[Site]:
        return [s for s in self.sites if not s.compliant]

    @property
    def patched(self) -> list[Site]:
        return [s for s in self.sites if s.compliant]

    @property
    def collapsible(self) -> bool:
        return len(self.sites) >= COLLAPSE_THRESHOLD

    def as_dict(self) -> dict:
        return {
            "swept_at": self.swept_at,
            "command": self.command,
            "root": self.root,
            "site_pattern": self.spec.site_pattern,
            "fix_pattern": self.spec.fix_pattern,
            "include": self.spec.include,
            "sites_audited": [str(s) for s in self.sites],
            "sites_patched": [str(s) for s in self.patched],
            "gaps_found": [str(s) for s in self.gaps],
        }


def _iter_files(root: Path, include: str):
    for p in sorted(root.glob(include)):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def sweep(spec: SweepSpec, root: Path) -> SweepResult:
    """Scan every governed site in the live tree. Compliance is read
    from the file, never taken on report."""
    site_re = re.compile(spec.site_pattern)
    fix_re = re.compile(spec.fix_pattern)
    cmd = (f"sweep(site={spec.site_pattern!r}, fix={spec.fix_pattern!r}, "
           f"include={spec.include!r}) over {root}")
    res = SweepResult(
        spec=spec,
        root=str(root),
        swept_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        command=cmd,
    )
    for path in _iter_files(root, spec.include):
        try:
            lines = path.read_text(
                encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if not site_re.search(line):
                continue
            window = "\n".join(lines[i:i + spec.window_lines])
            res.sites.append(Site(
                path=str(path.relative_to(root)).replace("\\", "/"),
                line=i + 1,
                text=line.strip()[:120],
                compliant=bool(fix_re.search(window)),
            ))
    return res


@dataclass
class SealVerdict:
    verdict: Verdict
    rule_id: str
    result: SweepResult | None
    reason: str
    collapse_proposal: str = ""

    @property
    def sealed(self) -> bool:
        return self.verdict is Verdict.ACCEPTED


def propose_collapse(res: SweepResult) -> str:
    """N sites means N chances to miss one. Removing the failure mode
    beats patrolling it."""
    if not res.collapsible:
        return ""
    files = sorted({s.path for s in res.sites})
    return (
        f"{len(res.sites)} sites across {len(files)} file(s) are governed "
        f"by this rule: {', '.join(files[:6])}"
        f"{' ...' if len(files) > 6 else ''}. Every one is a chance to "
        "miss one on the next edit. Before sealing a rule that must be "
        "hand-honoured in N places, consider collapsing them into one "
        "shared helper the rule can be enforced at ONCE -- then the rule "
        "governs a single site and cannot be forgotten. Patrol is the "
        "fallback, not the design."
    )


def seal(rule_id: str, title: str, res: SweepResult | None) -> SealVerdict:
    """A prevention rule earns its seal by surviving its own sweep."""
    if res is None:
        return SealVerdict(
            Verdict.REJECTED_NO_SWEEP, rule_id, None,
            "no sweep was run. A prevention rule that has not been swept "
            "across every site matching its pattern is a one-file fix "
            "wearing a rule's clothes (U-2). Run sweep(spec, root) first.",
        )
    if not res.sites:
        return SealVerdict(
            Verdict.REJECTED_NO_SWEEP, rule_id, res,
            f"the sweep audited 0 sites -- site_pattern "
            f"{res.spec.site_pattern!r} matched nothing under {res.root}. "
            "Either the pattern is wrong or the rule governs nothing. "
            "A rule with no sites cannot prevent anything.",
        )
    proposal = propose_collapse(res)
    if res.gaps:
        listed = ", ".join(str(g) for g in res.gaps[:8])
        more = f" (+{len(res.gaps) - 8} more)" if len(res.gaps) > 8 else ""
        return SealVerdict(
            Verdict.REJECTED_GAPS, rule_id, res,
            f"{len(res.gaps)} of {len(res.sites)} governed sites do not "
            f"comply: {listed}{more}. This is the exact shape of U-2 -- "
            "the rule is about to be sealed while legacy sites that "
            "already match its pattern go unpatched. Patch them, or the "
            "next bug is already written.",
            proposal,
        )
    return SealVerdict(
        Verdict.ACCEPTED, rule_id, res,
        f"swept {len(res.sites)} governed site(s); all comply. "
        f"Sweep recorded: command, sites audited, gaps found (0), sites "
        f"patched ({len(res.patched)}).",
        proposal,
    )


def gate_rule_write(rule_id: str, title: str,
                    res: SweepResult | None) -> tuple[bool, str]:
    """The write gate for ukdl-universal.md / HARD-RULES.md.

    Returns (allowed, reason). A prevention rule may not be appended to
    the ledger until its sweep is clean.
    """
    v = seal(rule_id, title, res)
    return v.sealed, v.reason
