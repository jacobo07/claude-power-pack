#!/usr/bin/env python3
"""V-gates for the deterministic gate provider and tree identity (C6).

Driven against a REAL git repository with REAL subprocesses: a provider tested
only against fakes proves the fake.

    python tools/test_gsd_x_goal_gate_provider.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gsd_x.goal import epoch as ep                      # noqa: E402
from modules.gsd_x.goal import git_state as gs                  # noqa: E402
from modules.gsd_x.goal.providers.gate import GateProvider      # noqa: E402

GIT = r"C:\Program Files\Git\cmd\git.exe"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def make_repo() -> Path:
    d = Path(tempfile.mkdtemp(prefix="gsdx_gate_repo_"))
    subprocess.run([GIT, "init", "-q", str(d)], check=True, env=ENV)
    (d / "gate_ok.py").write_text("print('12 passed')\n", encoding="utf-8")
    (d / "gate_bad.py").write_text("import sys\nprint('1 failed')\nsys.exit(1)\n",
                                   encoding="utf-8")
    (d / "gate_slow.py").write_text("import time\ntime.sleep(120)\n", encoding="utf-8")
    subprocess.run([GIT, "-C", str(d), "add", "."], check=True, env=ENV)
    subprocess.run([GIT, "-C", str(d), "commit", "-qm", "gates"], check=True, env=ENV)
    return d


def wait_ended(prov, handle, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        obs = prov.observe(handle)
        if obs.state == ep.OBS_ENDED:
            return obs
        time.sleep(0.05)
    return prov.observe(handle)


def spec_for(root: Path, gate_file: str, cls: str, token: str, eid: str):
    return {"epoch_id": eid, "revision": "rev1", "root": str(root),
            "identity": {"run_token": token, "epoch_id": eid},
            "scope_paths": ["."],
            "gate": {"id": gate_file, "command": [sys.executable, gate_file],
                     "class": cls, "files": [gate_file]}}


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    repo = make_repo()
    runs = Path(tempfile.mkdtemp(prefix="gsdx_gate_runs_"))
    prov = GateProvider(runs, wall_bound_s=30)
    ep.check_provider(prov)

    # --- tree identity ---------------------------------------------------------
    clean = gs.tree_id(repo, ["."])
    check("V-GATE-TREE-CLEAN", clean.startswith("git:"),
          f"a clean scope is named by its commit tree ({clean[:16]}...)", clean)
    (repo / "gate_ok.py").write_text("print('12 passed')\n# edited\n", encoding="utf-8")
    dirty = gs.tree_id(repo, ["."])
    check("V-GATE-TREE-DIRTY", dirty.startswith("work:") and dirty != clean,
          "an uncommitted scope says so rather than borrowing the commit's name", dirty)
    subprocess.run([GIT, "-C", str(repo), "checkout", "--", "gate_ok.py"], check=True, env=ENV)
    check("V-GATE-TREE-UNKNOWN",
          gs.tree_id(Path(tempfile.mkdtemp(prefix="gsdx_norepo_"))).startswith("unknown:"),
          "a tree we could not read is 'unknown:', never an empty string that matches",
          "a non-repo produced a usable tree id")

    # --- pin --------------------------------------------------------------------
    pin1 = gs.file_pin(repo, ["gate_ok.py"])
    (repo / "gate_ok.py").write_text("print('12 passed')  # changed\n", encoding="utf-8")
    check("V-GATE-PIN-MOVES", gs.file_pin(repo, ["gate_ok.py"]) != pin1,
          "editing the gate changes its pin", "the pin did not move")
    subprocess.run([GIT, "-C", str(repo), "checkout", "--", "gate_ok.py"], check=True, env=ENV)
    try:
        gs.file_pin(repo, ["missing.py"])
        bad("V-GATE-PIN-MISSING", "a pin was produced for a file that does not exist")
    except FileNotFoundError:
        ok("V-GATE-PIN-MISSING", "pinning a missing gate file refused")

    # --- a gate that passes -------------------------------------------------------
    s_ok = spec_for(repo, "gate_ok.py", "unit", "tok-ok", "ep-ok")
    h = prov.dispatch(s_ok)
    obs = wait_ended(prov, h)
    check("V-GATE-OBSERVE-ENDED", obs.state == ep.OBS_ENDED and obs.outcome == ep.COMPLETED,
          f"a passing gate ends COMPLETED ({obs.detail})", f"{obs}")
    r = prov.harvest(h, s_ok)
    v = r.verdicts[0] if r.verdicts else {}
    check("V-GATE-VERDICT-FIELDS",
          v.get("exit_status") == 0 and v.get("tree_hash", "").startswith("git:")
          and v.get("revision") == "rev1" and v.get("gate_class") == "unit"
          and v.get("gate_pin") and "passed" in v.get("observed", ""),
          "the verdict carries exit, tree, revision, class, pin and what it observed",
          f"verdict={v}")
    check("V-GATE-NO-FAILURE-ON-PASS", not r.failures,
          "a passing gate records no failure", f"failures={r.failures}")

    # --- a gate that fails ----------------------------------------------------------
    s_bad = spec_for(repo, "gate_bad.py", "unit", "tok-bad", "ep-bad")
    h2 = prov.dispatch(s_bad)
    obs2 = wait_ended(prov, h2)
    r2 = prov.harvest(h2, s_bad)
    check("V-GATE-FAILING-IS-EVIDENCE",
          obs2.outcome == ep.FAILED and r2.verdicts[0]["exit_status"] == 1
          and r2.failures and r2.failures[0]["signature"].startswith("gate-exit:"),
          "a failing gate is a verdict AND a failure with a signature",
          f"obs={obs2} verdicts={r2.verdicts} failures={r2.failures}")

    # --- refusals -------------------------------------------------------------------
    for gate_spec, name, why in (
            ({"id": "x", "command": [], "class": "unit", "files": ["gate_ok.py"]},
             "V-GATE-NEEDS-COMMAND", "a gate epoch with no command refused"),
            # These two carry a RUNNABLE command on purpose: if the refusal
            # under test were removed, the dispatch must get far enough to be
            # judged by the suite rather than dying on a missing executable --
            # which reports as a crashed mutant and proves nothing.
            ({"id": "x", "command": [sys.executable, "gate_ok.py"], "class": "smells-live",
              "files": ["gate_ok.py"]},
             "V-GATE-CLASS-DECLARED", "an unknown gate class refused, never inferred"),
            ({"id": "x", "command": [sys.executable, "gate_ok.py"], "class": "in_game",
              "files": []},
             "V-GATE-FILES-PINNED", "a gate that names no files of its own refused")):
        try:
            prov.dispatch({**spec_for(repo, "gate_ok.py", "unit", "t", "e"),
                           "gate": gate_spec})
            bad(name, "accepted")
        except ep.EpochError:
            ok(name, why)

    # --- cancellation and the bound ----------------------------------------------------
    s_slow = spec_for(repo, "gate_slow.py", "unit", "tok-slow", "ep-slow")
    h3 = prov.dispatch(s_slow)
    check("V-GATE-RUNNING", prov.observe(h3).state == ep.OBS_RUNNING,
          "a live gate reports running", "a live gate did not report running")
    prov.cancel(h3)
    time.sleep(1.0)
    alive = subprocess.run(["tasklist", "/FI", f"PID eq {h3['pid']}"],
                           capture_output=True, text=True).stdout
    check("V-GATE-CANCEL-KILLS", str(h3["pid"]) not in alive,
          f"cancel killed the process tree (pid {h3['pid']} gone)", alive[-200:])
    r3 = prov.harvest(h3, s_slow)
    check("V-GATE-CANCELLED-NO-VERDICT",
          not r3.verdicts and r3.failures
          and "no exit status" in r3.failures[0]["summary"],
          "a cancelled gate yields no verdict and says why, rather than inventing one",
          f"verdicts={r3.verdicts} failures={r3.failures}")

    # --- probe (crash between intent and dispatch) ---------------------------------------
    check("V-GATE-PROBE-NOTHING", prov.probe({"run_token": "never-started"}) is None,
          "a token that was never dispatched probes to None", "probe invented a run")
    found = prov.probe({"run_token": "tok-ok"})
    check("V-GATE-PROBE-FINDS", found is not None and found["pid"] == h["pid"],
          "a run started before a crash is found by its pre-minted token",
          f"probe={found}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GATE_PROVIDER_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
