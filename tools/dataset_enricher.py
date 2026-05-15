#!/usr/bin/env python3
"""dataset_enricher.py - aggregate cross-project errors/lessons/vaccines.

Walks every knowledge_base / mistakes / lessons file across the canonical
Power-Pack vault PLUS every Cursor Projects repo, parses entries at H2
granularity, categorizes via a 20-category transversal taxonomy, and
emits four enriched datasets at the standard datasets directory.

Outputs (all overwritten atomically per run):
    UNIVERSAL-ERRORS-CATALOG.md    - every error entry, source-tagged
    UNIVERSAL-LESSONS-COMPENDIUM.md - every lesson + vaccine, source-tagged
    CROSS-PROJECT-PATTERNS.md      - patterns appearing in >=2 projects
    DATASET_INDEX.md               - master index + provenance + stats

The point is full coverage, not summarization: every entry is preserved
verbatim in a collapsed details block, then GLOSSED with a deterministic
first-paragraph synthesis plus categorization metadata. Transversal
links connect entries that share keyword clusters across projects.

Run with `python tools/dataset_enricher.py --build`.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import hashlib
import io
import os
import re
import sys

HOME = os.path.expandvars(r"%USERPROFILE%")
OUT_DIR = (os.environ.get("SOVEREIGN_MINER_OUT_DIR")
           or os.path.join(HOME, "Downloads", "PowerPack_Sovereign_Datasets"))

PP_VAULT = os.path.join(
    HOME, ".claude", "skills", "claude-power-pack", "vault", "knowledge_base")
CURSOR_PROJECTS = os.path.join(HOME, "Desktop", "Cursor Projects")

# Canonical 19-source manifest: (project, kind, absolute_path).
SOURCES = [
    ("claude-power-pack", "lessons",
     os.path.join(PP_VAULT, "session_lessons.md")),
    ("claude-power-pack", "errors",
     os.path.join(PP_VAULT, "errors.md")),
    ("claude-power-pack", "vaccines-governance",
     os.path.join(PP_VAULT, "governance_vaccines.md")),
    ("claude-power-pack", "vaccines-distiller",
     os.path.join(PP_VAULT, "distiller_vaccines.md")),
    ("claude-power-pack", "index",
     os.path.join(PP_VAULT, "UNIVERSAL_VAULT.md")),
    ("InfinityOps", "lessons",
     os.path.join(CURSOR_PROJECTS, "InfinityOps", "vault",
                  "knowledge_base", "session_lessons.md")),
    ("InfinityOps", "errors",
     os.path.join(CURSOR_PROJECTS, "InfinityOps", "vault",
                  "knowledge_base", "errors.md")),
    ("InfinityOps-spc", "lessons",
     os.path.join(CURSOR_PROJECTS, "InfinityOps-spc", "vault",
                  "knowledge_base", "session_lessons.md")),
    ("InfinityOps-spc", "errors",
     os.path.join(CURSOR_PROJECTS, "InfinityOps-spc", "vault",
                  "knowledge_base", "errors.md")),
    ("LaptOps", "lessons",
     os.path.join(CURSOR_PROJECTS, "LaptOps", "vault",
                  "knowledge_base", "session_lessons.md")),
    ("LaptOps", "errors",
     os.path.join(CURSOR_PROJECTS, "LaptOps", "vault",
                  "knowledge_base", "errors.md")),
    ("LuckyFly", "lessons",
     os.path.join(CURSOR_PROJECTS, "Minecraft Projects", "LuckyFly", "vault",
                  "knowledge_base", "session_lessons.md")),
    ("LuckyFly", "errors",
     os.path.join(CURSOR_PROJECTS, "Minecraft Projects", "LuckyFly", "vault",
                  "knowledge_base", "errors.md")),
    ("TUA-X", "lessons",
     os.path.join(CURSOR_PROJECTS, "TUA-X", "vault",
                  "knowledge_base", "session_lessons.md")),
    ("TUA-X", "errors",
     os.path.join(CURSOR_PROJECTS, "TUA-X", "vault",
                  "knowledge_base", "errors.md")),
    ("KobiiAI", "lessons",
     os.path.join(CURSOR_PROJECTS, "Vibe Coding Projects", "KobiiAI",
                  "vault", "knowledge_base", "session_lessons.md")),
    ("KobiiAI", "errors",
     os.path.join(CURSOR_PROJECTS, "Vibe Coding Projects", "KobiiAI",
                  "vault", "knowledge_base", "errors.md")),
    ("KobiiAI", "leyes",
     os.path.join(CURSOR_PROJECTS, "Vibe Coding Projects", "KobiiAI",
                  "knowledge", "leyes.md")),
    ("KobiiAI", "mistakes",
     os.path.join(CURSOR_PROJECTS, "Vibe Coding Projects", "KobiiAI",
                  "knowledge", "mistakes-registry.md")),
]


# 20-category transversal taxonomy. Each entry: (label, keyword_list).
# An entry matches a category if ANY keyword is a case-insensitive
# substring of the entry's (heading + body) text. Multi-tagging allowed.
TAXONOMY = [
    ("Anti-Thrash / Edit Discipline",
     ["anti-thrash", "edit-thrash", "3+ edits", "consecutive edits",
      "edit revert", "edit silently revert", "without re-read"]),
    ("Hook System / PreToolUse / PostToolUse",
     ["preToolUse", "postToolUse", "hook fire", "hook block",
      "hook denied", "hook error", "hook timeout", "stop hook",
      "sessionEnd", "sessionStart", "hookSpecificOutput",
      "additionalContext"]),
    ("Permission / Classifier / Auto-Mode",
     ["classifier", "auto-mode", "auto mode", "permission denied",
      "permissions.allow", "permissions.deny", "bypassPermissions",
      "self-modification", "self-mod", "settings.json"]),
    ("Path / Filesystem / Windows",
     ["OneDrive", "CRLF", "BOM", "utf-8-sig", "Windows",
      "Win11", "NTFS", "%APPDATA%", "%USERPROFILE%", "%LOCALAPPDATA%"]),
    ("SQLite / FTS5 / WAL",
     ["sqlite", "WAL", "fts5", "BM25", "PRAGMA",
      "state.vscdb", "trio-mtime", "rebuild trigger"]),
    ("Git / Branch / Push",
     ["git push", "git fetch", "git rebase", "git checkout",
      "git commit", "FF-only", "force-push", "anti-overlap",
      "git add -A", "scope commit"]),
    ("Mtime / SHA / Cursor Heuristics",
     ["mtime", "SHA-256", "SHA256", "cursor file", "stamp file",
      "hybrid cursor", "incremental"]),
    ("Process Sandbox / Bash / Shell",
     ["process-sandbox", "process sandbox", "bash sandbox",
      "PowerShell", "heredoc", "Git-Bash"]),
    ("Stop Hook / Heartbeat / Detached Spawn",
     ["detached", "unref", "fire-and-forget", "heartbeat",
      "vault-heartbeat", "spawn", "child.unref"]),
    ("Compaction / Context Pressure / Resume",
     ["compact", "compaction", "context pressure", "CONTEXT THRESHOLD",
      "/resume", "lazarus", "session resume"]),
    ("Reality Contract / Scaffold Illusion / Mistake 16",
     ["scaffold", "reality contract", "mistake #16", "Mistake 16",
      "Scaffold Illusion", "empty catch", "stub return", "vapor"]),
    ("Quality Gate / Pre-Commit / Verdict",
     ["quality gate", "pre-commit", "tsc --noEmit", "verdict",
      "verdict-A", "verdict-B", "OVO", "completion gate"]),
    ("Plan-First / Anti-Monolith / Approval",
     ["anti-monolith", "plan-first", "plan first", "Ley 26",
      "approval gate", "Q&A pass", "ULTRA plan"]),
    ("Encoding / Newlines / Heredoc",
     ["utf-8", "utf-16", "CRLF", "newline=", "BOM",
      "io.open", "encoding="]),
    ("Frontend / UI / Component",
     ["framer motion", "tailwind", "react", "next.js", "vue",
      "shadcn", "shader", "WebGL", "displacement"]),
    ("Architecture / Pattern / Doctrine",
     ["doctrine", "playbook", "architecture", "topology",
      "Cortex", "Bento", "Mythic-Holding"]),
    ("Token Budget / Vault Loading / Tiered",
     ["token budget", "tiered loading", "token austerity",
      "vault load", "context window"]),
    ("Race Condition / Concurrency / Mutex",
     ["race", "mutex", "mkdir-mutex", "concurrent",
      "session-once", "stale lock"]),
    ("Verification / Real-Input / Evidence",
     ["empirical evidence", "real input", "verification",
      "Ley 25", "Gate 7", "smoke test", "observed evidence"]),
    ("Subagent / Dispatch / Agent Team",
     ["subagent", "subagent_type", "Agent tool", "agent dispatch",
      "oneshot-architect-auditor", "Explore agent"]),
]


H2 = re.compile(r"^##\s+(?!#)(.+?)\s*$", re.MULTILINE)
DATE_IN_H = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
VACCINE = re.compile(
    r"\*\*Vaccine[:\.]?\*\*\s*([^\n]+(?:\n(?!\n).+)*)", re.IGNORECASE)


def read_text(path):
    try:
        with io.open(path, "r", encoding="utf-8-sig") as fh:
            return fh.read()
    except OSError:
        return ""


def split_entries(text):
    matches = list(H2.finditer(text))
    if not matches:
        return [("(whole file)", text.strip())] if text.strip() else []
    out = []
    lead = text[:matches[0].start()].strip()
    if lead:
        out.append(("(file preface)", lead))
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body or heading:
            out.append((heading, body))
    return out


def categorize(entry_text):
    low = entry_text.lower()
    hits = []
    for cat, kws in TAXONOMY:
        for kw in kws:
            if kw.lower() in low:
                hits.append(cat)
                break
    return hits


def extract_vaccines(body):
    return [m.group(1).strip().rstrip(".") + "."
            for m in VACCINE.finditer(body)]


def first_paragraph(body, max_chars=600):
    paras = re.split(r"\n\s*\n", body, maxsplit=2)
    p = paras[0].strip() if paras else ""
    if len(p) > max_chars:
        p = p[: max_chars - 1].rstrip() + "..."
    return p


def entry_date(heading):
    m = DATE_IN_H.search(heading)
    return m.group(1) if m else None


class Entry:
    __slots__ = ("project", "kind", "src_path", "heading", "body",
                 "categories", "vaccines", "date", "sha")

    def __init__(self, project, kind, src_path, heading, body):
        self.project = project
        self.kind = kind
        self.src_path = src_path
        self.heading = heading
        self.body = body
        self.categories = categorize(heading + "\n" + body)
        self.vaccines = extract_vaccines(body)
        self.date = entry_date(heading)
        self.sha = hashlib.sha256(
            (heading + "\n" + body).encode("utf-8")).hexdigest()[:12]


def harvest():
    entries = []
    stats = {
        "files_attempted": 0,
        "files_found": 0,
        "files_missing": [],
        "total_bytes": 0,
        "total_entries": 0,
        "by_project": collections.Counter(),
        "by_kind": collections.Counter(),
        "by_category": collections.Counter(),
        "vaccines_count": 0,
    }
    for project, kind, path in SOURCES:
        stats["files_attempted"] += 1
        if not os.path.isfile(path):
            stats["files_missing"].append(path)
            continue
        stats["files_found"] += 1
        text = read_text(path)
        stats["total_bytes"] += len(text.encode("utf-8"))
        for heading, body in split_entries(text):
            if not body and len(heading) < 4:
                continue
            e = Entry(project, kind, path, heading, body)
            entries.append(e)
            stats["by_project"][project] += 1
            stats["by_kind"][kind] += 1
            for c in e.categories:
                stats["by_category"][c] += 1
            stats["vaccines_count"] += len(e.vaccines)
    stats["total_entries"] = len(entries)
    return entries, stats


def _wrap_header(title, intro):
    today = dt.date.today().isoformat()
    return (
        "# " + title + "\n\n"
        "_Generated by `tools/dataset_enricher.py` on " + today + ". "
        "Source-of-truth: every knowledge_base / mistakes / lessons file "
        "under the canonical Power-Pack vault and per-project vaults._\n\n"
        + intro + "\n\n---\n\n"
    )


def _entry_block(e, idx):
    cats = ", ".join(e.categories) if e.categories else "_(uncategorized)_"
    date_str = e.date or "_(undated)_"
    purpose = first_paragraph(e.body, 600)
    if not purpose:
        purpose = "_(no body content beyond heading)_"
    vaccines_block = ""
    if e.vaccines:
        vlist = "\n".join("  - " + v for v in e.vaccines)
        vaccines_block = "\n**Vaccines (extracted):**\n" + vlist + "\n"
    return (
        "### [" + ("%04d" % idx) + "] " + e.heading + "\n\n"
        "**Provenance:** `" + e.project + "` :: `" + e.kind + "` :: `"
        + os.path.basename(e.src_path) + "`  \n"
        "**Date:** " + date_str + "  \n"
        "**Categories:** " + cats + "  \n"
        "**SHA12:** `" + e.sha + "`\n\n"
        "**What it captures (gloss):** " + purpose + "\n"
        + vaccines_block + "\n"
        "<details><summary>Full original entry (verbatim)</summary>\n\n"
        "```markdown\n## " + e.heading + "\n\n" + e.body + "\n```\n\n"
        "</details>\n\n---\n\n"
    )


def write_errors_catalog(entries, stats, out_dir):
    err_entries = [e for e in entries
                   if e.kind in ("errors", "mistakes")
                   or any("error" in c.lower() or "mistake" in c.lower()
                          or "reality contract" in c.lower()
                          for c in e.categories)]
    err_entries.sort(key=lambda e: (e.project, e.heading))
    out_path = os.path.join(out_dir, "UNIVERSAL-ERRORS-CATALOG.md")
    intro = (
        "Every error / mistake / failure-mode entry harvested across all "
        "tracked knowledge vaults, normalized to a single catalog. Each "
        "entry shows its source project, kind, date (extracted from the "
        "heading if dated), categories matched in the transversal "
        "taxonomy, a synthesized gloss of what it captures, any vaccines "
        "found via the `**Vaccine**` pattern, and the full verbatim "
        "entry in a collapsed details block.\n\n"
        "**Total errors/mistakes entries in this catalog:** "
        + str(len(err_entries)) + ". **Generation provenance:** see "
        "DATASET_INDEX.md for the full source manifest."
    )
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(_wrap_header("Universal Errors Catalog", intro))
        by_proj = collections.defaultdict(list)
        for e in err_entries:
            by_proj[e.project].append(e)
        idx = 1
        for proj in sorted(by_proj):
            fh.write("## Project: " + proj + "\n\n")
            for e in by_proj[proj]:
                fh.write(_entry_block(e, idx))
                idx += 1
    print("  WROTE " + out_path + " (" + str(os.path.getsize(out_path))
          + " bytes, " + str(len(err_entries)) + " entries)")


def write_lessons_compendium(entries, stats, out_dir):
    lesson_entries = [e for e in entries
                      if e.kind in ("lessons", "leyes")
                      or e.kind.startswith("vaccines")
                      or e.kind == "index"]
    lesson_entries.sort(key=lambda e: (e.date or "0000-00-00",
                                        e.project, e.heading))
    out_path = os.path.join(out_dir, "UNIVERSAL-LESSONS-COMPENDIUM.md")
    intro = (
        "Every session-lesson, vaccine, doctrine, and law entry across "
        "all projects, ordered chronologically when dated and grouped "
        "by project otherwise. Lessons are operational learnings; "
        "vaccines are the preventive form of a lesson; leyes/laws are "
        "durable governance constants. Each entry exposes its "
        "transversal categories so cross-project pattern search works.\n\n"
        "**Total lessons/laws/vaccines entries:** "
        + str(len(lesson_entries)) + ". **Total vaccines extracted from "
        "bodies:** " + str(stats['vaccines_count']) + ". Feed into "
        "`/cpp-compound` for the Compound Learnings flywheel."
    )
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(_wrap_header("Universal Lessons Compendium", intro))
        by_year = collections.defaultdict(
            lambda: collections.defaultdict(list))
        undated = collections.defaultdict(list)
        for e in lesson_entries:
            if e.date:
                year = e.date[:7]
                by_year[year][e.project].append(e)
            else:
                undated[e.project].append(e)
        idx = 1
        for year in sorted(by_year):
            fh.write("## Window: " + year + "\n\n")
            for proj in sorted(by_year[year]):
                fh.write("### " + proj + "\n\n")
                for e in by_year[year][proj]:
                    fh.write(_entry_block(e, idx))
                    idx += 1
        if undated:
            fh.write("## Undated entries\n\n")
            for proj in sorted(undated):
                fh.write("### " + proj + "\n\n")
                for e in undated[proj]:
                    fh.write(_entry_block(e, idx))
                    idx += 1
    print("  WROTE " + out_path + " (" + str(os.path.getsize(out_path))
          + " bytes, " + str(len(lesson_entries)) + " entries)")


def write_cross_project_patterns(entries, stats, out_dir):
    cat_to_projects = collections.defaultdict(set)
    cat_to_entries = collections.defaultdict(list)
    for e in entries:
        for c in e.categories:
            cat_to_projects[c].add(e.project)
            cat_to_entries[c].append(e)
    transversal = sorted(
        ((c, len(cat_to_projects[c]), len(cat_to_entries[c]))
         for c in cat_to_projects if len(cat_to_projects[c]) >= 2),
        key=lambda t: (-t[1], -t[2], t[0])
    )
    out_path = os.path.join(out_dir, "CROSS-PROJECT-PATTERNS.md")
    intro = (
        "Patterns that recur across two or more independent projects -- "
        "the durable cross-project signal. Sorted by project-breadth "
        "then frequency. For each pattern: a one-line definition, "
        "the projects it spans, the keyword cluster that detected it, "
        "and the top entries (one per project) that exemplify it.\n\n"
        "**Transversal patterns surfaced:** " + str(len(transversal))
        + " of " + str(len(TAXONOMY)) + " taxonomy categories. "
        "**Project space scanned:** "
        + ", ".join(sorted(stats['by_project'].keys())) + "."
    )
    cat_kws = {name: kws for name, kws in TAXONOMY}
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(_wrap_header("Cross-Project Patterns", intro))
        for cat, n_proj, n_entries in transversal:
            kws = cat_kws.get(cat, [])
            fh.write("## " + cat + "\n\n")
            fh.write("**Project breadth:** " + str(n_proj) + " projects  \n")
            fh.write("**Total entries hit:** " + str(n_entries) + "  \n")
            projs = sorted(cat_to_projects[cat])
            fh.write("**Projects:** " + ", ".join(projs) + "  \n")
            display_kws = kws[:6]
            fh.write("**Keyword cluster:** "
                     + ", ".join("`" + k + "`" for k in display_kws)
                     + (" ..." if len(kws) > 6 else "") + "\n\n")
            fh.write("**Exemplar entries (one per project):**\n\n")
            seen_proj = set()
            for e in cat_to_entries[cat]:
                if e.project in seen_proj:
                    continue
                seen_proj.add(e.project)
                gloss = first_paragraph(e.body, 280) or e.heading
                fh.write("- **" + e.project + "** -- *" + e.heading[:80]
                         + "*  \n  SHA12 `" + e.sha + "`. " + gloss + "\n\n")
            fh.write("---\n\n")
    print("  WROTE " + out_path + " (" + str(os.path.getsize(out_path))
          + " bytes, " + str(len(transversal)) + " transversal patterns)")


def write_index(entries, stats, out_dir):
    out_path = os.path.join(out_dir, "DATASET_INDEX.md")
    today = dt.date.today().isoformat()
    proj_lines = "\n".join(
        "- **" + p + "** -- " + str(c) + " entries"
        for p, c in sorted(stats["by_project"].items(),
                            key=lambda t: -t[1]))
    kind_lines = "\n".join(
        "- **" + k + "** -- " + str(c) + " entries"
        for k, c in sorted(stats["by_kind"].items(), key=lambda t: -t[1]))
    cat_lines = "\n".join(
        "- **" + c + "** -- " + str(n) + " entries"
        for c, n in sorted(stats["by_category"].items(),
                            key=lambda t: -t[1]))
    src_lines = "\n".join(
        "- `" + path + "` -- (" + proj + "/" + kind + ")"
        for proj, kind, path in SOURCES)
    missing = stats["files_missing"]
    miss_block = ""
    if missing:
        miss_block = ("### Sources missing at generation time\n\n"
                      + "\n".join("- `" + m + "`" for m in missing)
                      + "\n\n")
    body_md = (
        "# Dataset Index -- PowerPack Sovereign Datasets (Enriched)\n\n"
        "**Generated:** " + today + "\n"
        "**Generator:** `tools/dataset_enricher.py` (run with `--build`)\n"
        "**Output directory:** `" + out_dir + "`\n\n"
        "## Companion files (regenerated by this tool)\n\n"
        "- `UNIVERSAL-ERRORS-CATALOG.md` -- every error/mistake entry, source-tagged, categorized, glossed.\n"
        "- `UNIVERSAL-LESSONS-COMPENDIUM.md` -- every lesson / vaccine / doctrine, chronological where dated.\n"
        "- `CROSS-PROJECT-PATTERNS.md` -- patterns recurring across >=2 projects (transversal signal).\n"
        "- `DATASET_INDEX.md` -- this file.\n\n"
        "## Sibling datasets (legacy, hand-curated, unchanged)\n\n"
        "- `UNIVERSAL-TRANSCRIPT-LAWS.TXT` -- 25 emergent laws from 2,121 transcripts.\n"
        "- `FRONTEND-CAPABILITIES.TXT` -- stack matrix across all Cursor Projects.\n"
        "- `POWER-PACK-POTENTIAL.TXT` -- ROI inventory.\n"
        "- `RESUME-UPGRADE-SPEC.TXT` -- Lazarus v3 feature spec.\n"
        "- `TOTAL-RECALL-MANIFEST.TXT` -- corpus coverage stats.\n"
        "- `MANIFEST.json` -- sovereign_miner extraction metadata.\n"
        "- `SOVEREIGN-HISTORY-VAULT.{db,jsonl}` -- the 45,625-row session corpus.\n\n"
        "## Generation stats\n\n"
        "- **Source files attempted:** " + str(stats["files_attempted"]) + "\n"
        "- **Source files found:** " + str(stats["files_found"]) + "\n"
        "- **Total source bytes:** " + ("{:,}".format(stats["total_bytes"])) + "\n"
        "- **Total entries harvested:** " + str(stats["total_entries"]) + "\n"
        "- **Total vaccines extracted from bodies:** " + str(stats["vaccines_count"]) + "\n\n"
        "### By project\n" + proj_lines + "\n\n"
        "### By kind (file role)\n" + kind_lines + "\n\n"
        "### By transversal category\n" + cat_lines + "\n\n"
        + miss_block
        + "### Source manifest\n" + src_lines + "\n\n"
        "## How the enrichment works (deterministic, zero-LLM)\n\n"
        "1. **Harvest.** Each source file is read with `utf-8-sig` (BOM-tolerant) and sliced on `^## ` H2 headers as the atomic-entry boundary. Pre-first-H2 content is preserved. Files without any H2 become a single entry so nothing is lost.\n"
        "2. **Tag.** Each entry's full text is scanned against the 20-category transversal taxonomy. An entry can carry multiple category tags.\n"
        "3. **Gloss.** The first paragraph of the body becomes the *gloss* -- a faithful, deterministic synthesis of what the entry captures.\n"
        "4. **Extract vaccines.** Body text is scanned for `**Vaccine:**` patterns (case-insensitive).\n"
        "5. **Transversal detection.** A category that hits entries from >=2 distinct projects is promoted to a cross-project pattern.\n"
        "6. **Provenance preserved.** Every entry carries project, kind, src_path, date, categories, and SHA12. Originals appear verbatim in a collapsed details block.\n\n"
        "## Regeneration contract\n\n"
        "Run `python tools/dataset_enricher.py --build` to refresh. Idempotent. Adding a new project: append a tuple to `SOURCES`. Adding a new category: append a tuple to `TAXONOMY`.\n\n"
        "## Honest limits\n\n"
        "- The gloss is the first paragraph of the body. If the body's first paragraph is meta-commentary, the gloss will mirror that.\n"
        "- The taxonomy is a keyword classifier, not an LLM. Synonyms not in the keyword cluster will miss.\n"
        "- The generator does NOT mutate source files. It only reads and writes the four output files.\n"
        "- Binary files (`SOVEREIGN-HISTORY-VAULT.db`, `.jsonl`) are NOT enriched here. Use `tools/vault_search.py --search` for fuzzy retrieval.\n"
    )
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body_md)
    print("  WROTE " + out_path + " (" + str(os.path.getsize(out_path))
          + " bytes)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true",
                    help="harvest + write all 4 enriched datasets")
    ap.add_argument("--list-sources", action="store_true",
                    help="show source manifest + path existence")
    ap.add_argument("--out", default=OUT_DIR,
                    help="output directory")
    args = ap.parse_args()

    if args.list_sources:
        for proj, kind, path in SOURCES:
            ok = "OK" if os.path.isfile(path) else "MISSING"
            sz = os.path.getsize(path) if os.path.isfile(path) else 0
            print("  [" + ok.ljust(7) + "] " + proj.ljust(18) + " "
                  + kind.ljust(22) + " (" + str(sz).rjust(6) + " B) " + path)
        return 0

    if not args.build:
        ap.print_help()
        return 2

    os.makedirs(args.out, exist_ok=True)
    print("=== dataset_enricher: harvesting " + str(len(SOURCES))
          + " sources ===")
    entries, stats = harvest()
    print("  found " + str(stats['files_found']) + "/"
          + str(stats['files_attempted']) + " files, "
          + str(stats['total_entries']) + " entries, "
          + ("{:,}".format(stats['total_bytes'])) + " source bytes, "
          + str(stats['vaccines_count']) + " vaccines")
    if stats["files_missing"]:
        print("  MISSING (" + str(len(stats['files_missing'])) + "):")
        for m in stats["files_missing"]:
            print("    - " + m)
    print("=== writing 4 enriched datasets ===")
    write_errors_catalog(entries, stats, args.out)
    write_lessons_compendium(entries, stats, args.out)
    write_cross_project_patterns(entries, stats, args.out)
    write_index(entries, stats, args.out)
    print("=== ENRICHMENT COMPLETE ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
