#!/usr/bin/env python3
"""Skill Index -- PP Sleepy Skills (skill_router).

Catalogues the general ``~/.claude/skills/<name>/SKILL.md`` library by
parsing each skill's frontmatter ``name`` + ``description`` -- the
curated trigger text the skill author wrote -- and classifying it into a
domain.

Design notes (sealed against the JIT hot-path cost lesson):
  * build_index() walks the skills root and reads frontmatter HEAD bytes
    only, never whole files. Disk-cached at
    ``~/.claude/state/skill-index.json`` with a 1 h TTL.
  * The UserPromptSubmit hot path (intent_classifier wired into
    jit_skill_loader) must NEVER call build_index() -- a per-prompt walk
    of ~80 skill dirs is the documented JIT cold-lag root cause
    (walk-cache lesson, 2026-05-31). Hot-path callers read the cached
    JSON via load_cached_index() (single file read) or rely on the
    classifier's embedded signals. build_index() is for the SessionStart
    warm path, enrichment, and tests.
  * Domain is classified from the DESCRIPTION text only (the author's
    curated trigger surface), not the whole file -- a 5 KB body matches
    every domain and destroys precision.
  * Keyword matching is word-boundary anchored: a naive substring test
    makes "ui" match "build"/"guide" and mis-classifies everything.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

SKILLS_ROOT = Path.home() / ".claude" / "skills"
CACHE_PATH = Path.home() / ".claude" / "state" / "skill-index.json"
CACHE_TTL_SEC = 3600
_FM_HEAD_BYTES = 4000  # frontmatter lives at the top; never read whole file

# Domain -> curated keyword set, scored against the DESCRIPTION only.
# Insertion order is the tie-break (frontend first for the pilot).
DOMAIN_PATTERNS: dict[str, tuple[str, ...]] = {
    "frontend": (
        "frontend", "front-end", "component", "react", "vue", "svelte",
        "tailwind", "css", "html", "ui", "ux", "design", "artifact",
        "web", "landing", "dashboard", "layout", "responsive",
        "animation", "framer", "shadcn", "figma", "wireframe", "mockup",
        "button", "form", "card", "poster", "palette", "typography",
        "font", "brand", "styling", "interface", "visual",
    ),
    "backend": (
        "api", "endpoint", "server", "database", "auth", "jwt", "rest",
        "graphql", "fastapi", "express", "middleware", "webhook",
        "phoenix", "elixir", "otp", "genserver",
    ),
    "ops": (
        "deploy", "docker", "kubernetes", "ci/cd", "pipeline", "vps",
        "nginx", "terraform", "github actions", "workflow",
    ),
    "data": (
        "sql", "query", "dataset", "pandas", "visualization", "chart",
        "schema", "csv", "etl",
    ),
    "docs": (
        "readme", "changelog", "documentation", "technical writing",
        "markdown", "spec",
    ),
}


@dataclass
class SkillEntry:
    name: str
    path: str
    description: str
    domain: str
    keywords: list[str] = field(default_factory=list)
    token_weight: int = 0
    invoke: str = ""  # CLI command for synthetic (non-Skill-tool) entries;
    #                   empty => the card says "invoke via the Skill tool"


# PP repo root (this file: modules/skill_router/skill_index.py).
PP_ROOT = Path(__file__).resolve().parents[2]

# Synthetic "skills" for spec-driven CLI tools that have no SKILL.md but
# are real runnable modules. Surfaced under the "spec" domain so the
# skill_router can point L/XL build prompts at them. A card is emitted
# only when the underlying file exists (checked in build_index), so a
# broken/absent tool (e.g. auto-testing, which currently fails to import)
# never produces a dangling pointer.
SYNTHETIC_SPEC_SKILLS: list["SkillEntry"] = [
    SkillEntry(
        name="karimo PRD parser",
        path=str(PP_ROOT / "modules" / "karimo-harness" / "prd_parser.py"),
        description=(
            "Use when building a new feature from scratch, implementing "
            "user stories, or creating a system: parses a PRD into a "
            "deterministic task list + blueprint."
        ),
        domain="spec",
        keywords=["prd", "requirements", "specification", "blueprint",
                  "user story", "from scratch"],
        token_weight=80,
        invoke="python modules/karimo-harness/prd_parser.py <prd-file>",
    ),
    SkillEntry(
        name="architecture decision check",
        path=str(PP_ROOT / "modules" / "arch-decision" / "arch_check.py"),
        description=(
            "Use when designing system architecture, choosing between "
            "technical approaches, or reviewing an architecture decision "
            "against existing patterns."
        ),
        domain="spec",
        keywords=["architecture", "design", "decision", "trade-off",
                  "approach", "blueprint"],
        token_weight=80,
        invoke="python modules/arch-decision/arch_check.py --fast",
    ),
]


_FM_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.S)


def _matched_keywords(text: str, patterns: tuple[str, ...]) -> list[str]:
    """Word-boundary-anchored keyword presence test. Avoids the
    substring trap where short tokens ("ui", "ux") match unrelated
    words ("build", "auxiliary")."""
    t = (text or "").lower()
    out: list[str] = []
    for p in patterns:
        if re.search(r"\b" + re.escape(p) + r"\b", t):
            out.append(p)
    return out


def _read_frontmatter(skill_md: Path) -> tuple[str, str]:
    """Return (name, description) from the YAML frontmatter head.

    Reads at most _FM_HEAD_BYTES -- frontmatter is always at the top.
    Handles single-line and YAML block-scalar descriptions. Fail-soft:
    missing fields fall back to the directory name / empty string.
    """
    name = skill_md.parent.name
    desc = ""
    try:
        with open(skill_md, "r", encoding="utf-8", errors="ignore") as fh:
            head = fh.read(_FM_HEAD_BYTES)
    except OSError:
        return name, desc
    m = _FM_RE.match(head)
    fm = m.group(1) if m else head
    nm = re.search(r"^name:\s*(.+)$", fm, re.M)
    if nm:
        name = nm.group(1).strip()
    dm = re.search(r"^description:\s*(.*)$", fm, re.M)
    if dm:
        inline = dm.group(1).strip()
        if inline in (">", "|", ">-", "|-", ">+", "|+", ""):
            # YAML block scalar -- gather indented continuation lines.
            lines = fm.splitlines()
            buf: list[str] = []
            capturing = False
            for ln in lines:
                if re.match(r"^description:\s*", ln):
                    capturing = True
                    continue
                if capturing:
                    if (re.match(r"^[A-Za-z_][\w-]*:\s", ln)
                            or ln.strip() == "---"):
                        break
                    buf.append(ln.strip())
            desc = " ".join(x for x in buf if x)
        else:
            desc = inline
    return name, desc


def classify_domain(description: str) -> str:
    """Classify a skill by its description text. Ties break on the
    DOMAIN_PATTERNS insertion order (frontend first for the pilot)."""
    best, best_score = "general", 0
    for domain, patterns in DOMAIN_PATTERNS.items():
        score = len(_matched_keywords(description, patterns))
        if score > best_score:
            best_score, best = score, domain
    return best


def _extract_keywords(description: str, domain: str) -> list[str]:
    """The matched domain keywords present in the description -- this
    skill's curated trigger surface."""
    return _matched_keywords(description, DOMAIN_PATTERNS.get(domain, ()))


