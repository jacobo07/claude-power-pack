"""Vault IO — atomic writers + JSONL index for the Auto-Testing Skill.

Spec ref: vault/specs/auto-testing-gate.md §10

Three artifact families:

1. `vault/test-results/<ts>_<slug>.md` — one per gate fire that
   reached pytest/vitest/mvn (verdict in {pass, fail, timeout}).
   Committable.

2. `vault/test-results/.auto-spawned.log` — newline-delimited JSON,
   one row per gate fire (including ceiling cases). Append-only;
   rotates at 100 KB to `.auto-spawned.log.1`.

3. `vault/test-failures/<project>/{index.json, <ts>_<slug>.md}` —
   closed-loop ledger. Each failure: one JSON row in the project's
   index.json + one .md with the full test text + failure output.
   Used by generators/_common.py read_existing_tests when assembling
   the AVOID clause for the next generation (F1).

All file writes are `.tmp.<pid>` + `os.replace` (atomic). Concurrent
writers serialize via `mkdir`-mutex on `<path>.lock` directories
(sister to deep-research's lock pattern).
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Optional


HOME = Path(os.path.expanduser("~"))
PP_REPO = HOME / ".claude" / "skills" / "claude-power-pack"
VAULT_RESULTS = PP_REPO / "vault" / "test-results"
VAULT_FAILURES = PP_REPO / "vault" / "test-failures"

ROTATE_BYTES = 100 * 1024  # 100 KB
ROTATIONS_KEPT = 3


_PROJECT_SLUG_BAD = re.compile(r"[^a-z0-9\-]+")


def _project_slug(project_root: Path) -> str:
    """Stable slug derived from the project root path."""
    name = project_root.name.lower() if project_root.name else "unknown"
    name = _PROJECT_SLUG_BAD.sub("-", name).strip("-")
    return name or "unknown"


def _acquire_lock(lock_dir: Path, timeout_sec: float = 5.0) -> bool:
    """mkdir-mutex with a polite timeout.

    Returns True on success; False on timeout. Stale-lock recovery is
    NOT done here (the caller is short-lived; if we time out, we
    surrender the write rather than racing).
    """
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            lock_dir.mkdir(parents=False, exist_ok=False)
            return True
        except FileExistsError:
            time.sleep(0.05)
        except OSError:
            return False
    return False


def _release_lock(lock_dir: Path) -> None:
    try:
        lock_dir.rmdir()
    except OSError:
        pass


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp." + str(os.getpid()))
    try:
        tmp.write_text(content, encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _rotate_if_oversized(log_path: Path) -> None:
    """If the log exceeds ROTATE_BYTES, shift .N -> .(N+1) and rename
    current to .1. Keep at most ROTATIONS_KEPT older rotations.
    """
    try:
        size = log_path.stat().st_size
    except OSError:
        return
    if size < ROTATE_BYTES:
        return
    # Drop the oldest, shift the rest.
    for n in range(ROTATIONS_KEPT, 0, -1):
        older = log_path.with_suffix(log_path.suffix + "." + str(n))
        newer = log_path.with_suffix(log_path.suffix + "." + str(n + 1))
        if n == ROTATIONS_KEPT and older.exists():
            try:
                older.unlink()
            except OSError:
                pass
        elif older.exists():
            try:
                os.replace(older, newer)
            except OSError:
                pass
    rotated = log_path.with_suffix(log_path.suffix + ".1")
    try:
        os.replace(log_path, rotated)
    except OSError:
        pass


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append a single JSON line under a per-file mkdir-lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_oversized(path)
    lock_dir = path.with_suffix(path.suffix + ".lock")
    if not _acquire_lock(lock_dir):
        return  # Quietly surrender; logs are best-effort.
    try:
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line + "\n")
    finally:
        _release_lock(lock_dir)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def now_slug() -> str:
    return time.strftime("%Y-%m-%d_%H%M%S", time.localtime())


def log_auto_spawn(record: dict[str, Any]) -> None:
    """Single-line JSON append to vault/test-results/.auto-spawned.log."""
    record = {"ts": now_iso(), **record}
    _append_jsonl(VAULT_RESULTS / ".auto-spawned.log", record)


def write_result_artifact(project_root: Path, verdict: str,
                           reason: str, body: str,
                           extra: Optional[dict[str, Any]] = None) -> Path:
    """Write a verdict report under vault/test-results/.

    Returns the absolute path of the artifact. Verdict is one of
    {pass, fail, timeout, ceiling, skip}. `body` should contain the
    test output / generator output for forensic value.
    """
    slug = _project_slug(project_root)
    fname = now_slug() + "_" + verdict + "_" + slug + ".md"
    path = VAULT_RESULTS / fname
    header = "\n".join([
        "---",
        "ts: " + now_iso(),
        "project: " + str(project_root),
        "project_slug: " + slug,
        "verdict: " + verdict,
        "reason: " + (reason or "")[:200].replace("\n", " | "),
        "---",
        "",
    ])
    extras_text = ""
    if extra:
        extras_text = (
            "## Extras\n\n```json\n"
            + json.dumps(extra, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n```\n\n"
        )
    full = header + "# Auto-Testing Verdict: " + verdict + "\n\n" + extras_text + body + "\n"
    _atomic_write_text(path, full)
    return path


def write_test_file(project_root: Path, filename: str,
                     content: str) -> Path:
    """Write a generated test under <project>/tests/auto-generated/.

    Creates the directory if missing. Atomic.
    """
    target_dir = project_root / "tests" / "auto-generated"
    target = target_dir / filename
    _atomic_write_text(target, content)
    return target


def write_failure(project_root: Path, target_file: str,
                   test_text: str, failure_output: str,
                   diff_excerpt: str = "") -> Path:
    """Record a failed gate run for closed-loop learning (F1).

    Writes both an .md (forensic) and one JSON row in the project's
    index.json (machine-readable).
    """
    slug = _project_slug(project_root)
    fail_dir = VAULT_FAILURES / slug
    fail_dir.mkdir(parents=True, exist_ok=True)

    md_name = now_slug() + "_" + slug + ".md"
    md_path = fail_dir / md_name
    md_body = "\n".join([
        "---",
        "ts: " + now_iso(),
        "project: " + str(project_root),
        "project_slug: " + slug,
        "target_file: " + target_file,
        "---",
        "",
        "# Auto-Testing Failure",
        "",
        "## Generated test text",
        "",
        "```",
        test_text,
        "```",
        "",
        "## Failure output (truncated to 4 KB)",
        "",
        "```",
        failure_output[:4096],
        "```",
        "",
        "## Diff excerpt (first 2 KB)",
        "",
        "```diff",
        diff_excerpt[:2048],
        "```",
        "",
        "## Avoidance note for next generation",
        "",
        "Do not regenerate the above test pattern. If the same diff is "
        "encountered again, the generator should propose a different "
        "assertion shape or fixture.",
        "",
    ])
    _atomic_write_text(md_path, md_body)

    index_path = fail_dir / "index.json"
    record = {
        "ts": now_iso(),
        "md": md_name,
        "target_file": target_file,
        "test_text_sha256": _sha256_short(test_text),
        "failure_excerpt": failure_output[:512],
        "diff_excerpt": diff_excerpt[:512],
    }
    _append_jsonl(index_path, record)
    return md_path


def read_failure_history(project_root: Path, limit: int = 20) -> list[dict[str, Any]]:
    """Read the most recent `limit` failure rows for `project_root`.

    Returns newest first. F1 closed-loop consumes this to build the
    AVOID clause.
    """
    slug = _project_slug(project_root)
    index_path = VAULT_FAILURES / slug / "index.json"
    if not index_path.exists():
        return []
    try:
        with open(index_path, "r", encoding="utf-8-sig") as fh:
            rows = []
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return list(reversed(rows))[:limit]


def read_failure_history_with_text(project_root: Path,
                                    limit: int = 20) -> list[dict[str, Any]]:
    """Like read_failure_history, but also extracts the full
    generated-test text from each failure's .md file.

    F1 closed-loop uses the test text to build the AVOID clause. The
    .md file is the source of truth (index.json only carries the
    sha256 + excerpts to keep its rows small).
    """
    rows = read_failure_history(project_root, limit)
    slug = _project_slug(project_root)
    fail_dir = VAULT_FAILURES / slug
    out: list[dict[str, Any]] = []
    for r in rows:
        md_name = r.get("md") or ""
        md_path = fail_dir / md_name
        if not md_path.exists():
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        marker = "## Generated test text"
        idx = text.find(marker)
        if idx < 0:
            continue
        block = text[idx + len(marker):idx + len(marker) + 8000]
        first_fence = block.find("```")
        if first_fence < 0:
            continue
        # Skip to end of opening fence line.
        nl = block.find("\n", first_fence)
        if nl < 0:
            continue
        close_fence = block.find("```", nl + 1)
        if close_fence < 0:
            continue
        test_text = block[nl + 1:close_fence].strip()
        out.append({**r, "test_text": test_text})
    return out


def _sha256_short(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]
