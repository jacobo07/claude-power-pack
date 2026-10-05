"""V-E1BANK-* gates: drive every pole of the E1 task driver and every refusal of the validator, red AND green.

    python3 test_validate_bank.py

Stdlib only, no pytest, no model call. Synthetic tasks are plain dicts around a one-function module, so no
gate depends on a real task. Temporary git repos and trees live in tempfile directories; nothing is created
inside the real repository. Ends `E1BANK_PASS=<passes>/<total>`; exit 0 only when every gate passed.
"""
import sys

sys.dont_write_bytecode = True

import contextlib  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _e1_common as C  # noqa: E402
import validate_bank as V  # noqa: E402

BASE_FULL = "78ba9e7414c3e046b1e91ce7b7fde86c78f205f5"

# ---- a synthetic task: pick(items) -------------------------------------------------------------------

SYN_STUB = '"""Picks the first entry for the dashboard tile."""\n\n\ndef pick(items):\n    ...\n'
SYN_NAIVE = "def pick(items):\n    return items[0] if items else 0\n"
SYN_REF = "def pick(items):\n    return items[0] if items else None\n"


def c_first(m):
    v = m.pick([1, 2])
    return v == 1, repr(v)


def c_string(m):
    v = m.pick(["a"])
    return v == "a", repr(v)


def j_empty(m):
    raised, v = C.attempt(m.pick, [])
    if raised:
        return True, "refused loudly"
    return v is None, repr(v)


def j_nested(m):
    raised, v = C.attempt(m.pick, [[]])
    if raised:
        return True, "refused loudly"
    return v == [], repr(v)


def always(m):
    return True, "always"


def syn(**over):
    ns = dict(
        RULE="rules/synthetic-rule.md", MODULE="e1j/pick.py", STUB=SYN_STUB, NAIVE=SYN_NAIVE, REF=SYN_REF,
        CHECKS=[("first_item", "control", c_first), ("string_item", "control", c_string),
                ("empty_list", "judgement", j_empty), ("nested_empty", "judgement", j_nested)],
        JUDGES={"empty_list": "an empty input has no first entry and must not become zero",
                "nested_empty": "a nested empty list is carried through unchanged"},
        STUB_FORBIDDEN=["zero", "default", "fallback"])
    ns.update(over)
    return ns


def selftest_of(ns):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = C.selftest(ns)
    return rc, buf.getvalue()


def pole(out, name):
    for ln in out.splitlines():
        if ln.startswith(f"  {name}:"):
            return ln
    return ""


def red_on(ns, who, needle):
    """A broken task must make the selftest return 1 with `needle` on the `who` pole line (or a lint line)."""
    rc, out = selftest_of(ns)
    line = pole(out, who) if who != "lint" else "\n".join(x for x in out.splitlines() if "lint:" in x)
    ok = rc == 1 and "SELFTEST BAD" in out and needle in line
    return ok, f"rc={rc} {who}-line={line.strip()[:150]!r}"


# ---- gates -------------------------------------------------------------------------------------------

def g_good():
    rc, out = selftest_of(syn())
    poles = [pole(out, p) for p in ("stub", "naive", "ref", "raiser")]
    ok = rc == 0 and "SELFTEST OK" in out and all(": OK" in p for p in poles)
    return ok, f"rc={rc} poles={[p.strip()[:24] for p in poles]}"


def g_naive_control():
    return red_on(syn(NAIVE="def pick(items):\n    return items[-1] if items else 0\n"), "naive", "control")


def g_naive_nojudge():
    return red_on(syn(NAIVE=SYN_REF), "naive", "no judgement")


def g_ref_red():
    return red_on(syn(REF=SYN_NAIVE), "ref", "must pass every check")


def g_stub_green():
    ns = syn(CHECKS=[("a", "control", always), ("b", "control", always),
                     ("c", "judgement", always), ("d", "judgement", always)],
             JUDGES={"c": "a decision text of enough length", "d": "another decision text of enough length"})
    return red_on(ns, "stub", "passes every check")


def g_raiser_control():
    def c_swallow(m):
        try:
            v = m.pick([1, 2])
        except Exception:
            return True, "swallowed the refusal"
        return v == 1, repr(v)
    ns = syn()
    ns["CHECKS"] = [("first_item", "control", c_swallow)] + ns["CHECKS"][1:]
    return red_on(ns, "raiser", "control checks pass on a raiser")


def g_raiser_judge():
    def j_direct(m):
        v = m.pick([])  # called directly: a loud refusal escapes and the check FAILs
        return v is None, repr(v)
    ns = syn()
    ns["CHECKS"] = ns["CHECKS"][:2] + [("empty_list", "judgement", j_direct)] + ns["CHECKS"][3:]
    return red_on(ns, "raiser", "judgement checks fail on a raiser")


