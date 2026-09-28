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
import verified_reuse as vr  # noqa: E402

COMPLETE, INCOMPLETE, VALID, REFUSED, UNJUDGED = "COMPLETE", "INCOMPLETE", "VALID", "REFUSED", "UNJUDGED"
REUSED = "REUSED"
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
    # The task specs are recorded here, not read back from the batch at validation time, so the
    # drafts admitted for reuse are bound to what THIS compile was asked for.
    (d / f"{batch['binding']}.json").write_text(json.dumps(
        {"binding": batch["binding"], "promptSha256": batch["promptSha256"], "root": str(root),
         "taskIds": batch["manifest"]["taskIds"], "tasks": tasks}, indent=1), encoding="utf-8")
    return COMPLETE, batch


def reuse_enabled() -> bool:
    return (os.environ.get("CPP_VERIFIED_REUSE") or "").strip().lower() not in ("off", "0", "false")


def compile_with_reuse(root: str, tasks: list[dict], max_chars: int | None = None) -> tuple[str, dict, dict]:
    """Hand back a verified prior draft for every task whose exact inputs were already reviewed;
    compile a batch only for the rest. Returns (outcome, batch, reused_by_task_id); outcome
    REUSED when nothing was left to dispatch. A reused draft is never accepted."""
    reused: dict = {}
    if reuse_enabled():
        remaining = []
        for t in tasks:
            outcome, info = vr.lookup(root, t, OUTPUT_BOUNDS)
            if outcome == vr.HIT:
                reused[t["id"]] = info
            else:
                remaining.append(t)
        tasks = remaining
    if not tasks:
        return REUSED, {}, reused
    outcome, batch = compile_batch(root, tasks, max_chars)
    return outcome, batch, reused


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
    if v.get("ok") and reuse_enabled() and rec.get("tasks"):
        # Well-formed drafts become reusable DRAFTS for identical future tasks. Admission can fail
        # (a source changed since compile) without changing this verdict; the outcome is reported.
        specs = {t["id"]: t for t in rec["tasks"]}
        v["admitted"] = {}
        for o in v.get("outputs") or []:
            t = specs.get(o.get("id"))
            if t is not None:
                v["admitted"][o["id"]] = vr.admit(rec["root"], t, OUTPUT_BOUNDS, o, plan_id=rec["binding"],
                                                  worker_id=WORKER["route"])[0]
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
        outcome, batch, reused = compile_with_reuse(spec["root"], tasks, spec.get("maxChars"))
        for tid, info in reused.items():
            # A reused draft is still a draft: it needs a fresh review, exactly like a new one.
            print(f"REUSED {tid}: draft from {info['sourceTask']['planId'][:12]} (accepted=false, "
                  f"fresh review required; avoided 1 dispatch, {info['avoided']['source_chars']} source chars)")
        if reused:
            Path(a.out).with_suffix(".reused.json").write_text(json.dumps(reused, indent=1), encoding="utf-8")
        if outcome == REUSED:
            print("REUSED: every task matched a verified prior draft; nothing to dispatch")
            return 0
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
