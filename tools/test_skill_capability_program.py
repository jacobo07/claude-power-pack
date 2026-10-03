#!/usr/bin/env python
"""test_skill_capability_program.py -- the done-gate of PLAN-SKILL-CAPABILITY-PROGRAM.

    python tools/test_skill_capability_program.py --final

A thin wrapper over tools/test_cognitive_economy_program.py. That verifier's clauses read
their module globals at call time, so this file imports it, rebinds the globals to this
program (ledger, freeze pointer, handoff dir, pillars A-N, its own path for the recursion
refusal) and calls its main(). It never edits the CE file: a live mission
(m-fdefb0fca0c0) runs on it.

Ledger clauses L1-L9 and the CE selftest are inherited unchanged. This wrapper adds:

  R1  retained global state (--final only): every key declared under
      ledger.retained.settings must hold its declared value / subtree sha256 / absence in
      the live settings file. The program edits global settings (HR-001 boundary 3); this
      clause is how "restored, or retained on purpose" becomes checkable at closeout.
  V-SCP-REBIND  a positive control that the rebinding took: a ledger holding CE's A-T is
      refused by L1 here. Without it a failed rebind would silently verify CE's ledger.

Modes and exit codes are CE's: --final / --status / --pillar X / --selftest; 0 pass,
1 fail, 2 could not run.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_cognitive_economy_program as ce  # noqa: E402

PROGRAM_DIR = "vault/programs/skill-capability/"
ce.SELF_REL = "tools/test_skill_capability_program.py"
ce.LEDGER_REL = PROGRAM_DIR + "ledger.json"
ce.FROZEN_AT_REL = PROGRAM_DIR + "FROZEN_AT"
ce.HANDOFF_DIR = PROGRAM_DIR + "handoffs/"
ce.PILLARS = [chr(c) for c in range(ord("A"), ord("N") + 1)]
REPO = ce.REPO
_MISSING = object()


def subtree_sha256(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"))
                          .encode("utf-8")).hexdigest()


def _pointer(doc, pointer: str):
    """RFC 6901 lookup over dicts only; _MISSING when any segment is absent."""
    if not pointer.startswith("/"):
        return _MISSING
    cur = doc
    for raw in pointer[1:].split("/"):
        seg = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(cur, dict) or seg not in cur:
            return _MISSING
        cur = cur[seg]
    return cur


def check_retained(led: dict, path_override: Path | None = None) -> list:
    decl = (led.get("retained") or {}).get("settings")
    if not decl or not decl.get("file"):
        return ["R1 retained.settings is not declared: closeout cannot tell kept from leaked"]
    p = path_override or Path(decl["file"]).expanduser()
    try:
        doc = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"R1 settings file {decl['file']} unreadable: {exc}"]
    f = []
    for k in decl.get("keys") or []:
        ptr = k.get("pointer") or ""
        if not (k.get("why") or "").strip():
            f.append(f"R1 {ptr}: retained without a why")
        got = _pointer(doc, ptr)
        if k.get("absent") is True:
            if got is not _MISSING:
                f.append(f"R1 {ptr}: declared absent but present")
        elif got is _MISSING:
            f.append(f"R1 {ptr}: declared retained but absent")
        elif "sha256" in k:
            if subtree_sha256(got) != k["sha256"]:
                f.append(f"R1 {ptr}: subtree sha256 differs from the declared one")
        elif "value" in k:
            if got != k["value"]:
                f.append(f"R1 {ptr}: value differs from the declared one")
        else:
            f.append(f"R1 {ptr}: declares none of absent / sha256 / value")
    return f


STALE_CE_CONTROL = "V-CEP-REAL-HANDOFF"
HANDOFF_PROBE = "vault/plans/cognitive-economy-program-2026-10-03.md"
_ce_selftest = ce.selftest


def real_handoff_control(verbose=True) -> bool:
    """CE's V-CEP-REAL-HANDOFF pins 'frozen at 1cabd117 -> not landed', which went false
    the moment fa9ae2ed / 8b62b6ce touched the probe file again (CE defect, reported, not
    edited here). Same two poles, pinned to the file's history as read NOW: frozen at its
    newest commit -> nothing landed after; frozen at its first commit's parent -> landed."""
    shas = ce._git("log", "--format=%H", "HEAD", "--", HANDOFF_PROBE).stdout.split()
    parent = ce._git("rev-parse", f"{shas[-1]}^").stdout.strip() if shas else ""
    if not shas or not parent:
        print(f"  INCONCLUSIVE V-SCP-REAL-HANDOFF: no history for {HANDOFF_PROBE}")
        return False

    def at(sha):
        return type("R", (ce.Resolver,), {"frozen_sha": lambda self: sha})()
    before, after = at(shas[0]).handoff_landed(HANDOFF_PROBE), at(parent).handoff_landed(HANDOFF_PROBE)
    good = before is False and after is True
    if verbose or not good:
        print(f"  {'ok  ' if good else 'FAIL'} V-SCP-REAL-HANDOFF (frozen at newest {shas[0][:8]} -> "
              f"{before}, frozen before first {shas[-1][:8]} -> {after}; replaces {STALE_CE_CONTROL})")
    return good


