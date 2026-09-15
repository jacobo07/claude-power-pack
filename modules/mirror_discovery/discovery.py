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
Three kinds of knowledge cannot be discovered and stay declared here, because
each is a decision rather than an observation:

  ALIASES           a pair whose two sides carry different names. Nothing in
                    either tree records that they are the same document.
  FOREIGN_PREFIXES  files another tool installs into `~/.claude/`. They are
                    present, unpaired, and not this repo's to mirror.
  EXTRA_REPO_ROOTS  repo directories that feed a live domain whose name they
                    do not share. Nothing in either tree records the mapping.

Everything else is derived. A file present on one side only is reported as
inventory, never as drift: the repo deliberately ships commands that are not
installed, and the live tree deliberately carries knowledge the repo does not
mirror. Calling those failures would rebuild the noise that
`modules/alert_escalation` exists to remove.

Aperture note (2026-09-14). Enrolment by construction fixed the file level and
left the level above it declared by hand: a domain was `(name, glob)` and the
repo side was assumed to live at the directory of the same name. The live tree
is flat -- every agent is in `~/.claude/agents/` whatever its canonical home --
so an agent whose repo home was `vault/agents/` or `vendor/rtk/agents/` was
invisible to the producer and surfaced as LIVE_ONLY, which reads as "no repo
copy exists". Measured on this host: 11 of 22 repo-backed agents, including
every cdio, graphify and rtk agent. A root declared by hand cannot accuse you
of what it never scanned, exactly as a file list could not.
"""
from __future__ import annotations

import os
import re
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

# live domain -> extra repo directories that also feed it. Irreducible: the
# live tree is flat, so nothing in it records which repo directory owns a
# given file. Order is precedence: the domain's own directory ranks first.
EXTRA_REPO_ROOTS: dict[str, tuple[str, ...]] = {
    "agents": ("vault/agents", "vendor/rtk/agents"),
}

# Installed by other tools into the shared live tree. Verified present on this
# host: 4 hook files, 12 agent files.
FOREIGN_PREFIXES: tuple[str, ...] = ("gsd-", "claude-mem", "kde-")

# live-relative -> repo-relative, for pairs whose names differ. Irreducible:
# no scan can infer that these two files are the same document.
#
# Measured 2026-09-15, because "irreducible" deserved a challenge. Frontmatter
# looks like the answer: twelve command sources drop a `cpp-` prefix on disk
# while declaring `name: cpp-<x>`, and deriving the live name from `name:`
# reproduces the resume-sovereign entry below unaided, with zero collisions.
# It is still WRONG. Seven live command files -- autoupdate, customclaw,
# design-md, obsidian-setup, update, vault-setup, vault-sync -- declare a
# `cpp-` name while living under the unprefixed filename, and the harness
# lists them by FILENAME. For commands the filename is the registered name and
# `name:` is decorative, so derivation would have renamed eleven working
# commands. The convention is not uniform and cannot be inferred; it has to be
# recorded. Detection of undeclared candidates lives in
# tools/test_mirror_discovery.py (V-MIRROR-ALIAS-CANDIDATE), which reports them
# for a human to declare rather than pairing them on a guess.
ALIASES: dict[str, str] = {
    "commands/cpp-resume-sovereign.md": "commands/resume-sovereign.md",
    # Found by the census, not by memory: the installer would have written a
    # second file at commands/compound.md while /cpp-compound sat beside it.
    "commands/cpp-compound.md": "commands/compound.md",
}

_FM_NAME = re.compile(r"^name:\s*[\"']?([A-Za-z0-9_.-]+)[\"']?\s*$", re.M)


def declared_name(path: Path) -> str | None:
    """The `name:` a file declares in its own frontmatter, or None.

    Decorative for commands -- the harness registers them by filename -- so
    this is NOT an identity oracle. It is a hint good enough to nominate an
    alias candidate for a human to confirm.
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    if not head.lstrip().startswith("---"):
        return None
    parts = head.split("---", 2)
    if len(parts) < 3:
        return None
    m = _FM_NAME.search(parts[1])
    return m.group(1) if m else None


