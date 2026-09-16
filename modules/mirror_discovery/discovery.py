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

Aperture note (2026-09-15) -- the same disease one level higher again, and the
last level this module has. Fixing the file level left the root level declared
by hand; fixing the root level left DOMAINS itself, a hand-typed tuple of four
names. `~/.claude/rules/` is a real live directory holding doctrine that
reaches every session, and no instrument in this estate could see it, because
an aperture cannot report what it does not enumerate. It was found by a human
noticing, which is not a mechanism.

That is the fifth occurrence of PR-COVERAGE-BY-CONSTRUCTION-001 in this one
module: hand-enrolled file list, hand-declared domain root, hand-curated
install manifest, hand-written identity map, hand-typed domain tuple. The
prevention is not a sixth note. `DOMAINS` is now held against the live tree's
ACTUAL directories by V-RULES-APERTURE-DECLARED in
tools/test_rule_domain_coverage.py: a live directory must be either a declared
domain or an explicitly declared non-domain carrying a reason. Adding a
directory to `~/.claude/` can no longer be silently invisible -- it fails the
gate until somebody decides which it is.
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
    # Added 2026-09-15. This domain is OWNERSHIP-MIXED, and that is the whole
    # reason it was missing: `~/.claude/rules/` is a GLOBAL USER surface that
    # PP shares rather than owns. Measured on this host: 2 paired (the ECC
    # absorptions, the only repo rules that have ever mirrored), 9 live-only
    # written by sessions in OTHER repositories, 107 repo-only.
    #
    # Listing the 9 is correct and accusing them is not. This producer's
    # contract already draws that line -- a one-sided file is inventory, never
    # drift -- so the domain needed no new ownership machinery to be safe.
    # Evidence: vault/audits/live-rule-ownership-2026-09-15.md.
    #
    # WARNING, and it is load-bearing. Adding a domain here ARMS
    # install_global_core._repo_population for it: that function resolves its
    # glob through dict(DOMAINS), so it returned {} for rules before this line
    # and returns 109 sources after it. The only thing between this repo's
    # rule tree and the operator's home is SHIPPABLE_KINDS, a separate tuple
    # in that module. Census aperture and deployment aperture were independent
    # by accident and are now independent by consequence. Pinned by
    # V-RULES-NOT-SHIPPABLE in tools/test_rule_domain_coverage.py, because a
    # comment cannot fail.
    ("rules", "**/*.md"),
)

