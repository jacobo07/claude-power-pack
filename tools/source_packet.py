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
    python tools/source_packet.py --root R path ... --persist     (store whole, print the card reference)
    python tools/source_packet.py --verify SHA256                  (exit 0 OK · 3 STALE · 4 MISSING)
exit 0 COMPLETE · 3 PARTIAL · 2 UNJUDGED

Never embedded in the successor card: the card is capped at 8000 bytes and one packet's default
excerpt budget alone is 24000. Decided by vault/experiments/exp-successor-packet-002 (REPORT.md):
a packet is stored whole and the card carries a REFERENCE, opt-in via
`gsd_mission.py handoff --packet PATH::ANCHOR` -- inlining would have truncated 28 of 32 real cards,
and a reference cost the same as no packet.
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


# --- durable packets: the evidence lives in a file, the successor card carries a reference ------
# A packet is never cut down to fit a card. It is written whole, content-addressed, and the card
# names its path, hash, size and gaps; the successor reads it only when it needs it, and `verify`
# says whether what it would read is still the packet that was built AND still today's source.
OK, STALE, MISSING = "OK", "STALE", "MISSING"


def packets_dir() -> Path:
    import os
    return Path(os.environ.get("CPP_SOURCE_PACKET_DIR") or (Path.home() / ".claude" / "state" / "source-packets"))


def build_context(root: str, paths: list[str], selectors: list[dict], expect: dict[str, str] | None = None,
                  max_chars: int | None = None) -> Packet:
    """Exact line ranges / literal anchors (genesis-task-context) instead of whole files: the
    region a successor is working on, each range hash-bound. Measured 2026-09-28: whole-file
    packets of tools/verified_reuse.py and tools/gsd_mission.py both lacked the lines a question
    needed (one cut at the excerpt budget, one blocked outright by the vendor's credential-line
    filter); a selector packet carried the exact range."""
    opts = {"root": str(root), "paths": list(paths), "selectors": list(selectors)}
    if expect:
        opts["expectedSourceHashes"] = dict(expect)
    if max_chars is not None:
        opts["maxChars"] = max_chars
    r = nb.call("taskContext", "compileTaskContext", [opts], timeout=60)
    if not r.ok:
        return Packet(UNJUDGED, gaps=[f"bridge {r.outcome}: {r.error}"])
    v = r.value or {}
    manifest = v.get("manifest") or {}
    gaps = [f"{(manifest.get('entries') or [{}])[q['sourceIndex']].get('path') if q.get('sourceIndex') is not None else '?'}"
            f" selector {q['id']}: {q.get('reason')}" for q in manifest.get("requests") or [] if q.get("status") != "included"]
    for e in manifest.get("entries") or []:
        if e.get("hashStatus") == "mismatch":
            gaps.append(f"{e.get('path')}: STALE -- bytes are {str(e.get('sourceSha256'))[:12]}, the plan expected otherwise")
    return Packet(COMPLETE if (v.get("complete") and not gaps) else PARTIAL, prompt=v.get("prompt") or "",
                  gaps=gaps, manifest=manifest)


def persist(root: str, paths: list[str], expect: dict[str, str] | None = None,
            selectors: list[dict] | None = None, **limits) -> dict:
    """Build a packet (whole files, or selected ranges when `selectors` is given) and store it
    whole. Returns the reference a card can carry."""
    import hashlib
    import json
    pk = build_context(root, paths, selectors, expect) if selectors else build(root, paths, expect, **limits)
    if pk.verdict == UNJUDGED:
        return {"verdict": UNJUDGED, "gaps": pk.gaps}
    body = pk.prompt.encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()
    d = packets_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{digest}.txt").write_bytes(body)
    sources = {e["path"]: e.get("sourceSha256") for e in pk.manifest.get("entries") or [] if e.get("path")}
    ref = {"verdict": pk.verdict, "path": str(d / f"{digest}.txt"), "sha256": digest, "bytes": len(body),
           "root": str(root), "files": len(sources), "sources": sources, "gaps": pk.gaps}
    (d / f"{digest}.json").write_text(json.dumps(ref, indent=1), encoding="utf-8")
    return ref


def verify(ref: dict) -> tuple[str, str]:
    """OK only if the packet file is the bytes that were built AND every quoted source still has
    the bytes it had then. A missing file is MISSING; any moved byte is STALE, named."""
    import hashlib
    p = Path(ref.get("path") or "")
    try:
        body = p.read_bytes()
    except OSError:
        return MISSING, f"packet file not found: {p}"
    if hashlib.sha256(body).hexdigest() != ref.get("sha256"):
        return STALE, "packet file bytes differ from the recorded hash"
    for rel, want in (ref.get("sources") or {}).items():
        try:
            got = hashlib.sha256((Path(ref["root"]) / rel).read_bytes()).hexdigest()
        except OSError:
            return STALE, f"{rel}: source no longer readable"
        if want and got != want:
            return STALE, f"{rel}: source changed since the packet was built"
    return OK, "packet and sources match"


def card_reference(ref: dict) -> str:
    """The few lines a successor card carries instead of the evidence itself."""
    gaps = f" gaps={len(ref['gaps'])} (listed in the .json beside it)" if ref.get("gaps") else ""
    return "\n".join([
        f"SOURCE PACKET ({ref['verdict']}, {ref['files']} file(s), {ref['bytes']} bytes, sha256 {ref['sha256'][:16]}){gaps}:",
        f"  {ref['path']}",
        "  Exact hashed excerpts of the files this work is about. Read it when you need them, instead of",
        # Absolute: mission workers run in OTHER repositories, where tools/source_packet.py is absent.
        f'  exploring. Check it first: python "{Path(__file__).resolve()}" --verify {ref["sha256"]}',
    ])


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--expect", action="append", default=[], help="path=sha256")
    ap.add_argument("--out")
    ap.add_argument("--persist", action="store_true", help="store the packet whole and print its card reference")
    ap.add_argument("--verify", metavar="SHA256", help="check a persisted packet: exit 0 OK, 3 STALE, 4 MISSING")
    a = ap.parse_args(argv)
    if a.verify:
        import json
        meta = packets_dir() / f"{a.verify}.json"
        try:
            ref = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            print(f"MISSING: no packet record {meta}")
            return 4
        state, why = verify(ref)
        print(f"{state}: {why}")
        return {OK: 0, STALE: 3}.get(state, 4)
    if not a.root or not a.paths:
        ap.error("--root and at least one path are required unless --verify is given")
    expect = dict(x.split("=", 1) for x in a.expect)
    if a.persist:
        ref = persist(a.root, a.paths, expect)
        if ref["verdict"] == UNJUDGED:
            print(f"UNJUDGED: {ref['gaps']}")
            return 2
        print(card_reference(ref))
        return {COMPLETE: 0, PARTIAL: 3}.get(ref["verdict"], 2)
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
