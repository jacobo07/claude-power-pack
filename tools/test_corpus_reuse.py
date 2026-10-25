#!/usr/bin/env python3
"""V-CORPUS-* gates for the CO-05 coverage receipt (spec: cognitive-work-reuse, cases A-P).
Phase W2 covers A, B, C, D, E, H, J, K and the assimilation computation. Later waves extend."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_STATE = tempfile.mkdtemp(prefix="corpus_state_")
os.environ["PP_CORPUS_STATE_DIR"] = _STATE   # hermetic: no test writes into the live vault
from modules.cognitive_os import coverage as cv  # noqa: E402
from modules.cognitive_os import corpus_delivery as cd  # noqa: E402
from modules.fable_distillation import fd_00_gate  # noqa: E402

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
        # N repair: corrupt line + orphan BEGIN quarantined, complete runs kept, verify ok after
        cv.begin(corpus_id="orphan", scope=["p1"], transform=T, config_digest=C, ledger=led)
        before = cv.verdict(m3, transform=T, config_digest=C, requester="p1", ledger=led).state
        rep_r = cv.repair_ledger(led)
        after = cv.verdict(m3, transform=T, config_digest=C, requester="p1", ledger=led).state
        check("V-CORPUS-N-REPAIR", rep_r["quarantined"] == 2 and cv.verify_ledger(led)["ok"]
              and before == after and Path(str(led) + ".quarantine").is_file(), str(rep_r))
        # M concurrency across real processes: one extracts, the other adopts
        led5 = Path(tmp) / "led5.jsonl"
        count = Path(tmp) / "count.txt"
        child = (
            "import sys,time;sys.path.insert(0,sys.argv[1]);from pathlib import Path\n"
            "from modules.cognitive_os import coverage as cv\n"
            "m=cv.build_manifest(sys.argv[2],cache_path=sys.argv[5])\n"
            "def ex(d):\n"
            "    time.sleep(1.0);open(sys.argv[4],'a').write('x');return {'depth':'FULL_READ'}\n"
            "r=cv.ensure(m,corpus_id='cm',requester='p1',transform='t@1',config_digest='c',extractor=ex,ledger=sys.argv[3])\n"
            "print(r['verdict'].state)\n")
        import subprocess
        procs = [subprocess.Popen([sys.executable, "-c", child, str(ROOT), str(root), str(led5), str(count),
                                   str(Path(tmp) / f"cc{i}.json")], stdout=subprocess.PIPE, text=True)
                 for i in range(2)]
        outs = sorted(p.communicate(timeout=60)[0].strip() for p in procs)
        check("V-CORPUS-M-ONE-EXTRACTS-ONE-ADOPTS",
              count.read_text() == "x" and outs == ["EXACT_REUSE", "NONE"] and cv.verify_ledger(led5)["ok"],
              f"{outs} calls={len(count.read_text()) if count.exists() else 0}")
        # H resume: after an interrupted BEGIN, ensure still extracts the full missing set once
        led6 = Path(tmp) / "led6.jsonl"
        cv.begin(corpus_id="ch", scope=["p1"], transform=T, config_digest=C, ledger=led6)
        c = Counter()
        cv.ensure(m3, corpus_id="ch", requester="p1", transform=T, config_digest=C, extractor=c, ledger=led6)
        check("V-CORPUS-H-RESUME", c.calls == 1 and cv.verdict(
            m3, transform=T, config_digest=C, requester="p1", ledger=led6).state == "EXACT_REUSE")
        check("V-CORPUS-UNKNOWN-EMPTY",cv.verdict(None, transform=T, config_digest=C, requester="p1").state == "UNKNOWN")
        os.environ["PP_CORPUS_REUSE"] = "off"
        v = cv.verdict(m3, transform=T, config_digest=C, requester="p1", ledger=led)
        os.environ.pop("PP_CORPUS_REUSE")
        check("V-CORPUS-KILL-SWITCH", v.state == "UNKNOWN" and "disabled" in v.reason)
        check("V-CORPUS-SOURCE-UNTOUCHED", (root / "a.txt").read_bytes() == b"alpha")
    delivery_gates()
    print(f"CORPUS_REUSE_PASS={passes}/{passes + fails}  threshold=N/N")
    return 0 if fails == 0 else 1


def run_hook(payload, *, env_extra=None):
    """Drive the REAL hook: node -> python -> stdout, exactly as the harness does."""
    import json
    import shutil
    import subprocess
    node = shutil.which("node")
    env = dict(os.environ, **(env_extra or {}))
    r = subprocess.run([node, str(ROOT / "hooks" / "corpus-reuse-sentinel.js")], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=60, env=env)
    return r.returncode, r.stdout.strip()


def delivery_gates():
    import json
    st = Path(_STATE)
    with tempfile.TemporaryDirectory() as tmp:
        part = mk(tmp, {"p/a.txt": b"A", "p/b.txt": b"B", "p/c.txt": b"C"})
        full = mk(Path(tmp) / "f", {"x.txt": b"X"})
        art = Path(tmp) / "brief.md"
        art.write_text("prior summary", encoding="utf-8")
        ptr = {"path": str(art), "sha256": cv.sha256_file(art)}
        mp = cv.build_manifest(part)
        mf = cv.build_manifest(full)
        cd.register("partial-corp", str(part))
        cd.register("full-corp", str(full))
        cv.record(mp, corpus_id="partial-corp", scope=["p1"], transform="t@1", config_digest="c",
                  depth_by_rel={"p/a.txt": "FULL_READ", "p/b.txt": "STRUCTURAL"}, artifacts=[ptr])
        cv.record(mf, corpus_id="full-corp", scope=["p1"], transform="t@1", config_digest="c",
                  depth_by_rel={"x.txt": "FULL_READ"}, artifacts=[ptr])
        base = {"hook_event_name": "UserPromptSubmit", "cwd": str(Path(tmp) / "p1")}
        env = {"PP_CORPUS_STATE_DIR": str(st), "PYTHONIOENCODING": "utf-8"}
        pr = f"please mine {str(part).replace(chr(92), '/')}/a.txt again for the ads"
        rc, out = run_hook(dict(base, prompt=pr), env_extra=env)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""
        check("V-CORPUS-DELIVERY-HOOK-E2E", rc == 0 and "partial-corp" in ctx and "uncovered" in ctx
              and "data from a ledger" in ctx, ctx[:90])
        rc, out = run_hook({"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": base["cwd"],
                            "tool_input": {"prompt": f"read everything under {part}"}}, env_extra=env)
        check("V-CORPUS-DELIVERY-SUBAGENT-SPAWN", rc == 0 and "partial-corp" in out)
        rc, out = run_hook({"hook_event_name": "PreToolUse", "tool_name": "Read", "cwd": base["cwd"],
                            "tool_input": {"prompt": f"{part}"}}, env_extra=env)
        check("V-CORPUS-DELIVERY-OTHER-TOOL-SILENT", rc == 0 and out == "")
        rc, out = run_hook(dict(base, prompt="nothing about any corpus here"), env_extra=env)
        check("V-CORPUS-DELIVERY-UNREGISTERED-SILENT", rc == 0 and out == "")
        rc, out = run_hook(dict(base, cwd=str(Path(tmp) / "intruder"), prompt=pr), env_extra=env)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""
        check("V-CORPUS-K-HOOK-SCOPE-NO-LEAK", "FULL_READ 0, STRUCTURAL 0" in ctx and brief_name(art) not in ctx, ctx[:120])
        rc, out = run_hook(dict(base, prompt=pr), env_extra=dict(env, PP_CORPUS_REUSE="off"))
        check("V-CORPUS-KILL-SWITCH-HOOK", rc == 0 and out == "")
        before = cd.delivery_status(log=st / "delivery.jsonl")
        rc, out = run_hook(dict(base, prompt=pr), env_extra=dict(env, PP_PYTHON=str(Path(tmp) / "no-python.exe")))
        after = cd.delivery_status(log=st / "delivery.jsonl")
        check("V-CORPUS-L-FAILURE-COUNTED-NOT-SILENT", rc == 0 and out == ""
              and after["FAILED"] == before["FAILED"] + 1 and before["DELIVERED"] >= 2, f"{before} -> {after}")
        # FD-00: the real consumer
        d = fd_00_gate.check_admission(f"mine {full} thoroughly", corpus_requester="p1")
        check("V-CORPUS-FD00-FULL-ANSWER-FROM-ASSET", d.verdict == "ANSWER_FROM_ASSET"
              and d.signals.get("corpus_artifacts") == [str(art)], d.verdict)
        d = fd_00_gate.check_admission(f"mine {part} thoroughly", corpus_requester="p1")
        check("V-CORPUS-FD00-PARTIAL-NOT-ANSWERED", d.verdict != "ANSWER_FROM_ASSET"
              and d.signals.get("corpus_coverage", {}).get("uncovered") == 1, d.verdict)
        d = fd_00_gate.check_admission(f"mine {full} thoroughly", corpus_requester="intruder")
        check("V-CORPUS-FD00-SCOPE", d.verdict != "ANSWER_FROM_ASSET")
        d = fd_00_gate.check_admission("write a regex to rename files")
        check("V-CORPUS-FD00-UNCHANGED-WITHOUT-CORPUS", "corpus_id" not in d.signals)


def brief_name(p):
    return p.name


if __name__ == "__main__":
    sys.exit(main())
