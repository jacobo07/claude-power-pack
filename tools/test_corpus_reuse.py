#!/usr/bin/env python3
"""V-CORPUS-* gates for the CO-05 coverage receipt (spec: cognitive-work-reuse, cases A-P).
Phase W2 covers A, B, C, D, E, H, J, K and the assimilation computation. Later waves extend."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.cognitive_os import coverage as cv  # noqa: E402

passes = fails = 0


def check(gate, cond, evidence=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {evidence}")
    else:
        fails += 1
        print(f"FAIL {gate} {evidence}")


def mk(tmp, files):
    root = Path(tmp) / "corpus"
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
    return root


class Counter:
    def __init__(self):
        self.calls = 0

    def __call__(self, delta):
        self.calls += 1
        return {"depth": "FULL_READ", "artifacts": [], "evidence": "test"}


def main():
    os.environ.pop("PP_CORPUS_REUSE", None)
    with tempfile.TemporaryDirectory() as tmp:
        led = Path(tmp) / "ledger.jsonl"
        cache = Path(tmp) / "cache.json"
        root = mk(tmp, {"a.txt": b"alpha", "b.txt": b"beta", "dup/a2.txt": b"alpha", "c.txt": b"gamma"})
        art = Path(tmp) / "artifact.md"
        art.write_text("summary", encoding="utf-8")
        art_ptr = {"path": str(art), "sha256": cv.sha256_file(art)}
        T, C = "extract@1", "cfg1"

        m = cv.build_manifest(root, cache_path=cache)
        check("V-CORPUS-A-MANIFEST-DUP", len(m.files) == 4 and len(m.duplicates) == 1 and len(m.unique_shas) == 3)
        v0 = cv.verdict(m, transform=T, config_digest=C, requester="p1", ledger=led)
        check("V-CORPUS-A-NONE-BEFORE", v0.state == "NONE", v0.state)

        # A first ingestion
        c = Counter()
        r = cv.ensure(m, corpus_id="c1", requester="p1", transform=T, config_digest=C,
                      extractor=lambda d: {"depth": "FULL_READ", "artifacts": [art_ptr]} | {"evidence": "e"}, ledger=led)
        check("V-CORPUS-A-FIRST", r["verdict"].state == "NONE" and r["run_id"], str(r["verdict"].state))
        # B exact repeat: zero extraction
        r = cv.ensure(m, corpus_id="c1", requester="p1", transform=T, config_digest=C, extractor=c, ledger=led)
        check("V-CORPUS-B-EXACT-ZERO-CALLS", r["verdict"].state == "EXACT_REUSE" and c.calls == 0
              and r["verdict"].artifacts == [art_ptr])
        # F fresh read from disk only
        m2 = cv.build_manifest(root, cache_path=cache)
        check("V-CORPUS-F-DISK-ONLY", cv.verdict(m2, transform=T, config_digest=C, requester="p1",
                                                 ledger=led).state == "EXACT_REUSE")
        # C partial: edit one file, add one
        (root / "b.txt").write_bytes(b"beta-edited")
        m3 = cv.build_manifest(root, cache_path=cache)
        v = cv.verdict(m3, transform=T, config_digest=C, requester="p1", ledger=led)
        check("V-CORPUS-C-PARTIAL-DELTA", v.state == "PARTIAL" and v.delta == ["b.txt"], f"{v.state} {v.delta}")
        c = Counter()
        cv.ensure(m3, corpus_id="c1", requester="p1", transform=T, config_digest=C, extractor=c, ledger=led)
        check("V-CORPUS-C-DELTA-ONLY-EXTRACT", c.calls == 1)
        # D transform change
        v = cv.verdict(m3, transform="extract@2", config_digest=C, requester="p1", ledger=led)
        check("V-CORPUS-D-TRANSFORM", v.state == "TRANSFORM_CHANGED" and not v.covered, v.state)
        # E / K scope
        v = cv.verdict(m3, transform=T, config_digest=C, requester="p2", ledger=led)
        check("V-CORPUS-K-UNAUTHORIZED", v.state == "UNAUTHORIZED" and v.artifacts == [], v.state)
        c = Counter()
        r = cv.ensure(m3, corpus_id="c1", requester="p2", transform=T, config_digest=C, extractor=c, ledger=led)
        check("V-CORPUS-K-NO-SPEND-ON-DENIED", c.calls == 0)
        cv.record(m3, corpus_id="c1", scope=["*"], transform=T, config_digest=C,
                  depth_by_rel={r_: "FULL_READ" for r_ in m3.files}, ledger=led)
        v = cv.verdict(m3, transform=T, config_digest=C, requester="p2", ledger=led)
        check("V-CORPUS-E-SECOND-SCOPE", v.state == "EXACT_REUSE", v.state)
        # INSUFFICIENT
        root2 = mk(Path(tmp) / "x", {"s.txt": b"s"})
        ms = cv.build_manifest(root2, cache_path=cache)
        cv.record(ms, corpus_id="c2", scope=["p1"], transform=T, config_digest=C,
                  depth_by_rel={"s.txt": "STRUCTURAL"}, ledger=led)
        v = cv.verdict(ms, transform=T, config_digest=C, requester="p1", need="FULL_READ", ledger=led)
        check("V-CORPUS-INSUFFICIENT", v.state == "INSUFFICIENT", v.state)
        rep = cv.coverage_report(ms, requester="p1", ledger=led)
        check("V-CORPUS-ASSIMILATED-COMPUTED", rep["assimilated_pct"] == 0.0 and rep["structural"] == 1)
        # H interruption
        led2 = Path(tmp) / "led2.jsonl"
        cv.begin(corpus_id="c3", scope=["p1"], transform=T, config_digest=C, ledger=led2)
        v = cv.verdict(ms, transform=T, config_digest=C, requester="p1", ledger=led2)
        check("V-CORPUS-H-BEGIN-NEVER-COMPLETE", v.state == "NONE" and not cv.verify_ledger(led2)["ok"])
        # J invalidated
        runs, *_ = cv.read_ledger(led)
        rid = next(iter(runs))
        led3 = Path(tmp) / "led3.jsonl"
        rid3 = cv.record(ms, corpus_id="c4", scope=["p1"], transform=T, config_digest=C,
                         depth_by_rel={"s.txt": "FULL_READ"}, ledger=led3)
        cv.invalidate(rid3, "source retracted", ledger=led3)
        v = cv.verdict(ms, transform=T, config_digest=C, requester="p1", ledger=led3)
        check("V-CORPUS-J-INVALIDATED", v.state == "INVALIDATED" and not v.covered, v.state)
        # artifact missing -> INACCESSIBLE
        led4 = Path(tmp) / "led4.jsonl"
        cv.record(ms, corpus_id="c5", scope=["p1"], transform=T, config_digest=C,
                  depth_by_rel={"s.txt": "FULL_READ"},
                  artifacts=[{"path": str(Path(tmp) / "gone.md"), "sha256": "0"}], ledger=led4)
        v = cv.verdict(ms, transform=T, config_digest=C, requester="p1", ledger=led4)
        check("V-CORPUS-INACCESSIBLE", v.state == "INACCESSIBLE", v.state)
        # corruption + UNKNOWN + kill switch
        with led.open("a", encoding="utf-8") as fh:
            fh.write("{not json\n")
        check("V-CORPUS-N-CORRUPT-DETECTED", cv.verify_ledger(led)["corrupt_lines"] == 1)
        check("V-CORPUS-UNKNOWN-EMPTY", cv.verdict(None, transform=T, config_digest=C, requester="p1").state == "UNKNOWN")
        os.environ["PP_CORPUS_REUSE"] = "off"
        v = cv.verdict(m3, transform=T, config_digest=C, requester="p1", ledger=led)
        os.environ.pop("PP_CORPUS_REUSE")
        check("V-CORPUS-KILL-SWITCH", v.state == "UNKNOWN" and "disabled" in v.reason)
        check("V-CORPUS-SOURCE-UNTOUCHED", (root / "a.txt").read_bytes() == b"alpha")
    print(f"CORPUS_REUSE_PASS={passes}/{passes + fails}  threshold=N/N")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
