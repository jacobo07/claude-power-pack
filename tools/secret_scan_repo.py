#!/usr/bin/env python3
"""Secret Scan Repo -- full-tree credential sweep (BL-SECRET-001).

Walks a directory and runs the Secret Firewall detector over every
text-ish file, reporting file + line + pattern (values REDACTED, never
printed). Composes the real detector API -- scan_text() / Hit / Severity
from modules.secret_firewall.detector -- it does NOT re-implement pattern
matching (SCS C28: compose, don't reinvent).

With --honor-allowlist, hits whose matched raw value is a widely-published
synthetic example (secret_rotation_advisor.KNOWN_SAFE_VALUES) OR is in the
Owner-managed sha256 allowlist (secret_firewall.allowlist.is_allowed) are
filtered out -- the same two sources the rotation advisor trusts, so a
clean allowlisted /secret-scan and a clean advisor agree by construction.

CLI:
  python tools/secret_scan_repo.py --path .                  # scan cwd
  python tools/secret_scan_repo.py --severity CRITICAL       # CRITICAL+
  python tools/secret_scan_repo.py --honor-allowlist         # drop known-safe
  python tools/secret_scan_repo.py --report                  # per-hit detail

Exit code: 0 = clean (no hits at/above severity), 1 = hits found.
Importable core: scan_repo(root, min_severity, honor_allowlist)
  -> list[(rel_path, [Hit])].
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.secret_firewall.allowlist import is_allowed
from modules.secret_firewall.detector import Hit, Severity, scan_text
# Both are committed PP modules (always importable). is_allowed() is itself
# fail-open on a missing on-disk allowlist.json, so --honor-allowlist simply
# filters nothing when no allowlist is configured rather than crashing.
from tools.secret_rotation_advisor import KNOWN_SAFE_VALUES

# Text-ish extensions worth scanning; binaries/images are skipped.
EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
    ".env", ".sh", ".ps1", ".bat", ".md", ".txt", ".toml", ".ini",
    ".cfg", ".conf", ".xml", ".html", ".sql", ".rs", ".go", ".java",
}
# Directories that are noise (deps, VCS, build output, vault archives).
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "dist",
    "build", ".next", ".turbo", "vendor", ".mypy_cache", ".pytest_cache",
}
MAX_FILE_BYTES = 500_000  # skip files larger than 500 KB (likely data/binary)


def _is_known_safe(matched: str) -> bool:
    """True if a matched raw value should not be reported under
    --honor-allowlist: a published synthetic example or an Owner-
    allowlisted value (sha256). Composes both real sources."""
    return matched in KNOWN_SAFE_VALUES or is_allowed(matched)


def scan_repo(
    root: Path | str,
    min_severity: str = "MEDIUM",
    honor_allowlist: bool = False,
) -> list[tuple[Path, list[Hit]]]:
    """Scan *root* recursively. Return [(relative_path, [Hit, ...]), ...]
    for every file with at least one hit at or above *min_severity*. When
    *honor_allowlist* is True, known-safe matched values are dropped."""
    root = Path(root)
    floor = Severity[min_severity] if min_severity in Severity.__members__ \
        else Severity.MEDIUM
    results: list[tuple[Path, list[Hit]]] = []

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if f.suffix.lower() not in EXTENSIONS:
            continue
        try:
            if f.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        hits: list[Hit] = []
        for h in scan_text(text):
            if h.severity < floor:
                continue
            if honor_allowlist and _is_known_safe(text[h.match_start:h.match_end]):
                continue
            hits.append(h)

        if hits:
            try:
                rel = f.relative_to(root)
            except ValueError:
                rel = f
            results.append((rel, hits))

    return results


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Scan a repository for leaked secrets (BL-SECRET-001)."
    )
    p.add_argument("--path", default=".", help="Directory to scan (default: cwd)")
    p.add_argument(
        "--severity", default="MEDIUM",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        help="Minimum severity to report (default: MEDIUM)",
    )
    p.add_argument("--honor-allowlist", action="store_true",
                   help="drop known-safe values (published examples + "
                        "Owner sha256 allowlist), like the rotation advisor")
    p.add_argument("--report", action="store_true",
                   help="Show per-hit detail (pattern + line, values redacted)")
    args = p.parse_args(argv)

    root = Path(args.path).resolve()
    suffix = "  [honoring allowlist]" if args.honor_allowlist else ""
    print(f"Scanning: {root}  (severity >= {args.severity}){suffix}")

    results = scan_repo(root, args.severity, honor_allowlist=args.honor_allowlist)

    if not results:
        print(f"OK -- clean. No {args.severity}+ secrets found.")
        return 0

    total = 0
    for rel_path, hits in results:
        print(f"\nFILE: {rel_path}")
        for h in hits:
            total += 1
            if args.report:
                print(f"  [{h.severity.name:<8}] line {h.line_no}: "
                      f"{h.pattern_name}  {h.redacted_preview()}")
            else:
                print(f"  [{h.severity.name:<8}] line {h.line_no}: "
                      f"{h.pattern_name}")

    print(f"\nFOUND {total} potential secret(s) across {len(results)} file(s).")
    print("Next: python tools/secret_rotation_advisor.py  "
          "(HR-SECRET-007: rotate-first, scrub-after).")
    return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main(sys.argv[1:]))