def load_cached_index() -> list[SkillEntry] | None:
    """Single-file read of the cached index if fresh; else None.
    Hot-path safe (no directory walk). Fail-open: any error -> None."""
    try:
        st = CACHE_PATH.stat()
    except OSError:
        return None
    if time.time() - st.st_mtime >= CACHE_TTL_SEC:
        return None
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return [SkillEntry(**e) for e in data]
    except Exception:
        return None


def _write_cache(entries: list[SkillEntry]) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_PATH.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps([asdict(e) for e in entries], indent=2),
            encoding="utf-8")
        tmp.replace(CACHE_PATH)
    except Exception:
        pass


def build_index(force: bool = False) -> list[SkillEntry]:
    """Walk the skills root, parse frontmatter, classify, cache.

    OFF the hot path -- intended for SessionStart warm, enrichment, and
    tests. Hot-path callers use load_cached_index(). When ``force`` is
    False a fresh cache is returned without walking.
    """
    if not force:
        cached = load_cached_index()
        if cached is not None:
            return cached

    entries: list[SkillEntry] = []
    if SKILLS_ROOT.is_dir():
        for skill_md in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
            try:
                name, desc = _read_frontmatter(skill_md)
                domain = classify_domain(desc)
                try:
                    weight = skill_md.stat().st_size // 4
                except OSError:
                    weight = 0
                entries.append(SkillEntry(
                    name=name,
                    path=str(skill_md),
                    description=desc[:400],
                    domain=domain,
                    keywords=_extract_keywords(desc, domain),
                    token_weight=weight,
                ))
            except Exception:
                continue
    # Append synthetic spec-driven CLI cards whose target file exists on
    # disk (a broken/absent tool gets no dangling pointer).
    entries.extend(s for s in SYNTHETIC_SPEC_SKILLS
                   if Path(s.path).is_file())
    _write_cache(entries)
    return entries


def get_frontend_skills(force: bool = False) -> list[SkillEntry]:
    """Frontend-domain skills only (the pilot scope)."""
    return [e for e in build_index(force=force) if e.domain == "frontend"]
