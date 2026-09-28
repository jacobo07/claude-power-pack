"""Done-evidence bundle (assimilation item 23, genesis-evidence-collector -> WRAP).

"Done" in this estate means a gate was OBSERVED to pass (HR-OUTPUT-002). The vendored collector
enforces the properties that make an observation worth something, and CPP had no producer for its
receipts. This is that producer:

  check receipts   each criterion names a CPP V-gate command; it is RUN here, and its receipt
                   records the exit code and the suite's own `X_PASS=n/m` line as checked/expected.
                   A suite that judged nothing (no summary, or m == 0) cannot pass -- an empty gate
                   is not a green one.
  review receipt   from a tools/review_intake.py reply: pass only on APPROVE, with the reviewer's
                   agent/model/effort; the collector refuses a reviewer who is the worker.
  binding          every receipt carries the SHA-256 of the artifacts it judged; the collector
                   re-reads them after assembly, so bytes that moved mid-collection fail.

Receipts live under <root>/_logs/evidence/<plan>/<task>/ (git-ignored). Missing stays MISSING:
the bundle lists every failure; `ok` is true only when there are none.

    python tools/evidence_bundle.py --plan P --task T --worker W --artifact tools/x.py
        --check "crit-a=python tools/test_x.py" [--review reply.txt --reviewer pp-code-reviewer
        --reviewer-model claude-sonnet-5 --reviewer-effort default]
exit 0 ok · 3 failures listed · 2 the bridge could not answer
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from modules.external_assimilation import node_bridge as nb  # noqa: E402
import review_intake as ri  # noqa: E402

_SUMMARY = re.compile(r"\b[A-Z][A-Z0-9_]*_PASS=(\d+)/(\d+)")
PY = sys.executable


def _proofs(root: Path, paths: list[str]) -> list[dict]:
    return [{"path": p, "sha256": hashlib.sha256((root / p).read_bytes()).hexdigest()} for p in paths]


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", s.lower()).strip("-")[:80] or "x"


def run_check(root: Path, plan: str, task: str, criterion: str, command: str, artifacts: list[str],
              timeout: float = 600) -> str:
    """Run one V-gate command and write its receipt. Returns the receipt's root-relative path.

    The artifacts are hashed BEFORE the run and again after: the receipt binds the bytes the gate
    actually ran against, and a byte that moved mid-run fails it. Hashing only afterwards bound a
    passed receipt to bytes no gate had seen (real review of this file, 2026-09-28)."""
    # posix=True treats a backslash as an escape, turning `tools\test_x.py` into `toolstest_x.py`.
    argv = shlex.split(command.replace("\\", "/") if os.name == "nt" else command, posix=True)
    if argv and argv[0] == "python":
        argv[0] = PY
    before = _proofs(root, artifacts)
    try:
        p = subprocess.run(argv, cwd=root, capture_output=True, timeout=timeout)
        out = p.stdout.decode("utf-8", errors="replace") + p.stderr.decode("utf-8", errors="replace")
        code = p.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        out, code = f"could not run: {exc.__class__.__name__}", -1
    moved = _proofs(root, artifacts) != before
    m = _SUMMARY.findall(out)
    checked, expected = (int(m[-1][0]), int(m[-1][1])) if m else (0, 0)
    receipt = {"schema": "genesis-check-v1", "planId": plan, "taskId": task, "criterion": criterion,
               "status": "passed" if code == 0 and expected > 0 and checked == expected and not moved else "failed",
               "command": command, "exitCode": code, "checkedCount": checked, "expectedCount": expected,
               "artifacts": before, "artifactsMovedDuringRun": moved}
    rel = f"_logs/evidence/{_slug(plan)}/{_slug(task)}/checks/{_slug(criterion)}.json"
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    return rel


def _ticket_path(root: Path, plan: str, task: str) -> Path:
    return root / "_logs" / "evidence" / _slug(plan) / _slug(task) / "review-ticket.json"


def ticket_line(nonce: str) -> str:
    """The line a dispatcher puts in the review prompt, and the reviewer must echo back."""
    return f"REVIEW-TICKET: {nonce}"


def ticket(root: Path, plan: str, task: str, artifacts: list[str]) -> tuple[str, str]:
    """Record the bytes a reviewer is about to read, under an unguessable nonce. Issue it
    IMMEDIATELY before dispatching the review, and put ticket_line(nonce) in the prompt.

    Hashes alone were not enough (second real review, 2026-09-28): they record when --ticket ran,
    so re-ticketing after an edit let an OLD approval pass. A reply can only carry the nonce if it
    was written after this ticket existed, which is what binds the reply to what was observed."""
    import secrets
    nonce = secrets.token_hex(12)
    p = _ticket_path(root, plan, task)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"planId": plan, "taskId": task, "nonce": nonce,
                             "artifacts": _proofs(root, artifacts)}, indent=1), encoding="utf-8")
    return p.relative_to(root).as_posix(), nonce


def write_review(root: Path, plan: str, task: str, reply: str, reviewer: dict, artifacts: list[str],
                 check_paths: list[str]) -> tuple[str, ri.Intake]:
    """The receipt carries the TICKET's hashes -- what the reviewer saw. If the code moved since,
    the collector compares those to today's bytes and fails the review as stale. With no ticket, or
    a reply that does not echo the ticket's nonce, nothing ties this reply to that observation."""
    res = ri.intake(reply, reviewer["agent"], reviewer["model"])
    try:
        t = json.loads(_ticket_path(root, plan, task).read_text(encoding="utf-8"))
        seen, unbound = t["artifacts"], ""
        if not t.get("nonce") or ticket_line(t["nonce"]) not in (reply or ""):
            unbound = "the reply does not echo this ticket's nonce: it was not written for this dispatch"
    except (OSError, ValueError, KeyError):
        seen, unbound = [], "no review ticket: nothing records which bytes the reviewer read"
    receipt = {"schema": "genesis-review-v1", "planId": plan, "taskId": task,
               "verdict": "pass" if res.verdict == ri.APPROVE and not unbound else "fail",
               "reviewer": reviewer, "intake": {"verdict": res.verdict, "reason": unbound or res.reason},
               "artifacts": seen, "checks": _proofs(root, check_paths)}
    rel = f"_logs/evidence/{_slug(plan)}/{_slug(task)}/review.json"
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    return rel, res


