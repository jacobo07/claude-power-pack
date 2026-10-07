"""Hard Rule Writer -- single authority, generated mirror.

The archive ``vault/hard_rules/HARD_RULES.md`` is the ONLY semantic
authority for hard rules. The PP-HARD-RULES sentinel block of
``<repo-root>/CLAUDE.md`` is a deterministic projection of it
(``render_mirror_block``): the archive's preamble plus every entry
whose ``stub_reason`` is None, byte for byte. Nothing writes rule text
into CLAUDE.md except ``project_mirror``.

New ids are allocated from the archive. ``append_hard_rule`` refuses
an entry that ``stub_reason`` flags, writes the archive, then
regenerates the mirror. Always backs up CLAUDE.md before any write.
Atomic write. Idempotent on content hash.

Sealed BL-HARDRULE-001 (2026-05-29); single authority E3 (2026-10-07).
"""
from __future__ import annotations

import hashlib
import json
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
        f"{SENTINEL_START}"
        f"{HARD_RULES_HEADER}"
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


def _block_ids(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        _, _, inner = _extract_block(_read(path))
    except ValueError:
        return []
    # HR- followed by either pure digits (HR-008) or a namespace token +
    # digits (HR-SECRET-001, HR-CASCADE-007).
    return re.findall(r"^###\s+(HR-\S+)", inner, re.MULTILINE)


def get_current_rules(claude_md_path: Path | None = None) -> list[str]:
    """Return the HR ids in the CLAUDE.md mirror (read-only view)."""
    return _block_ids(claude_md_path or DEFAULT_CLAUDE_MD)


def get_archive_rules(archive_path: Path | None = None) -> list[str]:
    """Return the HR ids in the archive -- the id allocation authority."""
    return _block_ids(archive_path or DEFAULT_ARCHIVE)


def next_rule_id(existing: list[str]) -> str:
    # Only the pure-numeric HR-NNN series participates in the
    # auto-increment sequence; namespaced rules (HR-SECRET-001,
    # HR-CASCADE-007) live in their own caller-managed series.
    nums: list[int] = []
    for rid in existing:
        m = re.fullmatch(r"HR-(\d+)", rid)
        if m:
            nums.append(int(m.group(1)))
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


def _existing_id_for(rule_text: str, path: Path) -> str | None:
    """Return the HR-NNN id of an existing matching rule in ``path``."""
    if not path.is_file():
        return None
    try:
        _, _, inner = _extract_block(_read(path))
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
    """Append the rule to the archive, then regenerate the mirror.

    `rule_text` may carry the ``HR-NEXT`` id token; it is rewritten
    to the next free ``HR-NNN`` id of the ARCHIVE. Raises ValueError
    when ``stub_reason`` flags the entry. Backs up CLAUDE.md to
    ``<name>.pre-hr-<ts>.bak`` before any write.
    """
    claude_md = claude_md_path or DEFAULT_CLAUDE_MD
    archive = archive_path or DEFAULT_ARCHIVE

    reason = stub_reason(rule_text)
    if reason is not None:
        raise ValueError(f"refused stub hard rule: {reason}")

    _ensure_claude_md(claude_md)
    _ensure_archive(archive)

    rule_id = next_rule_id(get_archive_rules(archive))
    rule_with_id = rule_text.replace(ID_TOKEN, rule_id)
    if not rule_with_id.endswith("\n"):
        rule_with_id += "\n"

    existing_id = _existing_id_for(rule_with_id, archive)
    if existing_id is not None:
        return existing_id

    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = claude_md.with_suffix(f".md.pre-hr-{iso}.bak")
    shutil.copy2(claude_md, backup)

    archive_content = _read(archive)
    try:
        archive_new = _insert_into_block(archive_content, rule_with_id)
    except ValueError:
        archive_new = archive_content + (
            f"\n{SENTINEL_START}{HARD_RULES_HEADER}{rule_with_id}"
            f"{SENTINEL_END}\n")
    _atomic_write_text(archive, archive_new)
    project_mirror(claude_md, archive)

    print(f"[OK] hard rule {rule_id} written")
    print(f"     - archive       : {archive}")
    print(f"     - CLAUDE.md     : {claude_md} (regenerated)")
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
        r"###\s+(HR-\S+)\s+--\s+(.+?)\n"
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


GENERIC_STOP = ("STOP. Verify preconditions in writing. Document what you "
                "are about to do.")

_ENTRY_START = re.compile(r"^###\s+(HR-\S+)", re.MULTILINE)
_TEST_ENTRY = re.compile(
    r"auto-propose pipeline|\bZZZ\b|^TRIGGER:\s+Test recognizer",
    re.MULTILINE)
_OBSOLETE = re.compile(r"\b(?:RETIRED|OBSOLETE|SUPERSEDED)\b|\[obsolete\]")
_EVIDENCE_PATH = re.compile(r"\b((?:hooks|modules|tools)/[\w./-]*\w)")
_EVIDENCE_DOTTED = re.compile(r"\bmodules(?:\.\w+)+")


def stub_reason(entry: str) -> str | None:
    """Why an HR entry is a stub that must not reach the mirror, or None.

    Stubs come from the auto-propose pipeline: a heading turned into a
    ``TRIGGER: Before: <heading>``, a STOP that is boilerplate or a
    sliced markdown table, or a pipeline test fixture.
    """
    if _TEST_ENTRY.search(entry):
        return "test entry for the auto-propose pipeline"
    trigger = re.search(r"^TRIGGER:\s*(.*)$", entry, re.MULTILINE)
    stop = re.search(r"^STOP:\s*(.*)$", entry, re.MULTILINE)
    if trigger is None or stop is None:
        return "missing TRIGGER or STOP"
    if trigger.group(1).startswith("Before: "):
        return "TRIGGER derived from a heading, not a real trigger"
    if stop.group(1).startswith("|"):
        return "STOP is a sliced markdown table fragment"
    if stop.group(1).startswith(GENERIC_STOP):
        return "STOP is generic boilerplate"
    return None


def _enforcer_paths(entry: str, root: Path) -> list[str]:
    """Repo paths named in EVIDENCE that exist under ``root``."""
    ev = re.search(r"^EVIDENCE:\s*(.*)$", entry, re.MULTILINE)
    if ev is None:
        return []
    named = [p.rstrip("/.") for p in _EVIDENCE_PATH.findall(ev.group(1))]
    named += [d.replace(".", "/") for d in _EVIDENCE_DOTTED.findall(ev.group(1))]
    found = []
    for rel in named:
        rel = rel.rstrip("/*")
        if (root / rel).exists() or (root / f"{rel}.py").is_file():
            found.append(rel)
    return found


def classify_rule(entry: str, root: Path | None = None) -> str:
    """Label one HR entry: test / stub / obsolete / mechanical / judgmental.

    ``mechanical`` = its EVIDENCE names a hook or module that exists in
    the repo and enforces it; ``judgmental`` = enforcement rests on the
    agent reading the rule. Labels inform E6; nothing removes a rule by
    its label.
    """
    reason = stub_reason(entry)
    if reason == "test entry for the auto-propose pipeline":
        return "test"
    if reason is not None:
        return "stub"
    if _OBSOLETE.search(entry):
        return "obsolete"
    if _enforcer_paths(entry, root or PP_ROOT):
        return "mechanical"
    return "judgmental"


def rule_classes(archive_path: Path | None = None,
                 root: Path | None = None) -> dict[str, str]:
    """``{rule_id: label}`` for every archive entry, in archive order."""
    _, _, inner = _extract_block(_read(archive_path or DEFAULT_ARCHIVE))
    _, entries = _split_entries(inner)
    return {rid: classify_rule(e, root) for rid, e in entries}


def _split_entries(inner: str) -> tuple[str, list[tuple[str, str]]]:
    """Split a block into (preamble, [(rule_id, entry_text), ...])."""
    starts = list(_ENTRY_START.finditer(inner))
    if not starts:
        return inner, []
    entries = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(inner)
        entries.append((m.group(1), inner[m.start():end]))
    return inner[:starts[0].start()], entries


def render_mirror_block(archive_text: str) -> str:
    """The mirror's sentinel-block inner text, generated from the archive."""
    _, _, inner = _extract_block(archive_text)
    preamble, entries = _split_entries(inner)
    return preamble + "".join(e for _, e in entries if stub_reason(e) is None)


def project_mirror(claude_md: Path | None = None,
                   archive: Path | None = None,
                   check: bool = False) -> bool:
    """Regenerate CLAUDE.md's block from the archive. Returns True on drift.

    Non-rule prose that sits inside the block ahead of the HARD RULES
    header is moved just above the start sentinel, unchanged, so the
    block holds generated text only. With ``check`` nothing is written.
    """
    claude_md = claude_md or DEFAULT_CLAUDE_MD
    content = _read(claude_md)
    start, end, inner = _extract_block(content)
    rendered = render_mirror_block(_read(archive or DEFAULT_ARCHIVE))
    cuts = [i for i in (inner.find(HARD_RULES_HEADER.strip()),
                        inner.find("### HR-")) if i != -1]
    lead = inner[:min(cuts)] if cuts else inner
    lead = lead.strip("\n")
    new = (content[:start] + (lead + "\n\n" if lead else "")
           + SENTINEL_START + rendered + content[end:])
    drift = new != content
    if drift and not check:
        _atomic_write_text(claude_md, new)
    return drift


def merge_into_archive(claude_md: Path, archive: Path,
                       prefer_mirror: frozenset[str] = frozenset()) -> dict:
    """Copy mirror-only entries into the archive; never drop one.

    Mirror-only entries are inserted after the nearest preceding id
    they follow in the mirror. Where both carry an id with different
    text (digest comments ignored), the archive wins unless the id is
    in ``prefer_mirror``; the losing body is returned for the record.
    """
    a_content = _read(archive)
    a_start, a_end, a_inner = _extract_block(a_content)
    pre, a_entries = _split_entries(a_inner)
    _, _, m_inner = _extract_block(_read(claude_md))
    _, m_entries = _split_entries(m_inner)
    norm = lambda t: re.sub(r"<!-- digest:[^>]*-->\n?", "", t).strip()  # noqa: E731
    order = [rid for rid, _ in a_entries]
    body = dict(a_entries)
    report: dict = {"copied": [], "differ": {}}
    prev = None
    for rid, entry in m_entries:
        if rid not in body:
            body[rid] = entry if entry.endswith("\n") else entry + "\n"
            order.insert(order.index(prev) + 1 if prev else 0, rid)
            report["copied"].append(rid)
        elif norm(entry) != norm(body[rid]):
            digests = "".join(re.findall(r"<!-- digest:[^>]*-->\n?", body[rid]))
            if rid in prefer_mirror:
                report["differ"][rid] = {"kept": "mirror", "other": body[rid]}
                body[rid] = norm(entry) + "\n" + digests
            else:
                report["differ"][rid] = {"kept": "archive", "other": entry}
        prev = rid
    new_inner = pre + "".join(body[r] for r in order)
    inner_start = a_start + len(SENTINEL_START)
    _atomic_write_text(archive, a_content[:inner_start] + new_inner
                       + a_content[a_end:])
    return report


def prune_stub_rules(path: Path, dry_run: bool = False) -> list[tuple[str, str]]:
    """Regenerate the sentinel block of ``path`` without stub entries.

    Returns ``[(rule_id, reason), ...]`` for every entry dropped. Real
    entries keep their exact text and order; nothing outside the
    sentinels changes.
    """
    content = _read(path)
    start, end, inner = _extract_block(content)
    preamble, entries = _split_entries(inner)
    kept, dropped = [], []
    for rid, entry in entries:
        reason = stub_reason(entry)
        if reason is None:
            kept.append(entry)
        else:
            dropped.append((rid, reason))
    if dropped and not dry_run:
        inner_start = start + len(SENTINEL_START)
        new = content[:inner_start] + preamble + "".join(kept) + content[end:]
        _atomic_write_text(path, new)
    return dropped


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Hard rules: the archive is the "
                                 "authority, the CLAUDE.md block its projection.")
    verb = ap.add_mutually_exclusive_group(required=True)
    verb.add_argument("--project", action="store_true",
                      help="regenerate the CLAUDE.md block from the archive")
    verb.add_argument("--check", action="store_true",
                      help="exit 1 if the CLAUDE.md block drifted")
    verb.add_argument("--classify", action="store_true",
                      help="print {id: label} for every archive entry")
    verb.add_argument("--prune", action="store_true",
                      help="drop stub entries from the archive, then project")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.classify:
        print(json.dumps(rule_classes(), indent=2))
        return 0
    if args.prune:
        for rid, reason in prune_stub_rules(DEFAULT_ARCHIVE, args.dry_run):
            print(f"{'would drop' if args.dry_run else 'dropped'} {rid}: "
                  f"{reason}")
        if args.dry_run:
            return 0
    drift = project_mirror(check=args.check or args.dry_run)
    print(f"mirror {'drift' if drift else 'in sync'}: {DEFAULT_CLAUDE_MD}")
    return 1 if (drift and (args.check or args.dry_run)) else 0


__all__ = [
    "stub_reason",
    "classify_rule",
    "rule_classes",
    "prune_stub_rules",
    "render_mirror_block",
    "project_mirror",
    "merge_into_archive",
    "SENTINEL_START",
    "SENTINEL_END",
    "HARD_RULES_HEADER",
    "ID_TOKEN",
    "DEFAULT_CLAUDE_MD",
    "DEFAULT_ARCHIVE",
    "append_hard_rule",
    "list_hard_rules",
    "get_current_rules",
    "get_archive_rules",
]


if __name__ == "__main__":
    sys.exit(main())