def alias_candidates(repo_root: Path, domain: str, pattern: str,
                     live_root: Path | None = None) -> list[tuple[str, str]]:
    """Unpaired live files that some repo source claims by declared name.

    The `cpp-compound` pair sat undeclared for months and only the census
    found it. A hand-maintained identity map is the same hand-maintained
    denominator as everything else in this module's history, so the map stays
    -- the filename really is unguessable -- but NOT noticing a candidate is
    no longer free.

    Reports (live_rel, repo_rel). Nominations, never pairings: acting on one
    would rename live files, which is exactly the mistake the comment above
    ALIASES records.
    """
    live_base = resolve_live_root(live_root) / domain
    if not live_base.is_dir():
        return []
    sources = repo_sources(repo_root, domain, pattern)
    alias_live = {k.split("/", 1)[1] for k in ALIASES
                  if k.startswith(f"{domain}/")}
    by_declared: dict[str, str] = {}
    for rel, paths in sources.items():
        n = declared_name(paths[0])
        if n and n not in by_declared:
            by_declared[n] = rel
    out: list[tuple[str, str]] = []
    for p in sorted(live_base.glob(pattern)):
        if not p.is_file():
            continue
        rel = p.relative_to(live_base).as_posix()
        if rel in sources or rel in alias_live or _is_foreign(rel):
            continue
        repo_rel = by_declared.get(p.stem)
        if repo_rel:
            out.append((rel, repo_rel))
    return out


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
    # (domain, rel, [repo path, ...]) for a file claimed by more than one repo
    # root. Two canonical sources for one live file is a defect the producer
    # reports rather than resolves: picking one silently is how the two copies
    # diverge unnoticed.
    duplicate_repo: list = field(default_factory=list)

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


def repo_bases(repo_root: Path, domain: str) -> list:
    """Every repo directory feeding `domain`, in precedence order."""
    return [repo_root / domain] + [
        repo_root / extra for extra in EXTRA_REPO_ROOTS.get(domain, ())]


def repo_sources(repo_root: Path, domain: str, pattern: str) -> dict:
    """{rel: [path, ...]} across all repo roots feeding `domain`.

    A rel found under more than one root keeps every path, in precedence
    order, so the caller can report the ambiguity instead of inheriting it.
    """
    out: dict = {}
    for base in repo_bases(repo_root, domain):
        if not base.is_dir():
            continue
        for p in sorted(base.glob(pattern)):
            if not p.is_file():
                continue
            rel = p.relative_to(base).as_posix()
            if _is_foreign(rel):
                continue
            out.setdefault(rel, []).append(p)
    return out


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
        sources = repo_sources(repo_root, domain, pattern)
        live -= {r.split("/", 1)[1] for r in alias_live
                 if r.split("/", 1)[0] == domain}
        for alias_rel in alias_repo:
            head, _sep, tail = alias_rel.partition("/")
            if head == domain:
                sources.pop(tail, None)

        for rel, paths in sorted(sources.items()):
            if len(paths) > 1:
                d.duplicate_repo.append(
                    (domain, rel, [str(p) for p in paths]))

        repo = set(sources)
        for rel in sorted(live & repo):
            d.pairs.append(Pair(live_root / domain / rel,
                                sources[rel][0], domain, "name"))
        for rel in sorted(live - repo):
            d.live_only.append((domain, rel))
        for rel in sorted(repo - live):
            d.repo_only.append((domain, rel))

    for domain, pattern in DOMAINS:
        bases = [(live_root / domain, "live")] + \
                [(b, "repo") for b in repo_bases(repo_root, domain)]
        for base, side in bases:
            if not base.is_dir():
                continue
            for p in base.glob(pattern):
                if p.is_file() and _is_foreign(p.relative_to(base).as_posix()):
                    d.excluded.append((domain, side,
                                       p.relative_to(base).as_posix()))

    d.pairs.sort(key=lambda p: (p.domain, str(p.repo).lower()))
    return d
