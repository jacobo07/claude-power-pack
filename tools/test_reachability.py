#!/usr/bin/env python3
"""V-gates for the Reachability Ledger (modules/liveness/reachability.py).

The gate under test exists to prove a module is invoked from a live surface. A gate
that cannot be shown to REFUSE proves nothing, so every positive assertion here is
paired with a negative one on a synthetic repo built for the purpose.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.liveness import reachability as R  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"[OK] {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"[FAIL] {gate}: {diag}")


def _mk_repo(td: Path) -> Path:
    """A synthetic PP: one live hook, one wired module, one corpse, one plugin loader."""
    (td / "hooks").mkdir(parents=True)
    (td / "modules" / "wired").mkdir(parents=True)
    (td / "modules" / "dead").mkdir(parents=True)
    (td / "modules" / "plug" / "kids").mkdir(parents=True)

    # A .js file merely SITTING in hooks/ invokes nothing; only what the dispatcher's
    # own registries name is live. Model that, or the synthetic repo tests a surface
    # production does not have (hooks/cascade_check_bash.js was the real corpse that
    # sealed the filter).
    (td / "hooks" / R._DISPATCHER_NAME).write_text(
        'const CHAIN_MAP = { start: ["./hub.js", "./plug.js"] };\n', encoding="utf-8"
    )

    # A live surface that reaches `wired.entry` -- via a Python import embedded in JS,
    # exactly as session_start_hub.js does.
    (td / "hooks" / "hub.js").write_text(
        'const py = "from modules.wired.entry import go\\n";\n', encoding="utf-8"
    )
    (td / "modules" / "wired" / "__init__.py").write_text("", encoding="utf-8")
    (td / "modules" / "wired" / "entry.py").write_text(
        "from . import helper\n", encoding="utf-8"      # relative import carries on
    )
    (td / "modules" / "wired" / "helper.py").write_text("", encoding="utf-8")

    # A corpse: importable, tested, imported by NOTHING live.
    (td / "modules" / "dead" / "__init__.py").write_text("", encoding="utf-8")
    (td / "modules" / "dead" / "arbiter.py").write_text("", encoding="utf-8")

    # A plugin loader: its children are only ever named at runtime.
    (td / "modules" / "plug" / "__init__.py").write_text("", encoding="utf-8")
    (td / "modules" / "plug" / "kids" / "__init__.py").write_text(
        'from importlib import import_module\n'
        'import_module(f"modules.plug.kids.{name}")\n', encoding="utf-8"
    )
    (td / "modules" / "plug" / "kids" / "leaf.py").write_text("", encoding="utf-8")
    (td / "hooks" / "plug.js").write_text(
        '"from modules.plug.kids import loader"\n', encoding="utf-8"
    )

    # A scheduled-task chain: task -> .ps1 -> tool -> module. Reached by NO hook,
    # command or agent, which is exactly how cognitive_os/hibernate_runner ran every
    # five minutes in production while being reported dead.
    (td / "tools").mkdir(parents=True, exist_ok=True)
    (td / "modules" / "sched").mkdir(parents=True)
    (td / "modules" / "sched" / "__init__.py").write_text("", encoding="utf-8")
    (td / "modules" / "sched" / "runner.py").write_text("", encoding="utf-8")
    (td / "tools" / "task_entry.py").write_text(
        "from modules.sched import runner\n", encoding="utf-8"
    )
    (td / "tools" / "daemon.ps1").write_text(
        "$runner = Join-Path $pp 'tools\\task_entry.py'\n", encoding="utf-8"
    )
    return td


def _task_xml(script: Path, *, enabled: bool) -> str:
    """A minimal `schtasks /query /xml` blob naming one script."""
    flag = "true" if enabled else "false"
    return (
        "<?xml version='1.0'?>\n<!-- \\SYNTH-Task -->\n"
        '<Task version="1.2">\n'
        f"  <Settings><Enabled>{flag}</Enabled></Settings>\n"
        "  <Actions>\n    <Exec>\n"
        "      <Command>powershell.exe</Command>\n"
        f"      <Arguments>-NoProfile -File &quot;{script}&quot;</Arguments>\n"
        "    </Exec>\n  </Actions>\n</Task>\n"
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _mk_repo(Path(tmp))
        rows = {r["unit"]: r for r in R.scan(repo, registry={"modules": {}, "known_orphans": []})}

        # V-REACH-POLYGLOT: a Python import embedded in a JS string is a live reference.
        r = rows.get("wired/entry")
        if r and r["status"] == R.REACHABLE:
            _ok("V-REACH-POLYGLOT", f"wired/entry REACHABLE via {r['via']}")
        else:
            _fail("V-REACH-POLYGLOT", f"wired/entry -> {r['status'] if r else 'missing'}")

        # V-REACH-TRANSITIVE: reachability flows through a relative import.
        if rows.get("wired/helper", {}).get("status") == R.REACHABLE:
            _ok("V-REACH-TRANSITIVE", "wired/helper REACHABLE via wired/entry")
        else:
            _fail("V-REACH-TRANSITIVE", "relative import did not carry reachability")

        # V-REACH-REFUSES: the negative pole. Without this the gate proves nothing.
        if rows.get("dead/arbiter", {}).get("status") == R.ORPHAN:
            _ok("V-REACH-REFUSES", "dead/arbiter correctly ORPHAN (gate can refuse)")
        else:
            _fail("V-REACH-REFUSES", "an unreferenced module was NOT reported orphan")

        # V-REACH-DYNAMIC: a plugin loader's children are live, not corpses.
        if rows.get("plug/kids/leaf", {}).get("status") == R.REACHABLE:
            _ok("V-REACH-DYNAMIC", "plug/kids/leaf REACHABLE via the import_module loader")
        else:
            _fail("V-REACH-DYNAMIC", "dynamically-loaded module misreported as orphan")

        # V-REACH-GATE-FAILS: an undeclared corpse must FAIL the gate.
        offs = R.offenders(list(rows.values()), registry={"modules": {}, "known_orphans": []})
        if any(o["unit"] == "dead/arbiter" for o in offs):
            _ok("V-REACH-GATE-FAILS", f"{len(offs)} offender(s); dead/arbiter among them")
        else:
            _fail("V-REACH-GATE-FAILS", "gate passed a repo containing an undeclared corpse")

        # V-REACH-EXEMPTION: a DECLARED corpse is debt, not a failure -- and a malformed
        # class is not an exemption.
        ok_reg = {"modules": {"dead/arbiter": {"class": R.DEPRECATED}}, "known_orphans": []}
        good = R.offenders(R.scan(repo, registry=ok_reg), registry=ok_reg)

        bad_reg = {"modules": {"dead/arbiter": {"class": "LOL"}}, "known_orphans": []}
        bogus_offs = R.offenders(R.scan(repo, registry=bad_reg), registry=bad_reg)

        if (not any(o["unit"] == "dead/arbiter" for o in good)
                and any(o["unit"] == "dead/arbiter" for o in bogus_offs)):
            _ok("V-REACH-EXEMPTION", "valid class exempts; malformed class does NOT")
        else:
            _fail("V-REACH-EXEMPTION", "exemption handling is not honest")

        # --- the scheduled-task surface (sealed 2026-07-27) ---------------------
        daemon = repo / "tools" / "daemon.ps1"

        # V-REACH-TASK-XML: an ENABLED task's script is a seed; a DISABLED one is not.
        # Both poles, because a producer that cannot refuse would make every task-named
        # script permanently live and hide exactly the corpses this module hunts.
        on = R.scheduled_task_seeds(repo, xml=_task_xml(daemon, enabled=True))
        off = R.scheduled_task_seeds(repo, xml=_task_xml(daemon, enabled=False))
        if daemon.is_absolute() and daemon.drive:
            if [p.name for p in on] == ["daemon.ps1"] and off == []:
                _ok("V-REACH-TASK-XML", "enabled task seeds daemon.ps1; disabled seeds nothing")
            else:
                _fail("V-REACH-TASK-XML", f"enabled={[p.name for p in on]} disabled={off}")
        else:
            # Task Scheduler is a Windows surface; a drive-less path proves nothing here.
            if on == [] and off == []:
                _ok("V-REACH-TASK-XML", "non-Windows host: producer correctly yields nothing")
            else:
                _fail("V-REACH-TASK-XML", "non-Windows host produced task seeds")

        # V-REACH-TASK-FAILOPEN: an empty or unavailable query is silence, never a crash.
        if R.scheduled_task_seeds(repo, xml="") == []:
            _ok("V-REACH-TASK-FAILOPEN", "empty schtasks output yields no seeds")
        else:
            _fail("V-REACH-TASK-FAILOPEN", "empty query did not fail open")

        # V-REACH-TASK-CHAIN: the full path task -> .ps1 -> tool -> module. The .ps1 must
        # be seeded BEFORE tool discovery, or the trace stops at the shell script.
        real_producer = R.scheduled_task_seeds
        R.scheduled_task_seeds = lambda repo_root=None, **kw: [daemon]
        try:
            chained = {r["unit"]: r for r in
                       R.scan(repo, registry={"modules": {}, "known_orphans": []})}
        finally:
            R.scheduled_task_seeds = real_producer
        row = chained.get("sched/runner")
        if row and row["status"] == R.REACHABLE:
            _ok("V-REACH-TASK-CHAIN", f"sched/runner REACHABLE via {row['via']}")
        else:
            _fail("V-REACH-TASK-CHAIN",
                  f"task-driven module -> {row['status'] if row else 'missing'}")

        # V-REACH-TASK-NEGATIVE: without the task, that same module is a corpse. This is
        # what proves the flip above was caused by the task and not by something else.
        if rows.get("sched/runner", {}).get("status") == R.ORPHAN:
            _ok("V-REACH-TASK-NEGATIVE", "sched/runner ORPHAN when no task names it")
        else:
            _fail("V-REACH-TASK-NEGATIVE", "module was reachable without the task")

    # V-REACH-SELF: the real repo scans, and the arbiter this mission was built to
    # resurrect is visible in the denominator (whatever its status today).
    real = {r["unit"]: r for r in R.scan()}
    if "session_resilience/acceptance" in real and len(real) > 100:
        _ok("V-REACH-SELF", f"real repo: {len(real)} modules, acceptance arbiter in scope")
    else:
        _fail("V-REACH-SELF", "real-repo scan did not enumerate the recovery arbiter")

    total = _passes + _fails
    print(f"REACHABILITY_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
