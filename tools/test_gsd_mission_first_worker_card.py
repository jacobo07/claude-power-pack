#!/usr/bin/env python
"""V-FWC-* gates: epoch 1 of a newly armed mission carries its Owner decisions (Phase 4.1, Owner D5 item 8).

The gap: the rehydration card was rendered only at a relay, between epochs. A mission armed, then given an
Owner decision while PREPARED, launched its first worker with no card at all, so the decision never reached it.

Hermetic, like test_gsd_mission_chain.py: state goes to a temp dir BEFORE import, the launch is a stub runner
(no claude process), memory is read from a stub. Never the live mission store.

Mutation control (V-FWC-MUTATION-GOES-RED): a copy of the REAL gsd_mission.py with the first-launch render
guard removed is loaded under another name; the very same predicate that is green on the real module must be
red on that copy. GSD_MISSION_DRILL_DIR is honoured like the sibling gates.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

TMP = tempfile.mkdtemp(prefix="gsd-mission-fwc-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
import gsd_mission as gm  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
NOW = 1_800_000_000.0
D1 = "FWC-DECISION-ONE use the narrow detector"
D2 = "FWC-DECISION-TWO record shared_service as OPEN"
MEM = lambda: {"available_mb": 10_000_000, "source": "test"}  # noqa: E731

_calls: list = []
_seq = [0]


def _runner(argv, cwd):
    _calls.append(list(argv))
    return SimpleNamespace(stdout=f"backgrounded · c0ffee{len(_calls):02x} · {argv[3]}", stderr="", returncode=0)


def _system_prompt(argv):
    """The value of --append-system-prompt in a launch argument list, or None."""
    return argv[argv.index("--append-system-prompt") + 1] if "--append-system-prompt" in argv else None


def _unique(module, prefix):
    _seq[0] += 1
    return f"{prefix}-{module.__name__}-{_seq[0]}"


def first_launch_argv(module, *, decisions=(D1, D2), with_decisions=True):
    """Arm a mission (no launch), deliver the decisions while PREPARED, launch epoch 1; return its argv."""
    mid = _unique(module, "m-fwc")
    module.arm(TMP, f"/gsd-autonomous --ws {mid}", launch=False, now=NOW, mission_id=mid)
    if with_decisions:
        for i, text in enumerate(decisions, 1):
            module.deliver_decision(mid, text, decision_id=f"D{i}", wake=False, now=NOW)
    n = len(_calls)
    res = module.launch_worker(mid, expect_epoch=0, expect_state=module.PREPARED, reason="armed",
                               runner=_runner, now=NOW, mem_reader=MEM)
    assert res.get("ok"), res
    assert len(_calls) == n + 1, "the launch stub was not called exactly once"
    return mid, _calls[-1]


def carries_all_decisions(argv, decisions=(D1, D2)):
    sp = _system_prompt(argv)
    return sp is not None and all(d in sp for d in decisions)


def _load_mutant():
    """The real gsd_mission.py with the first-launch render guard turned off, imported as gsd_mission_mutant."""
    src = (TOOLS / "gsd_mission.py").read_text(encoding="utf-8")
    needle = 'first_worker_decisions = expect_epoch == 0 and bool(rec.get("directives"))'
    assert src.count(needle) == 1, "mutation anchor not found exactly once: the guard moved, update the control"
    mut_dir = Path(TMP) / "mutant"
    mut_dir.mkdir(exist_ok=True)
    (mut_dir / "gsd_mission_mutant.py").write_text(src.replace(needle, "first_worker_decisions = False"),
                                                    encoding="utf-8")
    spec = importlib.util.spec_from_file_location("gsd_mission_mutant", mut_dir / "gsd_mission_mutant.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gsd_mission_mutant"] = mod
    spec.loader.exec_module(mod)
    mod.progress_fingerprint = lambda work_dir: None
    return mod


# --------------------------------------------------------------------------- pytest cases
def test_epoch_one_launch_argument_carries_every_decision():
    mid, argv = first_launch_argv(gm)
    assert carries_all_decisions(argv), _system_prompt(argv)
    sp = _system_prompt(argv)
    assert f"mission {mid}" in sp and "worker epoch 1" in sp


def test_a_mission_without_decisions_keeps_its_old_first_launch():
    """Control: the guard fires on decisions, not on every first launch (no legacy argv change)."""
    _, argv = first_launch_argv(gm, with_decisions=False)
    assert _system_prompt(argv) is None


def test_relay_still_renders_the_card_and_does_not_duplicate_it():
    mid, _ = first_launch_argv(gm)
    cur = gm.load(mid)
    assert cur["epoch"] == 1 and cur["state"] == gm.LAUNCHING
    gm.transition(mid, expect_epoch=1, expect_state=gm.LAUNCHING, event="t_running", now=NOW, state=gm.RUNNING)
    cur = gm.load(mid)
    res = gm.launch_worker(mid, expect_epoch=cur["epoch"], expect_state=cur["state"], reason="relay",
                           runner=_runner, now=NOW, note="predecessor note FWC-NOTE", mem_reader=MEM)
    assert res.get("ok"), res
    sp = _system_prompt(_calls[-1])
    assert "worker epoch 2" in sp and "FWC-NOTE" in sp
    assert sp.count("DECISION D1:") == 1 and sp.count("DECISION D2:") == 1, "card duplicated its decisions"
    assert carries_all_decisions(_calls[-1])


def test_mutation_goes_red_when_the_first_launch_render_is_disabled():
    mut = _load_mutant()
    assert mut.__name__ == "gsd_mission_mutant" and mut is not gm
    # Same predicate as test 1: green on the real module, red on the mutant.
    _, real_argv = first_launch_argv(gm)
    _, mut_argv = first_launch_argv(mut)
    assert carries_all_decisions(real_argv)
    assert not carries_all_decisions(mut_argv), "the control is blind: the mutant still carried the decisions"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
