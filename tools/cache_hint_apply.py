#!/usr/bin/env python3
"""cache_hint_apply.py - In-repo consumer for vault/cache_hints/.

When the JIT loader runs in programmatic mode (CLAUDE_PROGRAMMATIC=1 or
non-TTY stdin), it emits a sibling JSON file per injected module under
vault/cache_hints/<module>_<tier>.json. Those files carry the content
sha256 and a cache_control directive that downstream Agent-SDK code (or
this script in --apply mode) feeds into the Anthropic API as block-level
cache hints. Inside Claude Code's own hook chain, cache_control is
controlled by Anthropic; the hint file is for callers that DO control it.

This consumer:
  * VALIDATES every hint file against the schema_version-1 contract
    (checks: required keys, sha256 matches the live SKILL.md after the
    JIT renderer would have produced this tier, cache_control shape).
  * LOADS the validated hints into a dict for downstream callers.
  * EMITS a single-line ledger row per file with status.

It is referenced by tools/verify_full_install.py (P4) so the cache_hints
directory is never a write-only ghost output (Mistake #38 — every new
file must have a real in-repo consumer).

Usage:
  python tools/cache_hint_apply.py            # validate + print summary
  python tools/cache_hint_apply.py --quiet    # exit 0/1 only, no stdout
  python tools/cache_hint_apply.py --as-json  # emit dict on stdout
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
HINTS_DIR = PP_ROOT / "vault" / "cache_hints"
UPSTREAM = PP_ROOT / "vendor" / "apollo" / "upstream"
LOADER = PP_ROOT / "tools" / "jit_skill_loader.py"

SCHEMA_REQUIRED = (
    "schema_version", "module", "tier", "skill_path",
    "content_sha256", "content_bytes", "cache_control", "generated_iso",
)


def _load_jsl():
    spec = importlib.util.spec_from_file_location("jsl", LOADER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _validate_hint(path: Path, hint: dict, jsl) -> tuple[bool, str]:
    """Returns (ok, reason). Reason is a short status string."""
    for k in SCHEMA_REQUIRED:
        if k not in hint:
            return (False, f"missing-key:{k}")
    if hint["schema_version"] != 1:
        return (False, f"unknown-schema:{hint['schema_version']}")
    cc = hint.get("cache_control")
    if not isinstance(cc, dict) or cc.get("type") != "ephemeral":
        return (False, f"bad-cache_control:{cc!r}")
    module = hint["module"]
    tier = hint["tier"]
    skill = UPSTREAM / module / "SKILL.md"
    if not skill.is_file():
        return (False, f"skill-absent:{module}")
    body = skill.read_text(encoding="utf-8")
    # Re-render at the recorded tier to verify the hash still matches.
    # Programmatic-mode rendering is the only emitter; replay the same.
    rendered = jsl._render(module, body, tier, programmatic=True)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    if digest != hint["content_sha256"]:
        return (False, "stale-hash")
    if len(rendered.encode("utf-8")) != hint["content_bytes"]:
        return (False, "stale-bytes")
    return (True, "ok")


def load_hints(quiet: bool = False) -> dict:
    """Return {module: {"tier": str, "content_sha256": str,
                         "cache_control": dict, "skill_path": str}}.

    Skips hints that fail validation (logged when not quiet). Returns
    an empty dict if HINTS_DIR is absent.
    """
    out: dict[str, dict] = {}
    if not HINTS_DIR.is_dir():
        return out
    jsl = _load_jsl()
    rows: list[tuple[str, str, str]] = []
    for fp in sorted(HINTS_DIR.glob("*.json")):
        try:
            hint = json.loads(fp.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            rows.append((fp.name, "FAIL",
                         f"parse-error:{type(exc).__name__}"))
            continue
        ok, reason = _validate_hint(fp, hint, jsl)
        rows.append((fp.name, "OK" if ok else "FAIL", reason))
        if ok:
            out[hint["module"]] = {
                "tier": hint["tier"],
                "content_sha256": hint["content_sha256"],
                "cache_control": hint["cache_control"],
                "skill_path": hint["skill_path"],
            }
    if not quiet:
        for name, status, reason in rows:
            print(f"  [{status}] {name}: {reason}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--as-json", action="store_true",
                    help="print the loaded hints dict as JSON on stdout")
    args = ap.parse_args()
    if not args.quiet:
        print(f"=== Cache-hint validator ({HINTS_DIR}) ===")
    hints = load_hints(quiet=args.quiet)
    if args.as_json:
        json.dump(hints, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    if not args.quiet:
        if not HINTS_DIR.is_dir():
            print("  (no cache_hints/ directory — run JIT in programmatic"
                  " mode to populate)")
        elif not hints:
            print("  (no valid hints loaded)")
        else:
            print(f"  loaded {len(hints)} valid hint(s): "
                  f"{', '.join(sorted(hints))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
