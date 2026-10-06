"""Zero-model wake check. Carried by the existing PP-Vault-Summarize task (vault_summarize.py --check).

Runs the floor regression gate (pure Python, chars-only, never --probe) and decides WAKE or DORMANT.
It never invokes a model: every subprocess goes through run_gate(), which refuses a model-shaped argv,
and the report carries model_calls counted there (always 0 or the evaluator raised).
Gate exit 0 -> DORMANT; 1 (MATERIAL_RISE) -> WAKE; 2 (UNMEASURABLE) -> WAKE reason UNKNOWN (never green).
Override the gate for fixtures with env PP_WAKE_GATE_CMD (JSON list).
"""
from __future__ import annotations
import json, os, subprocess, sys
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


if __name__ == "__main__":
    r = evaluate()
    print("WAKE_CHECK " + json.dumps(r))
    sys.exit(0)