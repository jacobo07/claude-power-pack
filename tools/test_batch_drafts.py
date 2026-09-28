"""V-BDRAFT-*: tools/batch_drafts.py -- bounded batch review drafts through the vendored module.

Hermetic: a temporary source root and receipts directory (CPP_BATCH_DRAFTS_DIR). Replies are
synthetic here on purpose -- this suite pins the validator's poles; the real-producer run over two
CPP files is recorded in the commit that introduced this file.
    python tools/test_batch_drafts.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

passes = fails = 0


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def reply(results: list[dict]) -> str:
    return json.dumps({"results": results})


def good(tid: str, line: int, quote: str) -> dict:
    return {"id": tid, "verdict": "safe", "mechanism": "The function returns the literal its contract requires.",
            "evidence": [{"line": line, "quote": quote}], "fix": "No change: it returns exactly the required value."}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="bdraft_t_"))
    os.environ["CPP_BATCH_DRAFTS_DIR"] = str(tmp / "receipts")
    import batch_drafts as bd
    try:
        src = tmp / "src"
        src.mkdir()
        (src / "a.py").write_text("def one():\n    return 1\n\ndef two():\n    return 2\n", encoding="utf-8")
        tasks = [bd.task("rev-one", "Does one() return 1?", ["a.py"], [{"path": "a.py", "startLine": 1, "endLine": 2}],
                         ["quote the return line"]),
                 bd.task("rev-two", "Does two() return 2?", ["a.py"], [{"path": "a.py", "startLine": 4, "endLine": 5}],
                         ["quote the return line"])]
        check("V-BDRAFT-CONTRACT-READ-ONLY", all("Writes nothing: read-only role" in t["contract"]["constraints"]
                                                 for t in tasks), tasks[0]["contract"]["constraints"])
        outcome, batch = bd.compile_batch(str(src), tasks)
        check("V-BDRAFT-COMPILES", outcome == bd.COMPLETE and batch["manifest"]["sourceFilesRead"] == 1
              and batch["prompt"], (outcome, batch.get("gaps")))
        check("V-BDRAFT-RECEIPT-WRITTEN", (tmp / "receipts" / f"{batch['binding']}.json").is_file(), batch["binding"][:12])

        print("validation: a well-formed reply, then one refusal per failure")
        ok, v = bd.validate(batch, reply([good("rev-one", 2, "return 1"), good("rev-two", 5, "return 2")]))
        check("V-BDRAFT-VALID", ok == bd.VALID and all(o["accepted"] is False for o in v["outputs"]), v.get("reason"))
        out_of_scope, v = bd.validate(batch, reply([good("rev-one", 5, "return 2"), good("rev-two", 5, "return 2")]))
        check("V-BDRAFT-FOREIGN-LINE-REFUSED", out_of_scope == bd.REFUSED and "own task scope" in v.get("reason", ""),
              v.get("reason"))
        invented, v = bd.validate(batch, reply([good("rev-one", 2, "return 42"), good("rev-two", 5, "return 2")]))
        check("V-BDRAFT-INVENTED-QUOTE-REFUSED", invented == bd.REFUSED, v.get("reason"))
        missing, v = bd.validate(batch, reply([good("rev-one", 2, "return 1")]))
        check("V-BDRAFT-MISSING-RESULT-REFUSED", missing == bd.REFUSED, v.get("reason"))
        dup = '{"results":[],"results":[]}'
        d, v = bd.validate(batch, dup)
        check("V-BDRAFT-DUPLICATE-KEY-REFUSED", d == bd.REFUSED and "Duplicate" in v.get("reason", ""), v.get("reason"))
        tampered = {**batch, "prompt": batch["prompt"].replace("Does one() return 1?", "Does one() return 9?")}
        t_out, v = bd.validate(tampered, reply([good("rev-one", 2, "return 1"), good("rev-two", 5, "return 2")]))
        check("V-BDRAFT-TAMPERED-PROMPT-REFUSED", t_out == bd.REFUSED, v.get("reason"))

        print("the bounds the validator enforces are the bounds the contract states")
        vend = (ROOT / "vendor" / "genesis-suite" / "modules" / "genesis-batch-drafts" / "lib"
                / "genesis-batch-drafts.cjs").read_text(encoding="utf-8")
        b = bd.OUTPUT_BOUNDS
        literals = [f"text(item.mechanism, 1, {b['mechanism']}, 'mechanism')", f"text(item.fix, 1, {b['fix']}, 'fix')",
                    f"text(evidence.quote, 1, {b['quote']}, 'evidence quote')", f"maxEvidence: {b['evidence']}"]
        check("V-BDRAFT-BOUNDS-MATCH-VENDOR", all(x in vend for x in literals), [x for x in literals if x not in vend])
        stated = " ".join(tasks[0]["contract"]["constraints"])
        check("V-BDRAFT-BOUNDS-STATED", f"mechanism at most {b['mechanism']}" in stated and f"fix at most {b['fix']}" in stated,
              stated)
        long_mech = {**good("rev-one", 2, "return 1"), "mechanism": "x" * (b["mechanism"] + 1)}
        lm, v = bd.validate(batch, reply([long_mech, good("rev-two", 5, "return 2")]))
        check("V-BDRAFT-OVERLONG-MECHANISM-REFUSED", lm == bd.REFUSED and "mechanism" in v.get("reason", ""),
              v.get("reason"))

        print("trust comes from the receipt, never from the batch being judged")
        stranger = {**batch, "binding": "0" * 64}
        s_out, v = bd.validate(stranger, reply([good("rev-one", 2, "return 1"), good("rev-two", 5, "return 2")]))
        check("V-BDRAFT-NO-RECEIPT-UNJUDGED", s_out == bd.UNJUDGED and "no compile receipt" in v.get("reason", ""),
              v.get("reason"))

        print("compile refusals")
        one, b1 = bd.compile_batch(str(src), tasks[:1])
        check("V-BDRAFT-ONE-TASK-INCOMPLETE", one == bd.INCOMPLETE and not b1.get("prompt"), b1.get("gaps"))
        saved = os.environ.get("CPP_NODE_EXE")
        os.environ["CPP_NODE_EXE"] = str(tmp / "no-node.exe")
        try:
            down, bdn = bd.compile_batch(str(src), tasks)
            vdown, _ = bd.validate(batch, reply([good("rev-one", 2, "return 1"), good("rev-two", 5, "return 2")]))
        finally:
            if saved is None:
                os.environ.pop("CPP_NODE_EXE", None)
            else:
                os.environ["CPP_NODE_EXE"] = saved
        check("V-BDRAFT-BRIDGE-DOWN-UNJUDGED", down == bd.UNJUDGED and vdown == bd.UNJUDGED, bdn.get("error"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = passes + fails
    print(f"BDRAFT_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
