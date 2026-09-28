"""Vendored third-party trees: provenance record and byte-integrity check.

Owner of Release Integrity for ``vendor/`` (assimilated from genesis-release-integrity, MIT).
A vendored tree is judged against the record written when it was taken, never against a
rebuild or a re-download:

    python tools/vendor_provenance.py build  --name genesis-suite --source-zip <zip> [--inner <member>]
    python tools/vendor_provenance.py verify [--name genesis-suite] [--fresh-checkout]

``verify`` outcomes are four-valued and the process exit code carries them:
  0 VALID            every recorded file present with its recorded sha256, no extra file
  1 SUBJECT_INVALID  a file changed, went missing or appeared
  2 VERIFIER_FAILED  the check itself could not run (unreadable record, git failure)
  3 UNREADABLE       no record exists for a requested tree

``--fresh-checkout`` reads the tree out of ``git archive HEAD`` instead of the working copy,
which is the bytes a new clone receives. That is the mode that catches line-ending filters.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor"
RECORDS = VENDOR / "_provenance"
GIT = "git"

VALID, SUBJECT_INVALID, VERIFIER_FAILED, UNREADABLE = "VALID", "SUBJECT_INVALID", "VERIFIER_FAILED", "UNREADABLE"
EXIT = {VALID: 0, SUBJECT_INVALID: 1, VERIFIER_FAILED: 2, UNREADABLE: 3}
# A verifier failure outranks a subject failure found in the same run: it proves nothing
# about what it skipped.
RANK = {VALID: 0, SUBJECT_INVALID: 1, UNREADABLE: 2, VERIFIER_FAILED: 3}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_files(tree: Path) -> dict[str, bytes]:
    out = {}
    for p in sorted(tree.rglob("*")):
        if p.is_symlink():
            raise ValueError(f"symlink in vendored tree: {p}")
        if p.is_file():
            out[p.relative_to(tree).as_posix()] = p.read_bytes()
    return out


def archived_files(name: str) -> dict[str, bytes]:
    """The tree as ``git archive HEAD`` hands it to a fresh clone (filters applied)."""
    raw = subprocess.run([GIT, "-C", str(ROOT), "archive", "--format=tar", "HEAD", f"vendor/{name}"],
                         capture_output=True, check=True).stdout
    prefix = f"vendor/{name}/"
    out = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for m in tar.getmembers():
            if m.isfile() and m.name.startswith(prefix):
                out[m.name[len(prefix):]] = tar.extractfile(m).read()
    return out


def build(name: str, source_zip: Path, inner: str | None, license_fingerprint: str | None) -> dict:
    tree = VENDOR / name
    files = tree_files(tree)
    outer = source_zip.read_bytes()
    record = {
        "schema": "cpp-vendor-provenance/1",
        "name": name,
        "taken_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {"zip": source_zip.name, "zip_sha256": sha256_bytes(outer)},
        "license_gate_fingerprint": license_fingerprint,
        "local_patches": [],
        "files": [{"path": k, "sha256": sha256_bytes(v), "bytes": len(v)} for k, v in files.items()],
    }
    if inner:
        with zipfile.ZipFile(source_zip) as z:
            record["source"]["inner"] = inner
            record["source"]["inner_sha256"] = sha256_bytes(z.read(inner))
    pkg = tree / "package.json"
    if pkg.is_file():
        meta = json.loads(pkg.read_text(encoding="utf-8"))
        record["version"] = meta.get("version")
        record["license"] = meta.get("license")
        record["engines"] = meta.get("engines")
    RECORDS.mkdir(parents=True, exist_ok=True)
    (RECORDS / f"{name}.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    return record


def verify_one(name: str, fresh: bool) -> dict:
    rec_path = RECORDS / f"{name}.json"
    if not rec_path.is_file():
        return {"name": name, "outcome": UNREADABLE, "reason": f"no record {rec_path.name}"}
    try:
        record = json.loads(rec_path.read_text(encoding="utf-8"))
        expected = {f["path"]: f["sha256"] for f in record["files"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"name": name, "outcome": VERIFIER_FAILED, "reason": f"record unreadable: {exc!r}"}
    if not expected:
        return {"name": name, "outcome": VERIFIER_FAILED, "reason": "record lists no files"}
    try:
        actual = archived_files(name) if fresh else tree_files(VENDOR / name)
    except (OSError, ValueError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        return {"name": name, "outcome": VERIFIER_FAILED, "reason": f"could not read tree: {exc!r}"}
    changed = sorted(p for p in expected if p in actual and sha256_bytes(actual[p]) != expected[p])
    missing = sorted(p for p in expected if p not in actual)
    extra = sorted(p for p in actual if p not in expected)
    ok = not (changed or missing or extra)
    return {"name": name, "outcome": VALID if ok else SUBJECT_INVALID, "mode": "fresh-checkout" if fresh else "working-copy",
            "checked": len(expected), "changed": changed, "missing": missing, "extra": extra}


def verify(names: list[str], fresh: bool) -> tuple[str, list[dict]]:
    if not names:
        names = sorted(p.stem for p in RECORDS.glob("*.json")
                       if '"cpp-vendor-provenance/1"' in p.read_text(encoding="utf-8")) if RECORDS.is_dir() else []
    if not names:
        return UNREADABLE, [{"outcome": UNREADABLE, "reason": "no provenance records"}]
    results = []
    for n in names:
        try:
            results.append(verify_one(n, fresh))
        except Exception as exc:  # noqa: BLE001 -- one unexpected shape must not end the verdict
            results.append({"name": n, "outcome": VERIFIER_FAILED, "reason": repr(exc)})
    worst = max((r["outcome"] for r in results), key=RANK.__getitem__)
    return worst, results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--name", required=True)
    b.add_argument("--source-zip", required=True, type=Path)
    b.add_argument("--inner")
    b.add_argument("--license-fingerprint")
    v = sub.add_parser("verify")
    v.add_argument("--name", action="append", default=[])
    v.add_argument("--fresh-checkout", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "build":
        rec = build(args.name, args.source_zip, args.inner, args.license_fingerprint)
        print(json.dumps({"name": rec["name"], "files": len(rec["files"]), "version": rec.get("version")}))
        return 0
    outcome, results = verify(args.name, args.fresh_checkout)
    print(json.dumps({"outcome": outcome, "results": results}, indent=1))
    return EXIT[outcome]


if __name__ == "__main__":
    sys.exit(main())
