"""PP Self-Eval CLI (spec vault/specs/pp-self-eval.md).

    python tools/pp_eval.py night [--dry-run]    one automatic night (what the scheduler runs)
    python tools/pp_eval.py harvest [--max N]    mine + validate tasks now (no model calls)
    python tools/pp_eval.py report               regenerate and print REPORT.md
    python tools/pp_eval.py status               bank, last night, verdicts, quota
    python tools/pp_eval.py install [--time HH:MM] | uninstall    the nightly scheduled task
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

from modules.pp_eval import harvest, nightly  # noqa: E402
from modules.pp_eval.common import state_dir  # noqa: E402

TASK_NAME = "PP-SelfEval"


def cmd_night(a) -> int:
    log = open(state_dir() / "night.log", "a", encoding="utf-8")

    def say(*parts):
        print(*parts, file=log, flush=True)

    night = nightly.run_night(dry_run=a.dry_run, log=say)
    say(json.dumps(night))
    print(json.dumps(night, indent=1))
    return 0


def cmd_harvest(a) -> int:
    cfg = nightly.config()
    res = harvest.harvest([Path(r) for r in cfg["repos"]], max_new=a.max)
    print(json.dumps(res))
    return 0


def cmd_report(_a) -> int:
    print(nightly.write_report().read_text(encoding="utf-8"))
    return 0


def cmd_status(_a) -> int:
    bank = harvest.load_bank()
    nights = nightly._read_jsonl("nights.jsonl")
    print(json.dumps({"bank_tasks": len(bank["tasks"]), "rejected": len(bank["rejected"]),
                      "last_night": nights[-1] if nights else None,
                      "verdicts": {k: v["verdict"] for k, v in nightly._load("verdicts.json", {}).items()},
                      "quota": nightly._load("quota.json", {}), "state": str(state_dir())}, indent=1))
    return 0


def cmd_install(a) -> int:
    slash = chr(47)
    # hidden_launch.vbs passes its arguments through verbatim and is unsafe with embedded
    # quotes, so every path here must be space-free; refuse rather than build a broken task.
    parts = [str(PP / "tools" / "hidden_launch.vbs"), sys.executable, str(PP / "tools" / "pp_eval.py")]
    if any(" " in p for p in parts):
        print(f"refusing: a path contains a space, the launcher cannot carry it: {parts}")
        return 2
    action = f"wscript.exe {slash}{slash}B {slash}{slash}Nologo {' '.join(parts)} night"
    if len(action) > 261:
        print(f"refusing: /TR is limited to 261 characters, this one is {len(action)}")
        return 2
    r = subprocess.run(["schtasks", "/Create", "/TN", TASK_NAME, "/TR", action, "/SC", "DAILY",
                        "/ST", a.time, "/F"], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    q = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST"], capture_output=True, text=True)
    print(q.stdout.strip())
    return r.returncode


def cmd_uninstall(_a) -> int:
    r = subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PP Self-Eval")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("night")
    n.add_argument("--dry-run", action="store_true")
    h = sub.add_parser("harvest")
    h.add_argument("--max", type=int, default=20)
    sub.add_parser("report")
    sub.add_parser("status")
    i = sub.add_parser("install")
    i.add_argument("--time", default="03:30")
    sub.add_parser("uninstall")
    a = ap.parse_args(argv)
    return {"night": cmd_night, "harvest": cmd_harvest, "report": cmd_report, "status": cmd_status,
            "install": cmd_install, "uninstall": cmd_uninstall}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
