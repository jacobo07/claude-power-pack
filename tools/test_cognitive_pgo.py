#!/usr/bin/env python3
"""CDC C8 gates: cognitive_pgo + proof_digest. Synthetic transcripts; mutation drills flip RED."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def tool_turn(i, name, inp, result, tokens=1000, is_error=False):
    a = {"type": "assistant", "requestId": f"r{i}", "message": {"id": f"m{i}", "model": "claude-x",
         "usage": {"input_tokens": tokens, "output_tokens": 10},
         "content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]}}
    u = {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}",
         "content": result, "is_error": is_error}]}}
    return [a, u]


def write_tx(path: Path, turns):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "user", "message": {"content": "do the thing"}}) + "\n")
        for t in turns:
            for row in t:
                fh.write(json.dumps(row) + "\n")


def load(src_edit=None):
    src = (HERE / "cognitive_pgo.py").read_text(encoding="utf-8")
    if src_edit:
        src = src_edit(src)
    spec = importlib.util.spec_from_loader("pgo_mut", loader=None)
    m = importlib.util.module_from_spec(spec)
    m.__file__ = str(HERE / "cognitive_pgo.py")
    exec(compile(src, "pgo_mut", "exec"), m.__dict__)
    return m


with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "projects"
    (root / "projA").mkdir(parents=True)
    big = "\n".join(["tests/test_a.py::t%d PASSED" % i for i in range(300)]
                    + ["tests/test_a.py::test_bad FAILED", "AssertionError: 1 != 2"] + ["tests/test_a.py::u%d PASSED" % i for i in range(20)] + ["2 failed, 320 passed"])
    turns = [tool_turn(1, "Read", {"file_path": "/x/a.py"}, "code"),
             tool_turn(2, "Read", {"file_path": "/x/a.py"}, "code"),          # REREAD
             tool_turn(3, "Edit", {"file_path": "/x/a.py", "new_string": "y"}, "ok"),
             tool_turn(4, "PowerShell", {"command": "python -m pytest tests"}, big),
             tool_turn(5, "Grep", {"pattern": "FAILED"}, "hit"),
             tool_turn(6, "Read", {"file_path": "/x/log.txt"}, "more")]
    turns += [tool_turn(10 + i, "Grep", {"pattern": f"p{i}"}, "none") for i in range(30)]   # 30-call no-progress run
    write_tx(root / "projA" / "s1.jsonl", turns)

    import cognitive_pgo as pgo
    r = pgo.build(root, days=14, deadline_s=60)
    check("coverage", r["coverage"]["read"] == 1 and r["coverage"]["complete"], str(r["coverage"]))
    check("roles", r["by_role"].get("REREAD", {}).get("calls") == 1 and "PROOF" in r["by_role"], str(list(r["by_role"])))
    check("project", "projA" in r["by_project"], str(r["by_project"]))
    check("motif n-grams 2..4", {m["n"] for m in r["motifs"]} <= {2, 3, 4} and r["motifs"] and
          any(m["n"] == 2 for m in r["motifs"]), f"{len(r['motifs'])} motifs")
    check("grep run motif", any(m["motif"].startswith("Grep > Grep") for m in r["motifs"]), "")
    ca = r["unproductive"]["by_cause"]
    check("unproductive: reread + no-progress run", "REREAD" in ca and any(k.startswith("NO_PROGRESS_RUN") for k in ca), str(ca))
    run_calls = sum(v["calls"] for k, v in ca.items() if k.startswith("NO_PROGRESS_RUN"))
    check("run counted beyond trip only", 0 < run_calls < 30, f"{run_calls} (trip {pgo.TRIP})")
    debts = {d["debt"]: d for d in r["debt_register"]}
    check("UNKNOWN is not zero", debts["Owner"]["cost_tokens"] is None and debts["Constitutional"]["status"] == "UNKNOWN", "")
    check("interest = avoidable x recurrence", all(d["interest"] == d["avoidable_tokens"] * d["recurrence"]
          for d in r["debt_register"] if d["status"] == "MEASURED"), "")
    check("roic ordered", [d["roic"] for d in r["debt_register"] if d["roic"] is not None] ==
          sorted([d["roic"] for d in r["debt_register"] if d["roic"] is not None], reverse=True), "")
    check("frontier has reopen", all(f["reopen"] for f in r["frontier"]) and r["frontier"], "")
    md = pgo.render_md(r)
    check("md sections", all(s in md for s in ("Dominant tax", "Motifs", "Debt register", "Irreducibility", "Exit to determinism", "Unproductive")), "")
    out = Path(td) / "out"
    rc = pgo.main(["--root", str(root), "--out-dir", str(out)])
    check("cli writes json+md+corpus", rc == 0 and (out / "cognitive-pgo.json").exists() and (out / "cognitive-pgo.md").exists()
          and (out / "unproductive-corpus.jsonl").exists(), "")
    # deadline: partial coverage is declared, not hidden
    rp = pgo.build(root, days=14, deadline_s=-1)
    check("deadline -> PARTIAL declared", rp["coverage"]["read"] == 0 and not rp["coverage"]["complete"], str(rp["coverage"]))

    # mutation drills
    m1 = load(lambda s: s.replace('"cost_tokens": None, "recurrence": None', '"cost_tokens": 0, "recurrence": None'))
    r1 = m1.build(root, 14, 60)
    check("MUT unknown reported as zero -> RED", {d["debt"]: d for d in r1["debt_register"]}["Owner"]["cost_tokens"] is not None, "")
    m2 = load(lambda s: s.replace("elif run > TRIP:", "elif run > 10**9:"))
    r2 = m2.build(root, 14, 60)
    check("MUT trip disabled flips run check RED", not any(k.startswith("NO_PROGRESS_RUN") for k in r2["unproductive"]["by_cause"]), "")
    m3 = load(lambda s: s.replace("for n in range(lo, hi + 1):", "for n in range(lo, lo + 1):"))
    r3 = m3.build(root, 14, 60)
    check("MUT bigram-only flips n-gram check RED", {m["n"] for m in r3["motifs"]} == {2}, "")

    # proof_digest
    import proof_digest as pd
    d = pd.digest_text(big)
    txt = pd.render(d, 1, "L")
    check("digest keeps failing line", "test_bad FAILED" in txt and "AssertionError" in txt and "2 failed, 320 passed" in txt, "")
    check("digest much smaller", len(txt) < len(big) / 5, f"{len(big)} -> {len(txt)}")
    check("digest drops passing noise", "t150 PASSED" not in txt, "")
    log = Path(td) / "run.log"
    rc, body = pd.run([sys.executable, "-c", "print('a');print('b FAILED');raise SystemExit(3)"], log, 30, 1)
    check("run: rc passthrough + log", rc == 3 and "b FAILED" in body and log.exists() and "a" in log.read_text(), body.splitlines()[0])
    t0 = time.time()
    rc, body = pd.run([sys.executable, "-c", "import time;print('start',flush=True);time.sleep(60)"], Path(td) / "t.log", 2, 1)
    check("run awaits + kills on timeout", rc == 124 and "TIMEOUT" in body and time.time() - t0 < 20, f"{time.time()-t0:.1f}s")
    import os
    os.environ["CPP_PROOF_DIGEST"] = "off"
    rc, body = pd.run([sys.executable, "-c", "print('raw line')"], Path(td) / "k.log", 30, 1)
    check("kill switch -> raw output", "raw line" in body and "DIGEST" not in body, "")
    del os.environ["CPP_PROOF_DIGEST"]
    rep = pd.replay(root / "projA" / "s1.jsonl", 1000)
    check("replay before/after", rep["before"]["calls"] == 1 + rep["refetch_calls_observed"] and rep["refetch_calls_observed"] >= 2 and rep["after"]["calls"] == 1 and
          rep["after"]["tokens_est"] < rep["before"]["tokens_est"] / 5, str(rep["before"]) + str(rep["after"]))
    # mutant: digest that drops failing lines
    src = (HERE / "proof_digest.py").read_text(encoding="utf-8").replace('fails = [i for i, l in enumerate(lines) if FAIL_LINE.search(l)]', 'fails = []')
    spec = importlib.util.spec_from_loader("pd_mut", loader=None)
    pm = importlib.util.module_from_spec(spec)
    pm.__file__ = str(HERE / "proof_digest.py")
    exec(compile(src, "pd_mut", "exec"), pm.__dict__)
    check("MUT digest drops failures -> RED", "test_bad FAILED" not in pm.render(pm.digest_text(big), 1, "L"), "")

print(f"\n{passes} passed, {fails} failed")
sys.exit(1 if fails else 0)
