"""Integrity gate for the vendored Google Mantis skills (vendor/google-mantis).

Why: the security-research skill tells agents to read these files and follow
their method. A silent edit (or an upstream re-sync nobody reviewed) would
change what every security investigation does, so the copy is pinned to one
upstream commit and every byte is hashed in MANIFEST.json.

Checks, all must pass:
  V-MANTIS-MANIFEST    MANIFEST.json parses and names the pinned commit
  V-MANTIS-HASHES      every listed file exists with the recorded sha256
  V-MANTIS-NO-EXTRA    no file on disk that the manifest does not list
  V-MANTIS-NO-CODE     no executable/script file types (prompts only; the
                       ADK harness under upstream reference/ is NOT vendored)
  V-MANTIS-LICENSE     the Apache-2.0 LICENSE travels with the copy

Exit 0 when all pass, 1 otherwise. Usage:
  python tools/verify_mantis_vendor.py [--root vendor/google-mantis]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PINNED_COMMIT = "2b3bbdcbb8d259d1777b89dcfa3c8e87615ccc80"
CODE_SUFFIXES = {".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".ps1", ".bat", ".cmd", ".exe", ".rb", ".go"}
DEFAULT_ROOT = Path(__file__).resolve().parent.parent / "vendor" / "google-mantis"


def verify(root: Path) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    manifest_path = root / "MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return [("V-MANTIS-MANIFEST", False, f"unreadable: {exc}")]

    commit_ok = manifest.get("commit") == PINNED_COMMIT
    results.append(("V-MANTIS-MANIFEST", commit_ok, f"commit={manifest.get('commit')}"))

    listed = {entry["path"]: entry["sha256"] for entry in manifest.get("files", [])}
    bad: list[str] = []
    for rel, expected in listed.items():
        path = root / rel
        if not path.is_file():
            bad.append(f"missing {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            bad.append(f"hash {rel}")
    results.append(("V-MANTIS-HASHES", not bad and len(listed) > 0, f"{len(listed)} listed; problems={bad[:5]}"))

    on_disk = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "MANIFEST.json"}
    extra = sorted(on_disk - set(listed))
    results.append(("V-MANTIS-NO-EXTRA", not extra, f"extra={extra[:5]}"))

    code = sorted(p for p in on_disk if Path(p).suffix.lower() in CODE_SUFFIXES)
    results.append(("V-MANTIS-NO-CODE", not code, f"code={code[:5]}"))

    results.append(("V-MANTIS-LICENSE", (root / "LICENSE").is_file() and "LICENSE" in listed, "LICENSE present and hashed"))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    results = verify(args.root)
    fails = 0
    for gate, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'} {gate}: {detail}")
        fails += 0 if ok else 1
    print(f"MANTIS_VENDOR_PASS={len(results) - fails}/{len(results)}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
