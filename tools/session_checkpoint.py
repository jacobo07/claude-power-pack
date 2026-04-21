#!/usr/bin/env python3
"""Session Checkpoint — transactional /kclear backend.

Replaces the 6-step kclear flow with one atomic invocation.
Writes handoff + MEMORY.md index + insights.json in a single pass.

Subcommands:
    record   Read payload JSON (stdin or --input), write handoff and append insights.
    migrate  One-shot: ingest legacy memory/{feedback,project,reference,user}_*.md
             into _audit_cache/insights.json. Archives originals under
             memory/cold_storage/migrated_<date>/.
    list     Print the insights database.

Payload schema (record):
    {"session_id": str, "date": "YYYY-MM-DD",
     "summary": "markdown body",
     "pending": ["str", ...] | [{"title": str, "detail": str}, ...],
     "insights": [{"category": str, "title": str, "body": str,
                   "path": Optional[str], "tags": [str, ...]}, ...]}

Atomicity: every write is tmp-file + os.replace (atomic on Windows + POSIX).
Dedup: SHA256(category|title|body)[:16] as insight ID; duplicates skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PROJECT_MARKERS = ["SKILL.md", ".git", "pyproject.toml", "package.json", "CLAUDE.md", ".claude", ".vscode"]
HANDOFF_NAME = "project_session_handoff.md"
MEMORY_INDEX_NAME = "MEMORY.md"
INSIGHTS_REL = "_audit_cache/insights.json"
INSIGHTS_SCHEMA = "insights-v1"

# Vault knowledge base — project-local, Obsidian-compatible atomic learning store.
# Keeps MEMORY.md lean (index only) while per-session lessons and corrected errors
# accumulate in append-only vault files.
VAULT_KB_REL = "vault/knowledge_base"
VAULT_LESSONS_NAME = "session_lessons.md"
VAULT_ERRORS_NAME = "errors.md"
VAULT_LESSON_MAX = 600      # hard cap per atomic lesson (chars)
VAULT_ERROR_MAX = 400       # hard cap per corrected-error line (chars)


def find_project_root(start: Path) -> Path:
    """Walk up from `start` looking for any PROJECT_MARKERS, skipping the user
    home directory (whose CLAUDE.md is global governance, not a project marker).
    """
    home = Path.home().resolve()
    for d in [start.resolve(), *start.resolve().parents]:
        # Never treat the user home as a project root — its CLAUDE.md is global.
        if d == home:
            continue
        if any((d / m).exists() for m in PROJECT_MARKERS):
            return d
    raise SystemExit(
        f"[checkpoint] project root not found (looked for {PROJECT_MARKERS}). "
        f"Create an empty `.claude/` dir in the project root to anchor it."
    )


def claude_project_slug(root: Path) -> str:
    """Reproduce Claude Code's project-dir slug: every [:\\/.]  -> '-'."""
    return re.sub(r"[:\\/.]", "-", str(root.resolve()))


def get_memory_dir(root: Path) -> Path:
    """Prefer ./memory/ if present; else Claude's ~/.claude/projects/<slug>/memory/."""
    local = root / "memory"
    if local.exists():
        return local
    return Path.home() / ".claude" / "projects" / claude_project_slug(root) / "memory"


def atomic_write(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, target)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def insight_id(category: str, title: str, body: str) -> str:
    h = hashlib.sha256(f"{category}|{title}|{body}".encode("utf-8")).hexdigest()[:16]
    return f"insight_{h}"


def load_insights(root: Path) -> dict:
    path = root / INSIGHTS_REL
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"schema": INSIGHTS_SCHEMA, "entries": []}
    return {"schema": INSIGHTS_SCHEMA, "entries": []}


