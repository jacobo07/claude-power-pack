"""Batch source-review drafts (assimilation item 20, genesis-batch-drafts -> WRAP).

Two to four independent, static, read-only reviews of the same source share ONE bounded prompt,
so the source is read and sent once instead of once per reviewer. The vendored module does the
work through the one bridge: compileBatch reads the selected line ranges and binds each excerpt
to its SHA-256; validateBatchResult refuses any reply whose evidence quotes a line the task was
not given. Every result stays a DRAFT (accepted: false) -- this never replaces a real review.

What this wrapper adds:
  * each task's contract is a tools/task_contract.py contract (read-only role, stated stop and
    acceptance), so a batch cannot carry an unstated write scope;
  * the batch's binding and prompt hash are RECORDED at compile time in a receipt, and validation
    takes its expectations from that receipt -- never from the batch file it is judging, which
    would let the batch vouch for itself.

    python tools/batch_drafts.py compile --spec spec.json --out batch.json   (prompt -> batch.prompt.txt)
    python tools/batch_drafts.py validate --batch batch.json --result reply.json
compile: exit 0 complete · 3 incomplete (gaps printed) · 2 bridge could not answer
validate: exit 0 drafts accepted as well-formed · 3 refused (reason printed) · 2 bridge/receipt missing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from modules.external_assimilation import node_bridge as nb  # noqa: E402
import task_contract as tc  # noqa: E402

COMPLETE, INCOMPLETE, VALID, REFUSED, UNJUDGED = "COMPLETE", "INCOMPLETE", "VALID", "REFUSED", "UNJUDGED"
WORKER = {"route": "claude-code-agent", "requestedModel": "claude-sonnet-5", "config": {}}


def receipts_dir() -> Path:
    return Path(os.environ.get("CPP_BATCH_DRAFTS_DIR") or (Path.home() / ".claude" / "state" / "batch-drafts"))


# The bounds validateBatchResult ENFORCES (vendored lib/genesis-batch-drafts.cjs: text(item.mechanism,
# 1, 1200), text(item.fix, 1, 1600), text(evidence.quote, 1, 400), LIMITS.maxEvidence 12) but the
# compiled prompt never STATES. Measured 2026-09-28: the first real reply wrote a ~1900-char
# mechanism and was refused for a limit it was never told. The contract -- which the worker does
# see -- now carries them; test_batch_drafts reads the vendored literals so the two cannot drift.
OUTPUT_BOUNDS = {"mechanism": 1200, "fix": 1600, "quote": 400, "evidence": 12}


def task(id: str, review: str, paths: list[str], selectors: list[dict], acceptance: list[str],  # noqa: A002
         expected_hashes: dict | None = None) -> dict:
    b = OUTPUT_BOUNDS
    contract = tc.build(id=id, objective=review, owner="batch reviewer (read-only draft)", acceptance=acceptance,
                        stop="one result for this task id, then stop", writes=[], inputs=paths,
                        constraints=[f"mechanism at most {b['mechanism']} characters",
                                     f"fix at most {b['fix']} characters",
                                     f"at most {b['evidence']} evidence items, each quote at most {b['quote']} characters"])
    return {"id": id, "task": review, "contract": contract, "operation": "read-only-draft",
            "dependencyMode": "static", "dependsOn": [], "worker": WORKER, "sourcePaths": paths,
            "selectors": selectors, "expectedSourceHashes": expected_hashes or {}, "effects": ["source-read"]}


def compile_batch(root: str, tasks: list[dict], max_chars: int | None = None) -> tuple[str, dict]:
    req = {"root": str(root), "tasks": tasks}
    if max_chars is not None:
        req["maxChars"] = max_chars
    r = nb.call("batchDrafts", "compileBatch", [req], timeout=60)
    if not r.ok:
        return UNJUDGED, {"error": f"bridge {r.outcome}: {r.error}"}
    batch = r.value or {}
    if not batch.get("complete"):
        return INCOMPLETE, batch
    d = receipts_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{batch['binding']}.json").write_text(json.dumps(
        {"binding": batch["binding"], "promptSha256": batch["promptSha256"], "root": str(root),
         "taskIds": batch["manifest"]["taskIds"]}, indent=1), encoding="utf-8")
    return COMPLETE, batch


def validate(batch: dict, result_text: str) -> tuple[str, dict]:
    receipt = receipts_dir() / f"{batch.get('binding')}.json"
    try:
        rec = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return UNJUDGED, {"reason": f"no compile receipt for binding {str(batch.get('binding'))[:12]}: this batch "
                                   f"was not compiled here, so nothing trusted can vouch for it"}
    r = nb.call("batchDrafts", "validateBatchResult",
                [batch, result_text, {"expectedBinding": rec["binding"], "expectedPromptSha256": rec["promptSha256"]}],
                timeout=60)
    if not r.ok:
        return UNJUDGED, {"reason": f"bridge {r.outcome}: {r.error}"}
    v = r.value or {}
    return (VALID if v.get("ok") else REFUSED), v


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compile")
    c.add_argument("--spec", required=True, help='JSON {"root": ..., "tasks": [task() kwargs, ...]}')
    c.add_argument("--out", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--batch", required=True)
    v.add_argument("--result", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "compile":
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        try:
            tasks = [task(**t) for t in spec["tasks"]]
        except (TypeError, ValueError) as exc:
            print(f"INCOMPLETE: {exc}")
            return 3
        outcome, batch = compile_batch(spec["root"], tasks, spec.get("maxChars"))
        if outcome == UNJUDGED:
            print(f"UNJUDGED: {batch['error']}")
            return 2
        Path(a.out).write_text(json.dumps(batch, indent=1), encoding="utf-8")
        if outcome == INCOMPLETE:
            print(f"INCOMPLETE: {json.dumps(batch.get('gaps'))}")
            return 3
        Path(a.out).with_suffix(".prompt.txt").write_text(batch["prompt"], encoding="utf-8")
        m = batch["measurements"]
        print(f"COMPLETE binding={batch['binding'][:12]} tasks={batch['manifest']['taskCount']} "
              f"files_read={batch['manifest']['sourceFilesRead']} prompt_chars={m['promptChars']}")
        return 0
    batch = json.loads(Path(a.batch).read_text(encoding="utf-8"))
    outcome, res = validate(batch, Path(a.result).read_text(encoding="utf-8-sig").strip())
    if outcome == VALID:
        for o in res["outputs"]:
            print(f"DRAFT {o['id']}: {o['verdict']} -- {o['mechanism'][:160]}")
        return 0
    print(f"{outcome}: {res.get('reason')}")
    return 3 if outcome == REFUSED else 2


if __name__ == "__main__":
    sys.exit(main())
