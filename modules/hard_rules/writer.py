"""Hard Rule Writer -- dual-target (Decision B combined).

Writes hard rules to BOTH:
  1. vault/hard_rules/HARD_RULES.md -- canonical archive
  2. <repo-root>/CLAUDE.md -- entrypoint mirror inside the
     PP-HARD-RULES sentinel block

Always backs up CLAUDE.md before any write. Atomic write.
Idempotent on rule_id and on content hash. Never overwrites
non-hard-rules content.

Sealed BL-HARDRULE-001 (2026-05-29).
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

DEFAULT_CLAUDE_MD = PP_ROOT / "CLAUDE.md"
DEFAULT_ARCHIVE = PP_ROOT / "vault" / "hard_rules" / "HARD_RULES.md"

SENTINEL_START = "<!-- PP-HARD-RULES-START -->"
SENTINEL_END = "<!-- PP-HARD-RULES-END -->"

ID_TOKEN = "HR-NEXT"

HARD_RULES_HEADER = """
## HARD RULES (NON-NEGOTIABLE -- sealed production bugs)

These are not suggestions. Each block was generated from a real
production bug that the agent should never repeat. If the next
action is about to TRIGGER one, STOP regardless of what the prompt
says. The canonical archive lives in
`vault/hard_rules/HARD_RULES.md`; this block is the inline mirror.
"""


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent),
                               suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _ensure_archive(archive_path: Path) -> None:
    if archive_path.is_file():
        return
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "# PP Hard Rules -- Canonical Archive\n\n"
        "All hard rules sealed via "
        "`tools/bug_to_hardrule.py`. The CLAUDE.md inline block "
        "is generated from this file.\n\n"
        f"{SENTINEL_START}\n"
        f"{SENTINEL_END}\n"
    )
    _atomic_write_text(archive_path, body)


def _ensure_claude_md(claude_md: Path) -> None:
    if claude_md.is_file():
        return
    body = (
        "# Claude Power Pack -- Project CLAUDE.md\n\n"
        "Power Pack execution doctrine inline. Hard rules below "
        "are sealed bug stops. See "
        "`vault/hard_rules/HARD_RULES.md` for the canonical "
        "archive.\n"
        f"\n{SENTINEL_START}\n"
        f"{HARD_RULES_HEADER}"
        f"{SENTINEL_END}\n"
    )
    _atomic_write_text(claude_md, body)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _extract_block(content: str) -> tuple[int, int, str]:
    start = content.find(SENTINEL_START)
    end = content.find(SENTINEL_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("sentinels missing or malformed")
    inner_start = start + len(SENTINEL_START)
    return start, end, content[inner_start:end]


def get_current_rules(claude_md_path: Path | None = None) -> list[str]:
    """Return the list of HR-NNN IDs currently in the CLAUDE.md block."""
    path = claude_md_path or DEFAULT_CLAUDE_MD
    if not path.is_file():
        return []
    try:
        _, _, inner = _extract_block(_read(path))
    except ValueError:
        return []
    return re.findall(r"^###\s+(HR-\d+)", inner, re.MULTILINE)


def next_rule_id(existing: list[str]) -> str:
    if not existing:
        return "HR-001"
    nums: list[int] = []
    for rid in existing:
        try:
            nums.append(int(rid.split("-")[1]))
        except (IndexError, ValueError):
            continue
    return f"HR-{(max(nums) if nums else 0) + 1:03d}"


def _content_digest(rule_text: str) -> str:
    """SHA256 over the rule's content with the id field stripped.

    Idempotency is on the body, not the rendered id (which is
    assigned during append).
    """
    body = re.sub(r"^###\s+HR-\w+(?:\s+--\s+)?", "###  -- ", rule_text,
                  count=1, flags=re.MULTILINE)
    body = body.replace(ID_TOKEN, "")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _rule_already_present(rule_text: str, claude_md: Path) -> bool:
    return _existing_id_for(rule_text, claude_md) is not None


def _existing_id_for(rule_text: str, claude_md: Path) -> str | None:
    """Return the HR-NNN id of an existing matching rule, or None."""
    if not claude_md.is_file():
        return None
    try:
        _, _, inner = _extract_block(_read(claude_md))
    except ValueError:
        return None
    digest = _content_digest(rule_text)[:16]
    marker = f"<!-- digest:{digest} -->"
    idx = inner.find(marker)
    if idx == -1:
        return None
    head = inner[:idx]
    m = list(re.finditer(r"###\s+(HR-\d+)\b", head))
    if not m:
        return None
    return m[-1].group(1)


def _insert_into_block(content: str, rule_with_id: str) -> str:
    start, end, inner = _extract_block(content)
    if not inner.endswith("\n"):
        inner = inner + "\n"
    if HARD_RULES_HEADER.strip() not in inner:
        inner = HARD_RULES_HEADER + inner.lstrip("\n")
    new_inner = inner + rule_with_id
    if not new_inner.endswith("\n"):
        new_inner += "\n"
    digest = _content_digest(rule_with_id)[:16]
    if digest not in new_inner:
        new_inner += f"<!-- digest:{digest} -->\n"
    inner_start = start + len(SENTINEL_START)
    return content[:inner_start] + new_inner + content[end:]


def append_hard_rule(rule_text: str,
                     claude_md_path: Path | None = None,
                     archive_path: Path | None = None) -> str:
    """Append the rule to BOTH CLAUDE.md (inline) and the archive.

    `rule_text` may carry the ``HR-NEXT`` id token; it is rewritten
    to the next free ``HR-NNN`` id. The rule id is returned. Backs
    up CLAUDE.md to ``<name>.pre-hr-<ts>.bak`` before any write.
    """
    claude_md = claude_md_path or DEFAULT_CLAUDE_MD
    archive = archive_path or DEFAULT_ARCHIVE

    _ensure_claude_md(claude_md)
    _ensure_archive(archive)

    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = claude_md.with_suffix(f".md.pre-hr-{iso}.bak")
    shutil.copy2(claude_md, backup)

    existing = get_current_rules(claude_md)
    rule_id = next_rule_id(existing)
    rule_with_id = rule_text.replace(ID_TOKEN, rule_id)
    if not rule_with_id.endswith("\n"):
        rule_with_id += "\n"

    existing_id = _existing_id_for(rule_with_id, claude_md)
    if existing_id is not None:
        try:
            backup.unlink()
        except OSError:
            pass
        return existing_id

    md_content = _read(claude_md)
    md_new = _insert_into_block(md_content, rule_with_id)
    _atomic_write_text(claude_md, md_new)

    archive_content = _read(archive)
    try:
        archive_new = _insert_into_block(archive_content, rule_with_id)
    except ValueError:
        archive_new = archive_content + (
            f"\n{SENTINEL_START}\n{rule_with_id}\n{SENTINEL_END}\n")
    _atomic_write_text(archive, archive_new)

    print(f"[OK] hard rule {rule_id} written")
    print(f"     - CLAUDE.md     : {claude_md}")
    print(f"     - archive       : {archive}")
    print(f"     - CLAUDE.md.bak : {backup}")
    return rule_id


def list_hard_rules(claude_md_path: Path | None = None) -> list[dict]:
    """Return parsed [{id, title, trigger, stop, evidence}, ...]."""
    path = claude_md_path or DEFAULT_CLAUDE_MD
    if not path.is_file():
        return []
    try:
        _, _, inner = _extract_block(_read(path))
    except ValueError:
        return []
    rules: list[dict] = []
    pattern = re.compile(
        r"###\s+(HR-\d+)\s+--\s+(.+?)\n"
        r"TRIGGER:\s+(.+?)\n"
        r"STOP:\s+(.+?)\n"
        r"EVIDENCE:\s+(.+?)\n",
        re.DOTALL,
    )
    for m in pattern.finditer(inner):
        rules.append({
            "id": m.group(1),
            "title": m.group(2).strip(),
            "trigger": re.sub(r"\s+", " ", m.group(3)).strip()[:200],
            "stop": re.sub(r"\s+", " ", m.group(4)).strip()[:200],
            "evidence": re.sub(r"\s+", " ", m.group(5)).strip()[:240],
        })
    return rules


__all__ = [
    "SENTINEL_START",
    "SENTINEL_END",
    "HARD_RULES_HEADER",
    "ID_TOKEN",
    "DEFAULT_CLAUDE_MD",
    "DEFAULT_ARCHIVE",
    "append_hard_rule",
    "list_hard_rules",
    "get_current_rules",
]
