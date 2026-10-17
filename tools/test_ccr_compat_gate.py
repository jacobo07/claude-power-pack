"""V-COMPAT-* gates for tools/ccr_compat_gate.py (spec vault/specs/ccr-compat-gate.md). Run from the repo root:
    python tools/test_ccr_compat_gate.py
Every gate is driven from both poles on the real file shapes; the mutant gates prove the assertions can go red."""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import ccr_compat_gate as g  # noqa: E402

passes = fails = 0


def ok(name: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {name}: {ev}")


def fail(name: str, why: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {name}: {why}")


def gate(name: str, cond: bool, ev: str) -> None:
    (ok if cond else fail)(name, ev)


POLICY = "// header\nexport const RUNTIME_VERSION = '0.1.0'\nexport const COMPAT = ['2.1.296', '2.1.302']\nexport type Mode = 'enforce'\n"
REGISTER = "import x from 'y'\nconst compatible = COMPAT.includes(version)\n"


def mutant(old: str, new: str) -> dict:
    src = (HERE / "ccr_compat_gate.py").read_text(encoding="utf-8")
    assert old in src, f"mutation anchor missing: {old}"
    ns: dict = {"__name__": "mutant", "__file__": str(HERE / "ccr_compat_gate.py")}
    exec(compile(src.replace(old, new), "mutant", "exec"), ns)
    return ns


def verdict_file(d: pathlib.Path, version: str, host: str, verdicts: dict, flag: bool = True, limits=None) -> None:
    (d / f"verdict-{version}.json").write_text(json.dumps({"host_version": host, "verdicts": verdicts, "all_required_pass": flag, "named_limits": limits or []}), encoding="utf-8")


ALL = {"S1a": "PASS", "S1b": "PASS", "S2": "PASS", "S3": "PASS", "S4": "PASS", "S5": "PASS"}


def main() -> int:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="compat_gate_"))
    try:
        # parse and check
        gate("V-COMPAT-PARSE", g.parse_compat(POLICY) == ["2.1.296", "2.1.302"] and g.parse_compat("export const COMPAT = []  // none") == []
             and g.parse_compat("nothing here") is None, "list, empty list and absent line told apart")
        c1, c2 = g.check("2.1.302", POLICY, "r1"), g.check("2.1.303", POLICY, "r1")
        gate("V-COMPAT-CHECK-POLES", c1["verdict"] == "COVERED" and c2["verdict"] == "UNCOVERED", f"{c1['verdict']} / {c2['verdict']}")
        gate("V-COMPAT-CHECK-UNKNOWN", g.check(None, POLICY, "r")["verdict"] == "UNKNOWN" and g.check("2.1.302", "no line", "r")["verdict"] == "UNKNOWN"
             and g.check("2.1.302", None, "r")["verdict"] == "UNKNOWN", "unreadable version or policy is never COVERED")
        gate("V-COMPAT-CHECK-EMPTY-LIST", g.check("2.1.302", "export const COMPAT = []", "r")["verdict"] == "UNCOVERED", "an empty list covers nothing")
        m = mutant('"COVERED" if version in compat else "UNCOVERED"', '"COVERED"')
        gate("V-COMPAT-CHECK-MUTANT", m["check"]("2.1.999", POLICY, "r")["verdict"] == "COVERED" and c2["verdict"] == "UNCOVERED",
             "a check that ignores the list returns COVERED for 2.1.999, so the UNCOVERED assertion above goes red on it")

        # plan
        d = tmp / "v"
        d.mkdir()
        gate("V-COMPAT-PLAN-NO-FILE", not g.plan("2.1.302", d)["ok"], "no verdict file: refused")
        verdict_file(d, "2.1.302", "2.1.301", ALL)
        gate("V-COMPAT-PLAN-WRONG-VERSION", not g.plan("2.1.302", d)["ok"], "verdict measured on another build: refused")
        verdict_file(d, "2.1.302", "2.1.302", {**ALL, "S3": "FAIL"})
        gate("V-COMPAT-PLAN-FAIL", not g.plan("2.1.302", d)["ok"], "a failing required case: refused")
        verdict_file(d, "2.1.302", "2.1.302", {**ALL, "S2": "INCONCLUSIVE"})
        gate("V-COMPAT-PLAN-INCONCLUSIVE", not g.plan("2.1.302", d)["ok"], "INCONCLUSIVE is not PASS")
        verdict_file(d, "2.1.302", "2.1.302", {k: v for k, v in ALL.items() if k != "S4"})
        gate("V-COMPAT-PLAN-MISSING", not g.plan("2.1.302", d)["ok"], "a required case absent: refused")
        verdict_file(d, "2.1.302", "2.1.302", {**ALL, "S1b": "FAIL"}, flag=True)
        gate("V-COMPAT-PLAN-FLAG-NOT-TRUSTED", not g.plan("2.1.302", d)["ok"], "all_required_pass=true with S1b FAIL: the verdicts win")
        verdict_file(d, "2.1.302", "2.1.302", ALL, flag=False)
        p = g.plan("2.1.302", d)
        gate("V-COMPAT-PLAN-PASS", p["ok"] and len(p["steps"]) == 5 and "2.1.302" in p["steps"][1], "all required PASS: five steps naming the version")
        verdict_file(d, "2.1.302", "2.1.302", {**ALL, "S5": "INCONCLUSIVE"}, limits=["S5=INCONCLUSIVE"])
        p = g.plan("2.1.302", d)
        gate("V-COMPAT-PLAN-S5-LIMIT", p["ok"] and p["named_limits"] == ["S5=INCONCLUSIVE"], "S5 INCONCLUSIVE allowed and named")
        verdict_file(d, "2.1.302", "2.1.301", ALL)
        m = mutant('if v.get("host_version") != version:', "if False:")
        gate("V-COMPAT-PLAN-MUTANT", m["plan"]("2.1.302", d)["ok"] is True and not g.plan("2.1.302", d)["ok"],
             "a plan that ignores the recorded version accepts the 2.1.301 verdict, so the wrong-version assertion goes red on it")

        # reprobe must refuse without --confirm and must not run anything
        before = set(d.iterdir())
        rc, out = g.reprobe(False, "2.1.302", "r")
        gate("V-COMPAT-REPROBE-REFUSES", rc == 2 and not out["ok"] and set(d.iterdir()) == before, "no --confirm: refused, nothing written")

        # source-check
        ccr = tmp / "ccr"
        (ccr / "active" / "hooks").mkdir(parents=True)
        (ccr / "active" / "hooks" / "policy.ts").write_text(POLICY, encoding="utf-8")
        (ccr / "active" / "hooks" / "register.ts").write_text(REGISTER, encoding="utf-8")
        tree = tmp / "tree"
        (tree / "mods" / "cpp-cognitive-runtime" / "hooks").mkdir(parents=True)
        th = tree / "mods" / "cpp-cognitive-runtime" / "hooks"
        (th / "policy.ts").write_text(POLICY.replace("'2.1.302'", "'2.1.296', '2.1.303'").replace("['2.1.296', '2.1.296'", "['2.1.296'"), encoding="utf-8")
        (th / "register.ts").write_text(REGISTER.replace("\n", "\r\n"), encoding="utf-8", newline="")
        gate("V-COMPAT-SOURCE-SAME", g.source_check(tree, ccr)["verdict"] == "SAME_EXCEPT_COMPAT", "only COMPAT and CRLF differ: same")
        (th / "policy.ts").write_text(POLICY + "export const EXTRA = 1\n", encoding="utf-8")
        gate("V-COMPAT-SOURCE-DIFFERS", g.source_check(tree, ccr)["verdict"] == "DIFFERS", "an extra line: DIFFERS (the 2026-10-17 regression shape)")
        (th / "policy.ts").unlink()
        gate("V-COMPAT-SOURCE-UNKNOWN", g.source_check(tree, ccr)["verdict"] == "UNKNOWN", "a missing file is UNKNOWN, not SAME")

        # real environment: the shapes above are the real ones, so read the real active release too
        policy, rel = g.active_release()
        live = g.check(g.host_version(), policy, rel)
        gate("V-COMPAT-LIVE-READ", g.parse_compat(policy) is not None and live["verdict"] in ("COVERED", "UNCOVERED"),
             f"active {rel}: host {live['host']} {live['verdict']} compat={live['compat']}")

        # the durable probe: driver selftest and plugin validation
        run = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")   # validate prints non-cp1252 glyphs
        p1 = subprocess.run([sys.executable, "-I", str(HERE / "ccr_compat_probe.py"), "--selftest"], timeout=120, **run)
        gate("V-COMPAT-PROBE-SELFTEST", p1.returncode == 0 and "UZ_SELFTEST=PASS" in p1.stdout, "driver selftest")
        claude = shutil.which("claude")
        p2 = subprocess.run([claude, "plugin", "validate", str(REPO / "mods" / "ccr-uz-probe")], timeout=180, **run) if claude else None
        gate("V-COMPAT-PROBE-VALIDATES", bool(p2) and p2.returncode == 0 and "Validation passed" in p2.stdout, "claude plugin validate mods/ccr-uz-probe")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"COMPAT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
