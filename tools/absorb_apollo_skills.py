#!/usr/bin/env python3
"""absorb_apollo_skills.py — vendor apollographql/skills into the Power Pack.

Anonymous HTTPS shallow-clone -> pin upstream commit -> copy every skills/<module>/
tree (including references/) into vendor/apollo/upstream/<module>/, quarantining
rust-best-practices under vendor/apollo/optional/ (no auto-warm, per Q&A 3b).
Emits a SHA-256 MANIFEST.json, copies the upstream LICENSE untouched, writes
SOURCE.txt, runs lib/license_gate.js and appends the verdict to vendor/NOTICE.md
(vendor/README.md Rules 1 & 2). Idempotent; --refresh wipes upstream/+optional/
before repopulating (overlay/ and ground-rules-card.md are preserved).

Exit codes: 0 ok, 2 upstream-structure error, 3 git/clone error.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

REPO_URL = "https://github.com/apollographql/skills.git"
PP_ROOT = Path(__file__).resolve().parents[1]          # tools/ -> repo root
VENDOR = PP_ROOT / "vendor" / "apollo"
UPSTREAM = VENDOR / "upstream"
OPTIONAL = VENDOR / "optional"
OVERLAY = VENDOR / "overlay"
NOTICE = PP_ROOT / "vendor" / "NOTICE.md"
LICENSE_GATE = PP_ROOT / "lib" / "license_gate.js"
QUARANTINE = {"rust-best-practices"}                   # Q&A 3b: vendored, not auto-warmed


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, check=True, capture_output=True, text=True
    )


def _license_gate(target: Path) -> str:
    """Run lib/license_gate.js <target> --json. Advisory: never raises."""
    if not LICENSE_GATE.is_file():
        return "license_gate.js absent — skipped"
    try:
        res = subprocess.run(
            ["node", str(LICENSE_GATE), str(target), "--json"],
            check=False, capture_output=True, text=True,
        )
        out = (res.stdout or "").strip()
        try:
            verdict = json.loads(out)
            tier = verdict.get("tier") or verdict.get("classification") or "UNKNOWN"
            spdx = verdict.get("spdx") or verdict.get("license") or "?"
            return f"tier={tier} spdx={spdx} (exit {res.returncode})"
        except json.JSONDecodeError:
            return f"exit {res.returncode}: {out or (res.stderr or '').strip()}"
    except OSError as exc:
        return f"node invocation failed: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Vendor apollographql/skills.")
    ap.add_argument(
        "--refresh", action="store_true",
        help="wipe vendor/apollo/upstream/ and optional/ before repopulating",
    )
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="apollo_skills_"))
    try:
        repo = tmp / "repo"
        try:
            _run(["git", "clone", "--depth", "1", REPO_URL, str(repo)])
        except (subprocess.CalledProcessError, OSError) as exc:
            detail = getattr(exc, "stderr", "") or str(exc)
            print(f"FATAL: clone failed: {detail}", file=sys.stderr)
            return 3
        commit = _run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

        skills_dir = repo / "skills"
        if not skills_dir.is_dir():
            print(f"FATAL: no skills/ directory in {REPO_URL}", file=sys.stderr)
            return 2
        modules = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        if not modules:
            print("FATAL: skills/ contains no module directories", file=sys.stderr)
            return 2

        if args.refresh:
            shutil.rmtree(UPSTREAM, ignore_errors=True)
            shutil.rmtree(OPTIONAL, ignore_errors=True)
        UPSTREAM.mkdir(parents=True, exist_ok=True)
        OPTIONAL.mkdir(parents=True, exist_ok=True)
        OVERLAY.mkdir(parents=True, exist_ok=True)
        (OVERLAY / ".gitkeep").touch()

        files_manifest = []
        module_meta = []
        for name in modules:
            src = skills_dir / name
            dest_root = OPTIONAL if name in QUARANTINE else UPSTREAM
            dest = dest_root / name
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(src, dest)

            skill_md = None
            for f in sorted(dest.rglob("*")):
                if not f.is_file():
                    continue
                rel = PurePosixPath(f.relative_to(VENDOR).as_posix())
                files_manifest.append({
                    "path": str(rel),
                    "sha256": sha256_file(f),
                    "bytes": f.stat().st_size,
                })
                if f.name == "SKILL.md" and f.parent == dest:
                    skill_md = str(rel)
            module_meta.append({
                "name": name,
                "quarantined": name in QUARANTINE,
                "skill_md": skill_md,
            })

        # vendor/README.md Rule 1 — original LICENSE copied untouched.
        license_src = repo / "LICENSE"
        if license_src.is_file():
            shutil.copy2(license_src, VENDOR / "LICENSE")
        (VENDOR / "SOURCE.txt").write_text(
            f"upstream: {REPO_URL}\n"
            f"commit:   {commit}\n"
            f"snapshot: {_utc_now()}\n"
            f"modules:  {len(modules)} ({', '.join(modules)})\n",
            encoding="utf-8",
        )

        manifest = {
            "upstream_url": REPO_URL,
            "upstream_commit": commit,
            "generated_at": _utc_now(),
            "module_count": len(modules),
            "quarantined": sorted(QUARANTINE & set(modules)),
            "modules": module_meta,
            "files": sorted(files_manifest, key=lambda x: x["path"]),
        }
        # Atomic write LAST so a crash leaves the previous good MANIFEST.
        mtmp = VENDOR / "MANIFEST.json.tmp"
        mtmp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        os.replace(mtmp, VENDOR / "MANIFEST.json")

        # vendor/README.md Rule 2 — license gate verdict recorded in NOTICE.md.
        gate_verdict = _license_gate(VENDOR)
        NOTICE.parent.mkdir(parents=True, exist_ok=True)
        with open(NOTICE, "a", encoding="utf-8") as fh:
            fh.write(
                f"\n## apollo — apollographql/skills\n"
                f"- source: {REPO_URL}\n"
                f"- commit: {commit}\n"
                f"- snapshot: {manifest['generated_at']}\n"
                f"- modules: {len(modules)} "
                f"(upstream={len(modules) - len(manifest['quarantined'])}, "
                f"quarantined={manifest['quarantined'] or 'none'})\n"
                f"- license_gate: {gate_verdict}\n"
            )

        print(
            f"OK: {len(modules)} modules "
            f"({len(files_manifest)} files) @ {commit[:12]} | "
            f"gate: {gate_verdict}"
        )
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
