"""V-ROLLBUDGET-* gates: `rollover.py certify --budget-stop N --calls-estimate K` declares the
certifying session's envelope through mission_spend.feasibility, or refuses with the numbers
without undoing the certification. TOK-18 Slice A, fix #2, 2026-10-06. Both poles driven."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

passes = fails = 0


def _check(gate: str, cond: bool, ev: str) -> None:
    global passes, fails
    if cond:
        passes += 1
    else:
        fails += 1
    print(f"{'PASS' if cond else 'FAIL'} {gate}: {ev}")


def _transcript(path: Path, contexts: list[int]) -> None:
    rows = [{"type": "assistant", "timestamp": f"2026-10-06T10:00:{i:02d}",
             "message": {"id": f"m{i}", "model": "claude-opus", "content": [],
                         "usage": {"input_tokens": 0, "cache_creation_input_tokens": 0,
                                   "cache_read_input_tokens": c, "output_tokens": 0}}}
            for i, c in enumerate(contexts)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cfg, state, work = tmp / "cfg", tmp / "state", tmp / "work"
        work.mkdir()
        os.environ["CLAUDE_CONFIG_DIR"] = str(cfg)
        os.environ["GSD_LONG_RUN_STATE_DIR"] = str(state)
        import mission_spend as ms
        import rollover as ro
        sid = "claimant-1"
        _transcript(cfg / "projects" / ms.encode_cwd(str(work)) / f"{sid}.jsonl", [100_000] * 5)  # 500K spent

        # Red pole: a cap below the projection is refused, nothing declared, numbers printed.
        rc, f = ro.declare_budget_or_refuse(sid, 800_000, 10, cwd=str(work))
        _check("V-ROLLBUDGET-REFUSE", rc == 3 and f["feasible"] is False and f["projected"] and
               not (state / f"session-budget-{sid}.json").exists(), f"rc={rc} projected={f.get('projected')}")

        # Green pole: a covering cap declares target 75%, warn 90%, and records the feasibility.
        stop = 4_000_000
        rc, f = ro.declare_budget_or_refuse(sid, stop, 10, cwd=str(work))
        p = state / f"session-budget-{sid}.json"
        rec = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        _check("V-ROLLBUDGET-DECLARE", rc == 0 and rec.get("stop") == stop and rec.get("target") == 3_000_000
               and rec.get("warn") == 3_600_000 and (rec.get("feasibility") or {}).get("feasible") is True,
               f"rc={rc} rec_stop={rec.get('stop')} target={rec.get('target')} warn={rec.get('warn')}")

        # No call count -> unprojectable -> refused.
        rc, f = ro.declare_budget_or_refuse(sid, stop, None, cwd=str(work))
        _check("V-ROLLBUDGET-NO-CALLS", rc == 3, f"rc={rc}")

        # The flags exist on the certify CLI and certify's own verdict stays first: no capsule -> rc 4,
        # and no budget is declared for an uncertified session.
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg), GSD_LONG_RUN_STATE_DIR=str(state))
        r = subprocess.run([sys.executable, str(REPO / "tools" / "rollover.py"), "certify", "--from", "nope",
                            "--claimant", "claimant-2", "--budget-stop", "9000000", "--calls-estimate", "5"],
                           env=env, capture_output=True, text=True, timeout=60, cwd=work)
        _check("V-ROLLBUDGET-CLI-NOT-CERTIFIED", r.returncode == 4
               and not (state / "session-budget-claimant-2.json").exists(),
               f"rc={r.returncode} out={r.stdout.strip()[:100]} err={r.stderr.strip()[:100]}")
    print(f"ROLLBUDGET_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