def g_stub_body():
    stub = '"""Picks the first entry for the dashboard tile."""\n\n\ndef pick(items):\n    return None\n'
    ok, ev = red_on(syn(STUB=stub), "lint", "body is not")
    return ok and C.lint(syn()) == [], ev + " | clean task lints []"


def g_forbidden_task():
    stub = '"""Picks the first entry; an empty list yields the default."""\n\n\ndef pick(items):\n    ...\n'
    return red_on(syn(STUB=stub), "lint", "task-forbidden word 'default'")


def g_forbidden_common():
    a = '"""Picks the first entry. A grader reads it."""\n\n\ndef pick(items):\n    ...\n'
    b = '"""Picks the first entry (see common/code-review)."""\n\n\ndef pick(items):\n    ...\n'
    ok1, e1 = red_on(syn(STUB=a), "lint", "common-forbidden token 'grader'")
    ok2, e2 = red_on(syn(STUB=b), "lint", "common-forbidden token 'common/code-review'")
    return ok1 and ok2, e1 + " | " + e2


def g_judges():
    ns1 = syn(JUDGES={"empty_list": "an empty input has no first entry and must not become zero"})
    ns2 = syn(JUDGES={"empty_list": "an empty input has no first entry and must not become zero",
                      "nested_empty": "a nested empty list is carried through unchanged",
                      "first_item": "a control check must not appear in the decision table"})
    ok1, e1 = red_on(ns1, "lint", "JUDGES keys")
    ok2, e2 = red_on(ns2, "lint", "JUDGES keys")
    return ok1 and ok2, e1 + " | " + e2


def g_signature():
    return red_on(syn(REF="def pick(entries):\n    return entries[0] if entries else None\n"),
                  "lint", "REF.pick parameters")


def g_import():
    with tempfile.TemporaryDirectory() as d:
        bad = os.path.join(d, "bad.py")
        Path(bad).write_text("def pick(items:\n", encoding="utf-8")
        res = C.run_checks(syn()["CHECKS"], bad)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = C.report(res)
        out = buf.getvalue()
        good = os.path.join(d, "good.py")
        Path(good).write_text(SYN_REF, encoding="utf-8")
        gres = C.run_checks(syn()["CHECKS"], good)
    fails = [ln for ln in out.splitlines() if ln.startswith("FAIL")]
    ok = (len(res) == 1 and res[0][0] == "import" and res[0][2] is False and rc == 1 and len(fails) == 1
          and "E1J_PASS=0/1" in out and len(gres) == 4 and all(r[2] for r in gres))
    return ok, f"rc={rc} lines={out.strip().splitlines()[-2:]} control-import-loads={len(gres)}/4"


def _repo(d, files):
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    run = lambda *a: subprocess.run(a, cwd=d, env=env, capture_output=True, text=True, check=True).stdout.strip()  # noqa: E731
    run("git", "init", "-q", d)
    for rel, text in files.items():
        p = Path(d) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    run("git", "add", "-A")
    run("git", "-c", "user.name=e1", "-c", "user.email=e1@example.invalid", "commit", "-q", "-m", "x")
    return run("git", "rev-parse", "HEAD")


def g_base_leak():
    cases = [
        ("bank file", {"vault/programs/cognitive-economy/e1/bank-draft/x.py": "x\n"},
         ["vault/programs/cognitive-economy/e1/bank-draft/x.py"]),
        ("addendum only", {"vault/programs/cognitive-economy/e1/ADDENDUM-E1.md": "x\n"}, []),
        ("phase plan", {".planning/workstreams/cognitive-economy-e1/phases/01-x/01-01-PLAN.md": "x\n"},
         [".planning/workstreams/cognitive-economy-e1/phases/01-x/01-01-PLAN.md"]),
        ("unrelated", {"README.md": "x\n", ".planning/workstreams/cognitive-economy-e1/STATE.md": "x\n"}, []),
    ]
    bad = []
    for label, files, want in cases:
        with tempfile.TemporaryDirectory() as d:
            h = _repo(d, files)
            got = V.base_leaks(h, repo=d)
        if got != want:
            bad.append(f"{label}: {got}")
    return not bad, f"{len(cases)} cases, mismatches={bad}"