# Every live directory that is deliberately NOT a mirror domain, with the
# reason. Declared 2026-09-15 against the real tree (53 directories, 5 of them
# domains), because `rules/` proved that a hand-typed DOMAINS tuple cannot
# report what it never enumerates -- the fifth occurrence of
# PR-COVERAGE-BY-CONSTRUCTION-001 in this module.
#
# This is a RATCHET, not a clean bill. It freezes the population that exists
# today with one reason each; a directory appearing in `~/.claude/` that is
# neither a domain nor declared here FAILS the gate until somebody decides
# which it is. A declared name that no longer exists fails too, so the list
# cannot outlive its subjects. Both poles are driven in
# tools/test_rule_domain_coverage.py.
#
# RUNTIME      host or agent state, regenerated; no durable source to mirror
# FOREIGN      another tool installs and owns it; not this repo's to mirror
# OTHER_OWNER  may hold durable artifacts, but their durability belongs to a
#              named owner other than this census
# TRANSIENT    the host creates and removes it; MAY legitimately be absent, so
#              it is exempt from the stale-entry clause and from nothing else.
#              Use it only with observed evidence of a disappearance -- it is
#              the one class that can hide a real deletion, so a guess here
#              buys silence rather than safety.
NON_DOMAINS: dict[str, tuple[str, str]] = {
    # `~/.claude/.claude/` -- a nested copy of this very root, created
    # 2026-09-15 16:42 holding `cache/learnings/*.md`. Not a puzzle and not
    # TRANSIENT: the compound-learnings corpus is addressed as
    # `<cwd>/.claude/cache/learnings`, so a session whose cwd was `~/.claude`
    # grew its own. The files are durable and the writer was found before this
    # line was written -- the class is OTHER_OWNER because that pipeline owns
    # their durability, not because nobody looked.
    ".claude": ("OTHER_OWNER",
                "cwd-relative compound-learnings corpus; owned by that "
                "pipeline, mirrored by nothing here"),
    ".gsd-staging": ("RUNTIME", "gsd install staging"),
    ".vscode": ("RUNTIME", "editor settings for the live tree"),
    "autoresearch-engine": ("RUNTIME", "autoresearch working state"),
    "autoresearch-triggers": ("RUNTIME", "autoresearch trigger spool"),
    "backups": ("RUNTIME", "installer backups; restore input, not source"),
    "_backups": ("RUNTIME", "ad-hoc backups"),
    "_premutation_snapshots": ("RUNTIME", "mutation-drill snapshots"),
    "cache": ("RUNTIME", "derived cache"),
    "chrome": ("RUNTIME", "browser integration state"),
    "daemon": ("RUNTIME", "daemon pid/state"),
    "debug": ("RUNTIME", "debug dumps"),
    "downloads": ("RUNTIME", "scratch downloads"),
    "feedback": ("RUNTIME", "feedback spool"),
    "file-history": ("RUNTIME", "editor file history"),
    "ghost_input": ("RUNTIME", "input-injection scratch"),
    "gsd-migration-journal": ("RUNTIME", "gsd migration journal"),
    "ide": ("RUNTIME", "IDE bridge state"),
    "jobs": ("RUNTIME", "background job records"),
    "lazarus": ("RUNTIME", "session resurrection store"),
    "logs": ("RUNTIME", "logs"),
    "memory": ("RUNTIME", "per-project memory store"),
    "paste-cache": ("RUNTIME", "clipboard cache"),
    "projects": ("RUNTIME", "per-project transcripts and memory"),
    "session-env": ("RUNTIME", "per-session environment"),
    "sessions": ("RUNTIME", "session records"),
    "shell-snapshots": ("RUNTIME", "shell snapshots"),
    "sleepless-qa": ("RUNTIME", "QA run artifacts"),
    "sovereign_blackbox": ("RUNTIME", "blackbox recorder output"),
    "state": ("RUNTIME", "runtime state store"),
    "tmp": ("RUNTIME", "temporary files"),
    "traces": ("RUNTIME", "execution traces"),
    # The entry that taught this list it needed a fourth class.
    #
    # Found by the ratchet's FIRST real run at 15:26, forty minutes after the
    # population was frozen: the host created it empty, mid-session, and the
    # gate refused to pass until somebody classified it. It was classified
    # RUNTIME -- and then it DISAPPEARED before the mutation drill ran, which
    # made the stale-entry clause fail on it minutes later.
    #
    # Both readings were correct and the list was wrong. A directory that
    # comes and goes is neither a new artifact class nor a rotted entry, and
    # scoring it as either makes the gate flap -- which is how a ratchet gets
    # switched off. Hence TRANSIENT: declared, so its arrival is not a
    # surprise; exempt from staleness, so its departure is not an accusation.
    "telemetry": ("TRANSIENT",
                  "host telemetry spool; observed created empty and removed "
                  "again inside one session, 2026-09-15"),
    "get-shit-done": ("FOREIGN", "gsd plugin"),
    "gsd-core": ("FOREIGN", "gsd plugin core"),
    "gsd-local-patches": ("FOREIGN", "gsd plugin patches"),
    "kobiiclaw": ("FOREIGN", "KobiiClaw tooling"),
    "mcp-servers": ("FOREIGN", "MCP server configs"),
    "plugins": ("FOREIGN", "host plugin tree"),
    "bin": ("OTHER_OWNER", "binaries; tools/install_global_core"),
    "config": ("OTHER_OWNER", "host config; settings.json doctrine"),
    "governance": ("OTHER_OWNER", "GLOBAL_ALIGNMENT_LEDGER"),
    "plans": ("OTHER_OWNER", "plan files; SDD-OS spec gate"),
    "profiles": ("OTHER_OWNER", "host profiles"),
    "project-prompts": ("OTHER_OWNER", "per-project prompt overlays"),
    "scripts": ("OTHER_OWNER", "loose scripts; installer checklist"),
    "skills": ("OTHER_OWNER", "PP itself lives here; the git repo IS the source"),
    "skills-archive": ("OTHER_OWNER", "retired skills"),
    "tools": ("OTHER_OWNER", "loose tools; installer checklist"),
    "vault": ("OTHER_OWNER", "live vault projection; vault_sync"),
}

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

# An `origin:` value that means PP PRODUCED this artifact, so PP owes it a
# recoverable source. `/cpp-compound` stamps this on every rule it
# materialises into `~/.claude/rules/` (commands/compound.md, "Provenance is
# mandatory"), precisely so an unattended global write is never anonymous.
#
# The set is deliberately narrow. A live file is PP's because a PP mechanism
# WROTE it, never because it mentions PP or sits in a directory PP also uses:
# nine rules in `~/.claude/rules/` name other repositories as their source and
# one of them cites a Power Pack incident among six, which is content
# authorship and not artifact ownership.
PP_ORIGIN_MARKERS: frozenset[str] = frozenset({"unattended-compound"})

_FM_ORIGIN = re.compile(r"^origin:\s*[\"']?([A-Za-z0-9_.\-]+)[\"']?\s*$", re.M)


def declared_origin(path: Path) -> str | None:
    """The `origin:` a file stamps in its own frontmatter, or None.

    Unlike `declared_name`, this IS an ownership oracle -- but only in the
    positive direction. A stamped origin proves a PP mechanism wrote the file.
    Its absence proves nothing at all, which is why the nine unstamped rules
    were attributed by five other instruments rather than by this one.
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
    m = _FM_ORIGIN.search(parts[1])
    return m.group(1) if m else None


def pp_owned_live_only(repo_root: Path, live_root: Path | None = None,
                       domain: str = "rules") -> list[tuple[str, str]]:
    """Live files PP's own mechanisms produced that no repo source can restore.

    The durability question for a shared live surface. Returns
    `[(relative path, origin), ...]` -- empty is the healthy state and, on
    this host today, also the EMPTY state: `/cpp-compound`'s global pass has
    never run (`last_run_global: null`), so no rule carries a PP origin yet.

    That emptiness is why this was invisible. An empty offender list satisfies
    a completeness claim whether or not the check works, so the gate that
    consumes this ships a synthetic positive control rather than relying on a
    real subject to exist.
    """
    d = discover(repo_root, live_root)
    live_base = resolve_live_root(live_root) / domain
    out: list[tuple[str, str]] = []
    for dom, rel in d.live_only:
        if dom != domain:
            continue
        origin = declared_origin(live_base / rel)
        if origin in PP_ORIGIN_MARKERS:
            out.append((rel, origin))
    return sorted(out)


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
