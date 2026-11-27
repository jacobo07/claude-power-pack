"""smoke_pressure.py - phase-local live smoke for Phase 4 (host-pressure admission), plan 04-03.

Modes (run with `python3 -I`):
  --selftest-plane  check the plane header function on four (node, platform) pairs; takes no reading
  --live            print the plane line and the real reading from the shipped reader (read-only)
  --forced-red      drive the shipped bench_all.main against a TEMP ledger and TEMP floors files:
                    control GREEN regresses, forced RED through the count pole and the RAM pole is
                    INCONCLUSIVE and recorded, and the next GREEN window excludes the RED entries

Exit codes: 0 ran and all claims passed, 1 a claim failed, 2 usage or mode failure, 3 the plane line is
not the GEX44 one (no reading was taken), 5 the live host is not GREEN so no control can be built.

Stdlib only, never imported by tools/, never writes vault/. Prints counts, classes and its own claim
lines only: no pid, process name, command line, foreign path or environment value (HR-SECRET-002).
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import platform
import re
import sys
import tempfile
from pathlib import Path

GEX44_NODE = "kobicraft-gex44"
EXPECTED = 7


def plane_line(node, platform_name):
    """The plane header, a pure function of (node, platform). GEX44 only for the exact host on linux;
    every other pair is UNVERIFIED. There is no override path."""
    if (isinstance(node, str) and node == GEX44_NODE
            and isinstance(platform_name, str) and platform_name.startswith("linux")):
        return "plane: GEX44 host: %s" % GEX44_NODE
    return "plane: UNVERIFIED host: %s os: %s" % (node, platform_name)


PLANE_CASES = [
    (GEX44_NODE, "linux", "plane: GEX44 host: kobicraft-gex44"),
    (GEX44_NODE, "win32", "plane: UNVERIFIED host: kobicraft-gex44 os: win32"),
    ("some-other-node", "linux", "plane: UNVERIFIED host: some-other-node os: linux"),
    ("LAPTOP-OWNER", "win32", "plane: UNVERIFIED host: LAPTOP-OWNER os: win32"),
]


def plane_cases_ok(verbose):
    bad = 0
    for node, plat, want in PLANE_CASES:
        got = plane_line(node, plat)
        ok = got == want
        bad += 0 if ok else 1
        if verbose:
            print("  %s (%s, %s) -> %s" % ("PASS" if ok else "FAIL", node, plat, got))
    if verbose:
        print("PLANE_SELFTEST=%d/%d" % (len(PLANE_CASES) - bad, len(PLANE_CASES)))
    return bad == 0


def selftest_plane():
    return 0 if plane_cases_ok(True) else 1


def repo_root():
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "tools" / "bench_all.py").is_file() and (p / "tools" / "resource_admission.py").is_file():
            return p
    raise RuntimeError("repo root with tools/bench_all.py not found above the harness")


def load_by_path(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def live_reading(root, ra):
    """Print the real reading from the shipped reader; returns the pressure dict."""
    floors_file = root / "vault" / "config" / "resource-floors.json"
    ram = ra.read_available_mb()
    cnt = ra.read_claude_process_count()
    p = ra.pressure(ram, cnt)
    try:
        decl = json.loads(floors_file.read_text(encoding="utf-8-sig")).get("claude_process") or {}
    except Exception:  # noqa: BLE001
        decl = {}
    print("instrument: tools/resource_admission.py read_available_mb, read_claude_process_count, pressure")
    print("sample size: n=1 (one reading, a probe of this moment, not a distribution)")
    print("ram: available_mb=%s source=%s" % (ram.get("available_mb"), ram.get("source")))
    print("count: claude_processes=%s source=%s ambiguous=%s" % (cnt.get("count"), cnt.get("source"),
                                                                 cnt.get("ambiguous")))
    print("declared: ram_floor_mb=%s claude_ceiling=%s ceiling_status=%s"
          % (p.get("floor_mb"), p.get("claude_ceiling"), decl.get("status")))
    print("class: %s reasons=%s" % (p.get("class"), ",".join(p.get("reasons") or []) or "none"))
    return p


KEEP = re.compile(r"^(HOST PRESSURE:|REGRESSION|VERDICTS|bench_all exit|\s+SLOW-HOST-SUSPECT|"
                  r"\s+UNATTRIBUTABLE|\s+never_again_ms: .* -> .* ms)")


def key_lines(text):
    return [l.rstrip() for l in text.splitlines() if KEEP.match(l)]


class Smoke:
    """Runs bench_all.main in-process against temp state; restores every patch in finally."""

    def __init__(self, ba, td):
        self.ba = ba
        self.ledger = Path(td) / "ledger.json"
        self.value = [10.0]
        self.td = td

    def floors(self, name, default_mb, ceiling):
        p = Path(self.td) / name
        p.write_text(json.dumps({"default": default_mb, "claude_process": {"ceiling": ceiling}}),
                     encoding="utf-8")
        return p

    def run(self, value, floors=None):
        ba = self.ba
        self.value[0] = value
        argv = ["--quick"] + (["--floors", str(floors)] if floors is not None else [])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ba.main(argv)
        entries = json.loads(self.ledger.read_text(encoding="utf-8"))
        return rc, buf.getvalue(), entries[-1], len(entries)


def verdict_of(entry):
    return (entry.get("verdicts") or {}).get("never_again_ms") or {}


def forced_red(root, ba):
    real_ledger = root / "vault" / "benchmarks" / "ledger.json"
    real_floors = root / "vault" / "config" / "resource-floors.json"
    h0 = (sha256_of(real_ledger), sha256_of(real_floors))
    print("step0 real ledger sha256=%s" % h0[0])
    print("step0 real floors sha256=%s" % h0[1])
    claims = []

    def claim(name, ok, why):
        claims.append((name, bool(ok)))
        print("%s %s: %s" % ("PASS" if ok else "FAIL", name, why))

    claim("SMOKE-PLANE", plane_cases_ok(False) and plane_line(platform.node(), sys.platform).startswith(
        "plane: GEX44"), "plane_line pins four pairs and names this host GEX44")

    saved = (ba.LEDGER_PATH, ba.ALL_BENCHES, ba.get_head_commit)
    exit_code = None
    td = tempfile.mkdtemp(prefix="smoke_pressure_")
    try:
        sm = Smoke(ba, td)
        ba.LEDGER_PATH = sm.ledger
        ba.ALL_BENCHES = [("never_again", lambda: {"never_again_ms": sm.value[0]})]
        ba.get_head_commit = lambda: "smoke"
        print("temp ledger: %s" % sm.ledger)
        floors_count = sm.floors("floors_count.json", 1, 1)
        floors_ram = sm.floors("floors_ram.json", 1000000000, 1000000)
        print("temp floors (count pole): %s" % floors_count)
        print("temp floors (RAM pole): %s" % floors_ram)
        declared = real_floors

        # step 2: three control runs under the declared floors
        print("step2 control runs (stub 10.0, declared floors, 3 seeded runs)")
        classes = []
        for i in range(3):
            rc, out, e, n = sm.run(10.0)
            hs = e.get("host_state") or {}
            classes.append(hs.get("pressure"))
            print("  run %d rc=%d pressure=%s ram_mb=%s count=%s source=%s" % (
                i + 1, rc, hs.get("pressure"), hs.get("available_mb"), hs.get("claude_count"),
                hs.get("claude_count_source")))
            if i == 0 and hs.get("pressure") != "GREEN":
                print("live host class: %s reasons=%s" % (hs.get("pressure"),
                                                          ",".join(hs.get("pressure_reasons") or [])))
                print("live host is not GREEN; no control can be built")
                exit_code = 5
                return 5, claims, h0
        live_green = all(c == "GREEN" for c in classes)
        claim("SMOKE-LIVE-GREEN", live_green, "classes of the three control entries %s from the shipped "
              "read_host_state under the declared floors (%s)" % (classes, declared.name))

        # step 3: GREEN control with the same data that the RED runs will use
        rc, out, e, n = sm.run(18.0)
        v = verdict_of(e)
        print("step3 control GREEN run (stub 18.0 vs window of 10.0)")
        for l in key_lines(out):
            print("  " + l)
        claim("SMOKE-CONTROL-REGRESSES", v.get("regressed") is True and rc == 1 and "REGRESSIONS (" in out,
              "regressed=%s rc=%s REGRESSIONS block=%s" % (v.get("regressed"), rc, "REGRESSIONS (" in out))
        green_after_control = n

        def red_step(label, floors, want_reason, other_reason):
            rc_, out_, e_, n_ = sm.run(18.0, floors)
            hs_ = e_.get("host_state") or {}
            v_ = verdict_of(e_)
            low = out_.lower()
            print("%s (stub 18.0, same data as the control)" % label)
            print("  host_state: pressure=%s reasons=%s count=%s ram_mb=%s" % (
                hs_.get("pressure"), ",".join(hs_.get("pressure_reasons") or []),
                hs_.get("claude_count"), hs_.get("available_mb")))
            print("  verdict: regressed=%s evidence_sufficient=%s met_target=%s" % (
                v_.get("regressed"), v_.get("evidence_sufficient"), v_.get("met_target")))
            for l in key_lines(out_):
                print("  " + l)
            ok_ = (hs_.get("pressure") == "RED"
                   and want_reason in (hs_.get("pressure_reasons") or [])
                   and other_reason not in (hs_.get("pressure_reasons") or [])
                   and v_.get("regressed") is None and v_.get("evidence_sufficient") is False
                   and "INCONCLUSIVE" in out_ and "HOST PRESSURE: RED" in out_
                   and "no regressions" not in low and "REGRESSIONS (" not in out_
                   and rc_ == 0 and n_ == green_after_control + (1 if label.startswith("step4") else 2))
            return ok_, rc_, n_

        ok4, rc4, n4 = red_step("step4 forced RED by the count pole", floors_count,
                                "claude_count_over_ceiling", "ram_below_floor")
        claim("SMOKE-FORCED-RED-COUNT", ok4, "RED via claude_count_over_ceiling only, regressed None, "
              "evidence_sufficient False, INCONCLUSIVE printed, no REGRESSIONS block, rc=%s, entry kept "
              "(ledger entries=%s)" % (rc4, n4))
        ok5, rc5, n5 = red_step("step5 forced RED by the RAM pole", floors_ram,
                                "ram_below_floor", "claude_count_over_ceiling")
        claim("SMOKE-FORCED-RED-RAM", ok5, "RED via ram_below_floor only, same checks, rc=%s, entry kept "
              "(ledger entries=%s)" % (rc5, n5))

        # step 6: next GREEN run excludes the RED entries
        rc6, out6, e6, n6 = sm.run(10.0)
        print("step6 GREEN run after the RED entries (stub 10.0, declared floors)")
        for l in key_lines(out6):
            print("  " + l)
        wl = [l for l in out6.splitlines() if l.startswith("REGRESSION WINDOW:")]
        m = re.search(r"WINDOW: (\d+) matched entries .*under_pressure=(\d+)", wl[0]) if wl else None
        matched, under = (int(m.group(1)), int(m.group(2))) if m else (None, None)
        v6 = verdict_of(e6)
        claim("SMOKE-RED-EXCLUDED-FROM-WINDOW",
              m is not None and under == 2 and matched == 4 and e6.get("host_state", {}).get("pressure") == "GREEN",
              "window matched=%s under_pressure=%s (4 GREEN entries: 3 controls and the 18.0 control; 2 RED "
              "entries excluded), this run's own regressed=%s" % (matched, under, v6.get("regressed")))
    finally:
        ba.LEDGER_PATH, ba.ALL_BENCHES, ba.get_head_commit = saved
        restored = (ba.LEDGER_PATH, ba.ALL_BENCHES, ba.get_head_commit) == saved
        import shutil
        shutil.rmtree(td, ignore_errors=True)
        assert restored, "bench_all patches not restored"
    h1 = (sha256_of(real_ledger), sha256_of(real_floors))
    print("step7 real ledger sha256=%s" % h1[0])
    print("step7 real floors sha256=%s" % h1[1])
    claim("SMOKE-REAL-FILES-UNTOUCHED", h0 == h1 and ba.LEDGER_PATH == real_ledger,
          "sha256 of vault/benchmarks/ledger.json and vault/config/resource-floors.json equal before and "
          "after; bench_all.LEDGER_PATH restored to the real path")
    return exit_code if exit_code is not None else 0, claims, h0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest-plane" in argv:
        return selftest_plane()
    if "--live" not in argv and "--forced-red" not in argv:
        print("usage: smoke_pressure.py --selftest-plane | --live | --forced-red")
        return 64
    line = plane_line(platform.node(), sys.platform)
    print(line)
    if not line.startswith("plane: GEX44 "):
        print("plane is not GEX44: no reading taken")
        return 3
    root = repo_root()
    ra = load_by_path("smoke_ra", root / "tools" / "resource_admission.py")
    if "--live" in argv:
        live_reading(root, ra)
        return 0
    ba = load_by_path("smoke_ba", root / "tools" / "bench_all.py")
    code, claims, _h0 = forced_red(root, ba)
    if code == 5:
        return 5
    passed = sum(1 for _n, ok in claims if ok)
    total = len(claims)
    print("SMOKE_PASS=%d/%d  threshold=%d/%d" % (passed, total, EXPECTED, EXPECTED))
    if total != EXPECTED:
        print("FAIL count mismatch: ran %d claims, expected %d" % (total, EXPECTED))
        return 1
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