def g_leak_scan():
    stem = next(iter(sorted(p.stem for p in HERE.glob("task_*.py"))), "task_x")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "src").mkdir()
        (root / "src/a.py").write_text("print('a')\n")
        (root / "src/b.txt").write_text("b\n")
        (root / ".git").write_text(f"gitdir: E1J_PASS {stem}\n")  # the root .git entry is never listed
        n_clean, hits_clean = V.leak_scan(root)
        (root / "src/marker.txt").write_text("has E1J_PASS inside\n")
        (root / "src/stem.txt").write_text(f"mentions {stem}\n")
        (root / "src/common.txt").write_text("imports _e1_common\n")
        (root / "named").mkdir()
        (root / "named/_e1_common.py").write_text("x = 1\n")
        (root / "vault/programs/cognitive-economy/e1/bank").mkdir(parents=True)
        (root / "vault/programs/cognitive-economy/e1/bank/t.py").write_text("x = 1\n")
        (root / "vault/programs/cognitive-economy/e1/ADDENDUM-E1.md").write_text("contract\n")
        n_dirty, hits = V.leak_scan(root)
    want = {"src/marker.txt", "src/stem.txt", "src/common.txt", "named/_e1_common.py",
            "vault/programs/cognitive-economy/e1/bank/t.py"}
    ok = n_clean == 2 and hits_clean == [] and set(hits) == want and n_dirty == 8
    return ok, f"clean=({n_clean},{hits_clean}) dirty=({n_dirty},{sorted(set(hits) ^ want)})"


def g_drop_refuses():
    with tempfile.TemporaryDirectory() as d:
        victim = Path(d) / "keep"
        victim.mkdir()
        (victim / "f.txt").write_text("precious\n")
        try:
            V.drop_tree(victim)
            refused = False
        except RuntimeError:
            refused = True
        survived = (victim / "f.txt").read_text() == "precious\n"
        runs_itself = False
        try:
            V.drop_tree(V.RUNS)
        except RuntimeError:
            runs_itself = True
    escape = Path(str(V.RUNS) + "/../e1-escape-probe")
    try:
        V.fresh_tree("../e1-escape-probe", BASE_FULL)
        escaped = False
    except RuntimeError:
        escaped = True
    absent_ok = V.drop_tree(V.RUNS / "no-such-tree") is True  # positive control: a legal absent path
    ok = refused and survived and runs_itself and escaped and not escape.resolve().exists() and absent_ok
    return ok, (f"refused={refused} survived={survived} runs_root_refused={runs_itself} "
                f"fresh_tree_escape_refused={escaped} legal_absent_path_ok={absent_ok}")


def g_real_base():
    got = V.jbase()
    saved = V.base_leaks
    V.base_leaks = lambda base, repo=V.REPO: ["vault/programs/cognitive-economy/e1/bank/x.py"]
    try:
        try:
            V.jbase()
            leak_refused = False
        except SystemExit:
            leak_refused = True
    finally:
        V.base_leaks = saved
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "BASE").write_text("deadbeef" * 5 + "\n")
        saved_here, V.HERE = V.HERE, Path(d)
        try:
            try:
                V.jbase()
                ghost_refused = False
            except SystemExit:
                ghost_refused = True
        finally:
            V.HERE = saved_here
    ok = got == BASE_FULL and leak_refused and ghost_refused
    return ok, f"base={got[:10]} leak_refused={leak_refused} nonexistent_commit_refused={ghost_refused}"


def g_index():
    idx = V.build_index()
    ts = idx["tasks"]
    sizes = [t["rule_bytes"] for t in ts]
    rules = [t["rule"] for t in ts]
    all_e1 = [r["rule"] for r in V.e1_rules()]
    contract = [r for r in all_e1 if r in rules]
    first_ok = bool(ts) and ts[0]["id"] == "J-gceg_product_page" and ts[0]["rule_bytes"] == 6284
    covered = sorted(rules + idx["missing"]) == sorted(all_e1) and len(all_e1) == 11
    r2_clean = not (set(V.EXCLUDED_BY_R2) & set(rules + idx["missing"]))
    cp = V.base_rule_copies(idx["base"])
    copies_ok = (cp["rules/python/testing.md"] == ["rules/python/testing.md"]
                 and cp["rules/common/code-review.md"] == ["rules/common/code-review.md"]
                 and cp["rules/generated-content-needs-an-evidence-gate.md"] == []
                 and all(t["rule_copies_at_base"] == cp[t["rule"]] for t in ts))
    r = subprocess.run([sys.executable, str(HERE / "validate_bank.py"), "index", "--stdout"], capture_output=True,
                       text=True, env=V.child_env())
    cli_same = r.returncode == 0 and json.loads(r.stdout) == idx
    target = HERE / "index.json"
    chk = subprocess.run([sys.executable, str(HERE / "validate_bank.py"), "index", "--check"],
                         capture_output=True, text=True, env=V.child_env())
    want_chk = 0 if (not idx["missing"] and target.is_file()
                     and target.read_text(encoding="utf-8") == V._index_text(idx)) else 1
    refuse = True
    if idx["missing"]:  # only when --write would refuse: never write a partial index from a test
        w = subprocess.run([sys.executable, str(HERE / "validate_bank.py"), "index", "--write"],
                           capture_output=True, text=True, env=V.child_env())
        refuse = w.returncode == 1 and not target.exists()
    ok = (sizes == sorted(sizes, reverse=True) and rules == contract and first_ok and covered and r2_clean
          and copies_ok and cli_same and chk.returncode == want_chk and refuse)
    return ok, (f"tasks={len(ts)} missing={len(idx['missing'])} first={ts[0]['id'] if ts else None} "
                f"copies_ok={copies_ok} cli_same={cli_same} check_rc={chk.returncode}/{want_chk} write_refused={refuse}")


