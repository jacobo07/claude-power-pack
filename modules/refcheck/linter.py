"""Reference Integrity Linter (P4).

136+ measured instances -- the highest raw count in the AKOS macro audit
and the quietest failure class on the disk. A prompt with a dead path
does not error. It just silently does less. 126 paths still point at a
Windows user (`kobig`) that no longer exists; a mandatory pre-delivery
validation gate is cited by name and does not exist; 7 prompts depend on
2 files that were never written.

Every one of those is mechanically detectable, and none of them was
being detected.

PRECISION IS THE WHOLE PRODUCT. A reference report full of false
positives is a report nobody reads, which is how you end up with 136
broken paths and a linter that everyone ignores. So the linter grades
its findings by how confident it can honestly be:

  BROKEN      a markdown link `[x](path)` that resolves to nothing.
              A link is unambiguously a navigable reference. Gates.
  STALE_USER  a path under a username that does not exist on this host
              (the `kobig` class). Broken AND it tells you why. Gates.
  UNRESOLVED  a backtick path that resolves to nothing. Advisory only:
              prose legitimately cites gitignore entries, other repos'
              files, and naming conventions. Reported, never gating.
  OK / SKIPPED

Credentials: modules.secret_firewall is REUSED for the strong patterns.
It is not enough on its own, and the audit proved it -- its
`generic_secret` pattern needs a 16+ character value and matches only
secret|password|api_key|access_token. The two real credentials on this
disk were an `auth_token` browser cookie (key not in that alternation)
and a 12-character .env password (under the length floor). Both would
have passed. So a corpus-scoped layer is added here for credential-
shaped FILES and KEYS, rather than widening the firewall's thresholds,
which are a shared gate and could not be changed without a sweep of
their own.

Values are never emitted. Findings carry pattern name, file, and line.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

HOME = Path.home()

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "dist", "build", ".mypy_cache", "_audit_cache"}

# A reference must look like a path: it carries a separator, or a known
# file extension. Otherwise `os.replace` and `dict[str, int]` become
# "broken references" and the report becomes noise.
_EXTS = (
    ".md", ".py", ".js", ".ts", ".json", ".jsonl", ".yml", ".yaml",
    ".sh", ".ps1", ".bat", ".txt", ".toml", ".ini", ".cfg", ".sql",
    ".html", ".css", ".ex", ".exs", ".java", ".rs", ".go", ".csv",
    ".db", ".sqlite", ".env", ".vsix", ".jar", ".zip", ".tsx", ".jsx",
)

_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_BACKTICK = re.compile(r"`([^`\n]+)`")
_WIN_PATH = re.compile(r"[A-Za-z]:\\[^\s`\"'|,;)\]]+")
_HOME_PATH = re.compile(r"~[/\\][^\s`\"'|,;)\]]+")

_STALE_USER = re.compile(r"[/\\]Users[/\\](kobig)\b", re.I)

# Credential-shaped filenames -- the container is the signal.
_CRED_FILENAME = re.compile(
    r"(cookie|credential|passwd|id_rsa|\.pem$|^\.env|\.env$|\.env\.)",
    re.I)

# Credential-shaped KEYS with any non-empty value. Deliberately looser
# than the firewall's generic_secret: no length floor, and auth_token /
# cookie / pwd are included -- the two real leaks on this disk were
# missed on exactly those two counts.
#
# The (?:[A-Za-z0-9]+[_-])* prefix matters: the real .env key on this
# disk is DASH_KOBIICRAFT_PWD, and `\bpwd\b` cannot match it because `_`
# is a word character, so there is no boundary before PWD. Without the
# prefix the key is invisible to the content scan and only the filename
# saves you -- which it would not, in a config.json.
_CRED_KEY = re.compile(
    r"(?i)[\"']?(?:[A-Za-z0-9]+[_-])*"
    r"(auth[_-]?token|access[_-]?token|refresh[_-]?token|"
    r"session[_-]?id|sessionid|cookie|set-cookie|passwd|pwd|password|"
    r"api[_-]?key|client[_-]?secret)\b[\"']?"
    r"\s*[:=]\s*[\"']?(?!\s*$)[^\s\"',}]{4,}")

_CRED_SCAN_SUFFIXES = (".json", ".env", ".yml", ".yaml", ".txt", ".ini",
                       ".cfg", ".sh", ".ps1", "")
_MAX_SCAN_BYTES = 2_000_000


class Origin(str, Enum):
    LINK = "link"           # [text](path) -- unambiguously a reference
    PROSE = "prose"         # `path` in backticks -- may be an example


class RefStatus(str, Enum):
    OK = "OK"
    BROKEN = "BROKEN"            # a dead LINK. gates.
    STALE_USER = "STALE_USER"    # dead, and we know why. gates.
    UNRESOLVED = "UNRESOLVED"    # a dead prose path. advisory.
    SKIPPED = "SKIPPED"          # url, glob, remote posix path, template


@dataclass(frozen=True)
class Reference:
    source: str
    line: int
    raw: str
    status: RefStatus
    origin: Origin = Origin.PROSE
    resolved: str = ""
    note: str = ""


@dataclass(frozen=True)
class Credential:
    path: str
    line: int
    signal: str          # WHY it fired -- never the value


@dataclass
class Report:
    roots: list[str] = field(default_factory=list)
    docs_scanned: int = 0
    refs: list[Reference] = field(default_factory=list)
    credentials: list[Credential] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)

    def _of(self, *st: RefStatus) -> list[Reference]:
        return [r for r in self.refs if r.status in st]

    @property
    def broken(self) -> list[Reference]:
        """Findings the linter will stake a gate on."""
        return self._of(RefStatus.BROKEN, RefStatus.STALE_USER)

    @property
    def unresolved(self) -> list[Reference]:
        """Advisory. A prose path may name another repo, a gitignore
        entry, or a convention -- absence is not proof of a defect."""
        return self._of(RefStatus.UNRESOLVED)

    @property
    def stale_user(self) -> list[Reference]:
        return self._of(RefStatus.STALE_USER)

    @property
    def clean(self) -> bool:
        return not self.broken and not self.credentials


def _is_skippable(ref: str) -> tuple[bool, str]:
    low = ref.strip()
    if not low:
        return True, "empty"
    if low.startswith(("http://", "https://", "mailto:", "#")):
        return True, "url or anchor"
    if any(c in low for c in "*?"):
        return True, "glob"
    if low.startswith(("<", "{")) or low.endswith((">", "}")):
        return True, "template"
    if low.startswith("/") and not low.startswith("//"):
        # A posix absolute path on a Windows host is a remote/VPS path.
        # Calling it BROKEN would be a false positive.
        return True, "posix absolute (remote host path)"
    return False, ""


def _looks_like_path(ref: str) -> bool:
    if _WIN_PATH.fullmatch(ref) or ref.startswith("~"):
        return True
    if "/" in ref or "\\" in ref:
        return True
    return ref.lower().endswith(_EXTS)


def _resolve(ref: str, doc: Path, bases: list[Path]) -> Path | None:
    r = ref.strip().rstrip(".,;:)")
    if r.startswith("~"):
        return HOME / r[2:].replace("\\", "/")
    p = Path(r)
    if p.is_absolute():
        return p
    for base in [doc.parent, *bases]:
        cand = base / r
        if cand.exists():
            return cand
    return (bases[0] / r) if bases else (doc.parent / r)


def extract_refs(text: str) -> list[tuple[int, str, Origin]]:
    out: list[tuple[int, str, Origin]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in _MD_LINK.finditer(line):
            out.append((i, m.group(1), Origin.LINK))
        for m in _BACKTICK.finditer(line):
            cand = m.group(1).strip()
            if _looks_like_path(cand) and " " not in cand:
                out.append((i, cand, Origin.PROSE))
        for m in _WIN_PATH.finditer(line):
            out.append((i, m.group(0), Origin.PROSE))
        for m in _HOME_PATH.finditer(line):
            out.append((i, m.group(0), Origin.PROSE))
    return out


def check_doc(doc: Path, bases: list[Path]) -> list[Reference]:
    try:
        text = doc.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        return [Reference(str(doc), 0, "", RefStatus.BROKEN,
                          note=f"unreadable: {exc}")]
    refs: list[Reference] = []
    seen: set[tuple[int, str]] = set()
    for line, raw, origin in extract_refs(text):
        if (line, raw) in seen:
            continue
        seen.add((line, raw))
        skip, why = _is_skippable(raw)
        if skip:
            refs.append(Reference(str(doc), line, raw, RefStatus.SKIPPED,
                                  origin, note=why))
            continue
        if not _looks_like_path(raw):
            continue
        stale = _STALE_USER.search(raw)
        target = _resolve(raw, doc, bases)
        resolved = str(target) if target else ""
        if stale:
            refs.append(Reference(
                str(doc), line, raw, RefStatus.STALE_USER, origin, resolved,
                f"names a user ('{stale.group(1)}') that does not exist on "
                "this host; the reference cannot resolve",
            ))
        elif target and target.exists():
            refs.append(Reference(str(doc), line, raw, RefStatus.OK,
                                  origin, resolved))
        elif origin is Origin.LINK:
            refs.append(Reference(
                str(doc), line, raw, RefStatus.BROKEN, origin, resolved,
                "markdown link resolves to nothing on this filesystem",
            ))
        else:
            refs.append(Reference(
                str(doc), line, raw, RefStatus.UNRESOLVED, origin, resolved,
                "prose path does not resolve here (may name another repo, "
                "a gitignore entry, or a convention)",
            ))
    return refs


def scan_credentials(root: Path) -> tuple[list[Credential], list[str]]:
    """Reuse the firewall for strong patterns; add the corpus-scoped
    layer it demonstrably misses. Values are never emitted."""
    try:
        from modules.secret_firewall.detector import scan_file
    except ImportError:
        scan_file = None  # type: ignore[assignment]

    found: list[Credential] = []
    unreadable: list[str] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            if p.stat().st_size > _MAX_SCAN_BYTES:
                continue
        except OSError as exc:
            unreadable.append(f"{p}: {exc}")
            continue
        rel = str(p)

        if _CRED_FILENAME.search(p.name):
            found.append(Credential(rel, 0, "credential-shaped filename"))

        if p.suffix.lower() not in _CRED_SCAN_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as exc:
            unreadable.append(f"{rel}: {exc}")
            continue

        for i, line in enumerate(text.splitlines(), 1):
            m = _CRED_KEY.search(line)
            if m:
                found.append(Credential(
                    rel, i,
                    f"credential key '{m.group(1)}' with a non-empty value"))
        if scan_file is not None:
            try:
                for hit in scan_file(p):
                    found.append(Credential(
                        rel, hit.line_no,
                        f"secret_firewall:{hit.pattern_name} "
                        f"severity={hit.severity.name}"))
            except OSError as exc:
                unreadable.append(f"{rel}: {exc}")
    return found, unreadable


def lint(roots: list[Path], scan_secrets: bool = True,
         repo_root: Path | None = None) -> Report:
    """A root that does not exist is a loud failure, not a quiet zero."""
    missing = [str(r) for r in roots if not r.exists()]
    if missing:
        raise FileNotFoundError(
            f"refcheck was pointed at path(s) that do not exist: {missing}. "
            "Refusing to report a clean tree for a tree that is not there.")

    # Resolution bases: every directory root, plus the repo root. Without
    # the repo root, `CLAUDE.md` cited from governance/README.md resolves
    # against governance/ only and is reported broken while it sits at the
    # repo root, existing.
    bases = [r for r in roots if r.is_dir()]
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    if repo_root not in bases:
        bases.append(repo_root)

    rep = Report(roots=[str(r) for r in roots])
    docs: list[Path] = []
    for root in roots:
        if root.is_file():
            docs.append(root)
            continue
        for p in root.rglob("*.md"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            docs.append(p)

    for doc in sorted(set(docs)):
        rep.docs_scanned += 1
        rep.refs.extend(check_doc(doc, bases))

    if scan_secrets:
        for root in roots:
            if root.is_dir():
                creds, bad = scan_credentials(root)
                rep.credentials.extend(creds)
                rep.unreadable.extend(bad)
    return rep


def render(rep: Report) -> str:
    ok = sum(1 for r in rep.refs if r.status is RefStatus.OK)
    skipped = sum(1 for r in rep.refs if r.status is RefStatus.SKIPPED)
    lines = [
        "# REFERENCE INTEGRITY REPORT",
        "",
        f"roots        : {', '.join(rep.roots)}",
        f"docs scanned : {rep.docs_scanned}",
        f"references   : {len(rep.refs)} ({ok} ok, {len(rep.broken)} broken, "
        f"{len(rep.unresolved)} unresolved, {skipped} skipped)",
        f"stale-user   : {len(rep.stale_user)}",
        f"credentials  : {len(rep.credentials)}",
        "",
    ]
    if rep.broken:
        lines += ["## BROKEN (gating -- a dead link or a dead user path)", "",
                  "| referencing doc | line | reference | why |",
                  "|---|---:|---|---|"]
        for r in rep.broken:
            lines.append(f"| {r.source} | {r.line} | `{r.raw}` | {r.note} |")
        lines.append("")
    if rep.credentials:
        lines += [
            "## CREDENTIAL FINDINGS (gating)",
            "",
            "Values are never printed. Rotate at the provider FIRST, then "
            "scrub (HR-SECRET-007).",
            "",
            "| file | line | signal |",
            "|---|---:|---|",
        ]
        for c in rep.credentials:
            lines.append(f"| {c.path} | {c.line or '-'} | {c.signal} |")
        lines.append("")
    if rep.unresolved:
        lines += [
            "## UNRESOLVED (advisory -- prose paths that do not resolve here)",
            "",
            "A prose path may name another repo, a gitignore entry, or a "
            "naming convention. These do not gate; read them.",
            "",
            "| referencing doc | line | reference |",
            "|---|---:|---|",
        ]
        for r in rep.unresolved:
            lines.append(f"| {r.source} | {r.line} | `{r.raw}` |")
        lines.append("")
    if rep.unreadable:
        lines += ["## UNREADABLE (named, not silently skipped)", ""]
        lines += [f"- {u}" for u in rep.unreadable]
        lines.append("")
    if rep.clean:
        lines.append("No broken references and no credentials found.")
    return "\n".join(lines).rstrip() + "\n"
