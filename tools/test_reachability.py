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
    return td


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