def ce_selftest_with_live_handoff(verbose=True) -> bool:
    """CE's selftest with exactly its stale real-git line replaced by real_handoff_control.
    Every other CE line must pass, and the stale line must have been reached (the CE
    selftest ran to its end)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _ce_selftest(verbose=True)
    lines = buf.getvalue().splitlines()
    reached = any(STALE_CE_CONTROL in x for x in lines)
    other_fails = [x for x in lines if x.strip().startswith("FAIL") and STALE_CE_CONTROL not in x]
    for x in lines:
        if STALE_CE_CONTROL in x:
            continue
        if verbose or x in other_fails:
            print(x)
    if not reached:
        print(f"  FAIL CE selftest never reached {STALE_CE_CONTROL}: it did not run to its end")
    return reached and not other_fails and real_handoff_control(verbose)


ce.selftest = ce_selftest_with_live_handoff


def selftest(verbose=True) -> bool:
    ok = True

    def say(good, label):
        nonlocal ok
        if not good:
            ok = False
            print(f"  FAIL {label}")
        elif verbose:
            print(f"  ok   {label}")

    # Rebind control: CE's own pillar set must be refused here.
    led = json.loads((REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))
    ce_ids = [chr(c) for c in range(ord("A"), ord("T") + 1)]
    wide = copy.deepcopy(led)
    wide["frozen"]["pillars"] = [{"id": i, "predicted": "MERGED_INTO_EXISTING_OWNER", "owner": []}
                                 for i in ce_ids]
    wide["state"] = {i: {"terminal": None} for i in ce_ids}
    got = ce.check_ledger(wide, ce.FakeResolver(wide["frozen"]), final=False, run_gates=False)
    say(ce.PILLARS == [chr(c) for c in range(ord("A"), ord("N") + 1)]
        and any(x.startswith("L1") for x in got),
        "V-SCP-REBIND (pillars A-N; a CE A-T ledger is refused by L1)")

    settings = {"skillOverrides": {"a": "name-only", "b": "name-only"},
                "env": {"CLAUDE_DOCTRINE_CARDS": "deny"}, "hooks": {}}
    clean = {"retained": {"settings": {"file": "unused", "keys": [
        {"pointer": "/skillOverrides", "sha256": subtree_sha256(settings["skillOverrides"]), "why": "C6"},
        {"pointer": "/env/CLAUDE_DOCTRINE_CARDS", "value": "deny", "why": "C4b"},
        {"pointer": "/env/GONE", "absent": True, "why": "restored"}]}}}

    with tempfile.TemporaryDirectory() as td:
        sp = Path(td) / "settings.json"

        def run(led_, doc=settings, raw=None):
            sp.write_text(raw if raw is not None else json.dumps(doc), encoding="utf-8")
            return check_retained(led_, sp)

        say(not run(clean), "V-SCP-RETAINED-CLEAN (green)")

        def key(i, **kw):
            led_ = copy.deepcopy(clean)
            led_["retained"]["settings"]["keys"][i].update(kw)
            return led_

        def doc_with(fn):
            d = copy.deepcopy(settings)
            fn(d)
            return d

        mutants = {
            "override-added": (clean, doc_with(lambda d: d["skillOverrides"].__setitem__("c", "off"))),
            "value-changed": (clean, doc_with(lambda d: d["env"].__setitem__("CLAUDE_DOCTRINE_CARDS", "ledger"))),
            "retained-key-removed": (clean, doc_with(lambda d: d.pop("skillOverrides"))),
            "restored-key-leaked": (clean, doc_with(lambda d: d["env"].__setitem__("GONE", "1"))),
            "no-why": (key(1, why=" "), settings),
            "no-expectation": ({"retained": {"settings": {"file": "x", "keys": [
                {"pointer": "/hooks", "why": "w"}]}}}, settings),
            "undeclared": ({"retained": {}}, settings),
        }
        for name, (led_, doc) in mutants.items():
            say(any(x.startswith("R1") for x in run(led_, doc)), f"V-SCP-MUT-{name} killed by R1")
        say(any(x.startswith("R1") for x in run(clean, raw="{not json")),
            "V-SCP-MUT-unreadable-settings killed by R1")
    return ok


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        own = selftest()
        rc = ce.main(["--selftest"])
        good = own and rc == 0
        print(f"SCP_SELFTEST={'PASS' if good else 'FAIL'}")
        return 0 if good else 1
    if "--final" in argv:
        fails = []
        if not selftest(verbose=False):
            fails.append("S1 wrapper selftest failed")
        rc = ce.main(["--final"])
        if rc == 2:
            print("SCP_VERDICT=COULD_NOT_RUN")
            return 2
        if rc != 0:
            fails.append(f"CE clauses failed (rc {rc})")
        try:
            led = json.loads((REPO / ce.LEDGER_REL).read_text(encoding="utf-8"))
            fails += check_retained(led)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"SCP_VERDICT=COULD_NOT_RUN ledger unreadable: {exc}")
            return 2
        for x in fails:
            print("  FAIL", x)
        print(f"SCP_VERDICT={'PASS' if not fails else 'FAIL'} failures={len(fails)}")
        return 0 if not fails else 1
    return ce.main(argv)


if __name__ == "__main__":
    sys.exit(main())
