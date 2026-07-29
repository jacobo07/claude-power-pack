"""Discover mirror pairs instead of remembering them.

A mirror pair is one authoritative file under the non-git `~/.claude/` live
tree and its version-controlled sibling in this repo (`vault/standards/
mirror-parity-law.md` sec. 1). Until 2026-07-29 the tracked set was a literal
list of nine tuples, and the law's own "adding a new pair" procedure was to
append another tuple by hand. A denominator enrolled by hand cannot fail you
if it never enrolled the file: the set held 5 of 10 name-matched hooks, 2 of
13 commands, and missed `core/skill-completion-standard.md` outright.
That is `PR-COVERAGE-BY-CONSTRUCTION-001`.

Discovery scans both trees and pairs by identity of the repo-relative path.
Two kinds of knowledge cannot be discovered and stay declared here, because
each is a decision rather than an observation:

  ALIASES           a pair whose two sides carry different names. Nothing in
                    either tree records that they are the same document.
  FOREIGN_PREFIXES  files another tool installs into `~/.claude/`. They are
                    present, unpaired, and not this repo's to mirror.

Everything else is derived. A file present on one side only is reported as
inventory, never as drift: the repo deliberately ships commands that are not
installed, and the live tree deliberately carries knowledge the repo does not
mirror. Calling those failures would rebuild the noise that
`modules/alert_escalation` exists to remove.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

LIVE_ROOT_DEFAULT = Path.home() / ".claude"
ENV_LIVE_ROOT = "POWERPACK_LIVE_ROOT"  # test seam; the live tree is otherwise fixed

# (repo-relative domain, glob). The live tree uses the same layout.
DOMAINS: tuple[tuple[str, str], ...] = (
    ("hooks", "*.js"),
    ("commands", "*.md"),
    ("agents", "*.md"),
    ("knowledge_vault", "**/*.md"),
)

# Installed by other tools into the shared live tree. Verified present on this
# host: 4 hook files, 12 agent files.
FOREIGN_PREFIXES: tuple[str, ...] = ("gsd-", "claude-mem", "kde-")

# live-relative -> repo-relative, for pairs whose names differ. Irreducible:
# no scan can infer that these two files are the same document.
ALIASES: dict[str, str] = {
    "commands/cpp-resume-sovereign.md": "commands/resume-sovereign.md",
}

PAIRED = "PAIRED"
LIVE_ONLY = "LIVE_ONLY"
REPO_ONLY = "REPO_ONLY"


@dataclass(frozen=True)
class Pair:
    live: Path
    repo: Path
    domain: str
    origin: str  # "name" | "alias"

    @property
    def label(self) -> str:
        return self.live.name if self.origin == "name" else \
            f"{self.live.name} -> {self.repo.name}"


@dataclass
class Discovery:
    pairs: list = field(default_factory=list)
    live_only: list = field(default_factory=list)
    repo_only: list = field(default_factory=list)
    excluded: list = field(default_factory=list)

    @property
    def unpaired_total(self) -> int:
        return len(self.live_only) + len(self.repo_only)

    def domain_counts(self) -> dict:
        out: dict = {}
        for dom, _glob in DOMAINS:
            out[dom] = {
                PAIRED: sum(1 for p in self.pairs if p.domain == dom),
                LIVE_ONLY: sum(1 for p in self.live_only if p[0] == dom),
                REPO_ONLY: sum(1 for p in self.repo_only if p[0] == dom),
            }
        return out

    def covers(self, live_path: str, repo_path: str) -> bool:
        """Is this specific pair in the discovered set? Used to prove that
        replacing the literal list lost nothing."""
        want = (str(live_path).replace("\\", "/").lower(),
                str(repo_path).replace("\\", "/").lower())
        for p in self.pairs:
            if (str(p.live).replace("\\", "/").lower(),
                    str(p.repo).replace("\\", "/").lower()) == want:
                return True
        return False


def _is_foreign(rel: str) -> bool:
    return Path(rel).name.startswith(FOREIGN_PREFIXES)


def _scan(root: Path, domain: str, pattern: str) -> set:
    base = root / domain
    if not base.is_dir():
        return set()
    found = set()
    for p in base.glob(pattern):
        if not p.is_file():
            continue
        rel = p.relative_to(base).as_posix()
        if not _is_foreign(rel):
            found.add(rel)
    return found


def resolve_live_root(live_root: Path | None = None) -> Path:
    if live_root is not None:
        return Path(live_root)
    env = os.environ.get(ENV_LIVE_ROOT)
    return Path(env) if env else LIVE_ROOT_DEFAULT


def discover(repo_root: Path, live_root: Path | None = None) -> Discovery:
    repo_root = Path(repo_root)
    live_root = resolve_live_root(live_root)
    d = Discovery()

    # Aliases first so their two halves are not also reported as unpaired.
    alias_live: set = set()
    alias_repo: set = set()
    for live_rel, repo_rel in ALIASES.items():
        lp, rp = live_root / live_rel, repo_root / repo_rel
        domain = live_rel.split("/", 1)[0]
        alias_live.add(live_rel)
        alias_repo.add(repo_rel)
        if lp.is_file() and rp.is_file():
            d.pairs.append(Pair(lp, rp, domain, "alias"))

    for domain, pattern in DOMAINS:
        live = _scan(live_root, domain, pattern)
        repo = _scan(repo_root, domain, pattern)
        live -= {r.split("/", 1)[1] for r in alias_live
                 if r.split("/", 1)[0] == domain}
        repo -= {r.split("/", 1)[1] for r in alias_repo
                 if r.split("/", 1)[0] == domain}

        for rel in sorted(live & repo):
            d.pairs.append(Pair(live_root / domain / rel,
                                repo_root / domain / rel, domain, "name"))
        for rel in sorted(live - repo):
            d.live_only.append((domain, rel))
        for rel in sorted(repo - live):
            d.repo_only.append((domain, rel))

    for domain, pattern in DOMAINS:
        for root, side in ((live_root, "live"), (repo_root, "repo")):
            base = root / domain
            if not base.is_dir():
                continue
            for p in base.glob(pattern):
                if p.is_file() and _is_foreign(p.relative_to(base).as_posix()):
                    d.excluded.append((domain, side,
                                       p.relative_to(base).as_posix()))

    d.pairs.sort(key=lambda p: (p.domain, str(p.repo).lower()))
    return d