def collect(root: Path, plan: str, task: str, worker: str, criteria: list[str], artifacts: list[str],
            check_paths: list[str], review_path: str | None = None, required_reviewer: dict | None = None) -> dict:
    # The vendored collector refuses any proof path matching /secret|credential/ (or .env, .git).
    # Say so by name instead of surfacing its bare throw as an unexplained UNJUDGED (second review).
    # Receipt paths are built from the plan/task/criterion slugs, so a plan named for the secret
    # firewall trips it too (third review): every path the collector will read is screened.
    # Known limit, recorded not hidden: the ticket binds bytes at ISSUE time. An edit A->B->A by a
    # concurrent writer between the ticket and the reviewer's read passes as a review of A.
    every = [*artifacts, *check_paths, *([review_path] if review_path else [])]
    protected = [a for a in every if re.search(r"(^|/)(\.env(\.|$)|\.git$)|secret|credential", a, re.I)]
    if protected:
        return {"ok": False, "unjudged": True,
                "failures": [f"the collector refuses protected proof paths by design: {', '.join(protected)}; "
                             "this bundle cannot be judged by it"]}
    inp = {"root": str(root), "planId": plan, "taskId": task, "worker": worker, "criteria": criteria,
           "artifactPaths": artifacts, "checkPaths": check_paths}
    if review_path:
        inp["reviewPath"] = review_path
        inp["requiredReviewer"] = required_reviewer
    r = nb.call("evidenceCollector", "collectEvidence", [inp], timeout=60)
    if not r.ok:
        return {"ok": False, "unjudged": True, "failures": [f"bridge {r.outcome}: {r.error}"]}
    return r.value or {"ok": False, "failures": ["collector returned nothing"]}


def main(argv=None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--plan", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--worker", required=True)
    ap.add_argument("--artifact", action="append", required=True)
    ap.add_argument("--check", action="append", default=[], help="criterion=command")
    ap.add_argument("--ticket", action="store_true",
                    help="only record the bytes a reviewer is about to read; run right before dispatching it")
    ap.add_argument("--review")
    ap.add_argument("--reviewer")
    ap.add_argument("--reviewer-model")
    ap.add_argument("--reviewer-effort", default="default")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    arts = [x.replace("\\", "/") for x in a.artifact]
    if a.ticket:
        path, nonce = ticket(root, a.plan, a.task, arts)
        print(f"TICKET {path}")
        print(f"Put this line in the review prompt and require the reviewer to echo it verbatim:\n"
              f"  {ticket_line(nonce)}")
        return 0
    if not a.check:
        ap.error("--check is required unless --ticket")
    crits, paths = [], []
    for spec in a.check:
        crit, _, cmd = spec.partition("=")
        crits.append(crit)
        paths.append(run_check(root, a.plan, a.task, crit, cmd, arts))
    review_path, required = None, None
    if a.review:
        required = {"agent": a.reviewer, "model": a.reviewer_model, "effort": a.reviewer_effort}
        review_path, res = write_review(root, a.plan, a.task, Path(a.review).read_text(encoding="utf-8-sig"),
                                        required, arts, paths)
        print(f"review intake: {res.verdict} {res.reason}")
    b = collect(root, a.plan, a.task, a.worker, crits, arts, paths, review_path,
                {"model": a.reviewer_model, "effort": a.reviewer_effort} if a.review else None)
    print("OK" if b.get("ok") else ("UNJUDGED" if b.get("unjudged") else "NOT DONE"))
    for f in b.get("failures") or []:
        print(f"  - {f}")
    return 0 if b.get("ok") else (2 if b.get("unjudged") else 3)


if __name__ == "__main__":
    sys.exit(main())