def g_pin_scrub():
    pin_text = b"line1\nline2\n"
    pin = hashlib.sha256(pin_text).hexdigest()
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for rel, data in {"other/x.md": b"line1\r\nline2\r\n",
                          "rules/common/code-review.md": b"matches no pin\n",
                          "docs/code-review.md": b"matches no pin\n",
                          "notes.txt": b"an ordinary file\n"}.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_bytes(data)
        removed = V.scrub_pin_copies(root, {pin})
        kept = [(root / p).exists() for p in ("docs/code-review.md", "notes.txt")]
        clean = V.pin_matches(root, {pin}) == [] and not any(os.path.lexists(root / p) for p in V.RULE_PATHS)
    plain_ok = removed == ["other/x.md", "rules/common/code-review.md"] and all(kept) and clean

    # I2: a symlinked `rules` dir pointing outside the tree, a symlinked file, and a pin copy outside.
    with tempfile.TemporaryDirectory() as d:
        outside = Path(d) / "outside"
        (outside / "common").mkdir(parents=True)
        (outside / "common/code-review.md").write_bytes(b"outside rule copy\n")
        (outside / "pinned.md").write_bytes(pin_text)
        (outside / "target.md").write_bytes(b"outside target\n")
        root = Path(d) / "tree"
        root.mkdir()
        (root / "rules").symlink_to(outside, target_is_directory=True)
        (root / "ln.md").symlink_to(outside / "pinned.md")
        (root / "keep").mkdir()
        (root / "keep/python").mkdir()
        removed2 = V.scrub_pin_copies(root, {pin})
        root2 = Path(d) / "tree2"
        (root2 / "rules/python").mkdir(parents=True)
        (root2 / "rules/python/testing.md").symlink_to(outside / "target.md")
        removed3 = V.scrub_pin_copies(root2, {pin})
        survived = all((outside / n).exists() for n in ("common/code-review.md", "pinned.md", "target.md"))
        links = os.path.islink(root / "rules") and os.path.islink(root / "ln.md") \
            and os.path.islink(root2 / "rules/python/testing.md")
    sym_ok = removed2 == [] and removed3 == [] and survived and links
    return plain_ok and sym_ok, (f"content+path removed={removed} kept_same_name_elsewhere={kept} rescan_clean={clean} | "
                                 f"symlinks removed={removed2 + removed3} outside_survived={survived} links_kept={links}")


def g_floor():
    with tempfile.TemporaryDirectory() as d:
        empty = V.leak_scan(d)
    g = {"rc": 1, "summary": "E1J_PASS=0/8 control=0/4 judgement=0/4"}
    good = dict(selftest_rc=0, g=g, files_listed=1, leak=[], module_absent=True, rescan=[], removed=True)
    zero = V.task_ok(**{**good, "files_listed": 0})
    one = V.task_ok(**good)
    flips = {"selftest_rc": 1, "g": {"rc": 0, "summary": g["summary"]}, "leak": ["x"], "module_absent": False,
             "rescan": ["y"], "removed": False}
    flipped = {k: V.task_ok(**{**good, k: v}) for k, v in flips.items()}
    flipped["no_e1j_line"] = V.task_ok(**{**good, "g": {"rc": 1, "summary": "no E1J line"}})
    ok = empty == (0, []) and zero is False and one is True and not any(flipped.values())
    return ok, f"empty_scan={empty} files_listed0={zero} files_listed1={one} single_condition_flips={flipped}"


