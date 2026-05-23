"""build_index.py -- Architecture Decision Skill index builder.

Scans 8 vault paths with weights and emits two artifacts:
  vault/.arch-index/index.json   (sources + shingles + concepts + entities)
  vault/.arch-index/vocab.json   (verbs + concepts + entities)

Spec: vault/specs/arch-decision-skill.md
Plan: vault/plans/arch-decision-skill-2026-05-23.md

Determinism: byte-identical output across runs given the same input
files. No network calls. No LLM. Pure Python stdlib.

Encoding: opens every source with `utf-8-sig` to strip BOM (per
feedback_python_utf8_bom).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
KV_ROOT = HOME / ".claude" / "knowledge_vault"
PROJECTS_ROOT = HOME / ".claude" / "projects"

OUT_DIR = PP_ROOT / "vault" / ".arch-index"
OUT_INDEX = OUT_DIR / "index.json"
OUT_VOCAB = OUT_DIR / "vocab.json"

# --- curated vocabulary seeds (extended by auto-derivation) ---

DESIGN_VERBS = [
    # Spanish
    "diseña", "diseñar", "diseño", "arquitectura", "arquitectonico",
    "implementar", "implementacion", "propon", "proponer", "propuesta",
    "deberia", "deberiamos", "elegir", "escoger", "construir", "construye",
    "planificar", "planear", "estrategia", "evaluar", "decidir",
    # English
    "design", "architecture", "architectural", "implement", "implementation",
    "propose", "proposal", "should", "should-i", "choose", "chose",
    "between", "vs", "versus", "build", "builds", "plan", "planning",
    "strategy", "evaluate", "decide", "decision",
]

# Tech entities seed list. Curated for HIGH-SIGNAL veto/decision targets.
# Bare language names (rust, python, go, java) are EXCLUDED -- they appear
# in too many neutral contexts (snippet explanations, "valid alternative"
# lists, etc.) and produce false-positive collisions.
ENTITY_SEEDS = [
    # Runtime bans (Owner-declared forbidden surfaces)
    "n8n", "zapier", "make.com", "pipedream", "ifttt",
    # DB / cache choices (commonly debated, often have prior decisions)
    "redis", "postgres", "postgresql", "mysql", "mongodb", "sqlite",
    "memcached", "dynamodb", "elasticsearch",
    # JS frameworks (similar -- choice typically has prior decision)
    "react", "vue", "svelte", "angular", "next.js", "nextjs", "nuxt",
    "remix", "astro", "solidjs",
    # Backend frameworks
    "fastapi", "django", "flask", "express", "koa", "nestjs",
    "phoenix", "rails",
    # Minecraft stack (Owner has strong opinions here per kobiicraft-ai)
    "bukkit", "spigot", "paper", "citizens", "essentialsx", "luckperms",
    # NOTE: project names (lazarus, kobiicraft, tuax, etc.) are
    # deliberately EXCLUDED -- they appear in every memory file of
    # their project as a label and trigger noisy entity matches that
    # do not correspond to a real architectural decision.
    # Pattern entities (kebab-cased; word-boundary-matched against prompt)
    "parallel-write", "parallel-edit", "parallel-explore",
    "auto-fire", "slash-command", "hook-fanout",
    "force-push", "git-add-a", "rm-rf", "mock-database",
    "n8n-workflow", "zapier-workflow", "pipedream-workflow",
]

STOPWORDS = {
    # Spanish
    "a", "al", "ante", "bajo", "cabe", "con", "contra", "de", "del", "desde",
    "en", "entre", "hacia", "hasta", "para", "por", "segun", "sin", "so",
    "sobre", "tras", "y", "e", "o", "u", "ni", "que", "no", "si", "es",
    "son", "ser", "estar", "este", "esto", "esta", "estos", "estas", "el",
    "la", "los", "las", "lo", "un", "una", "unos", "unas", "me", "te", "se",
    "le", "les", "su", "sus", "mi", "tu", "yo", "el", "ella", "nosotros",
    "vosotros", "ellos", "ellas", "muy", "mas", "menos", "ya", "todo", "todos",
    # English
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to",
    "in", "on", "at", "by", "for", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below", "from",
    "up", "down", "out", "off", "over", "under", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "can", "could", "may", "might", "must", "shall", "i",
    "you", "he", "she", "it", "we", "they", "this", "that", "these", "those",
}

# --- tokenization ---

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-\._]*", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    """Lowercase + tokenize + drop stopwords + drop bare digits."""
    if not text:
        return []
    raw = TOKEN_RE.findall(text.lower())
    out = []
    for t in raw:
        if t in STOPWORDS:
            continue
        if t.isdigit():
            continue
        if len(t) < 2:
            continue
        out.append(t)
    return out


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:80]


def read_text_safe(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except (OSError, UnicodeError):
        return ""


# --- per-class extractors ---

VETO_MARKERS = re.compile(
    r"(?i)\b(never|nunca|forbidden|prohibit|prohibido|ban|banned|rejected|"
    r"reject|must not|do not|don\'t|cannot|can\'t|may not|shall not|"
    r"refused|off[- ]limits|no\b)\b",
)


def looks_like_veto(text: str) -> bool:
    """First 500 chars contain a prohibition verb."""
    return bool(VETO_MARKERS.search(text[:500]))


def _entity_pattern(entity: str) -> re.Pattern:
    """Build a word-boundary regex for an entity.

    Special chars (., -) are kept literal but word-boundary anchors
    use the broader sense: a leading/trailing non-alphanumeric (or
    start/end of string).
    """
    esc = re.escape(entity)
    return re.compile(rf"(?<![a-z0-9_]){esc}(?![a-z0-9_])", re.IGNORECASE)


_ENTITY_PATTERNS = {e: _entity_pattern(e) for e in ENTITY_SEEDS}


def extract_entities(text: str) -> list[str]:
    """Find entity seeds appearing in the source body with word-boundary
    semantics. 'redis' must not match 'rediscovery'; 'react' must not
    match 'reactor'."""
    hits = []
    for e in ENTITY_SEEDS:
        if _ENTITY_PATTERNS[e].search(text):
            hits.append(e)
    return sorted(set(hits))


def make_source(path: Path, section: str | None, body: str, klass: str,
                weight: float, title: str) -> dict:
    """Build a single source record."""
    summary = body[:400].strip()
    shingles = tokenize(body)
    # Cap shingles per source for size control.
    shingles_unique = list(dict.fromkeys(shingles))[:300]
    entities = extract_entities(body) + extract_entities(title)
    entities = sorted(set(entities))
    # Concept = the section title or filename, kebab-cased.
    concept = slug(title)
    rec_id_input = f"{path}|{section or ''}|{title}"
    rec_id = hashlib.sha1(rec_id_input.encode("utf-8")).hexdigest()[:16]
    return {
        "id": rec_id,
        "path": str(path).replace("\\", "/"),
        "section": section,
        "class": klass,
        "weight": weight,
        "title": title,
        "summary": summary,
        "shingles": shingles_unique,
        "concepts": [concept],
        "entities": entities,
        "is_veto": looks_like_veto(body) or looks_like_veto(title),
    }


SECTION_RE = re.compile(r"(?m)^(#{2,4})\s+([^\n]+)$")


def split_by_headers(text: str, max_level: int = 3) -> list[tuple[str, str]]:
    """Split markdown by H2/H3 headers. Returns [(title, body), ...].

    First chunk before any header gets title='__preamble__' and is
    returned only if it has substantial body (>= 50 chars).
    """
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return [("__preamble__", text)] if len(text.strip()) >= 50 else []
    out = []
    preamble = text[: matches[0].start()].strip()
    if len(preamble) >= 50:
        out.append(("__preamble__", preamble))
    for i, m in enumerate(matches):
        level = len(m.group(1))
        if level > max_level:
            continue
        title = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if len(body) >= 30:
            out.append((title, body))
    return out


def scan_apex(out: list[dict]) -> int:
    """Source 1: apex-completion-standard.md -- weight 1.0, class=standard."""
    p = KV_ROOT / "core" / "apex-completion-standard.md"
    if not p.exists():
        return 0
    text = read_text_safe(p)
    sections = split_by_headers(text)
    n = 0
    for title, body in sections:
        out.append(make_source(p, title, body, "standard", 1.0, title))
        n += 1
    return n


def scan_feedback_memory(out: list[dict]) -> int:
    """Source 2: feedback_*.md across all projects -- weight 0.9, class=veto."""
    n = 0
    if not PROJECTS_ROOT.exists():
        return 0
    for proj_dir in PROJECTS_ROOT.iterdir():
        mem = proj_dir / "memory"
        if not mem.is_dir():
            continue
        for f in mem.glob("feedback_*.md"):
            text = read_text_safe(f)
            if not text.strip():
                continue
            # Use file body as one source.
            title = f.stem.replace("_", " ").replace("feedback ", "feedback: ")
            out.append(make_source(f, None, text, "veto", 0.9, title))
            n += 1
    return n


def scan_glob_dir(out: list[dict], root: Path, klass: str, weight: float) -> int:
    """Generic directory scanner: every .md file becomes one source."""
    if not root.exists():
        return 0
    n = 0
    for f in root.rglob("*.md"):
        text = read_text_safe(f)
        if not text.strip():
            continue
        title = f.stem.replace("-", " ").replace("_", " ")
        out.append(make_source(f, None, text, klass, weight, title))
        n += 1
    return n


def scan_session_lessons(out: list[dict]) -> int:
    """Source 5: PP session_lessons.md -- weight 0.7, class=lesson.

    Each `## YYYY-MM-DD — ...` section becomes its own source.
    """
    p = PP_ROOT / "vault" / "knowledge_base" / "session_lessons.md"
    if not p.exists():
        return 0
    text = read_text_safe(p)
    sections = split_by_headers(text, max_level=2)
    n = 0
    for title, body in sections:
        if title == "__preamble__":
            continue
        out.append(make_source(p, title, body, "lesson", 0.7, title))
        n += 1
    return n


def scan_ukdl(out: list[dict]) -> int:
    """Source 8: ukdl-universal.md -- weight 1.0, class=ukdl."""
    p = PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"
    if not p.exists():
        return 0
    text = read_text_safe(p)
    sections = split_by_headers(text, max_level=3)
    n = 0
    for title, body in sections:
        if title == "__preamble__":
            continue
        out.append(make_source(p, title, body, "ukdl", 1.0, title))
        n += 1
    return n


def build_vocab(sources: list[dict]) -> dict:
    """Derive vocab from indexed sources."""
    concepts = set()
    entities = set(ENTITY_SEEDS)
    for s in sources:
        for c in s.get("concepts", []):
            if c and len(c) >= 3:
                concepts.add(c)
        for e in s.get("entities", []):
            entities.add(e)
    return {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verbs": sorted(set(DESIGN_VERBS)),
        "concepts": sorted(concepts),
        "entities": sorted(entities),
    }


def main(argv: list[str]) -> int:
    sources: list[dict] = []
    counts = {}
    counts["apex"] = scan_apex(sources)
    counts["feedback_memory"] = scan_feedback_memory(sources)
    counts["gex44_antipatterns"] = scan_glob_dir(
        sources, KV_ROOT / "gex44_antipatterns", "antipattern", 0.85)
    counts["antipatterns"] = scan_glob_dir(
        sources, KV_ROOT / "antipatterns", "antipattern", 0.80)
    counts["session_lessons"] = scan_session_lessons(sources)
    counts["governance"] = scan_glob_dir(
        sources, KV_ROOT / "governance", "governance", 0.60)
    counts["errors"] = scan_glob_dir(
        sources, KV_ROOT / "errors", "error", 0.50)
    counts["ukdl"] = scan_ukdl(sources)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    index_payload = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown",
        "pp_root": str(PP_ROOT).replace("\\", "/"),
        "kv_root": str(KV_ROOT).replace("\\", "/"),
        "counts": counts,
        "total_sources": len(sources),
        "sources": sources,
    }

    OUT_INDEX.write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2,
                   sort_keys=False),
        encoding="utf-8",
    )

    vocab = build_vocab(sources)
    OUT_VOCAB.write_text(
        json.dumps(vocab, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )

    # Console summary (one line per class + total).
    print(f"[build_index] PP_ROOT={PP_ROOT}")
    print(f"[build_index] KV_ROOT={KV_ROOT}")
    for k, v in counts.items():
        print(f"  {k:24s} {v:4d}")
    print(f"  {'TOTAL':24s} {len(sources):4d}")
    print(f"[build_index] vocab verbs={len(vocab['verbs'])} "
          f"concepts={len(vocab['concepts'])} "
          f"entities={len(vocab['entities'])}")
    print(f"[build_index] wrote {OUT_INDEX}")
    print(f"[build_index] wrote {OUT_VOCAB}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
