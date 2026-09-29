"""Shared grade / selftest driver for the P3 judgement tasks (task_*.py beside this file).

grade <path>: load the subject module, run every check in isolation, print one PASS/FAIL line per
check and `P3J_PASS=n/m`; exit 0 only when every check passed. A module that fails to import scores
one failed `import` check, so it can never read as a clean zero-check pass.
selftest: the stub and the naive solution must each fail at least one check; the reference must pass
all -- both poles of every grader driven with no model call.
"""
import importlib.util
import os
import tempfile


def _load(path):
    spec = importlib.util.spec_from_file_location("p3j_subject", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_checks(checks, path):
    try:
        m = _load(path)
    except Exception as e:
        return [("import", False, f"{type(e).__name__}: {e}")]
    out = []
    for name, fn in checks:
        try:
            ok, detail = fn(m)
        except Exception as e:
            ok, detail = False, f"{type(e).__name__}: {e}"
        out.append((name, bool(ok), detail))
    return out


def report(res):
    for n, ok, d in res:
        print(("PASS " if ok else "FAIL ") + n + " " + str(d)[:160])
    k = sum(ok for _, ok, _ in res)
    print(f"P3J_PASS={k}/{len(res)}")
    return 0 if k == len(res) else 1


def selftest(checks, stub, naive, ref):
    good = True
    for name, src, want in (("stub", stub, False), ("naive", naive, False), ("ref", ref, True)):
        p = os.path.join(tempfile.mkdtemp(), "m.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(src)
        res = run_checks(checks, p)
        passed = all(ok for _, ok, _ in res)
        print(f"  {name}: {'all pass' if passed else 'fails ' + str([n for n, ok, _ in res if not ok])}")
        good &= passed == want
    print("SELFTEST", "OK" if good else "BAD")
    return 0 if good else 1


def main(checks, stub, naive, ref, doc):
    import sys
    a = sys.argv[1:]
    if a[:1] == ["grade"] and len(a) == 2:
        return report(run_checks(checks, a[1]))
    if a[:1] == ["selftest"]:
        return selftest(checks, stub, naive, ref)
    print(doc)
    return 2
