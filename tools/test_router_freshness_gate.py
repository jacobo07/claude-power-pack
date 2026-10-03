"""V-gates for the router freshness gate.

The point of these gates is falsifiability. A gate that cannot fail is the defect
it was built to catch, so every check below constructs a state that MUST fail and
asserts that it does -- not only that the clean repo passes.
"""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.router_freshness_gate as gate  # noqa: E402

PASSES: list[str] = []
FAILS: list[str] = []


def _ok(name: str, evidence: str) -> None:
    PASSES.append(name)
    print(f"  PASS  {name}  {evidence}")


def _fail(name: str, diagnostic: str) -> None:
    FAILS.append(name)
    print(f"  FAIL  {name}  {diagnostic}")


class Scenario:
    """A throwaway ~/.claude tree: a repo root, a vault, and a derived router."""

    def __enter__(self) -> "Scenario":
        self.tmp = Path(tempfile.mkdtemp(prefix="rfg_"))
        self.claude = self.tmp / ".claude"
        self.repo = self.claude / "skills" / "claude-power-pack"
        (self.repo / "vault" / "knowledge_base").mkdir(parents=True)
        (self.claude / "knowledge_vault").mkdir(parents=True)
        self._saved = (gate.CLAUDE_DIR, gate.KNOWLEDGE_VAULT)
        gate.CLAUDE_DIR = self.claude
        gate.KNOWLEDGE_VAULT = self.claude / "knowledge_vault"
        self.router = gate.router_path(self.repo)
        self.router.parent.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, *exc: object) -> None:
        gate.CLAUDE_DIR, gate.KNOWLEDGE_VAULT = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_router(self, body: str) -> None:
        self.router.write_text(body, encoding="utf-8")

    def make_store(self, rel: str, n_ids: int) -> Path:
        """Write a file dense enough in distinct sealed ids to count as a store."""
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        ids = "\n".join(f"- T-SYNTHETIC-RULE-{i:04d}-001 body" for i in range(n_ids))
        p.write_text(f"# store\n{ids}\n", encoding="utf-8")
        return p

    def rel_to_router(self, target: Path) -> str:
        return os.path.relpath(target, self.router.parent).replace("\\", "/")

    def run(self) -> int:
        return gate.run(self.repo)