def save_insights(root: Path, data: dict) -> None:
    atomic_write(root / INSIGHTS_REL, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def append_insights(root: Path, new_entries: list, session_id: str, date: str) -> tuple[int, int]:
    db = load_insights(root)
    existing_ids = {e["id"] for e in db["entries"]}
    added = 0
    skipped = 0
    for raw in new_entries:
        category = raw.get("category") or "unknown"
        title = raw.get("title") or "(untitled)"
        body = raw.get("body") or ""
        iid = insight_id(category, title, body)
        if iid in existing_ids:
            skipped += 1
            continue
        db["entries"].append({
            "id": iid,
            "session_id": session_id,
            "date": date,
            "category": category,
            "title": title,
            "body": body,
            "path": raw.get("path"),
            "tags": raw.get("tags") or [],
        })
        existing_ids.add(iid)
        added += 1
    save_insights(root, db)
    return added, skipped


def render_handoff(payload: dict) -> str:
    date = payload.get("date") or datetime.now().strftime("%Y-%m-%d")
    session_id = payload.get("session_id") or "unknown"
    lines = [
        f"# Session Handoff — {date}",
        "",
        f"**Session ID**: `{session_id}`",
        "",
        "## Summary",
        "",
        (payload.get("summary") or "(no summary provided)").rstrip(),
        "",
    ]
    pending = payload.get("pending") or []
    if pending:
        lines += ["## Pending", ""]
        for i, p in enumerate(pending, 1):
            if isinstance(p, str):
                lines.append(f"{i}. {p}")
            elif isinstance(p, dict):
                lines.append(f"{i}. **{p.get('title','?')}** — {p.get('detail','')}")
        lines.append("")
    insights = payload.get("insights") or []
    if insights:
        lines += ["## Insights captured", ""]
        for e in insights:
            lines.append(f"- **{e.get('category','?')}**: {e.get('title','?')}")
        lines.append("")
    return "\n".join(lines)


def vault_kb_dir(root: Path) -> Path:
    """Project-local vault/knowledge_base — created on first write."""
    return root / VAULT_KB_REL


def ensure_vault_kb(root: Path) -> Path:
    """Create vault/knowledge_base/ skeleton if absent. Returns the dir."""
    kb = vault_kb_dir(root)
    kb.mkdir(parents=True, exist_ok=True)
    lessons = kb / VAULT_LESSONS_NAME
    if not lessons.exists():
        atomic_write(lessons, (
            "# Session Lessons — Atomic Learning\n\n"
            "Append-only log of concrete, non-derivable learnings per session.\n"
            "One entry per `/kclear` with a `lesson` field. Keep each entry short and\n"
            "self-contained — if a future reader can't grok it without the conversation,\n"
            "rewrite it.\n\n"
            "---\n\n"
        ))
    errors = kb / VAULT_ERRORS_NAME
    if not errors.exists():
        atomic_write(errors, (
            "# Corrected Errors — Learning Log\n\n"
            "Append-only log of bugs/misfires the assistant made and the fix.\n"
            "One line per entry: `YYYY-MM-DD [category] symptom -> root cause -> fix`.\n\n"
            "---\n\n"
        ))
    return kb


def append_lesson(root: Path, date: str, session_id: str, title: str, body: str) -> Path:
    """Append one atomic lesson entry. Returns target file path."""
    ensure_vault_kb(root)
    target = vault_kb_dir(root) / VAULT_LESSONS_NAME
    body = (body or "").strip()
    if len(body) > VAULT_LESSON_MAX:
        body = body[: VAULT_LESSON_MAX - 1] + "…"
    title = (title or "(untitled lesson)").strip()
    entry = (
        f"## {date} — {title}\n\n"
        f"**Session:** `{session_id}`\n\n"
        f"{body}\n\n"
        "---\n\n"
    )
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    atomic_write(target, existing + entry)
    return target


def append_error_line(root: Path, date: str, category: str, symptom: str, root_cause: str, fix: str) -> Path:
    """Append one 1-line corrected-error entry."""
    ensure_vault_kb(root)
    target = vault_kb_dir(root) / VAULT_ERRORS_NAME
    line = f"- {date} [{category or 'misc'}] {symptom} -> {root_cause} -> {fix}"
    if len(line) > VAULT_ERROR_MAX:
        line = line[: VAULT_ERROR_MAX - 1] + "…"
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    atomic_write(target, existing + line + "\n")
    return target


def update_memory_index(root: Path, date: str, headline: str) -> None:
    path = get_memory_dir(root) / MEMORY_INDEX_NAME
    entry = f"- [Session Handoff {date}](project_session_handoff.md) — {headline}"
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        # Drop any prior "Session Handoff" index line; keep everything else.
        kept = [ln for ln in lines if not ln.lstrip().startswith("- [Session Handoff")]
        kept.insert(0, entry)
        atomic_write(path, "\n".join(kept).rstrip() + "\n")
    else:
        atomic_write(path, entry + "\n")


def cmd_record(args) -> int:
    root = find_project_root(Path.cwd())
    if args.stdin:
        payload = json.loads(sys.stdin.read())
    else:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))

    date = payload.get("date") or datetime.now().strftime("%Y-%m-%d")
    session_id = payload.get("session_id") or "unknown"

    handoff_path = get_memory_dir(root) / HANDOFF_NAME
    atomic_write(handoff_path, render_handoff(payload))
    added, skipped = append_insights(root, payload.get("insights") or [], session_id, date)

    summary_first_line = ((payload.get("summary") or "").strip().splitlines() or [""])[0]
    headline = summary_first_line.lstrip("#").strip()[:140] or "session handoff"
    update_memory_index(root, date, headline)

    # Optional atomic lesson: append one entry to vault/knowledge_base/session_lessons.md.
    # Payload format: "lesson" can be a string (becomes body, title derived from headline)
    # OR {"title": str, "body": str}.
    lesson_path = None
    lesson = payload.get("lesson")
    if lesson:
        if isinstance(lesson, str):
            lesson_title = headline[:80] or "session lesson"
            lesson_body = lesson
        else:
            lesson_title = (lesson.get("title") or headline)[:80] or "session lesson"
            lesson_body = lesson.get("body") or ""
        lesson_path = append_lesson(root, date, session_id, lesson_title, lesson_body)

    msg = (
        f"[checkpoint] handoff -> {handoff_path} | "
        f"insights: +{added} dup-skip {skipped} | index updated"
    )
    if lesson_path:
        msg += f" | lesson -> {lesson_path}"
    print(msg)
    return 0


