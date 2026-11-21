"""test_bcap2_agsk.py -- CPP-AGSK-001 pilot gate (V-AGSK-*). Run: python3 tools/test_bcap2_agsk.py ; exit 0 iff all pass.

Pilot slice AGSK-C (constraint non-weakening): modules/sqi/floor_guard.py is driven from both poles -- every seeded
weakening move must be refused by its named rule, every clean twin must pass. Also: disposition-ledger integrity
(one row per upstream skill/command, closed vocabulary, owner path exists, pin matches NOTICE), routing recall/precision
for the new card, and a real-git CLI run (exit 0 clean / 1 violation / 2 cannot-run).
Scope honesty: only AGSK-C is implemented. Other dispositions are HYPOTHESIS rows; this gate does not close CPP-AGSK-001.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.sqi import floor_guard as fg  # noqa: E402
from modules.skill_router.intent_classifier import classify_intent  # noqa: E402
from modules.skill_router.skill_index import build_index  # noqa: E402

P = F = 0


def check(g, cond, detail=""):
    global P, F
    if cond:
        P += 1
        print(f"  [PASS] {g}: {detail}")
    else:
        F += 1
        print(f"  [FAIL] {g}: {detail}")


def mk(file, minus=(), plus=(), new=False, deleted=False):
    h = f"diff --git a/{file} b/{file}\n"
    h += f"--- {'/dev/null' if new else 'a/' + file}\n+++ {'/dev/null' if deleted else 'b/' + file}\n@@ -1 +1 @@\n"
    return h + "".join(f"-{x}\n" for x in minus) + "".join(f"+{x}\n" for x in plus)


def rules(diff):
    return sorted({f.rule for f in fg.analyze(diff)})


def test_poles():
    seeded = [
        ("silenced-checker", mk("src/a.py", ["x = f()"], ["x = f()  # noqa: E501"])),
        ("silenced-checker", mk("src/a.ts", ["call()"], ["// @ts-ignore", "call()"])),
        ("unfinished-work", mk("src/a.py", [], ["def g():", "    raise NotImplementedError"])),
        ("unfinished-work", mk("src/a.py", [], ["try:", "    x()", "except Exception: pass"])),
        ("test-made-easier", mk("tests/test_a.py", ["def test_x():"], ["@pytest.mark.skip", "def test_x():"])),
        ("test-made-easier", mk("tests/a.test.ts", ["it('x', f)"], ["it.skip('x', f)"])),
        ("assertion-removed", mk("tests/test_a.py", ["    self.assertEqual(f(), 2)", "    assert g()"], ["    g()"])),
        ("test-deleted", mk("tests/test_gone.py", ["assert 1"], [], deleted=True)),
        ("rule-removed", mk("CONSTRAINTS.md", ["- no-network: tests must not call out"], [])),
        ("threshold-loosened", mk("CONSTRAINTS.md", ["- coverage: at least 80 percent"], ["- coverage: at least 60 percent"])),
        ("threshold-loosened", mk("CONSTRAINTS.md", ["- latency: at most 200 ms"], ["- latency: at most 900 ms"])),
        ("new-exception", mk("CONSTRAINTS.md", [], ["| E1 | src/a.py | legacy | nobody | never |"])),
    ]
    for want, d in seeded:
        got = rules(d)
        check(f"V-AGSK-POLE-RED[{want}]", want in got, f"rules={got}")

    clean = [
        ("tightened-threshold", mk("CONSTRAINTS.md", ["- coverage: at least 60 percent"], ["- coverage: at least 80 percent"])),
        ("tightened-max", mk("CONSTRAINTS.md", ["- latency: at most 900 ms"], ["- latency: at most 200 ms"])),
        ("moved-suppression", mk("src/a.py", ["x = f()  # noqa: E501"], ["x = f()  # noqa: E501", "y = 1"])),
        ("reflowed-assertion", mk("tests/test_a.py", ["    assert f() == 1"], ["    assert f() == 1, 'msg'"])),
        ("assertion-in-comment-only", mk("tests/test_a.py", ["    # assert old idea"], ["    # dropped note"])),
        ("renamed-test-file", mk("tests/test_a.py", ["assert 1"], [], deleted=True) + mk("tests/sub/test_a.py", [], ["assert 1"], new=True)),
        ("todo-alone", mk("src/a.py", [], ["# TODO: later"])),
        ("exception-row-dropped", mk("CONSTRAINTS.md", ["| E1 | src/a.py | legacy | o | 2027-01-01 |"], [])),
        ("plain-code", mk("src/a.py", ["a = 1"], ["a = 2"])),
    ]
    for name, d in clean:
        got = rules(d)
        check(f"V-AGSK-POLE-GREEN[{name}]", got == [], f"rules={got}")


def test_approvals():
    f = fg.analyze(mk("src/a.py", [], ["x = 1  # noqa: E501"]))
    ap = {"rule": "silenced-checker", "path": "src/*.py", "owner": "dev", "reason": "generated line",
          "approved_by": "owner", "expires": (dt.date.today() + dt.timedelta(days=30)).isoformat()}
    fg.apply_approvals(f, [ap])
    check("V-AGSK-APPROVAL-WAIVES", all(x.waived_by for x in f) and f, f"waived_by={[x.waived_by for x in f]}")
    for label, mut in (("expired", {"expires": "2020-01-01"}), ("missing-owner", {"owner": ""}),
                       ("wrong-rule", {"rule": "test-deleted"}), ("wrong-path", {"path": "docs/*"}),
                       ("bad-date", {"expires": "soon"})):
        f2 = fg.analyze(mk("src/a.py", [], ["x = 1  # noqa: E501"]))
        fg.apply_approvals(f2, [dict(ap, **mut)])
        check(f"V-AGSK-APPROVAL-REFUSED[{label}]", f2 and not any(x.waived_by for x in f2), "finding stays unwaived")


def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def test_cli_real_git():
    with tempfile.TemporaryDirectory(prefix="agsk-git-") as d:
        d = Path(d)
        for c in (["git", "init", "-q"], ["git", "config", "user.email", "t@t"], ["git", "config", "user.name", "t"]):
            sh(c, d)
        (d / "tests").mkdir()
        (d / "tests" / "test_a.py").write_text("def test_a():\n    assert 1 + 1 == 2\n")
        (d / "CONSTRAINTS.md").write_text("- coverage: at least 80 percent\n")
        sh(["git", "add", "-A"], d)
        sh(["git", "commit", "-qm", "base"], d)

        def cli(*extra):
            return sh([sys.executable, "-m", "modules.sqi.floor_guard", "--repo", str(d), *extra], ROOT)

        r = cli()
        check("V-AGSK-CLI-CLEAN-EXIT0", r.returncode == 0, f"rc={r.returncode} {r.stdout.strip()[:60]}")
        (d / "tests" / "test_a.py").write_text("def test_a():\n    pass\n")
        r = cli()
        check("V-AGSK-CLI-ASSERTION-REMOVED-EXIT1", r.returncode == 1 and "assertion-removed" in r.stdout,
              f"rc={r.returncode} {r.stdout.strip()[:80]}")
        (d / "tests" / "test_a.py").write_text("def test_a():\n    assert 1 + 1 == 2\n")
        (d / "new.py").write_text("x = 1  # noqa\n")  # untracked file: plain `git diff` is blind to it
        r = cli()
        check("V-AGSK-CLI-UNTRACKED-SEEN", r.returncode == 1 and "silenced-checker" in r.stdout,
              f"rc={r.returncode}")
        ap = d / "ap.json"
        ap.write_text(json.dumps([{"rule": "silenced-checker", "path": "new.py", "owner": "o", "reason": "r",
                                   "approved_by": "a", "expires": (dt.date.today() + dt.timedelta(days=5)).isoformat()}]))
        r = cli("--approvals", str(ap))
        check("V-AGSK-CLI-WAIVED-EXIT0-AND-REPORTED", r.returncode == 0 and "WAIVED" in r.stdout, f"rc={r.returncode}")
        r = cli("--approvals", str(d / "missing.json"))
        check("V-AGSK-CLI-BAD-APPROVALS-EXIT2", r.returncode == 2, f"rc={r.returncode}")
    with tempfile.TemporaryDirectory(prefix="agsk-nogit-") as nd:
        r = sh([sys.executable, "-m", "modules.sqi.floor_guard", "--repo", nd], ROOT)
        check("V-AGSK-CLI-NOT-A-REPO-EXIT2", r.returncode == 2, f"rc={r.returncode} (never 0)")
    r = sh([sys.executable, "-m", "modules.sqi.floor_guard", "--base", "no-such-ref-xyz"], ROOT)
    check("V-AGSK-CLI-BAD-BASE-EXIT2", r.returncode == 2, f"rc={r.returncode}")


VOCAB = {"ALREADY OWNED", "EXTEND", "CONNECT", "MERGE", "CONDITIONAL", "UPSTREAM-ONLY", "REJECT", "UNVERIFIED"}
PIN = "8c99fa36d90068c82d547f7c12a9d67a3e95f4ee"
UPSTREAM_SKILLS = 26
UPSTREAM_COMMANDS = 10


def read_row_problems(rows, tsv):
    """A READ row needs a tsv row for the same name whose evidence cites upstream file:line."""
    out = []
    for r in rows:
        if r[4] != "READ" or (r[0], r[1]) in {("skill", "constraint-driven-development"), ("command", "constraints")}:
            continue
        c = tsv.get((r[0], r[1]))
        if c is None or len(c) < 5 or not re.search(r"SKILL\.md:\d+|\.toml:\d+|\.md:\d+|:\d+", c[4]) or "upstream-read-b/AGSK_" not in r[5]:
            out.append(r[1])
    return out


def test_ledger():
    p = ROOT / "vault/programs/bcap-2/agsk/DISPOSITIONS.md"
    text = p.read_text(encoding="utf-8")
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in text.splitlines()
            if re.match(r"^\|\s*(skill|command)\s*\|", ln)]
    sk = [r for r in rows if r[0] == "skill"]
    cm = [r for r in rows if r[0] == "command"]
    check("V-AGSK-LEDGER-COUNTS", len(sk) == UPSTREAM_SKILLS and len(cm) == UPSTREAM_COMMANDS, f"skills={len(sk)} commands={len(cm)}")
    names = [(r[0], r[1]) for r in rows]
    check("V-AGSK-LEDGER-UNIQUE", len(names) == len(set(names)), "one row per upstream name")
    check("V-AGSK-LEDGER-VOCAB", all(r[2] in VOCAB for r in rows), str(sorted({r[2] for r in rows} - VOCAB)))
    miss = [r[3] for r in rows if not (ROOT / r[3]).exists()]
    check("V-AGSK-LEDGER-OWNERS-EXIST", not miss, f"missing={miss}")
    check("V-AGSK-LEDGER-BASIS-HONEST", all(r[4] in ("READ", "HYPOTHESIS") for r in rows), "READ|HYPOTHESIS only")
    tsv = {}
    for f in "AB":
        for ln in (ROOT / f"vault/programs/bcap-2/upstream-read-b/AGSK_{f}_rows.tsv").read_text(encoding="utf-8").splitlines():
            c = ln.split("\t")
            tsv[(c[0], c[1])] = c
    probs = read_row_problems(rows, tsv)
    check("V-AGSK-LEDGER-READ-HAS-EVIDENCE", not probs, f"problems={probs}")
    check("V-AGSK-LEDGER-NO-HYPOTHESIS-LEFT", not [r[1] for r in rows if r[4] != "READ"], "all rows READ")
    bad = [{"rows": [["skill", "x", "EXTEND", "modules/sqi", "READ", "gap: none [evidence: nowhere]"]], "tsv": {}},
           {"rows": [["skill", "x", "EXTEND", "modules/sqi", "READ", "gap: g [evidence: upstream-read-b/AGSK_A_rows.tsv]"]],
            "tsv": {("skill", "x"): ["skill", "x", "EXTEND", "o", "no line refs here", "g", "n"]}}]
    check("V-AGSK-LEDGER-READ-WITHOUT-EVIDENCE-REJECTED", all(read_row_problems(b["rows"], b["tsv"]) for b in bad), "pole: both bad shapes caught")
    check("V-AGSK-PIN-MATCH", PIN in text and PIN in (ROOT / "vault/programs/bcap-2/agsk/NOTICE.md").read_text(), "ledger and NOTICE carry the pin")
    notice = (ROOT / "vault/programs/bcap-2/agsk/NOTICE.md").read_text()
    check("V-AGSK-LICENCE-ATTRIBUTION", "MIT" in notice and "Addy Osmani" in notice, "MIT + author in NOTICE")


def test_routing():
    idx = build_index(force=True)
    for prompt, want in (("skip the failing test so the build goes green", True),
                         ("add a noqa to silence the lint and get it green", True),
                         ("lower the coverage threshold to make CI pass", True),
                         ("saltar el test que falla", True),
                         ("fix a typo in the readme", False),
                         ("write a unit test for the parser", False),
                         ("the login keeps failing after the last deploy", False),
                         ("build a landing page", False),
                         ("explain what a threshold is in signal processing", False)):
        r = classify_intent(prompt, idx)
        woke = r.should_wakeup and r.domain == "constraints"
        check(f"V-AGSK-ROUTE[{prompt[:34]}]", woke == want, f"domain={r.domain} wake={r.should_wakeup}")
    r = classify_intent("the login keeps failing after the last deploy", idx)
    check("V-AGSK-ROUTE-DIAGNOSE-INTACT", r.domain == "diagnose", r.domain)
    card = [e for e in idx if e.domain == "constraints"]
    check("V-AGSK-CARD-LATENT", len(card) == 1 and card[0].token_weight <= 100, "one pointer card, not always-on")


def test_reachability():
    r = sh([sys.executable, "modules/liveness/reachability.py"], ROOT)
    out = r.stdout + r.stderr
    check("V-AGSK-LIVENESS-NOT-OFFENDER", "floor_guard" not in out or "OFFENDER" not in out.split("floor_guard")[0][-0:] , "floor_guard reachable or declared")
    check("V-AGSK-REACHED-FROM-ROUTER", "modules.sqi.floor_guard" in (ROOT / "modules/skill_router/skill_index.py").read_text()
          or "modules/sqi/floor_guard.py" in (ROOT / "modules/skill_router/skill_index.py").read_text(), "card invokes it")


def main():
    for t in (test_poles, test_approvals, test_cli_real_git, test_ledger, test_routing, test_reachability):
        print(t.__name__)
        t()
    print(f"\nAGSK gate: {P} PASS / {F} FAIL")
    return 0 if F == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