def g_only():
    src = HERE / "task_gceg_product_page.py"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "_e1_common.py").write_bytes((HERE / "_e1_common.py").read_bytes())
        (tmp / src.name).write_bytes(src.read_bytes())
        (tmp / "task_zzz_broken.py").write_text("raise RuntimeError('half written')\n", encoding="utf-8")
        one = V.tasks(only=["J-gceg_product_page"], here=tmp)
        try:
            V.tasks(here=tmp)
            full_refused = False
        except SystemExit:
            full_refused = True
        try:
            V.tasks(only=["J-no_such_task"], here=tmp)
            missing_refused = False
        except SystemExit:
            missing_refused = True
    ok = [t["id"] for t in one] == ["J-gceg_product_page"] and full_refused and missing_refused
    return ok, f"only={[t['id'] for t in one]} full_load_refused={full_refused} unknown_id_refused={missing_refused}"


def g_jprepare():
    rule_text = (Path.home() / ".claude/rules/generated-content-needs-an-evidence-gate.md").read_bytes()
    t = {"module": "e1j/probe.py", "stub": "def f():\n    ...\n"}
    saved = V.RUNS
    with tempfile.TemporaryDirectory() as d:
        V.RUNS = Path(d) / "runs"
        try:
            wt = V.RUNS / "wt"
            (wt / "other").mkdir(parents=True)
            (wt / "other/copy.md").write_bytes(rule_text.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            (wt / "rules/python").mkdir(parents=True)
            (wt / "rules/python/testing.md").write_text("not a pin\n")
            (wt / "docs").mkdir()
            (wt / "docs/testing.md").write_text("keep me\n")
            removed = V.jprepare(wt, t)
            stub_written = (wt / "e1j/probe.py").read_text() == t["stub"]
            kept = (wt / "docs/testing.md").exists()
            try:
                V.jprepare(wt, t)
                collision = False
            except RuntimeError:
                collision = True
            try:
                V.jprepare(Path(d) / "elsewhere", t)
                outside = False
            except RuntimeError:
                outside = True
        finally:
            V.RUNS = saved
    ok = removed == ["other/copy.md", "rules/python/testing.md"] and stub_written and kept and collision and outside
    return ok, f"removed={removed} stub_written={stub_written} collision_refused={collision} outside_refused={outside}"


def g_common_stems():
    stems = {r["rule"][len("rules/"):-len(".md")] for r in V.packet_rules()}
    ok = stems <= set(C.COMMON_FORBIDDEN) and {"grader", "judgement", "hidden", "E1J"} <= set(C.COMMON_FORBIDDEN)
    return ok, f"packet stems missing from COMMON_FORBIDDEN={sorted(stems - set(C.COMMON_FORBIDDEN))}"


GATES = [
    ("V-E1BANK-GOOD", g_good), ("V-E1BANK-NAIVE-CONTROL", g_naive_control),
    ("V-E1BANK-NAIVE-NOJUDGE", g_naive_nojudge), ("V-E1BANK-REF-RED", g_ref_red),
    ("V-E1BANK-STUB-GREEN", g_stub_green), ("V-E1BANK-RAISER-CONTROL", g_raiser_control),
    ("V-E1BANK-RAISER-JUDGE", g_raiser_judge), ("V-E1BANK-STUB-BODY", g_stub_body),
    ("V-E1BANK-FORBIDDEN-TASK", g_forbidden_task), ("V-E1BANK-FORBIDDEN-COMMON", g_forbidden_common),
    ("V-E1BANK-JUDGES", g_judges), ("V-E1BANK-SIGNATURE", g_signature), ("V-E1BANK-IMPORT", g_import),
    ("V-E1BANK-BASE-LEAK", g_base_leak), ("V-E1BANK-LEAK-SCAN", g_leak_scan),
    ("V-E1BANK-DROP-REFUSES", g_drop_refuses), ("V-E1BANK-REAL-BASE", g_real_base),
    ("V-E1BANK-INDEX", g_index), ("V-E1BANK-PIN-SCRUB", g_pin_scrub), ("V-E1BANK-FLOOR", g_floor),
    ("V-E1BANK-ONLY", g_only), ("V-E1BANK-JPREPARE", g_jprepare),
    ("V-E1BANK-COMMON-STEMS", g_common_stems),
]


def main():
    passes = 0
    for name, fn in GATES:
        try:
            ok, ev = fn()
        except Exception as e:  # a crashing gate is a FAIL, never a silent skip
            ok, ev = False, f"crashed: {type(e).__name__}: {e} | {traceback.format_exc().splitlines()[-3:]}"
        passes += bool(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name} {str(ev)[:300]}")
    print(f"E1BANK_PASS={passes}/{len(GATES)}  threshold={len(GATES)}/{len(GATES)}")
    return 0 if passes == len(GATES) else 1


if __name__ == "__main__":
    sys.exit(main())