def _skill_repo(s: "Scenario", live_text: str) -> None:
    """Make s.repo a git repo that commits skills/x/SKILL.md, with a live copy under <tmp>/.claude/skills/x."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import skill_mirror_drift as smd  # noqa: PLC0415
    exe = smd.vgm._git_exe()
    skill = s.repo / "skills" / "x" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: x\n---\nbody\n", encoding="utf-8")
    live = s.claude / "skills" / "x" / "SKILL.md"
    live.parent.mkdir(parents=True)
    live.write_text(live_text, encoding="utf-8")
    for args in (["init", "-q"], ["add", "skills/x/SKILL.md"], ["commit", "-q", "-m", "x"]):
        subprocess.run([exe, "-C", str(s.repo), "-c", "user.name=gate", "-c", "user.email=gate@invalid",
                        "-c", "core.autocrlf=false", *args], check=True, capture_output=True, timeout=30)


def main() -> int:
    print("== V-RFG gates ==")

    # V-RFG-CLEAN -- the real repo, as repaired, passes. Behaviour unchanged (review WR-01): it still runs the
    # real router AND the host's real live skills tree. Its red is made attributable: the diagnostic names every
    # sub-check that failed, so a pre-existing router-layout failure (V-ROUTER-LINKS "router absent") and real
    # host drift (V-ROUTER-SKILL-DRIFT) read as what they are, never as one opaque "does not pass".
    _buf = io.StringIO()
    with contextlib.redirect_stdout(_buf):
        _rc = gate.run()
    _out = _buf.getvalue()
    print(_out, end="")
    if _rc == 0:
        _ok("V-RFG-CLEAN", "live repo exits 0")
    else:
        _why = [ln.split("  ")[0].split(" ")[0] + ": " + ln.split("FAIL", 1)[1].strip()[:140]
                for ln in _out.splitlines() if ln.startswith("V-ROUTER-") and " FAIL " in f" {ln} "]
        _fail("V-RFG-CLEAN", "live repo does not pass; failing sub-checks: " + ("; ".join(_why) or "none named"))

    # V-RFG-BROKEN-LINK -- an unresolvable pointer must fail.
    with Scenario() as s:
        s.write_router("- [gone](does_not_exist.md) - hook\n")
        if s.run() == 1:
            _ok("V-RFG-BROKEN-LINK", "unresolvable pointer exits 1")
        else:
            _fail("V-RFG-BROKEN-LINK", "broken link did not fail the gate")

    # V-RFG-INLINE -- a bullet with no pointer is stored knowledge, not an index.
    with Scenario() as s:
        s.write_router("- knowledge written straight into the router\n")
        if s.run() == 1:
            _ok("V-RFG-INLINE", "inline entry exits 1")
        else:
            _fail("V-RFG-INLINE", "inline entry did not fail the gate")

    # V-RFG-STORE-UNREACHABLE -- a store nobody points at must fail.
    with Scenario() as s:
        s.make_store("vault/knowledge_base/corpus.md", gate.DENSITY_STORE_MIN)
        s.write_router("")
        if s.run() == 1:
            _ok("V-RFG-STORE-UNREACHABLE", "unindexed store exits 1")
        else:
            _fail("V-RFG-STORE-UNREACHABLE", "unindexed store did not fail the gate")

    # V-RFG-STORE-REACHABLE -- pointing at it clears the same state.
    with Scenario() as s:
        store = s.make_store("vault/knowledge_base/corpus.md", gate.DENSITY_STORE_MIN)
        s.write_router(f"- [corpus]({s.rel_to_router(store)}) - hook\n")
        if s.run() == 0:
            _ok("V-RFG-STORE-REACHABLE", "indexed store exits 0")
        else:
            _fail("V-RFG-STORE-REACHABLE", "indexed store still fails")

    # V-RFG-DISCOVERED -- the store set is walked off disk, not listed.
    with Scenario() as s:
        s.write_router("")
        before = len(gate.discover_stores(s.repo))
        s.make_store("vault/knowledge_base/late_arrival.md", gate.DENSITY_STORE_MIN)
        after = len(gate.discover_stores(s.repo))
        if before == 0 and after == 1:
            _ok("V-RFG-DISCOVERED", "store appears without being declared")
        else:
            _fail("V-RFG-DISCOVERED", f"before={before} after={after}, expected 0 then 1")

    # V-RFG-BELOW-THRESHOLD -- a file that merely cites rules is not a store.
    with Scenario() as s:
        s.make_store("vault/knowledge_base/citing_doc.md", gate.DENSITY_STORE_MIN - 1)
        s.write_router("")
        if s.run() == 0:
            _ok("V-RFG-BELOW-THRESHOLD", "citing document is not enrolled")
        else:
            _fail("V-RFG-BELOW-THRESHOLD", "citing document wrongly enrolled as a store")

    # V-RFG-BUDGET -- an over-budget router is inline knowledge creeping back.
    with Scenario() as s:
        s.write_router("\n".join("- [x](MEMORY.md) h" for _ in range(gate.ROUTER_MAX_LINES + 1)))
        if s.run() == 1:
            _ok("V-RFG-BUDGET", f"over {gate.ROUTER_MAX_LINES} lines exits 1")
        else:
            _fail("V-RFG-BUDGET", "over-budget router did not fail the gate")

    # V-RFG-SKILL-DRIFT-GREEN -- a live copy identical to the committed skill passes.
    with Scenario() as s:
        _skill_repo(s, "---\nname: x\n---\nbody\n")
        verdict, lines = gate.skill_drift_check(s.repo)
        if verdict == "PASS":
            _ok("V-RFG-SKILL-DRIFT-GREEN", lines[0])
        else:
            _fail("V-RFG-SKILL-DRIFT-GREEN", f"{verdict} {lines}")

    # V-RFG-SKILL-DRIFT-RED -- one byte of drift fails the check and the gate run.
    with Scenario() as s:
        _skill_repo(s, "---\nname: x\n---\nbodz\n")
        verdict, lines = gate.skill_drift_check(s.repo)
        s.write_router("")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = s.run()
        out = buf.getvalue()
        if verdict == "FAIL" and rc == 1 and "V-ROUTER-SKILL-DRIFT FAIL" in out and "x: DRIFT" in out:
            _ok("V-RFG-SKILL-DRIFT-RED", "one-byte live drift: check FAIL, gate exits 1 naming x")
        else:
            _fail("V-RFG-SKILL-DRIFT-RED", f"verdict={verdict} rc={rc} out={out[:200]!r}")

    # V-RFG-SKILL-DRIFT-UNMEASURED -- no skills in the checkout is neither pass nor fail, and does not read the
    # real live tree (the Scenario live root is <tmp>/.claude/skills).
    with Scenario() as s:
        s.write_router("")
        verdict, lines = gate.skill_drift_check(s.repo)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = s.run()
        if verdict == "UNMEASURED" and rc == 0 and "V-ROUTER-SKILL-DRIFT UNMEASURED" in buf.getvalue():
            _ok("V-RFG-SKILL-DRIFT-UNMEASURED", "no skills/: UNMEASURED, printed, gate result unchanged")
        else:
            _fail("V-RFG-SKILL-DRIFT-UNMEASURED", f"verdict={verdict} rc={rc}")

    # V-RFG-SKILL-DRIFT-NO-LIVE -- a live root that is absent, or that holds none of the repo skills, compared
    # nothing: UNMEASURED, never PASS (review CR-01). Control: the same checkout against its identical copy passes.
    with Scenario() as s:
        _skill_repo(s, "---\nname: x\n---\nbody\n")
        v_abs, l_abs = gate.skill_drift_check(s.repo, s.tmp / "no-such-skills")
        empty = s.tmp / "empty-live"
        empty.mkdir()
        v_emp, l_emp = gate.skill_drift_check(s.repo, empty)
        v_ctl, _ = gate.skill_drift_check(s.repo)
    if v_abs == "UNMEASURED" and v_emp == "UNMEASURED" and v_ctl == "PASS":
        _ok("V-RFG-SKILL-DRIFT-NO-LIVE", f"absent root UNMEASURED ({l_abs[0]}); empty root UNMEASURED; "
                                         "identical-copy control PASS")
    else:
        _fail("V-RFG-SKILL-DRIFT-NO-LIVE", f"absent={v_abs} {l_abs[:1]}; empty={v_emp} {l_emp[:1]}; control={v_ctl}")

    # V-RFG-SKILL-DRIFT-GIT-FAILURE -- git missing: the router line is FAIL carrying the INCONCLUSIVE reason, never
    # PASS and never a traceback (review IN-03). The control is the same Scenario with git present: PASS.
    import skill_mirror_drift as smd  # noqa: PLC0415 -- _skill_repo put tools/ on sys.path
    with Scenario() as s:
        _skill_repo(s, "---\nname: x\n---\nbody\n")
        v_ctl, _ = gate.skill_drift_check(s.repo)
        _orig = smd.vgm._git_exe

        def _gone():
            raise FileNotFoundError("git executable not found (drill)")
        smd.vgm._git_exe = _gone
        try:
            v_g, l_g = gate.skill_drift_check(s.repo)
        except Exception as e:  # noqa: BLE001 -- the clause asserts that nothing escapes
            v_g, l_g = "RAISED", [f"{type(e).__name__}: {e}"]
        finally:
            smd.vgm._git_exe = _orig
    if v_ctl == "PASS" and v_g == "FAIL" and "INCONCLUSIVE: git not found" in l_g[0]:
        _ok("V-RFG-SKILL-DRIFT-GIT-FAILURE", f"git missing: {v_g} ({l_g[0][:60]}); git present control PASS")
    else:
        _fail("V-RFG-SKILL-DRIFT-GIT-FAILURE", f"control={v_ctl}; git missing -> {v_g} {l_g[:1]}")

    total = len(PASSES) + len(FAILS)
    print(f"ROUTER_GATE_TESTS={len(PASSES)}/{total}  threshold={total}/{total}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
