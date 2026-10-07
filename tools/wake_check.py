"""Zero-model wake check. Carried by the existing PP-Vault-Summarize task (vault_summarize.py --check).

Runs the floor regression gate (pure Python, chars-only, never --probe) and decides WAKE or DORMANT.
It never invokes a model: every subprocess goes through run_gate(), which refuses a model-shaped argv,
and the report carries model_calls counted there (always 0 or the evaluator raised).
Gate exit 0 -> DORMANT; 1 (MATERIAL_RISE) -> WAKE; 2 (UNMEASURABLE) -> WAKE reason UNKNOWN (never green).
Override the gate for fixtures with env PP_WAKE_GATE_CMD (JSON list).
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLAG = ROOT / "vault" / "programs" / "cognitive-economy" / "gen2" / "WAKE_FLAG.json"
FORBIDDEN = ("--probe", "claude", "anthropic")
DEFAULT_PROJECT_DIR = Path.home() / ".claude" / "projects" / "C--Users-User--claude-skills-claude-power-pack"


def default_gate_cmd() -> list[str]:
    return [sys.executable, str(ROOT / "tools" / "floor_regression_gate.py"), "--check",
            "--reference", str(ROOT / "vault/programs/incremental-cognition/floor/reference.json"),
            "--project-dir", str(DEFAULT_PROJECT_DIR), "--chars-only", "--admit-cwd"]


def run_gate(argv: list[str], counter: dict) -> int:
    if any(a == "--probe" or Path(a).name.lower().startswith(FORBIDDEN) for a in argv):
        counter["model_calls"] += 1
        raise RuntimeError("wake check refuses a model-shaped argv")
    return subprocess.run(argv, capture_output=True, text=True, timeout=120).returncode


def evaluate(flag: Path | None = None) -> dict:
    flag = Path(os.environ.get("PP_WAKE_FLAG") or flag or FLAG)
    counter = {"model_calls": 0}
    env = os.environ.get("PP_WAKE_GATE_CMD")
    argv = json.loads(env) if env else default_gate_cmd()
    code = run_gate(argv, counter)
    wake = code != 0
    reason = {0: "DORMANT", 1: "MATERIAL_RISE"}.get(code, "UNKNOWN_GATE_EXIT_%s" % code)
    rep = {"wake": wake, "reason": reason, "gate_exit": code, "model_calls": counter["model_calls"],
           "at": datetime.now(timezone.utc).isoformat()}
    if wake:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    return rep


RECEIPTS = FLAG.parent / "wake_receipts"


def _goal_log_module():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from modules.gsd_x.goal import log as gl
    return gl


def _receipt(rdir: Path, rep: dict) -> dict:
    rdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = rdir / ("wake-%s-%s.json" % (stamp, rep["outcome"]))
    rep["receipt"] = str(path)
    path.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    return rep


def consume(goal, flag: Path | None = None, receipts: Path | None = None,
            actor: str = "wake_check") -> dict:
    """WAKE_FLAG consumer: flag -> one `wake` event on the bound goal's log (gsd_x GoalLog) -> receipt.

    Absent flag: NO_FLAG, no receipt, goal untouched. Flag or goal log unreadable: REFUSED receipt,
    goal untouched. A flag whose sha256 is already on the log is DUPLICATE, never appended twice.
    A consumed flag is renamed aside so the next producer run starts from absence.
    """
    gl = _goal_log_module()
    flag = Path(os.environ.get("PP_WAKE_FLAG") or flag or FLAG)
    rdir = Path(os.environ.get("PP_WAKE_RECEIPTS") or receipts or RECEIPTS)
    base = {"goal": "%s/%s" % (goal.repo, goal.goal_id), "flag": str(flag),
            "at": datetime.now(timezone.utc).isoformat()}
    if not flag.is_file():
        return {**base, "outcome": "NO_FLAG", "moved": False}
    try:
        raw = flag.read_bytes()
        rep = json.loads(raw.decode("utf-8"))
        if not isinstance(rep, dict) or rep.get("wake") is not True:
            raise ValueError("flag is not a wake report")
        events = goal.read()
    except (OSError, ValueError, gl.GoalLogError) as exc:
        return _receipt(rdir, {**base, "outcome": "REFUSED", "moved": False,
                               "cause": "%s: %s" % (type(exc).__name__, exc)})
    digest = hashlib.sha256(raw).hexdigest()
    out = {**base, "flag_sha256": digest, "reason": rep.get("reason")}
    if any(e.type == "wake" and e.data.get("flag_sha256") == digest for e in events):
        out.update(outcome="DUPLICATE", moved=False)
    else:
        data = {"reason": rep.get("reason"), "gate_exit": rep.get("gate_exit"),
                "flag_at": rep.get("at"), "flag_sha256": digest}
        try:
            ev = goal.append(len(events) + 1, "wake", data, actor)
        except gl.GoalLogError as exc:
            return _receipt(rdir, {**out, "outcome": "REFUSED", "moved": False,
                                   "cause": "%s: %s" % (type(exc).__name__, exc)})
        out.update(outcome="MOVED", moved=True, seq=ev.seq, event_digest=ev.digest)
    try:
        flag.replace(flag.with_name(flag.stem + ".consumed.json"))
    except OSError as exc:
        out["flag_not_moved"] = str(exc)
    return _receipt(rdir, out)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--consume":
        r = consume(_goal_log_module().GoalLog(sys.argv[2], sys.argv[3]))
        print("WAKE_CONSUME " + json.dumps(r))
        sys.exit(1 if r["outcome"] == "REFUSED" else 0)
    r = evaluate()
    print("WAKE_CHECK " + json.dumps(r))
    sys.exit(0)