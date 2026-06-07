#!/usr/bin/env python3
"""Secret rotation advisor -- BL-DATASET-BUILD M11.

Scans the repo for credentials and emits per-pattern rotation
instructions. NEVER auto-rotates (HR-SECRET-003 / OD1 sealed). Owner
runs --dry-run by default; output is a list of (file, line, pattern,
instructions), no side effects.

Built on top of modules.secret_firewall.detector.scan_file (M1).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.secret_firewall.detector import scan_text, Severity

# Widely-published synthetic example credentials that are SAFE to
# ignore -- detection is correct, but the advisor should not prompt
# rotation on these. AWS documents AKIAIOSFODNN7EXAMPLE explicitly
# as their non-functional example credential.
KNOWN_SAFE_VALUES: frozenset[str] = frozenset({
    "AKIAIOSFODNN7EXAMPLE",
    "AKIAI44QH8DHBEXAMPLE",
})

# Provider-specific rotation guidance. Strings are advisory; the
# Owner is always the one who actually rotates (per OD1).
ROTATION_INSTRUCTIONS: dict[str, str] = {
    "anthropic_key": (
        "Rotate at https://console.anthropic.com/settings/keys -- "
        "create a new key, replace in env, revoke the old one."
    ),
    "openai_key": (
        "Rotate at https://platform.openai.com/api-keys -- create new, "
        "replace in env, revoke old."
    ),
    "github_pat": (
        "Rotate at https://github.com/settings/tokens -- regenerate "
        "the token; update every CI / local consumer that uses it."
    ),
    "aws_access_key": (
        "Rotate via the IAM console or `aws iam create-access-key`. "
        "Deactivate the OLD key only AFTER the new key is rolled out."
    ),
    "private_key": (
        "Regenerate the keypair; redistribute the public half; revoke "
        "the old private key wherever it was authorized."
    ),
    "connection_string": (
        "Rotate the DB credentials at the provider (RDS / Cloud SQL / "
        "Atlas / etc.); update all env files; restart consumers."
    ),
    "jwt_token": (
        "Re-sign with a new signing secret; invalidate all previously "
        "issued tokens; force a logout-cycle on active users."
    ),
    "bearer_token": (
        "Provider-specific. Check the issuer's dashboard for the "
        "rotation flow."
    ),
    "generic_secret": (
        "Generic credential -- review and rotate via the provider."
    ),
}

# Subdirectories to skip when walking the repo.
_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "_logs", "vault/handoffs", "vault/ceps", "vault/test-results",
    "vault/telemetry", "vault/token_logs",
    "vendor", "dist", "build",
})

# Files larger than this byte threshold are skipped (likely
# generated or binary).
_MAX_SCAN_BYTES = 256 * 1024

# Extensions assumed to be binary / generated.
_BINARY_EXTS: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".pdf",
    ".zip", ".tar", ".gz", ".whl", ".bin",
    ".exe", ".dll", ".so", ".dylib", ".class",
    ".db", ".sqlite", ".onnx",
})


def _iter_scan_targets(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        # Skip any path under a known-skip dir. Two cases:
        #  (1) single-component skips (__pycache__, .git, vendor, ...)
        #      can appear at ANY depth (e.g. tools/__pycache__/), so we
        #      test path-component membership -- a root-anchored
        #      startswith() misses nested ones and leaks compiled .pyc;
        #  (2) multi-segment skips (vault/handoffs, ...) need a prefix
        #      match against the relative path.
        rel_str = str(rel).replace("\\", "/")
        if set(rel_str.split("/")) & _SKIP_DIRS:
            continue
        if any(rel_str.startswith(d + "/") or rel_str == d
               for d in _SKIP_DIRS):
            continue
        if p.suffix.lower() in _BINARY_EXTS:
            continue
        try:
            if p.stat().st_size > _MAX_SCAN_BYTES:
                continue
        except OSError:
            continue
        yield p


def advise(root: Path | str | None = None) -> list[dict]:
    """Return a list of {file, line, pattern, severity, instructions}
    records for every CRITICAL credential detected under root."""
    r = Path(root).resolve() if root else ROOT
    out: list[dict] = []
    for f in _iter_scan_targets(r):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for h in scan_text(text):
            if h.severity != Severity.CRITICAL:
                continue
            matched = text[h.match_start:h.match_end]
            if matched in KNOWN_SAFE_VALUES:
                continue
            out.append({
                "file": str(f.relative_to(r)),
                "line": h.line_no,
                "pattern": h.pattern_name,
                "severity": h.severity.name,
                "instructions": ROTATION_INSTRUCTIONS.get(
                    h.pattern_name,
                    "Rotate at the provider; revoke the old credential.",
                ),
            })
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="(default) report only; no side effects")
    ap.add_argument("--root", default=None,
                    help="repo root to scan (default: PP root)")
    args = ap.parse_args(argv)
    records = advise(args.root)
    if not records:
        print("No CRITICAL credentials detected. Scan clean.")
        return 0
    print(f"=== Secret rotation advisor: {len(records)} CRITICAL hit(s) ===")
    for rec in records:
        print(f"  {rec['file']}:{rec['line']}  [{rec['pattern']}]")
        print(f"    -> {rec['instructions']}")
    print(
        f"\nFound {len(records)} CRITICAL credential(s). "
        f"Owner-decision: rotate per OD1 / HR-SECRET-003."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
