"""Bounded source packet (assimilation item 12, genesis-source-packets -> WRAP).

A worker that cannot read the repository gets exact, bounded, hashed excerpts instead of a broad
file dump. The vendored buildSourcePacket does the reading through the one bridge -- secret and
private-path exclusion, credential-content blocking, private-line redaction, byte budgets -- and
this wrapper adds what it does not have: EXPECTED hashes. A path whose bytes no longer match the
hash the caller planned against is STALE, so a packet cannot silently describe a newer file than
the one a decision was made about.

Verdicts: COMPLETE (every path included whole, every expectation matched) · PARTIAL (a gap exists:
blocked, truncated, redacted, missing or stale -- each named) · UNJUDGED (the bridge could not answer).

    python tools/source_packet.py --root R path [path ...] [--expect path=sha256 ...] [--out packet.txt]
exit 0 COMPLETE · 3 PARTIAL · 2 UNJUDGED

Not embedded in the successor card: the card is capped at 8000 bytes (SessionStart truncation,
measured) and one packet's default excerpt budget alone is 24000. Which consumer earns it is the
question the T8 paired experiment is registered to answer.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.external_assimilation import node_bridge as nb  # noqa: E402

COMPLETE, PARTIAL, UNJUDGED = "COMPLETE", "PARTIAL", "UNJUDGED"


@dataclass
class Packet:
    verdict: str
    prompt: str = ""
    gaps: list = field(default_factory=list)
    manifest: dict = field(default_factory=dict)


def build(root: str, paths: list[str], expect: dict[str, str] | None = None, **limits) -> Packet:
    r = nb.call("sourcePackets", "buildSourcePacket", [{"root": str(root), "paths": list(paths), **limits}], timeout=60)
    if not r.ok:
        return Packet(UNJUDGED, gaps=[f"bridge {r.outcome}: {r.error}"])
    value = r.value or {}
    manifest = value.get("manifest") or {}
    gaps = []
    for e in manifest.get("entries") or []:
        if e.get("status") != "included":
            gaps.append(f"{e.get('path')}: {e.get('status')} ({e.get('reason')})")
        elif e.get("redactedLines"):
            gaps.append(f"{e.get('path')}: {e['redactedLines']} private line(s) redacted")
    by_path = {e.get("path"): e for e in manifest.get("entries") or []}
    for p, want in (expect or {}).items():
        got = (by_path.get(p.replace("\\", "/")) or {}).get("sourceSha256")
        if got is None:
            gaps.append(f"{p}: expected hash not checkable (no bytes read)")
        elif got.lower() != want.lower():
            gaps.append(f"{p}: STALE -- bytes are {got[:12]}, the plan expected {want[:12]}")
    return Packet(PARTIAL if gaps else COMPLETE, prompt=value.get("prompt") or "", gaps=gaps, manifest=manifest)


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--expect", action="append", default=[], help="path=sha256")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    expect = dict(x.split("=", 1) for x in a.expect)
    pk = build(a.root, a.paths, expect)
    if a.out and pk.prompt:
        Path(a.out).write_text(pk.prompt, encoding="utf-8")
    m = pk.manifest
    print(f"{pk.verdict} files_read={m.get('filesRead')} excerpt_bytes={m.get('totalBytes')}")
    for g in pk.gaps:
        print(f"  gap  {g}")
    return {COMPLETE: 0, PARTIAL: 3}.get(pk.verdict, 2)


if __name__ == "__main__":
    sys.exit(main())