def cmd_learn_error(args) -> int:
    """Append one 1-line corrected-error entry to vault/knowledge_base/errors.md."""
    root = find_project_root(Path.cwd())
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    target = append_error_line(
        root,
        date=date,
        category=args.category or "misc",
        symptom=args.symptom,
        root_cause=args.root_cause,
        fix=args.fix,
    )
    print(f"[checkpoint] error learned -> {target}")
    return 0


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---", 4)
    if end == -1:
        return {}, raw
    fm: dict = {}
    for ln in raw[4:end].splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            fm[k.strip()] = v.strip()
    body_start = end + len("\n---")
    if raw[body_start:body_start + 1] == "\n":
        body_start += 1
    return fm, raw[body_start:].lstrip()


def cmd_migrate(args) -> int:
    root = find_project_root(Path.cwd())
    memory_dir = get_memory_dir(root)
    if not memory_dir.exists():
        print(f"[migrate] no memory/ dir at {memory_dir}")
        return 1

    patterns = ["feedback_*.md", "project_*.md", "reference_*.md", "user_*.md"]
    files: list[Path] = []
    for p in patterns:
        files.extend(memory_dir.glob(p))

    skip_names = {"MEMORY.md", "project_session_handoff.md"}
    files = [f for f in files if f.name not in skip_names]

    if not files:
        print("[migrate] no legacy files found")
        return 0

    entries: list[dict] = []
    for f in files:
        raw = f.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(raw)
        category = fm.get("type") or f.stem.split("_")[0]
        title = fm.get("name") or f.stem.replace("_", " ")
        entries.append({
            "category": category,
            "title": title,
            "body": body.strip(),
            "tags": [],
        })

    if args.dry_run:
        print(f"[migrate] DRY-RUN: {len(entries)} entries would migrate from {len(files)} files")
        for e in entries:
            print(f"  [{e['category']:10}] {e['title']}")
        return 0

    archive = memory_dir / "cold_storage" / f"migrated_{datetime.now().strftime('%Y-%m-%d')}"
    archive.mkdir(parents=True, exist_ok=True)
    for f in files:
        target = archive / f.name
        f.rename(target)

    added, skipped = append_insights(
        root, entries,
        session_id="migration",
        date=datetime.now().strftime("%Y-%m-%d"),
    )
    print(
        f"[migrate] moved {len(files)} files -> {archive} | "
        f"insights: +{added} dup-skip {skipped}"
    )
    return 0


def cmd_list(args) -> int:
    root = find_project_root(Path.cwd())
    db = load_insights(root)
    print(f"Insights: {len(db['entries'])} entries (schema={db.get('schema','?')})")
    for e in db["entries"]:
        path = f" path={e['path']}" if e.get("path") else ""
        print(f"  [{e['category']:10}] {e['id']} {e['date']} {e['title']}{path}")
    return 0


def main() -> None:
    # Force UTF-8 on stdin/stdout. Windows Git Bash and cmd default to the console
    # code page (often CP1252), which mangles em-dashes and other non-ASCII in
    # heredoc-piped JSON payloads. Reconfigure is available on Python 3.7+.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description="Session Checkpoint — /kclear transactional backend.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="Write handoff + insights from payload JSON.")
    g = rec.add_mutually_exclusive_group(required=True)
    g.add_argument("--stdin", action="store_true", help="Read payload from stdin.")
    g.add_argument("--input", help="Read payload from JSON file path.")
    rec.set_defaults(func=cmd_record)

    mig = sub.add_parser("migrate", help="Ingest legacy memory/*.md into insights.json.")
    mig.add_argument("--dry-run", action="store_true", help="Report what would migrate without moving files.")
    mig.set_defaults(func=cmd_migrate)

    lst = sub.add_parser("list", help="Print insights database.")
    lst.set_defaults(func=cmd_list)

    le = sub.add_parser("learn-error", help="Append 1-line corrected-error entry to vault/knowledge_base/errors.md.")
    le.add_argument("--category", help="Short tag (e.g. 'windows', 'hook-json', 'regex'). Default: misc.")
    le.add_argument("--symptom", required=True, help="What broke (user-visible).")
    le.add_argument("--root-cause", required=True, help="Why it broke (technical cause).")
    le.add_argument("--fix", required=True, help="What fixed it (one-line action).")
    le.add_argument("--date", help="YYYY-MM-DD override; default: today.")
    le.set_defaults(func=cmd_learn_error)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
