"""V-FINJ-* -- family baselines reach the prompt (spec 2026-09-24 slice S4).

The seam under test is `modules/gsd_x/cli.py::family_block`, called from `main()`,
which is the process `hooks/gsd_x_tier.js` spawns on every UserPromptSubmit.

Poles are the PREDECLARED prompts of tools/test_family_baselines.py (commit 247ffc0),
reused verbatim rather than written to make the injection look good. Every drill
mutates the LINK, not an end, and proves its mutation was reached before it scores.

Hermetic: HOME/USERPROFILE point at a temp dir for the whole run, so offer counters,
the consumption ledger and heartbeats never touch the real ~/.claude.

Run: python tools/test_family_injection.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
if _PP_ROOT not in sys.path:
    sys.path.insert(0, _PP_ROOT)

from modules.gsd_x import cli  # noqa: E402
from modules.tower import baselines as bl, families as fm, select as sel  # noqa: E402
from tools.test_family_baselines import PROMPTS  # noqa: E402

_PASS = 0
_FAIL = 0
NONE_PROMPT = "qué hora es"
CLI = os.path.join(_PP_ROOT, "modules", "gsd_x", "cli.py")
HOOK = os.path.join(_PP_ROOT, "hooks", "gsd_x_tier.js")


def check(gate: str, cond, evidence) -> None:
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-38s %s" % (gate, str(evidence)[:150]))
    else:
        _FAIL += 1
        print("  FAIL %-38s %s" % (gate, str(evidence)[:400]))


def header(fid: str) -> str:
    return "Family baseline %s/B%d " % (fid, bl.generations(fid)[-1])


def run_main(payload: dict) -> str:
    """cli.main() in-process, stdin/stdout swapped; returns what the model would read."""
    old_in, old_out = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = io.StringIO(json.dumps(payload)), io.StringIO()
    try:
        cli.main()
        return sys.stdout.getvalue()
    finally:
        sys.stdin, sys.stdout = old_in, old_out


class Counting:
    """Wraps a replacement so a drill can prove the seam actually reached it."""
    def __init__(self, fn):
        self.fn, self.calls = fn, 0

    def __call__(self, *a, **k):
        self.calls += 1
        return self.fn(*a, **k)


def main() -> int:
    home = tempfile.mkdtemp(prefix="finj-home-")
    env = dict(os.environ, HOME=home, USERPROFILE=home, PYTHONIOENCODING="utf-8")
    env.pop(cli.FAMILY_SWITCH, None)
    # cli was imported above, BEFORE this swap. heartbeat.py resolves its path per
    # call (WR-07), and CLAUDE_STATE_DIR is pinned to the temp home for this process
    # AND the subprocesses so an inherited value cannot point either at the real one.
    saved_state = os.environ.get("CLAUDE_STATE_DIR")
    state_dir = os.path.join(home, ".claude", "state")
    env["CLAUDE_STATE_DIR"] = state_dir
    os.environ.update(HOME=home, USERPROFILE=home, CLAUDE_STATE_DIR=state_dir)
    os.environ.pop(cli.FAMILY_SWITCH, None)
    try:
        check("V-FINJ-HERMETIC-HOME", Path.home() == Path(home), Path.home())
        fams = sorted(f.id for f in fm.load_families())
        check("V-FINJ-POPULATION", fams == sorted(PROMPTS) and all(bl.active_entries(f) for f in fams),
              "4 families, each with an active generation: %s" % fams)

        # -- every family, both poles, and the text is the compiler's choice --------
        for fid, (inside, outside) in PROMPTS.items():
            got = cli.family_block(inside, {})
            s = sel.select_for_injection(bl.active_entries(fid))
            block = got.split(header(fid), 1)[-1].split("\n\nFamily baseline", 1)[0]
            shown = all(("- [%s] %s" % (e["id"], e["requirement"])) in block for e in s.injected)
            tail = block.split("Not shown", 1)[1] if "Not shown" in block else ""
            named = all(str(e["id"]) in tail for e in s.deferred) and bool(tail) == bool(s.deferred)
            check("V-FINJ-IN-%s" % fid, header(fid) in got and shown and named,
                  "%d shown, %d named as deferred" % (len(s.injected), len(s.deferred)))
            check("V-FINJ-OUT-%s" % fid, header(fid) not in cli.family_block(outside, {}),
                  "outside pole gets no %s block" % fid)
            sha = bl.generation_sha256(fid, bl.generations(fid)[-1])
            check("V-FINJ-STAMP-%s" % fid, ("sha256 %s" % sha[:12]) in got, sha[:12])

        check("V-FINJ-POSITIVE-CONTROL", cli.family_block(NONE_PROMPT, {}) == "",
              "a prompt of no family receives no baseline")

        # -- kill switch, with the same prompt as its own control ----------------------
        k_in = PROMPTS["kobiicraft_mode"][0]
        os.environ[cli.FAMILY_SWITCH] = "off"
        off = cli.family_block(k_in, {})
        del os.environ[cli.FAMILY_SWITCH]
        check("V-FINJ-KILL-SWITCH", off == "" and cli.family_block(k_in, {}) != "",
              "off -> nothing; unset -> injects")

        # -- per-session offer cap, per family --------------------------------------
        pl = {"session_id": "finj-cap"}
        seq = [bool(cli.family_block(k_in, pl)) for _ in range(cli.MAX_OFFERS + 1)]
        other = bool(cli.family_block(PROMPTS["wii_homebrew"][0], pl))
        check("V-FINJ-OFFER-CAP", seq == [True] * cli.MAX_OFFERS + [False] and other,
              "offers %s; another family still offered=%s" % (seq, other))

        ledger = Path(home) / ".claude" / "state" / "tower" / "consumption.jsonl"
        rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines()
                if '"kind": "family"' in x] if ledger.exists() else []
        want = sel.select_for_injection(bl.active_entries("kobiicraft_mode")).as_dict()
        krow = [r for r in rows if r.get("family") == "kobiicraft_mode"]
        check("V-FINJ-LEDGER", krow and krow[-1]["injected"] == want["injected"]
              and krow[-1]["judged_under"].startswith("kobiicraft_mode/B")
              and krow[-1]["generation_sha256"],
              "%d family rows in the TEMP ledger" % len(rows))

        # -- drills on the LINK, each proving it was reached --------------------------
        real_cls = fm.classify_prompt
        m1 = Counting(lambda *a, **k: [])
        fm.classify_prompt = m1
        try:
            dead = cli.family_block(k_in, {})
        finally:
            fm.classify_prompt = real_cls
        check("V-FINJ-DRILL-CLASSIFIER-LINK", m1.calls >= 1 and dead == ""
              and fm.classify_prompt is real_cls,
              "reached %d time(s); a blind classifier silences the block" % m1.calls)

        real_sel = sel.select_for_injection
        m2 = Counting(lambda entries, *a, **k: sel.Selection(injected=list(entries)))
        sel.select_for_injection = m2
        try:
            uncapped = cli.family_block(k_in, {})
        finally:
            sel.select_for_injection = real_sel
        capped = cli.family_block(k_in, {})
        check("V-FINJ-DRILL-COMPILER-LINK", m2.calls >= 1 and "Not shown" in capped
              and "Not shown" not in uncapped and len(uncapped) > len(capped),
              "reached %d time(s); bypassing the ceiling changes the text" % m2.calls)

        control = run_main({"prompt": k_in})
        real_fb = cli.family_block
        m3 = Counting(lambda *a, **k: "")
        cli.family_block = m3
        try:
            unwired = run_main({"prompt": k_in})
        finally:
            cli.family_block = real_fb
        check("V-FINJ-DRILL-MAIN-LINK", header("kobiicraft_mode") in control and m3.calls == 1
              and header("kobiicraft_mode") not in unwired and cli.family_block is real_fb,
              "main() reaches family_block; unwiring it removes the block")

        # -- WR-07: the in-process main() heartbeats landed in the TEMP home ----------
        # run_main() above called cli.main() twice in this process (the control and
        # the unwired drill); each records a gsd_x heartbeat. The subprocess runs
        # below are not counted: they never shared this process's import-time binding.
        hb_file = Path(home) / ".claude" / "state" / "gsd-x-heartbeat.json"
        try:
            judged = int(json.loads(hb_file.read_text(encoding="utf-8")).get("judgements", 0))
        except (OSError, ValueError):
            judged = 0
        check("V-FINJ-HEARTBEAT-HERMETIC", judged >= 2,
              "the in-process cli.main() heartbeats landed in the temp home "
              "(%d judgements), not the real ~/.claude/state" % judged)

        # -- the real process, and the real hook that spawns it ------------------------
        def spawn(argv, prompt):
            r = subprocess.run(argv, input=json.dumps({"prompt": prompt, "session_id": ""}),
                               capture_output=True, text=True, encoding="utf-8",
                               env=env, cwd=_PP_ROOT, timeout=60)
            return r.returncode, r.stdout
        rc_in, out_in = spawn([sys.executable, CLI], k_in)
        rc_no, out_no = spawn([sys.executable, CLI], NONE_PROMPT)
        check("V-FINJ-E2E-CLI", rc_in == 0 and rc_no == 0 and header("kobiicraft_mode") in out_in
              and "Family baseline" not in out_no, "rc=%s/%s" % (rc_in, rc_no))

        node = shutil.which("node")
        if not node:
            check("V-FINJ-E2E-HOOK", False, "node not on PATH: the hook plane was NOT exercised")
        else:
            rc_h, out_h = spawn([node, HOOK], k_in)
            check("V-FINJ-E2E-HOOK", rc_h == 0 and header("kobiicraft_mode") in out_h,
                  "rc=%s, hook stdout carries the block (%d chars)" % (rc_h, len(out_h)))
    finally:
        if saved_state is None:
            os.environ.pop("CLAUDE_STATE_DIR", None)
        else:
            os.environ["CLAUDE_STATE_DIR"] = saved_state
        shutil.rmtree(home, ignore_errors=True)

    total = _PASS + _FAIL
    print("FINJ_PASS=%d/%d  threshold=%d/%d" % (_PASS, total, total, total))
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
